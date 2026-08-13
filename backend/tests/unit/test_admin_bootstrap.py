import io
import sys
import unittest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from argon2 import PasswordHasher

from database import Base
from app.models.radiusflow.admin_user import AdminUser, Role, AdminUserRole
from app.models.app.user import AppUser
from create_user import (
    create_administrator,
    list_administrators,
    validate_password_policy,
)


class TestEnterpriseAdminBootstrap(unittest.TestCase):
    def setUp(self):
        # In-memory SQLite DB with schema_translate_map to map radiusflow schema -> default SQLite
        self.engine = create_engine(
            "sqlite:///:memory:",
            execution_options={"schema_translate_map": {"radiusflow": None}},
        )

        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed enterprise radiusflow.roles in test database
        self.super_role = Role(name="super_admin", description="Super Administrator")
        self.net_role = Role(name="network_admin", description="Network Administrator")
        self.db.add_all([self.super_role, self.net_role])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_validate_password_policy(self):
        # Valid password
        validate_password_policy("SecurePass123!")

        # Weak passwords
        with self.assertRaises(ValueError):
            validate_password_policy("short1!")  # Too short

        with self.assertRaises(ValueError):
            validate_password_policy("nouppercase123!")  # Missing upper

        with self.assertRaises(ValueError):
            validate_password_policy("NOLOWERCASE123!")  # Missing lower

        with self.assertRaises(ValueError):
            validate_password_policy("NoNumbersHere!")  # Missing digit

        with self.assertRaises(ValueError):
            validate_password_policy("NoSpecialChar123")  # Missing special

    @patch("getpass.getpass")
    def test_successful_administrator_creation(self, mock_getpass):
        mock_getpass.side_effect = ["ValidPassword123!", "ValidPassword123!"]

        create_administrator(
            email_input="Admin@Example.com",
            full_name="System Administrator",
            requested_role="super_admin",
            db=self.db,
        )

        # 1. User created with normalized email
        user = self.db.query(AdminUser).filter(AdminUser.email == "admin@example.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.full_name, "System Administrator")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)

        # 2. Password is encrypted with Argon2 (not stored plaintext)
        self.assertNotEqual(user.password_hash, "ValidPassword123!")
        ph = PasswordHasher()
        self.assertTrue(ph.verify(user.password_hash, "ValidPassword123!"))

        # 3. Role assignment created in admin_user_roles
        user_role = self.db.query(AdminUserRole).filter(AdminUserRole.admin_user_id == user.id).first()
        self.assertIsNotNone(user_role)
        self.assertEqual(user_role.role_id, self.super_role.id)
        self.assertEqual(user.roles[0].name, "super_admin")

    @patch("getpass.getpass")
    def test_duplicate_email_rejection(self, mock_getpass):
        mock_getpass.side_effect = ["ValidPassword123!", "ValidPassword123!"]

        # First creation
        create_administrator(
            email_input="admin@example.com",
            full_name="First Admin",
            requested_role="super_admin",
            db=self.db,
        )

        # Second creation should refuse duplicate
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            create_administrator(
                email_input="ADMIN@example.com",
                full_name="Duplicate Admin",
                requested_role="super_admin",
                db=self.db,
            )

        self.assertIn("already exists", stdout_capture.getvalue())

        # Verify only 1 admin user exists
        count = self.db.query(AdminUser).filter(AdminUser.email == "admin@example.com").count()
        self.assertEqual(count, 1)

    @patch("getpass.getpass")
    def test_invalid_role_rejection_and_rollback(self, mock_getpass):
        mock_getpass.side_effect = ["ValidPassword123!", "ValidPassword123!"]

        with self.assertRaises(ValueError) as ctx:
            create_administrator(
                email_input="newadmin@example.com",
                full_name="New Admin",
                requested_role="non_existent_role",
                db=self.db,
            )

        self.assertIn("does not exist in database", str(ctx.exception))

        # Ensure transaction was rolled back (no partial user created)
        user = self.db.query(AdminUser).filter(AdminUser.email == "newadmin@example.com").first()
        self.assertIsNone(user)

    @patch("getpass.getpass")
    def test_password_mismatch_rejection(self, mock_getpass):
        mock_getpass.side_effect = ["ValidPassword123!", "DifferentPassword123!"]

        with self.assertRaises(ValueError) as ctx:
            create_administrator(
                email_input="mismatch@example.com",
                full_name="Mismatch Admin",
                requested_role="super_admin",
                db=self.db,
            )

        self.assertIn("confirmation does not match", str(ctx.exception))

        # Ensure no user created
        user = self.db.query(AdminUser).filter(AdminUser.email == "mismatch@example.com").first()
        self.assertIsNone(user)

    @patch("getpass.getpass")
    def test_list_administrators_does_not_expose_hashes(self, mock_getpass):
        mock_getpass.side_effect = ["ValidPassword123!", "ValidPassword123!"]

        create_administrator(
            email_input="admin@example.com",
            full_name="System Administrator",
            requested_role="super_admin",
            db=self.db,
        )

        user = self.db.query(AdminUser).first()
        secret_hash = user.password_hash

        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            list_administrators(self.db)

        output = stdout_capture.getvalue()
        self.assertIn("admin@example.com", output)
        self.assertIn("System Administrator", output)
        self.assertIn("super_admin", output)
        # Secret hash must NOT be printed
        self.assertNotIn(secret_hash, output)

    def test_legacy_app_users_isolation(self):
        # Verify app_users table is empty and unaffected
        legacy_count = self.db.query(AppUser).count()
        self.assertEqual(legacy_count, 0)


if __name__ == "__main__":
    unittest.main()
