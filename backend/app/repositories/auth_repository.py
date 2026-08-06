from datetime import datetime

from app.models.app.session import AppSession
from app.models.app.user import AppUser
from app.repositories.base import BaseRepository


class AuthRepository(BaseRepository):
    def get_user_by_id(self, user_id: int):
        return self.db.query(AppUser).filter(AppUser.id == user_id).first()

    def get_user_by_username(self, username: str):
        return self.db.query(AppUser).filter(AppUser.username == username).first()

    def list_users(self):
        return self.db.query(AppUser).order_by(AppUser.username).all()

    def add_user(self, user: AppUser) -> None:
        self.db.add(user)

    def get_session_by_hash(self, token_hash: str):
        return (
            self.db.query(AppSession)
            .filter(AppSession.token_hash == token_hash)
            .first()
        )

    def add_session(self, auth_session: AppSession) -> None:
        self.db.add(auth_session)

    def revoke_session(self, auth_session: AppSession, revoked_at: datetime) -> None:
        auth_session.revoked_at = revoked_at

    def revoke_user_sessions(self, user_id: int, revoked_at: datetime) -> int:
        return (
            self.db.query(AppSession)
            .filter(
                AppSession.user_id == user_id,
                AppSession.revoked_at.is_(None),
            )
            .update({AppSession.revoked_at: revoked_at}, synchronize_session=False)
        )
