import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.app.session import AppSession
from app.models.app.user import AppUser
from app.repositories.auth_repository import AuthRepository
from app.validators.auth import normalize_username, validate_password, validate_role
from app.core.jwt import create_access_token, verify_token

logger = logging.getLogger("radiusflow.auth")

_DUMMY_PASSWORD_HASH = generate_password_hash(
    "Dummy-Password-Only-For-Timing-Checks-9!",
    method="scrypt",
)


class AuthenticationError(Exception):
    pass


class InvalidCredentialsError(AuthenticationError):
    pass


class DuplicateUserError(AuthenticationError):
    pass


@dataclass(frozen=True)
class AuthenticatedSession:
    user: AppUser
    session: AppSession


class AuthService:
    def __init__(self, db, session_hours: int = 12):
        self.db = db
        self.repository = AuthRepository(db)
        self.session_hours = max(1, min(session_hours, 168))

    def create_user(self, username: str, password: str, role: str = "viewer") -> AppUser:
        normalized_username = normalize_username(username)
        validated_password = validate_password(password)
        validated_role = validate_role(role)

        if self.repository.get_user_by_username(normalized_username):
            raise DuplicateUserError("An application user with that username already exists.")

        user = AppUser(
            username=normalized_username,
            password_hash=generate_password_hash(validated_password, method="scrypt"),
            role=validated_role,
            is_active=True,
        )
        self.repository.add_user(user)
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateUserError(
                "An application user with that username already exists."
            ) from exc
        except Exception:
            self.db.rollback()
            logger.exception("Failed to create application user")
            raise

    def authenticate(self, username: str, password: str) -> AppUser:
        input_str = (username or "").strip().lower()

        # 1. Check enterprise radiusflow.admin_users table (email + Argon2)
        try:
            from app.models.radiusflow.admin_user import AdminUser
            admin_user = (
                self.db.query(AdminUser)
                .filter(AdminUser.email == input_str, AdminUser.deleted_at.is_(None))
                .first()
            )
            if admin_user:
                password_valid = False
                if admin_user.password_hash.startswith("$argon2"):
                    try:
                        from argon2 import PasswordHasher
                        PasswordHasher().verify(admin_user.password_hash, password or "")
                        password_valid = True
                    except Exception:
                        password_valid = False
                else:
                    password_valid = check_password_hash(admin_user.password_hash, password or "")

                if password_valid and admin_user.is_active:
                    admin_user.last_login_at = self._now()
                    self.db.commit()
                    role_name = admin_user.roles[0].name if admin_user.roles else "super_admin"
                    return AppUser(
                        id=admin_user.id,
                        username=admin_user.email,
                        password_hash=admin_user.password_hash,
                        role=role_name,
                        is_active=admin_user.is_active,
                        last_login_at=admin_user.last_login_at,
                    )
        except Exception:
            self.db.rollback()

        # 2. Fallback to legacy app_users table
        try:
            normalized_username = normalize_username(username)
        except ValueError:
            normalized_username = ""

        user = self.repository.get_user_by_username(normalized_username)
        password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
        password_is_valid = check_password_hash(password_hash, password or "")

        if not user or not password_is_valid or not user.is_active:
            logger.warning("Rejected management login for username=%r", normalized_username)
            raise InvalidCredentialsError("Invalid username or password.")

        user.last_login_at = self._now()
        try:
            self.db.commit()
            return user
        except Exception:
            self.db.rollback()
            logger.exception("Failed to update application user login timestamp")
            raise

    def start_session(
        self,
        user: AppUser,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        raw_token = secrets.token_urlsafe(48)
        now = self._now()
        auth_session = AppSession(
            user_id=user.id,
            token_hash=self._hash_token(raw_token),
            ip_address=(ip_address or "")[:45] or None,
            user_agent=(user_agent or "")[:255] or None,
            last_seen_at=now,
            expires_at=now + timedelta(hours=self.session_hours),
        )
        self.repository.add_session(auth_session)
        try:
            self.db.commit()
            return raw_token
        except Exception:
            self.db.rollback()
            logger.exception("Failed to create management session")
            raise

    def resolve_session(self, raw_token: str | None) -> AuthenticatedSession | None:
        if not raw_token:
            return None

        auth_session = self.repository.get_session_by_hash(self._hash_token(raw_token))
        if not auth_session or auth_session.revoked_at is not None:
            return None

        now = self._now()
        if self._as_utc(auth_session.expires_at) <= now or not auth_session.user.is_active:
            self.repository.revoke_session(auth_session, now)
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                logger.exception("Failed to revoke an expired management session")
            return None

        last_seen_at = self._as_utc(auth_session.last_seen_at)
        if last_seen_at <= now - timedelta(minutes=5):
            auth_session.last_seen_at = now
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                logger.exception("Failed to update management session activity")

        return AuthenticatedSession(user=auth_session.user, session=auth_session)

    def revoke_session(self, raw_token: str | None) -> None:
        if not raw_token:
            return
        auth_session = self.repository.get_session_by_hash(self._hash_token(raw_token))
        if not auth_session or auth_session.revoked_at is not None:
            return
        self.repository.revoke_session(auth_session, self._now())
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception("Failed to revoke management session")
            raise

    def change_password(self, user: AppUser, new_password: str) -> None:
        user.password_hash = generate_password_hash(
            validate_password(new_password),
            method="scrypt",
        )
        self.repository.revoke_user_sessions(user.id, self._now())
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception("Failed to change application user password")
            raise

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


__all__ = [
    "AuthenticatedSession",
    "AuthenticationError",
    "AuthService",
    "DuplicateUserError",
    "InvalidCredentialsError",
    "create_access_token",
    "verify_token",
]
