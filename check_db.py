from app import create_app, db
from app.models import Barangay

app = create_app()

with app.app_context():
    barangays = Barangay.query.all()
    print([b.name for b in barangays])