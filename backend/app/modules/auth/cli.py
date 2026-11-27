"""Create an admin or mechanic account (self sign-up only ever creates drivers).

    python -m app.modules.auth.cli --name "Nkenten Admin" --email admin@example.com --role admin
"""

import argparse
import getpass
import sys

from pydantic import ValidationError

from app.core.db import SessionLocal, create_all
from app.core.errors import ApiError
from app.modules.auth import service
from app.modules.auth.models import ROLES
from app.modules.auth.schemas import RegisterRequest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a user with a given role")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email")
    parser.add_argument("--phone")
    parser.add_argument("--role", choices=ROLES, default="admin")
    args = parser.parse_args(argv)
    password = getpass.getpass("Password (min 8 chars): ")
    try:
        body = RegisterRequest(
            full_name=args.name, email=args.email, phone=args.phone, password=password
        )
    except ValidationError as e:
        print(e, file=sys.stderr)
        return 1
    create_all()
    with SessionLocal() as db:
        try:
            out = service.register(db, body, role=args.role)
        except ApiError as e:
            print(e.message, file=sys.stderr)
            return 1
    print(f"Created {out.user.role} #{out.user.id}: {out.user.email or out.user.phone}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
