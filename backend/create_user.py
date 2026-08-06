"""
RadiusFlow Management User CLI Tool

Use this script to safely create or list management accounts (app_users).
Usage:
  python create_user.py --username admin --password MyPassword123! --role admin
  python create_user.py --list
"""
import sys
import argparse
from database import SessionLocal
from app.services.auth_service import AuthService, DuplicateUserError


def main():
    parser = argparse.ArgumentParser(description="RadiusFlow Management User CLI")
    parser.add_argument("--username", "-u", type=str, help="Management username")
    parser.add_argument("--password", "-p", type=str, help="Management password")
    parser.add_argument(
        "--role", "-r", type=str, default="admin",
        choices=["admin", "super_admin", "network_admin", "operator", "viewer"],
        help="Management role (default: admin)",
    )
    parser.add_argument("--list", "-l", action="store_true", help="List all existing management users")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        service = AuthService(db)
        if args.list:
            users = service.repository.list_users()
            print(f"\nRegistered Management Users ({len(users)}):")
            print("-" * 50)
            for u in users:
                status = "Active" if u.is_active else "Disabled"
                last_login = u.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if u.last_login_at else "Never"
                print(f" • Username: {u.username:<15} Role: {u.role:<12} Status: {status:<8} Last Login: {last_login}")
            print("-" * 50)
            return

        if not args.username or not args.password:
            print("Error: Both --username and --password are required to create a user.")
            print("Example: python create_user.py -u admin -p MySecurePass123! -r admin")
            sys.exit(1)

        user = service.create_user(args.username, args.password, args.role)
        print(f"\n Successfully created management user '{user.username}' with role '{user.role}'.\n")
    except DuplicateUserError:
        print(f"\n Error: User '{args.username}' already exists in app_users.\n")
        sys.exit(1)
    except Exception as exc:
        print(f"\n Unexpected error: {exc}\n")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
