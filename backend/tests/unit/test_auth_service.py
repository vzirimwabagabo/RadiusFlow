import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from werkzeug.security import check_password_hash

from app.models.app.session import AppSession
from app.models.app.user import AppUser
from app.services.auth_service import (
    AuthService,
    DuplicateUserError,
    InvalidCredentialsError,
)
from database import Base


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db = self.session_factory()
        self.service = AuthService(self.db, session_hours=12)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_creates_normalized_user_with_scrypt_password_hash(self):
        user = self.service.create_user(
            "Admin.User",
            "Correct-Horse-9-Battery",
            "admin",
        )

        self.assertEqual(user.username, "admin.user")
        self.assertEqual(user.role, "admin")
        self.assertNotEqual(user.password_hash, "Correct-Horse-9-Battery")
        self.assertTrue(
            check_password_hash(user.password_hash, "Correct-Horse-9-Battery")
        )

    def test_rejects_duplicate_application_username(self):
        self.service.create_user("operator", "Operator-Password-9!", "operator")

        with self.assertRaises(DuplicateUserError):
            self.service.create_user("OPERATOR", "Another-Password-8!", "operator")

    def test_authenticates_and_revokes_database_backed_session(self):
        user = self.service.create_user("admin", "Admin-Password-9!", "admin")
        authenticated = self.service.authenticate("ADMIN", "Admin-Password-9!")
        token = self.service.start_session(
            authenticated,
            ip_address="192.0.2.20",
            user_agent="test-client",
        )

        stored_session = self.db.query(AppSession).one()
        self.assertNotEqual(stored_session.token_hash, token)
        self.assertEqual(stored_session.user_id, user.id)

        resolved = self.service.resolve_session(token)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.user.username, "admin")

        self.service.revoke_session(token)
        self.assertIsNone(self.service.resolve_session(token))

    def test_rejects_invalid_password_and_inactive_user(self):
        user = self.service.create_user("viewer", "Viewer-Password-9!", "viewer")

        with self.assertRaises(InvalidCredentialsError):
            self.service.authenticate("viewer", "incorrect-password")

        user.is_active = False
        self.db.commit()
        with self.assertRaises(InvalidCredentialsError):
            self.service.authenticate("viewer", "Viewer-Password-9!")

    def test_password_change_revokes_existing_sessions(self):
        user = self.service.create_user("operator", "Operator-Password-9!", "operator")
        token = self.service.start_session(user)

        self.service.change_password(user, "Changed-Password-8!")

        self.assertIsNone(self.service.resolve_session(token))
        with self.assertRaises(InvalidCredentialsError):
            self.service.authenticate("operator", "Operator-Password-9!")
        self.assertEqual(
            self.service.authenticate("operator", "Changed-Password-8!").id,
            user.id,
        )


if __name__ == "__main__":
    unittest.main()
