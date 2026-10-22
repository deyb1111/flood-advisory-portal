"""
Barangay Personnel blueprint.

Mounts at /personnel/* . All routes require staff/admin role + barangay assignment.
Reuses existing models (Report, Verification, Advisory, Road) and writes
ActivityLog entries on state changes.
"""
from datetime import datetime
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from app import db
from app.models import Advisory, ActivityLog, Report, Road, Verification

from flask import current_app, send_from_directory
from werkzeug.utils import secure_filename


bp = Blueprint('personnel', __name__, template_folder='../templates/personnel')


# ------------------------------------------------------------------ guards
def personnel_required(view):
    @wraps(view)
    @login_required
    def wrapper(*a, **kw):
        if current_user.role not in ('staff', 'admin') or not current_user.barangay_id:
            abort(403)
        return view(*a, **kw)
    return wrapper


# ------------------------------------------------------------------ helpers
def _demo_mode():
    return bool(current_app.config.get('PERSONNEL_DEMO', False))


def _reports_query():
    return Report.query.filter_by(barangay_id=current_user.barangay_id)


def _advisories_query():
    return Advisory.query.filter_by(barangay_id=current_user.barangay_id)


def _stats():
    q = _reports_query()
    return dict(
        total_submitted=q.count(),
        awaiting_verification=q.filter(Report.status.in_(['pending', 'unverified'])).count(),
        verified=q.filter_by(status='verified').count(),
        rejected=q.filter_by(status='rejected').count(),
        active_advisories=_advisories_query()
            .filter_by(status='published', is_resolved=False).count(),
    )


def _log(action, record_type=None, record_id=None, details=''):
    db.session.add(ActivityLog(
        user_id=current_user.user_id,
        barangay_id=current_user.barangay_id,
        action=action, record_type=record_type,
        record_id=record_id, details=details,
    ))


def _streets():
    """Return [(road_id, name), ...] for the current user's barangay."""
    return [(r.road_id, r.name) for r in Road.query
            .filter_by(barangay_id=current_user.barangay_id)
            .order_by(Road.name).all()]


# ------------------------------------------------------------------ dashboard
@bp.route('/')
@bp.route('/dashboard')
@personnel_required
def dashboard():
    recent_reports = (_reports_query()
        .order_by(Report.created_at.desc()).limit(4).all())
    recent_actions = (ActivityLog.query
        .filter_by(barangay_id=current_user.barangay_id)
        .order_by(ActivityLog.created_at.desc()).limit(6).all())
    return render_template('personnel/dashboard.html',
        active_nav='dashboard',
        stats=_stats(),
        recent_reports=recent_reports,
        recent_actions=recent_actions,
        demo_mode=_demo_mode(),
    )


# ------------------------------------------------------------------ reports
@bp.route('/reports')
@personnel_required
def reports():
    q = _reports_query()
    status = request.args.get('status')
    if status == 'unverified':
        q = q.filter(Report.status.in_(['pending', 'unverified']))
    elif status:
        q = q.filter_by(status=status)
    if request.args.get('type'):
        q = q.filter_by(report_type=request.args['type'])
    if request.args.get('q'):
        needle = f"%{request.args['q']}%"
        q = q.filter(Report.description.ilike(needle))
    q = q.order_by(Report.created_at.desc())

    per_page = 6
    total = q.count()
    page = max(1, min(int(request.args.get('page', 1) or 1),
                      max(1, (total + per_page - 1) // per_page)))
    items = q.offset((page - 1) * per_page).limit(per_page).all()

    def page_url(p):
        args = request.args.to_dict()
        args['page'] = p
        return url_for('personnel.reports', **args)

    pagination = dict(
        total=total, page=page, per_page=per_page,
        pages=range(1, max(2, (total + per_page - 1) // per_page + 1)),
        has_prev=page > 1, has_next=page * per_page < total,
        prev_url=page_url(page - 1), next_url=page_url(page + 1),
        start=(page - 1) * per_page + 1, end=min(page * per_page, total),
        url_for=page_url,
    )

    return render_template('personnel/reports.html',
        active_nav='reports',
        reports=items, pagination=pagination,
        stats=_stats(), filters=request.args,
        demo_mode=_demo_mode(),
    )


@bp.route('/reports/<int:report_id>')
@personnel_required
def report_detail(report_id):
    report = _reports_query().filter_by(report_id=report_id).first_or_404()
    next_report = (_reports_query()
        .filter(Report.status.in_(['pending', 'unverified']))
        .filter(Report.report_id != report.report_id)
        .order_by(Report.created_at.asc()).first())
    return render_template('personnel/report_detail.html',
        active_nav='reports',
        report=report, next_report=next_report, stats=_stats(),
        demo_mode=_demo_mode(),
    )


@bp.post('/reports/<int:report_id>/verify')
@personnel_required
def report_verify(report_id):
    report = _reports_query().filter_by(report_id=report_id).first_or_404()
    remarks = (request.form.get('review_notes') or '').strip() or None
    db.session.add(Verification(
        report_id=report.report_id,
        staff_id=current_user.user_id,
        decision='verified',
        remarks=remarks,
    ))
    report.status = 'verified'
    _log('Report verified', 'report', report.report_id,
         remarks or 'Accepted after photo and location review.')
    db.session.commit()
    flash(f'Report {report.short_ref} verified.', 'success')
    return redirect(url_for('personnel.report_detail', report_id=report.report_id))


@bp.post('/reports/<int:report_id>/reject')
@personnel_required
def report_reject(report_id):
    report = _reports_query().filter_by(report_id=report_id).first_or_404()
    reason = (request.form.get('reason') or '').strip()
    if not reason:
        flash('A rejection reason is required.', 'warning')
        return redirect(url_for('personnel.report_detail', report_id=report.report_id))
    db.session.add(Verification(
        report_id=report.report_id,
        staff_id=current_user.user_id,
        decision='rejected',
        remarks=reason,
    ))
    report.status = 'rejected'
    _log('Report rejected', 'report', report.report_id, f'Reason: {reason}')
    db.session.commit()
    flash(f'Report {report.short_ref} rejected.', 'success')
    return redirect(url_for('personnel.reports'))


# ------------------------------------------------------------------ map
@bp.route('/map')
@personnel_required
def map():
    reports = (_reports_query()
        .filter(Report.latitude.isnot(None))
        .order_by(Report.created_at.desc()).all())
    return render_template('personnel/map.html',
        active_nav='map',
        map_reports=[{
            'id': r.report_id,
            'reference': r.short_ref,
            'status': r.status_key,
            'report_type': r.report_type,
            'street': r.road.name if r.road else '',
            'description': r.description or '',
            'water_level': r.water_level,
            'traffic_level': r.traffic_level,
            'submitted_at': r.created_at.strftime('%-d %b · %-I:%M %p'),
            'lat': float(r.latitude), 'lng': float(r.longitude),
        } for r in reports],
        demo_mode=_demo_mode(),
    )


# ------------------------------------------------------------------ advisories
@bp.route('/advisories')
@personnel_required
def advisories():
    q = _advisories_query()
    status = request.args.get('status')
    if status:
        q = q.filter_by(status=status)
    if request.args.get('q'):
        q = q.filter(Advisory.title.ilike(f"%{request.args['q']}%"))
    items = q.order_by(Advisory.published_at.desc()).all()

    drafts = sum(1 for a in items if a.status == 'draft')
    published = sum(1 for a in items if a.status == 'published')
    archived = sum(1 for a in items if a.status == 'archived')
    return render_template('personnel/advisories.html',
        active_nav='advisories', advisories=items,
        stats=dict(drafts=drafts, published=published, archived=archived),
        filters=request.args,
        demo_mode=_demo_mode(),
    )


@bp.route('/advisories/new', methods=['GET', 'POST'])
@personnel_required
def advisory_create():
    return _advisory_form(None)


@bp.route('/advisories/<int:advisory_id>/edit', methods=['GET', 'POST'])
@personnel_required
def advisory_edit(advisory_id):
    adv = _advisories_query().filter_by(advisory_id=advisory_id).first_or_404()
    return _advisory_form(adv)


@bp.route('/advisories/<int:advisory_id>')
@personnel_required
def advisory_published(advisory_id):
    adv = _advisories_query().filter_by(advisory_id=advisory_id).first_or_404()
    return render_template('personnel/advisory_published.html',
        active_nav='advisories', advisory=adv, demo_mode=_demo_mode(),
    )


@bp.post('/advisories/<int:advisory_id>/archive')
@personnel_required
def advisory_archive(advisory_id):
    adv = _advisories_query().filter_by(advisory_id=advisory_id).first_or_404()
    adv.status = 'archived'
    _log('Advisory archived', 'advisory', adv.advisory_id,
         'Outdated; no longer current information.')
    db.session.commit()
    flash(f'Advisory {adv.reference} archived.', 'success')
    return redirect(url_for('personnel.advisories'))


def _advisory_form(adv):
    eligible = (_reports_query().filter_by(status='verified')
        .order_by(Report.created_at.desc()).all())
    streets = _streets()

    if request.method == 'POST':
        f = {
            'title': (request.form.get('title') or '').strip(),
            'message': (request.form.get('message') or '').strip(),
            'road_id': request.form.get('road_id') or '',
            'report_id': request.form.get('report_id') or '',
            'road_status': request.form.get('road_status') or 'caution',
        }
        intent = request.form.get('intent', 'draft')
        errors = {}
        if not f['title']:
            errors['title'] = 'Title is required.'
        if not f['message']:
            errors['message'] = 'Description is required.'
        if not f['report_id']:
            errors['report_id'] = 'Select an accepted, verified report.'
        if not f['road_id']:
            errors['road_id'] = 'Choose a street.'

        if errors:
            return render_template('personnel/advisory_compose.html',
                active_nav='advisories', advisory=adv, form=f,
                streets=streets, eligible_reports=eligible,
                form_errors=errors, demo_mode=_demo_mode())

        if adv is None:
            adv = Advisory(barangay_id=current_user.barangay_id,
                           published_by=current_user.user_id,
                           road_id=int(f['road_id']),
                           published_at=datetime.utcnow(),
                           status='draft')
            db.session.add(adv)

        adv.title = f['title']
        adv.message = f['message']
        adv.report_id = int(f['report_id'])
        adv.road_id = int(f['road_id'])
        adv.road_status = f['road_status']

        if intent == 'publish':
            adv.status = 'published'
            adv.published_at = datetime.utcnow()
            _log('Advisory published', 'advisory', adv.advisory_id,
                 f'Published {adv.reference}.')
            db.session.commit()
            flash(f'Advisory {adv.reference} published.', 'success')
            return redirect(url_for('personnel.advisory_published',
                                    advisory_id=adv.advisory_id))

        adv.status = 'draft'
        _log('Advisory drafted', 'advisory', adv.advisory_id,
             'Saved draft; not visible to residents.')
        db.session.commit()
        flash('Draft saved.', 'success')
        return redirect(url_for('personnel.advisories'))

    form = dict(
        title=adv.title if adv else '',
        message=adv.message if adv else '',
        road_id=str(adv.road_id) if adv else '',
        report_id=str(adv.report_id) if adv and adv.report_id else '',
        road_status=adv.road_status if adv else 'not_passable',
    )
    return render_template('personnel/advisory_compose.html',
        active_nav='advisories', advisory=adv, form=form,
        streets=streets, eligible_reports=eligible,
        form_errors=None, demo_mode=_demo_mode())


# ------------------------------------------------------------------ activity
@bp.route('/activity')
@personnel_required
def activity_log():
    q = (ActivityLog.query
        .filter_by(barangay_id=current_user.barangay_id)
        .order_by(ActivityLog.created_at.desc()))
    if request.args.get('q'):
        q = q.filter(ActivityLog.details.ilike(f"%{request.args['q']}%"))
    return render_template('personnel/activity_log.html',
        active_nav='activity',
        activities=q.limit(100).all(),
        filters=request.args,
        demo_mode=_demo_mode(),
    )


# ------------------------------------------------------------------ account
@bp.route('/account', methods=['GET', 'POST'])
@personnel_required
def account_settings():
    if request.method == 'POST':
        current_user.full_name = (request.form.get('full_name') or current_user.full_name).strip()
        current_user.email = (request.form.get('email') or current_user.email).strip()
        db.session.commit()
        flash('Account changes saved.', 'success')
        return redirect(url_for('personnel.account_settings'))
    return render_template('personnel/account_settings.html',
        active_nav='account', demo_mode=_demo_mode())


@bp.post('/account/password')
@personnel_required
def account_password():
    current = request.form.get('current_password', '')
    new = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')
    if len(new) < 12 or new != confirm or not current_user.check_password(current):
        flash('Could not update password. Check your current password and confirm the new one (12+ characters).', 'warning')
    else:
        current_user.set_password(new)
        db.session.commit()
        flash('Password updated.', 'success')
    return redirect(url_for('personnel.account_settings'))

#--------------------------------------------------------------- file upload

@bp.route('/photos/<int:report_id>/<path:filename>')
@personnel_required
def report_photo(report_id, filename):
    """Serve report photos, scoped to the current barangay."""
    report = _reports_query().filter_by(report_id=report_id).first_or_404()
    if not report.photo_path:
        abort(404)
    safe = secure_filename(filename)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], safe)

# Alias so `from app.views.personnel import personnel_bp` works, matching
# the *_bp convention used by public/resident/auth/api blueprints.
personnel_bp = bp