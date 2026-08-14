"""
RadiusFlow AuthService
======================
Handles authentication and session management for two user stores:

  1. Enterprise admins  → radiusflow.admin_users + radiusflow.admin_sessions
  2. Legacy app users   → app_users + app_sessions  (FreeRADIUS subscriber mgmt)

Enterprise and legacy session paths are fully separated.  Enterprise admins
never touch app_users or app_sessions; legacy users never touch the radiusflow
schema.  The FK on app_sessions.user_id → app_users.id is preserved untouched.
"""
import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy import text as sa_text
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.app.session import AppSession
from app.models.app.user import AppUser
from app.models.radiusflow.admin_session import AdminSession
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


@dataclass
class EnterpriseUser:
    """
    Lightweight representation of an authenticated enterprise admin.
    Never persisted; created transiently during login.
    Shares the same field names as AppUser where auth.py inspects them
    (id, username, role, is_active) so resolve_session() can return a
    unified object.
    """
    id: int
    username: str       # holds the email address
    role: str
    is_active: bool
    password_hash: str = field(default="", repr=False)
    last_login_at: datetime | None = None
    # Sentinel so start_session() knows which session table to use
    _enterprise: bool = field(default=True, init=False)


@dataclass(frozen=True)
class AuthenticatedSession:
    """Returned by resolve_session() regardless of session table used."""
    user: AppUser | EnterpriseUser
    session: AppSession | AdminSession


class AuthService:
    def __init__(self, db, session_hours: int = 12):
        self.db = db
        self.repository = AuthRepository(db)
        self.session_hours = max(1, min(session_hours, 168))

    # ------------------------------------------------------------------ #
    # User creation (legacy app_users only)                               #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # Authentication                                                       #
    # ------------------------------------------------------------------ #

    def authenticate(self, username: str, password: str) -> AppUser | EnterpriseUser:
        input_str = (username or "").strip().lower()
        logger.info("authenticate: input_str=%r", input_str)

        # ── 1. Enterprise radiusflow.admin_users ───────────────────────
        try:
            from app.models.radiusflow.admin_user import AdminUser
            admin_user = (
                self.db.query(AdminUser)
                .filter(AdminUser.email == input_str, AdminUser.deleted_at.is_(None))
                .first()
            )
            logger.info("authenticate: admin_user lookup=%r", admin_user)

            if admin_user:
                password_valid = False
                if admin_user.password_hash.startswith("$argon2"):
                    try:
                        from argon2 import PasswordHasher
                        PasswordHasher().verify(admin_user.password_hash, password or "")
                        password_valid = True
                        logger.info("authenticate: Argon2 verify OK")
                    except Exception as e:
                        logger.warning("authenticate: Argon2 verify FAIL: %s", e)
                else:
                    password_valid = check_password_hash(
                        admin_user.password_hash, password or ""
                    )
                    logger.info("authenticate: scrypt check=%r", password_valid)

                if not password_valid or not admin_user.is_active:
                    raise InvalidCredentialsError("Invalid email or password.")

                # Fetch role via direct SQL (avoids ORM relationship column issues)
                role_row = self.db.execute(
                    sa_text(
                        "SELECT r.name FROM radiusflow.roles r "
                        "JOIN radiusflow.admin_user_roles ur ON ur.role_id = r.id "
                        "WHERE ur.admin_user_id = :uid LIMIT 1"
                    ),
                    {"uid": admin_user.id},
                ).fetchone()
                role_name = role_row[0] if role_row else "super_admin"

                admin_user.last_login_at = self._now()
                self.db.commit()
                logger.info("authenticate: enterprise OK email=%r role=%r", input_str, role_name)
                return EnterpriseUser(
                    id=admin_user.id,
                    username=admin_user.email,
                    role=role_name,
                    is_active=admin_user.is_active,
                    last_login_at=admin_user.last_login_at,
                )

        except InvalidCredentialsError:
            raise
        except Exception as exc:
            logger.exception("authenticate: enterprise lookup error: %s", exc)
            self.db.rollback()

        # ── 2. Legacy app_users fallback ───────────────────────────────
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
            logger.exception("Failed to update legacy user login timestamp")
            raise

    # ------------------------------------------------------------------ #
    # Session management                                                   #
    # ------------------------------------------------------------------ #

    def start_session(
        self,
        user: AppUser | EnterpriseUser,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        """
        Create a session row and return the raw bearer token.
        Enterprise admins → radiusflow.admin_sessions
        Legacy users      → app_sessions
        """
        raw_token = secrets.token_urlsafe(48)
        now = self._now()
        expires_at = now + timedelta(hours=self.session_hours)
        token_hash = self._hash_token(raw_token)
        ip = (ip_address or "")[:45] or None
        ua = (user_agent or "")[:255] or None

        if getattr(user, "_enterprise", False):
            # ── Enterprise path ────────────────────────────────────────
            session = AdminSession(
                admin_user_id=user.id,
                token_hash=token_hash,
                ip_address=ip,
                user_agent=ua,
                role_name=user.role,
                last_seen_at=now,
                expires_at=expires_at,
            )
            self.repository.add_enterprise_session(session)
        else:
            # ── Legacy path ────────────────────────────────────────────
            session = AppSession(
                user_id=user.id,
                token_hash=token_hash,
                ip_address=ip,
                user_agent=ua,
                last_seen_at=now,
                expires_at=expires_at,
            )
            self.repository.add_session(session)

        try:
            self.db.commit()
            logger.info(
                "start_session: created %s session for user_id=%s",
                "enterprise" if getattr(user, "_enterprise", False) else "legacy",
                user.id,
            )
            return raw_token
        except Exception:
            self.db.rollback()
            logger.exception("Failed to create session")
            raise

    def resolve_session(self, raw_token: str | None) -> AuthenticatedSession | None:
        """
        Resolve a bearer token to an AuthenticatedSession.
        Tries enterprise admin_sessions first, then legacy app_sessions.
        """
        if not raw_token:
            return None

        token_hash = self._hash_token(raw_token)
        now = self._now()

        # ── 1. Try enterprise session ──────────────────────────────────
        ent_session = self.repository.get_enterprise_session_by_hash(token_hash)
        if ent_session:
            if ent_session.revoked_at is not None:
                return None
            if self._as_utc(ent_session.expires_at) <= now:
                self.repository.revoke_enterprise_session(ent_session, now)
                self._safe_commit("revoke expired enterprise session")
                return None

            admin_user = ent_session.admin_user
            if not admin_user or not admin_user.is_active:
                return None

            # Refresh last_seen_at if stale > 5 min
            if self._as_utc(ent_session.last_seen_at) <= now - timedelta(minutes=5):
                ent_session.last_seen_at = now
                self._safe_commit("update enterprise session last_seen_at")

            # Build a transient EnterpriseUser from session data
            ent_user = EnterpriseUser(
                id=admin_user.id,
                username=admin_user.email,
                role=ent_session.role_name,
                is_active=admin_user.is_active,
                last_login_at=admin_user.last_login_at,
            )
            return AuthenticatedSession(user=ent_user, session=ent_session)

        # ── 2. Try legacy session ──────────────────────────────────────
        legacy_session = self.repository.get_session_by_hash(token_hash)
        if not legacy_session or legacy_session.revoked_at is not None:
            return None

        if (
            self._as_utc(legacy_session.expires_at) <= now
            or not legacy_session.user.is_active
        ):
            self.repository.revoke_session(legacy_session, now)
            self._safe_commit("revoke expired legacy session")
            return None

        if self._as_utc(legacy_session.last_seen_at) <= now - timedelta(minutes=5):
            legacy_session.last_seen_at = now
            self._safe_commit("update legacy session last_seen_at")

        return AuthenticatedSession(user=legacy_session.user, session=legacy_session)

    def revoke_session(self, raw_token: str | None) -> None:
        """
        Revoke a session by its raw bearer token.
        Tries enterprise admin_sessions first, then legacy app_sessions.
        """
        if not raw_token:
            return
        token_hash = self._hash_token(raw_token)
        now = self._now()

        # Try enterprise first
        ent_session = self.repository.get_enterprise_session_by_hash(token_hash)
        if ent_session and ent_session.revoked_at is None:
            self.repository.revoke_enterprise_session(ent_session, now)
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                logger.exception("Failed to revoke enterprise session")
                raise
            return

        # Fall back to legacy
        legacy_session = self.repository.get_session_by_hash(token_hash)
        if not legacy_session or legacy_session.revoked_at is not None:
            return
        self.repository.revoke_session(legacy_session, now)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception("Failed to revoke legacy session")
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

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _safe_commit(self, context: str) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception("Failed to commit: %s", context)

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
    "EnterpriseUser",
    "InvalidCredentialsError",
    "create_access_token",
    "verify_token",
]
