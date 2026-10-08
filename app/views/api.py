from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/advisories')
def get_advisories():
    # Placeholder — replaced by a real MySQL query in Phase 5
    return jsonify([
        {'id': 1, 'lat': 14.5764, 'lng': 121.0851, 'kind': 'caution',
         'title': 'Kalawaan Road — gutter-deep flooding', 'barangay': 'Kalawaan'},
        {'id': 2, 'lat': 14.5798, 'lng': 121.0902, 'kind': 'not_passable',
         'title': 'San Joaquin Road — not passable', 'barangay': 'San Joaquin'},
    ])