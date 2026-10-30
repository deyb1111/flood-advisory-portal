from datetime import datetime

from flask import Blueprint, jsonify
from app import db
from app.models import Advisory, Report, Barangay

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/advisories')
def get_advisories():
    rows = (Advisory.query
            .filter(Advisory.status == 'published',
                    Advisory.is_resolved.is_(False),
                    db.or_(Advisory.expires_at.is_(None), Advisory.expires_at > datetime.utcnow()),
                    db.or_(Advisory.report_id.is_(None), Advisory.report.has(Report.status == 'verified')))
            .order_by(Advisory.published_at.desc())
            .all())
    return jsonify([{
        'id': a.advisory_id,
        'reference': a.reference,
        'lat': float(a.report.latitude) if a.report else None,
        'lng': float(a.report.longitude) if a.report else None,
        'kind': a.road_status,
        'road': a.road.name if a.road else '',
        'published_at': a.published_at.isoformat() if a.published_at else None,
        'title': a.title or (a.road.name if a.road else ''),
        'barangay': a.barangay.name if a.barangay else '',
    } for a in rows if a.report])