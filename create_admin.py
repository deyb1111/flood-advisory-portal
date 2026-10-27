
from getpass import getpass

from app import create_app, db
from app.models import User, Barangay

app = create_app()

with app.app_context():
    print("\n=== Create Administrator Account ===")

    name = input("Full name: ").strip()
    email = input("Email: ").strip().lower()

    if not name or not email or "@" not in email:
        raise SystemExit("Invalid name or email.")

    existing = User.query.filter(
        db.func.lower(User.email) == email
    ).first()

    if existing:
        raise SystemExit(
            "This email already exists. No account was changed."
        )

    barangays = Barangay.query.order_by(
        Barangay.barangay_id
    ).all()

    if not barangays:
        raise SystemExit(
            "No barangays exist. Add a valid barangay first."
        )

    print("\nAvailable barangays:")
    for barangay in barangays:
        print(f"{barangay.barangay_id}: {barangay.name}")

    try:
        barangay_id = int(input("Choose barangay ID: "))
    except ValueError:
        raise SystemExit("Invalid barangay ID.")

    barangay = db.session.get(Barangay, barangay_id)
    if not barangay:
        raise SystemExit("Barangay not found.")

    password = getpass("New password (12+ characters): ")
    confirm = getpass("Confirm password: ")

    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")

    if password != confirm:
        raise SystemExit("Passwords do not match.")

    admin = User(
        full_name=name,
        email=email,
        barangay_id=barangay.barangay_id,
        role="admin",
        is_active=True,
    )
    admin.set_password(password)

    try:
        db.session.add(admin)
        db.session.commit()
        print("\nAdministrator account created successfully.")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")
    except Exception:
        db.session.rollback()
        raise
