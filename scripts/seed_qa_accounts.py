"""Create or update the nine QA accounts for Bantay Daan Pasig.

Run from the project root (the directory containing app/ and .env):
    python scripts/seed_qa_accounts.py

This script only creates/updates the reserved qa.*@example.test accounts.
Use only with a development or QA database, never production.
"""

from pathlib import Path
import sys

# Ensure imports work when this file is run directly from scripts/ on Windows.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db  # noqa: E402
from app.models import Barangay, User  # noqa: E402

BARANGAY_NAMES = ("Kalawaan", "San Joaquin", "Bambang")
ROLES = ("resident", "staff", "admin")


def barangay_slug(name: str) -> str:
    return "".join(name.lower().split())


def role_label(role: str) -> str:
    return role.capitalize()


def email_for(role: str, barangay_name: str) -> str:
    return f"qa.{role}.{barangay_slug(barangay_name)}@example.test"


def password_for(role: str, barangay_name: str) -> str:
    # Matches the credentials documented for the QA account set.
    return f"QA-{role.capitalize()}-{barangay_name.replace(' ', '')}-2026!"


def main() -> None:
    app = create_app()

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in the project's .env file "
            "and run this script from the project root."
        )

    with app.app_context():
        # Use the real model field, Barangay.name, and look up IDs dynamically.
        for name in BARANGAY_NAMES:
            if Barangay.query.filter_by(name=name).first() is None:
                db.session.add(Barangay(name=name))
        db.session.flush()

        created = 0
        updated = 0

        for barangay_name in BARANGAY_NAMES:
            barangay = Barangay.query.filter_by(name=barangay_name).one()

            for role in ROLES:
                email = email_for(role, barangay_name)
                user = User.query.filter_by(email=email).first()
                full_name = f"QA {role_label(role)} - {barangay_name}"
                password = password_for(role, barangay_name)

                if user is None:
                    user = User(
                        full_name=full_name,
                        email=email,
                        role=role,
                        barangay_id=barangay.barangay_id,
                        is_active=True,
                    )
                    user.set_password(password)
                    db.session.add(user)
                    created += 1
                else:
                    # Only reserved QA emails are modified by this script.
                    user.full_name = full_name
                    user.role = role
                    user.barangay_id = barangay.barangay_id
                    user.is_active = True
                    user.set_password(password)
                    updated += 1

        db.session.commit()
        print("QA account seed completed successfully.")
        print(f"Created: {created}; updated: {updated}; total accounts: {created + updated}")
        print("Use the credentials from the QA account table in the project notes.")


if __name__ == "__main__":
    main()
