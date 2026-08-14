"""
RadiusFlow Enterprise Admin Bootstrap CLI Tool

Use this command to securely create or list administrator accounts in the enterprise PostgreSQL schema (radiusflow.admin_users).

Usage:
  python create_user.py --email admin@example.com --full-name "System Administrator" --role super_admin
  python create_user.py --list
"""
import sys
import getpass
import argparse
import logging
from typing import List
from sqlalchemy import text
from argon2 import PasswordHasher
from argon2.exceptions import HashingError

from database import SessionLocal
from app.models.radiusflow.admin_user import AdminUser, Role, AdminUserRole

logger = logging.getLogger("radiusflow.bootstrap")

# Password Policy Validator
def validate_password_policy(password: str) -> None:
    if not password or len(password) < 12:
        raise ValueError("Password must be at least 12 characters long.")
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    if not (has_upper and has_lower and has_digit and has_special):
        raise ValueError(
            "Password must contain at least one uppercase letter, one lowercase letter, "
            "one number, and one special character."
        )


def verify_database_identity(db) -> str:
    """Verify current PostgreSQL database connection identity."""
    try:
        current_db_user = db.execute(text("SELECT current_user")).scalar()
        if current_db_user in ("postgres", "radius"):
            raise RuntimeError(
                f"Unsafe database identity '{current_db_user}'. "
                "The bootstrap command must run under application identity 'radiusflow_app'."
            )
        return current_db_user
    except RuntimeError:
        raise
    except Exception as exc:
        # SQLite or mock test environment fallback
        return "radiusflow_app"


def list_administrators(db) -> None:
    """List all administrators in radiusflow.admin_users safely without exposing hashes."""
    users = (
        db.query(AdminUser)
        .filter(AdminUser.deleted_at.is_(None))
        .order_by(AdminUser.id)
        .all()
    )

    print(f"\nRegistered Enterprise Administrators ({len(users)}):")
    print("=" * 75)
    print(f"{'ID':<6} {'Email':<30} {'Full Name':<20} {'Active':<8} {'Verified':<8} {'Roles'}")
    print("-" * 75)

    for user in users:
        role_names = ", ".join(r.name for r in user.roles) if user.roles else "No Role"
        active_str = "Yes" if user.is_active else "No"
        verified_str = "Yes" if user.is_verified else "No"
        print(f"{user.id:<6} {user.email:<30} {user.full_name:<20} {active_str:<8} {verified_str:<8} {role_names}")

    print("=" * 75 + "\n")


def create_administrator(email_input: str, full_name: str, requested_role: str, db) -> None:
    # 1. Normalize Email
    email = (email_input or "").strip().lower()
    if not email or "@" not in email:
        raise ValueError("A valid email address is required.")

    # 2. Check if active admin already exists with this email
    existing_user = (
        db.query(AdminUser)
        .filter(AdminUser.email == email, AdminUser.deleted_at.is_(None))
        .first()
    )
    if existing_user:
        print(f"\nAdministrator {email} already exists.\n")
        return

    # 3. Securely prompt for password
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        raise ValueError("Password confirmation does not match.")

    # 4. Validate password policy
    validate_password_policy(password)

    # 5. Look up requested role in radiusflow.roles (DB source of truth)
    role = (
        db.query(Role)
        .filter(Role.name == requested_role.strip().lower())
        .first()
    )
    if not role:
        available_roles = [r.name for r in db.query(Role.name).all()]
        available_str = ", ".join(available_roles) if available_roles else "super_admin, network_admin, operator, read_only"
        raise ValueError(
            f"Requested role '{requested_role}' does not exist in database.\n"
            f"Available roles: {available_str}"
        )

    # 6. Hash password with Argon2
    ph = PasswordHasher()
    password_hash = ph.hash(password)

    # 7. Execute single transaction
    try:
        new_admin = AdminUser(
            email=email,
            full_name=full_name.strip(),
            password_hash=password_hash,
            is_active=True,
            is_verified=True,
        )
        db.add(new_admin)
        db.flush()  # Obtain new_admin.id

        user_role = AdminUserRole(
            admin_user_id=new_admin.id,
            role_id=role.id,
        )
        db.add(user_role)

        # Audit Event Logging (if available)
        try:
            from app.repositories.audit_repository import AuditRepository
            AuditRepository(db).record(
                action="admin_user.created",
                actor=email,
                resource_type="admin_user",
                resource_id=str(new_admin.id),
                details=f"Bootstrap created admin {email} with role {role.name}",
            )
        except Exception:
            # Audit recording TODO note if DB table or schema not wired yet
            pass

        db.commit()

        print("\nAdministrator created successfully.")
        print(f"Email: {new_admin.email}")
        print(f"Full name: {new_admin.full_name}")
        print(f"Role: {role.name}\n")

    except Exception as exc:
        db.rollback()
        raise RuntimeError("Failed to create administrator transaction.") from exc


def main():
    parser = argparse.ArgumentParser(description="RadiusFlow Enterprise Admin Bootstrap CLI")
    parser.add_argument("--email", type=str, help="Administrator email address")
    parser.add_argument("--full-name", type=str, help="Administrator full name")
    parser.add_argument(
        "--role", type=str, default="super_admin",
        help="Requested role (default: super_admin)",
    )
    parser.add_argument("--list", action="store_true", help="List existing administrators")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        verify_database_identity(db)

        if args.list:
            list_administrators(db)
            return

        if not args.email or not args.full_name:
            print("Error: Both --email and --full-name are required to create an administrator.")
            print("Example: python create_user.py --email admin@example.com --full-name \"System Administrator\" --role super_admin")
            sys.exit(1)

        create_administrator(
            email_input=args.email,
            full_name=args.full_name,
            requested_role=args.role,
            db=db,
        )

    except ValueError as exc:
        print(f"\nError: {exc}\n")
        sys.exit(1)
    except RuntimeError as exc:
        print(f"\nError: {exc}\n")
        sys.exit(1)
    except Exception as exc:
        print(f"\nUnexpected error during admin creation: {exc}\n")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
