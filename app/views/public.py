from datetime import datetime, timedelta
import os

from flask import Blueprint, render_template, abort, current_app, send_from_directory
from werkzeug.utils import secure_filename

from app import db
from app.models import Advisory, Report

public_bp = Blueprint('public', __name__)


def _time_ago(dt):
    secs = max(int((datetime.utcnow() - dt).total_seconds()), 0)
    if secs < 60: return 'just now'
    if secs < 3600: return f'{secs // 60} min ago'
    if secs < 86400: return f'{secs // 3600} hr ago'
    return f'{secs // 86400} d ago'


@public_bp.route('/')
def home():
    # Same visibility rule as /api/advisories: published, unresolved (and not expired).
    now = datetime.utcnow()
    visible = (Advisory.status == 'published',
               Advisory.is_resolved.is_(False),
               db.or_(Advisory.expires_at.is_(None), Advisory.expires_at > now),
               db.or_(Advisory.report_id.is_(None), Advisory.report.has(Report.status == 'verified')))
    recent = (Advisory.query
              .filter(*visible)
              .order_by(Advisory.published_at.desc())
              .limit(5).all())
    active_query = Advisory.query.filter(*visible)
    stats = {
        'active': active_query.count(),
        'flood': active_query.filter(Advisory.report.has(Report.report_type == 'flood')).count(),
        'affected': active_query.filter(Advisory.road_status.in_(['caution', 'not_passable'])).count(),
        'resolved': Advisory.query.filter(Advisory.is_resolved.is_(True),
                    Advisory.published_at >= now - timedelta(hours=24)).count(),
    }
    return render_template('public/home.html', active_page='home',
                           recent_advisories=recent, time_ago=_time_ago, stats=stats)

@public_bp.route('/advisories')
def advisories():
    now = datetime.utcnow()
    items = (Advisory.query
             .filter(Advisory.status == 'published',
                     Advisory.is_resolved.is_(False),
                     db.or_(Advisory.expires_at.is_(None), Advisory.expires_at > now),
               db.or_(Advisory.report_id.is_(None), Advisory.report.has(Report.status == 'verified')))
             .order_by(Advisory.published_at.desc()).all())
    return render_template('public/advisories.html', active_page='advisories',
                           advisories=items, time_ago=_time_ago)

@public_bp.route('/advisories/<advisory_id>')
def advisory_detail(advisory_id):
    now = datetime.utcnow()
    advisory = (Advisory.query
                .filter(Advisory.advisory_id == advisory_id,
                        Advisory.status == 'published',
                        Advisory.is_resolved.is_(False),
                        db.or_(Advisory.expires_at.is_(None), Advisory.expires_at > now),
                        db.or_(Advisory.report_id.is_(None), Advisory.report.has(Report.status == 'verified')))
                .first())
    if advisory is None:
        abort(404)
    return render_template('public/advisory_detail.html', active_page='advisories',
                           advisory=advisory, time_ago=_time_ago)



@public_bp.route('/advisories/<int:advisory_id>/photo')
def advisory_photo(advisory_id):
    now = datetime.utcnow()
    advisory = (Advisory.query
                .filter(Advisory.advisory_id == advisory_id,
                        Advisory.status == 'published',
                        Advisory.is_resolved.is_(False),
                        db.or_(Advisory.expires_at.is_(None), Advisory.expires_at > now),
                        Advisory.report.has(Report.status == 'verified'))
                .first_or_404())
    photo_path = advisory.report.photo_path if advisory.report else None
    if not photo_path:
        abort(404)
    filename = secure_filename(photo_path.split('/')[-1])
    folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.isabs(folder):
        folder = os.path.join(current_app.root_path, folder)
    return send_from_directory(folder, filename)


@public_bp.route('/map', endpoint='map')
def map_view():
    return render_template('public/map.html', active_page='map')