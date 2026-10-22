from flask import Blueprint, jsonify
from app.models import Advisory, Report, Barangay

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/advisories')
def get_advisories():
    rows = (Advisory.query
            .filter(Advisory.status == 'published',
                    Advisory.is_resolved.is_(False))
            .order_by(Advisory.published_at.desc())
            .all())
    return jsonify([{
        'id': a.advisory_id,
        'reference': a.reference,
        'lat': float(a.report.latitude) if a.report else None,
        'lng': float(a.report.longitude) if a.report else None,
        'kind': a.road_status,
        'title': a.title or (a.road.name if a.road else ''),
        'barangay': a.barangay.name if a.barangay else '',
    } for a in rows if a.report])