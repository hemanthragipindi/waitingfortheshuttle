import argparse
import getpass
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.enums import UserRole
from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.user import User


def create_admin() -> None:
    email_input = input("Administrator email: ").strip()
    try:
        email = str(TypeAdapter(EmailStr).validate_python(email_input)).casefold()
    except ValidationError:
        print("Enter a valid email address.", file=sys.stderr)
        raise SystemExit(2) from None

    full_name = input("Administrator full name: ").strip()
    if not full_name or len(full_name) > 120:
        print("Full name must be between 1 and 120 characters.", file=sys.stderr)
        raise SystemExit(2)

    password = getpass.getpass("Administrator password (12+ characters): ")
    if len(password) < 12 or len(password) > 128:
        print("Password must be between 12 and 128 characters.", file=sys.stderr)
        raise SystemExit(2)
    if password != getpass.getpass("Confirm password: "):
        print("Passwords do not match.", file=sys.stderr)
        raise SystemExit(2)

    with get_session_factory()() as session:
        if session.scalar(select(User.id).where(User.email == email)) is not None:
            print("An account with that email already exists.", file=sys.stderr)
            raise SystemExit(2)

        session.add(
            User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                role=UserRole.ADMIN.value,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            if session.scalar(select(User.id).where(User.email == email)) is not None:
                print("An account with that email already exists.", file=sys.stderr)
                raise SystemExit(2) from None
            raise

    print(f"Administrator account created for {email}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="P05 Shuttle Platform administration tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("create-admin", help="Create an administrator using an interactive prompt.")
    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin()


if __name__ == "__main__":
    main()
