from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app import db
from app.models import ActivityLog, Barangay, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates/admin')


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def _audit(action, record_type=None, record_id=None, details=''):
    db.session.add(ActivityLog(
        user_id=current_user.user_id,
        barangay_id=current_user.barangay_id,
        action=action, record_type=record_type,
        record_id=record_id, details=details
    ))


@admin_bp.route('/')
@admin_bp.route('/overview')
@admin_required
def overview():
    return render_template('admin/overview.html',
        active_admin='overview',
        counts={
            'residents': User.query.filter_by(role='resident').count(),
            'personnel': User.query.filter_by(role='staff').count(),
            'admins': User.query.filter_by(role='admin').count(),
            'inactive': User.query.filter_by(is_active=False).count(),
        },
        recent=ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all())


@admin_bp.route('/users/<role>')
@admin_required
def users(role):
    if role not in ('resident', 'staff'):
        abort(404)
    q = User.query.filter_by(role=role)
    status = request.args.get('status', 'all')
    if status == 'active':
        q = q.filter_by(is_active=True)
    elif status == 'inactive':
        q = q.filter_by(is_active=False)
    needle = (request.args.get('q') or '').strip()
    if needle:
        pattern = '%' + needle + '%'
        q = q.filter(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))
    rows = q.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', active_admin=role,
                           users=rows, role=role, status=status, needle=needle)


@admin_bp.post('/users/<int:user_id>/status')
@admin_required
def user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin' or user.user_id == current_user.user_id:
        abort(403)
    action = request.form.get('action')
    if action not in ('activate', 'deactivate'):
        abort(400)
    user.is_active = action == 'activate'
    _audit('user_' + action, 'user', user.user_id,
           f'{user.role}: {user.full_name} ({user.email})')
    db.session.commit()
    flash(f'Account {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.users', role=user.role))


@admin_bp.route('/audit-log')
@admin_required
def audit_log():
    rows = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(250).all()
    return render_template('admin/audit_log.html', active_admin='audit', rows=rows)


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    from app.models import SystemSetting
    setting = SystemSetting.query.filter_by(key='flood_threshold_cm').first()
    if request.method == 'POST':
        try:
            value = int(request.form.get('flood_threshold_cm', ''))
            if not 1 <= value <= 300:
                raise ValueError()
        except (TypeError, ValueError):
            flash('Flood threshold must be a whole number from 1 to 300 cm.', 'warning')
        else:
            if setting is None:
                setting = SystemSetting(key='flood_threshold_cm', value=str(value))
                db.session.add(setting)
            else:
                setting.value = str(value)
            _audit('system_setting_updated', 'setting', None,
                   f'flood_threshold_cm={value}')
            db.session.commit()
            flash('System setting saved.', 'success')
            return redirect(url_for('admin.settings'))
    return render_template('admin/settings.html', active_admin='settings',
                           threshold=setting.value if setting else '30')


@admin_bp.route('/data-privacy')
@admin_required
def data_privacy():
    from app.models import DataDisposalRequest
    requests_list = DataDisposalRequest.query.order_by(DataDisposalRequest.created_at.desc()).limit(100).all()
    return render_template('admin/data_privacy.html', active_admin='privacy', requests_list=requests_list)


@admin_bp.post('/data-privacy/<int:request_id>/status')
@admin_required
def disposal_status(request_id):
    from app.models import DataDisposalRequest
    item = DataDisposalRequest.query.get_or_404(request_id)
    status = request.form.get('status')
    if status not in ('pending', 'approved', 'rejected', 'completed'):
        abort(400)
    item.status = status
    item.reviewed_by = current_user.user_id
    item.reviewed_at = datetime.utcnow()
    _audit('data_disposal_' + status, 'data_disposal_request', item.request_id, item.email)
    db.session.commit()
    flash('Data disposal request updated.', 'success')
    return redirect(url_for('admin.data_privacy'))
