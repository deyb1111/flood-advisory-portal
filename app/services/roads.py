"""Official Main Thoroughfares & Arterial Roads per covered barangay.

Single source of truth (from the barangay thoroughfares PDF). Both the resident
report form and personnel advisory form are restricted to these names. Rows are
created lazily in the existing `roads` table, so no schema change is needed.
"""
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Barangay, Road

OFFICIAL_ROADS = {
    'Kalawaan': [
        'Elisco Road',
        'Pedro Cayetano Boulevard',
        'Axis Road',
        'Dr. A. Natividad Street',
        'L. Labao Street',
    ],
    'San Joaquin': [
        'M. Concepcion Avenue',
        'Elisco Road',
        'Ramon Jabson Street',
        'J. P. Rizal Extension',
        'E. Santos Avenue',
    ],
    'Bambang': [
        'E. Jacinto Street',
        'M. H. Del Pilar Street',
        'F. Manalo Street',
        'A. Luna Street',
    ],
}


# Map focus points (lat, lng) per official road. APPROXIMATE placeholders:
# verify against OSM/field data before production. Missing keys fall back
# to BARANGAY_CENTERS on the client.
OFFICIAL_ROAD_COORDS = {
    'Kalawaan': {
        'Elisco Road': (14.5598, 121.0825),
        'Pedro Cayetano Boulevard': (14.5575, 121.0900),
        'Axis Road': (14.5560, 121.0870),
        'Dr. A. Natividad Street': (14.5585, 121.0860),
        'L. Labao Street': (14.5570, 121.0845),
    },
    'San Joaquin': {
        'M. Concepcion Avenue': (14.5620, 121.0920),
        'Elisco Road': (14.5612, 121.0840),
        'Ramon Jabson Street': (14.5635, 121.0905),
        'J. P. Rizal Extension': (14.5648, 121.0890),
        'E. Santos Avenue': (14.5655, 121.0935),
    },
    'Bambang': {
        'E. Jacinto Street': (14.5700, 121.0815),
        'M. H. Del Pilar Street': (14.5685, 121.0800),
        'F. Manalo Street': (14.5715, 121.0830),
        'A. Luna Street': (14.5692, 121.0845),
    },
}


def official_names(barangay_name):
    return OFFICIAL_ROADS.get(barangay_name, [])


def official_roads(barangay_id):
    """Return Road rows (official names only, PDF order) for a barangay,
    creating any that are missing from the `roads` table."""
    b = db.session.get(Barangay, barangay_id)
    if not b:
        return []
    names = official_names(b.name)
    existing = {r.name: r for r in Road.query.filter_by(barangay_id=b.barangay_id)
                .filter(Road.name.in_(names)).all()}
    missing = [n for n in names if n not in existing]
    if missing:
        try:
            for n in missing:
                existing[n] = Road(barangay_id=b.barangay_id, name=n)
                db.session.add(existing[n])
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return [r for r in (Road.query.filter_by(barangay_id=b.barangay_id)
                                .filter(Road.name.in_(names)).all())]
    return [existing[n] for n in names if n in existing]
