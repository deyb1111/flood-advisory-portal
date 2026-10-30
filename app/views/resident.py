import os
import re
from datetime import datetime, timedelta
from uuid import uuid4

from flask import (Blueprint, abort, current_app, flash, jsonify, render_template, redirect,
                   request, send_from_directory, url_for)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from app import db
from app.models import Barangay, Notification, Report, Road, User
from app.services.notifications import notify_new_report, notify_upvote
from app.services.upvotes import OPEN_STATUSES, block_reason, toggle_upvote
from app.services.roads import OFFICIAL_ROAD_COORDS, OFFICIAL_ROADS, official_names, official_roads

_OTHER_ROAD = '__other__'   # form value for a resident-typed street
_WATER = {'none', 'gutter', 'ankle', 'knee', 'waist_or_higher'}
_TRAFFIC_FROM_ROAD = {'passable': 'light', 'caution': 'heavy', 'not_passable': 'standstill'}
_PHOTO_EXT = {'jpg', 'jpeg', 'png'}

resident_bp = Blueprint('resident', __name__)

@resident_bp.route('/report', methods=['GET'])
def report():
    return render_template('resident/report_form.html', active_page='report',
                           barangays=Barangay.query.order_by(Barangay.name).all(),
                           roads_by_barangay=OFFICIAL_ROADS,
                           road_coords=OFFICIAL_ROAD_COORDS)

@resident_bp.route('/report', methods=['POST'])
@login_required
def report_submit():
    f = request.form
    barangay = db.session.get(Barangay, f.get('barangay_id', type=int) or 0)
    rtype = f.get('report_type')
    water = f.get('water_level')
    traffic = _TRAFFIC_FROM_ROAD.get(f.get('road_status'))
    road_name = (f.get('road_name') or '').strip()
    custom_road = (f.get('custom_road') or '').strip()[:150]
    desc = (f.get('description') or '').strip()
    try:
        lat, lng = round(float(f['latitude']), 6), round(float(f['longitude']), 6)
    except (KeyError, ValueError):
        lat = lng = None

    err = None
    if rtype not in ('flood', 'traffic'): err = 'Choose a report type.'
    elif not barangay: err = 'Choose a barangay.'
    elif road_name == _OTHER_ROAD and not custom_road:
        err = 'Enter the specific street or road.'
    elif road_name != _OTHER_ROAD and road_name not in official_names(barangay.name):
        err = f'Choose a listed street / road in Barangay {barangay.name}.'
    elif not desc: err = 'A description is required.'
    elif lat is None or not (14.5 <= lat <= 14.7 and 121.0 <= lng <= 121.15):
        err = 'Pin a valid location on the map.'
    elif rtype == 'flood' and water not in _WATER: err = 'Select a water level.'
    elif rtype == 'traffic' and not traffic: err = 'Select road passability.'
    if err:
        flash(err, 'warning')
        return redirect(url_for('resident.report'))

    if (f.get('landmark') or '').strip():   # no landmark column; keep it with the description
        desc = f"{desc}\nLandmark: {f['landmark'].strip()}"

    photo_path = None
    photo = request.files.get('photo')
    if photo and photo.filename:
        ext = photo.filename.rsplit('.', 1)[-1].lower()
        if ext not in _PHOTO_EXT:
            flash('Photo must be a JPG or PNG.', 'warning')
            return redirect(url_for('resident.report'))
        folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.isabs(folder):   # personnel.report_photo resolves relative to root_path
            folder = os.path.join(current_app.root_path, folder)
        os.makedirs(folder, exist_ok=True)
        photo_path = f'{uuid4().hex}.{ext}'
        photo.save(os.path.join(folder, photo_path))

    if road_name == _OTHER_ROAD:    # resident-typed street: reuse an existing row or create one
        road = Road.query.filter_by(barangay_id=barangay.barangay_id, name=custom_road).first()
        if not road:
            road = Road(barangay_id=barangay.barangay_id, name=custom_road)
            db.session.add(road)
            db.session.flush()
    else:
        road = next(r for r in official_roads(barangay.barangay_id) if r.name == road_name)

    r = Report(user_id=current_user.user_id, barangay_id=barangay.barangay_id,
               road_id=road.road_id, report_type=rtype,
               water_level=water if water in _WATER else None,
               traffic_level=traffic, description=desc,
               latitude=lat, longitude=lng, photo_path=photo_path, status='pending')
    db.session.add(r)
    try:
        db.session.flush()           # assigns report_id / created_at
        db.session.commit()          # save the resident report independently
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Could not save resident report')
        flash('The report could not be saved. Check the database connection and schema, then try again.', 'warning')
        return redirect(url_for('resident.report'))

    # Notifications are secondary to saving the report. In some local setups,
    # the optional notifications migration has not yet been applied. A missing
    # notifications table must not turn a valid report submission into a 500.
    try:
        notify_new_report(r)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception(
            'Report %s was saved, but personnel notifications could not be created',
            r.report_id,
        )

    return redirect(url_for('resident.report_submitted', report_id=r.report_id))

@resident_bp.route('/report/submitted')
@login_required
def report_submitted():
    r = Report.query.filter_by(report_id=request.args.get('report_id', type=int),
                               user_id=current_user.user_id).first_or_404()
    return render_template('resident/report_submitted.html', active_page='report', report=r)

_PERIODS = {'24h': timedelta(hours=24), '7d': timedelta(days=7), '30d': timedelta(days=30)}


@resident_bp.route('/my-reports')
@login_required
def my_reports():
    all_reports = Report.query.filter_by(user_id=current_user.user_id).all()
    stats = {k: sum(1 for r in all_reports if r.resident_status == k)
             for k in ('pending', 'verified', 'resolved', 'rejected')}

    f = {k: request.args.get(k, d) for k, d in
         (('status', 'all'), ('condition', 'all'), ('period', 'all'), ('sort', 'newest'))}
    items = all_reports
    if f['status'] != 'all':
        items = [r for r in items if r.resident_status == f['status']]
    if f['condition'] != 'all':
        items = [r for r in items if r.road_condition == f['condition']]
    if f['period'] in _PERIODS:
        cutoff = datetime.utcnow() - _PERIODS[f['period']]
        items = [r for r in items if r.created_at >= cutoff]
    items = sorted(items, key=lambda r: r.created_at, reverse=(f['sort'] != 'oldest'))

    return render_template('resident/my_reports.html', active_page='my_reports',
                           reports=items, stats=stats, filters=f, total=len(all_reports))

@resident_bp.route('/my-reports/<int:report_id>')
@login_required
def report_detail(report_id):
    r = Report.query.filter_by(report_id=report_id,
                               user_id=current_user.user_id).first_or_404()
    return render_template('resident/report_detail.html',
                           active_page='my_reports', report=r)


# ------------------------------------------------------------ community upvotes
def _community_report_or_404(report_id):
    """A neighbour's report in the user's own barangay (residents only)."""
    if current_user.role != 'resident':
        abort(403)
    return (Report.query.filter(Report.report_id == report_id,
                                Report.barangay_id == current_user.barangay_id,
                                Report.status != 'rejected').first_or_404())


@resident_bp.route('/community')
@login_required
def community():
    if current_user.role != 'resident':
        abort(403)
    items = (Report.query.filter(Report.barangay_id == current_user.barangay_id,
                                 Report.status.in_(OPEN_STATUSES),
                                 Report.user_id != current_user.user_id)
             .order_by(Report.created_at.desc()).limit(50).all())
    return render_template('resident/community.html', active_page='community', reports=items)


@resident_bp.route('/community/<int:report_id>')
@login_required
def community_detail(report_id):
    r = _community_report_or_404(report_id)
    if r.user_id == current_user.user_id:
        return redirect(url_for('resident.report_detail', report_id=r.report_id))
    return render_template('resident/community_detail.html', active_page='community',
                           report=r, block_reason=block_reason(r, current_user))


@resident_bp.post('/community/<int:report_id>/upvote')
@login_required
def community_upvote(report_id):
    r = _community_report_or_404(report_id)
    ajax = request.headers.get('X-Requested-With') == 'fetch'
    reason = block_reason(r, current_user)
    if reason:
        if ajax:
            return jsonify(ok=False, message=reason, count=r.upvote_count), 403
        flash(reason, 'warning')
        return redirect(url_for('resident.community_detail', report_id=r.report_id))
    try:
        upvoted = toggle_upvote(r, current_user)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Could not save upvote')
        msg = 'Your confirmation could not be saved. Please try again.'
        if ajax:
            return jsonify(ok=False, message=msg, count=r.upvote_count), 500
        flash(msg, 'warning')
        return redirect(url_for('resident.community_detail', report_id=r.report_id))
    db.session.refresh(r)
    if upvoted:   # notifications are secondary: never fail a saved vote because of them
        try:
            notify_upvote(r, r.upvote_count)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception('Upvote %s saved, but notifications failed', r.report_id)
    if ajax:
        return jsonify(ok=True, upvoted=upvoted, count=r.upvote_count)
    return redirect(url_for('resident.community_detail', report_id=r.report_id))


@resident_bp.get('/api/notifications')
@login_required
def api_notifications():
    if current_user.role != 'resident':
        abort(403)
    q = Notification.query.filter_by(user_id=current_user.user_id)
    items = q.order_by(Notification.notification_id.desc()).limit(8).all()
    return jsonify(unread=q.filter_by(is_read=False).count(),
                   items=[n.to_dict() for n in items])


@resident_bp.post('/api/notifications/read')
@login_required
def api_notifications_read():
    if current_user.role != 'resident':
        abort(403)
    Notification.query.filter_by(user_id=current_user.user_id, is_read=False
                                 ).update({'is_read': True})
    db.session.commit()
    return jsonify(ok=True)


@resident_bp.route('/my-reports/<int:report_id>/photo/<path:filename>')
@login_required
def report_photo(report_id, filename):
    """Serve a report photo to its owner (mirrors personnel.report_photo)."""
    r = Report.query.filter_by(report_id=report_id,
                               user_id=current_user.user_id).first_or_404()
    safe = secure_filename(filename)
    if not r.photo_path or safe != secure_filename(r.photo_path.split('/')[-1]):
        abort(404)
    folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.isabs(folder):
        folder = os.path.join(current_app.root_path, folder)
    return send_from_directory(folder, safe)

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@resident_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # barangay_id is intentionally never read: home barangay is fixed at registration.
        f = request.form
        full_name = (f.get('full_name') or '').strip()[:120]
        email = (f.get('email') or '').strip().lower()
        err = None
        if not full_name: err = 'Name is required.'
        elif len(email) > 190 or not _EMAIL_RE.match(email): err = 'Enter a valid email address.'
        elif email != current_user.email.lower():
            if not current_user.check_password(f.get('current_password', '')):
                err = 'Enter your current password to change your email.'
            elif User.query.filter(db.func.lower(User.email) == email,
                                   User.user_id != current_user.user_id).first():
                err = 'That email is already in use.'
        if err:
            flash(err, 'warning')
            return redirect(url_for('resident.profile'))
        current_user.full_name = full_name
        current_user.email = email
        try:
            db.session.commit()
            flash('Profile updated.', 'success')
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception('Could not update profile')
            flash('Profile could not be saved. Please try again.', 'warning')
        return redirect(url_for('resident.profile'))
    return render_template('resident/profile.html', active_page='profile')


@resident_bp.post('/profile/password')
@login_required
def profile_password():
    current = request.form.get('current_password', '')
    new = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')
    if not current_user.check_password(current):
        flash('Current password is incorrect.', 'warning')
    elif len(new) < 12:
        flash('New password must be at least 12 characters.', 'warning')
    elif new != confirm:
        flash('New passwords do not match.', 'warning')
    elif current_user.check_password(new):
        flash('New password must be different from the current one.', 'warning')
    else:
        current_user.set_password(new)
        try:
            db.session.commit()
            flash('Password updated.', 'success')
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception('Could not update password')
            flash('Password could not be saved. Please try again.', 'warning')
    return redirect(url_for('resident.profile'))