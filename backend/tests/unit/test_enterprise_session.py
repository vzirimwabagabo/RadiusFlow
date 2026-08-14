import unittest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from app.models.radiusflow.admin_user import AdminUser, Role, AdminUserRole
from app.models.radiusflow.admin_session import AdminSession
from app.models.app.user import AppUser
from app.models.app.session import AppSession
from app.services.auth_service import AuthService, EnterpriseUser, InvalidCredentialsError
from argon2 import PasswordHasher


class TestEnterpriseSessionArchitecture(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed roles
        self.super_admin_role = Role(id=1, name="super_admin")
        self.db.add(self.super_admin_role)
        self.db.commit()

        # Seed enterprise admin
        ph = PasswordHasher()
        self.admin = AdminUser(
            id=10,
            email="enterprise.admin@example.com",
            full_name="Enterprise Admin",
            password_hash=ph.hash("EnterprisePass123!"),
            is_active=True,
            is_verified=True,
        )
        self.db.add(self.admin)
        self.db.flush()

        self.user_role = AdminUserRole(admin_user_id=self.admin.id, role_id=self.super_admin_role.id)
        self.db.add(self.user_role)
        self.db.commit()

        self.auth_service = AuthService(self.db, session_hours=12)

    def tearDown(self):
        self.db.close()

    def test_successful_enterprise_login(self):
        user = self.auth_service.authenticate("enterprise.admin@example.com", "EnterprisePass123!")
        self.assertIsInstance(user, EnterpriseUser)
        self.assertEqual(user.id, 10)
        self.assertEqual(user.username, "enterprise.admin@example.com")
        self.assertEqual(user.role, "super_admin")
        self.assertTrue(user._enterprise)

    def test_enterprise_session_creation(self):
        user = self.auth_service.authenticate("enterprise.admin@example.com", "EnterprisePass123!")
        raw_token = self.auth_service.start_session(user, ip_address="192.168.1.1", user_agent="PyTest")

        self.assertIsNotNone(raw_token)
        self.assertGreater(len(raw_token), 30)

        # Verify row in admin_sessions
        admin_session = self.db.query(AdminSession).filter_by(admin_user_id=10).first()
        self.assertIsNotNone(admin_session)
        self.assertEqual(admin_session.ip_address, "192.168.1.1")
        self.assertEqual(admin_session.role_name, "super_admin")

        # Verify NO row inserted in app_sessions
        app_sessions_count = self.db.query(AppSession).count()
        self.assertEqual(app_sessions_count, 0)

        # Verify NO row inserted in app_users
        app_users_count = self.db.query(AppUser).count()
        self.assertEqual(app_users_count, 0)

    def test_current_user_resolution(self):
        user = self.auth_service.authenticate("enterprise.admin@example.com", "EnterprisePass123!")
        raw_token = self.auth_service.start_session(user)

        resolved = self.auth_service.resolve_session(raw_token)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.user.id, 10)
        self.assertEqual(resolved.user.username, "enterprise.admin@example.com")
        self.assertEqual(resolved.user.role, "super_admin")
        self.assertIsInstance(resolved.session, AdminSession)

    def test_logout_and_revocation(self):
        user = self.auth_service.authenticate("enterprise.admin@example.com", "EnterprisePass123!")
        raw_token = self.auth_service.start_session(user)

        # Active initially
        resolved = self.auth_service.resolve_session(raw_token)
        self.assertIsNotNone(resolved)

        # Revoke
        self.auth_service.revoke_session(raw_token)

        # Now resolution fails
        resolved_after = self.auth_service.resolve_session(raw_token)
        self.assertIsNone(resolved_after)

        admin_session = self.db.query(AdminSession).filter_by(admin_user_id=10).first()
        self.assertIsNotNone(admin_session.revoked_at)

    def test_expired_session_handling(self):
        user = self.auth_service.authenticate("enterprise.admin@example.com", "EnterprisePass123!")
        raw_token = self.auth_service.start_session(user)

        # Manually expire the session in DB
        admin_session = self.db.query(AdminSession).filter_by(admin_user_id=10).first()
        admin_session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        self.db.commit()

        # Resolution should revoke and return None
        resolved = self.auth_service.resolve_session(raw_token)
        self.assertIsNone(resolved)

        admin_session_after = self.db.query(AdminSession).filter_by(admin_user_id=10).first()
        self.assertIsNotNone(admin_session_after.revoked_at)

    def test_no_app_users_and_no_app_sessions_for_enterprise_admin(self):
        user = self.auth_service.authenticate("enterprise.admin@example.com", "EnterprisePass123!")
        self.auth_service.start_session(user)

        self.assertEqual(self.db.query(AppUser).count(), 0)
        self.assertEqual(self.db.query(AppSession).count(), 0)
        self.assertEqual(self.db.query(AdminUser).count(), 1)
        self.assertEqual(self.db.query(AdminSession).count(), 1)


if __name__ == "__main__":
    unittest.main()
