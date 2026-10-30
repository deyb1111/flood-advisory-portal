from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Barangay(db.Model):
    __tablename__ = 'barangays'
    barangay_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    users = db.relationship('User', backref='barangay', lazy=True)
    roads = db.relationship('Road', backref='barangay', lazy=True)
    reports = db.relationship('Report', backref='barangay', lazy=True)
    advisories = db.relationship('Advisory', backref='barangay', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangays.barangay_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(190), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('resident', 'staff', 'admin', name='user_roles'), nullable=False, default='resident')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.user_id)


class Road(db.Model):
    __tablename__ = 'roads'
    road_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangays.barangay_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    name = db.Column(db.String(150), nullable=False)

    __table_args__ = (db.UniqueConstraint('barangay_id', 'name', name='uq_roads_barangay_name'),)


class Report(db.Model):
    __tablename__ = 'reports'
    report_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangays.barangay_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    road_id = db.Column(db.Integer, db.ForeignKey('roads.road_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=True)
    report_type = db.Column(db.Enum('flood', 'traffic', name='report_types'), nullable=False)
    water_level = db.Column(db.Enum('none', 'gutter', 'ankle', 'knee', 'waist_or_higher', name='water_levels'), nullable=True)
    traffic_level = db.Column(db.Enum('light', 'heavy', 'standstill', name='traffic_levels'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Numeric(9, 6), nullable=False)
    longitude = db.Column(db.Numeric(9, 6), nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Enum('pending', 'verified', 'unverified', 'rejected', name='report_statuses'), nullable=False, default='pending')
    duplicate_of = db.Column(db.Integer, db.ForeignKey('reports.report_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='reports', foreign_keys=[user_id])
    road = db.relationship('Road', backref='reports')
    duplicate_of_report = db.relationship('Report', remote_side=[report_id], backref='duplicates')

    # ----- display helpers (no schema change) -----
    @property
    def reference(self):
        if not self.report_id or not self.created_at:
            return 'BDP-NEW'
        return f'BDP-{self.created_at:%Y-%m%d}-{self.report_id:04d}'

    @property
    def short_ref(self):
        return f'{self.report_id:04d}' if self.report_id else 'NEW'

    @property
    def status_key(self):
        # 'pending' and 'unverified' both mean "awaiting review" to personnel.
        return 'unverified' if self.status == 'pending' else self.status

    @property
    def status_label(self):
        return {'pending': 'Unverified', 'unverified': 'Unverified',
                'verified': 'Verified', 'rejected': 'Rejected'}.get(self.status, self.status.title())

    @property
    def latest_verification(self):
        if not self.verifications:
            return None
        return max(self.verifications, key=lambda v: v.decided_at, default=None)

    @property
    def report_type_label(self):
        return {'flood': 'Flood', 'traffic': 'Road / traffic'}.get(self.report_type, self.report_type)

    @property
    def submitted_at(self):
        return self.created_at

    # ----- community upvotes (see ReportUpvote) -----
    @property
    def upvote_count(self):
        return len(self.upvotes)

    def is_upvoted_by(self, user):
        return any(u.user_id == user.user_id for u in self.upvotes)

    # ----- resident "My Reports" helpers (derived; no schema change) -----
    @property
    def road_condition(self):
        """'passable' | 'caution' | 'not_passable' | None.
        Published advisory wins; otherwise inferred from traffic/water level."""
        published = [a for a in self.advisories if a.status == 'published']
        if published:
            return max(published, key=lambda a: a.published_at).road_status
        if self.traffic_level:
            return {'light': 'passable', 'heavy': 'caution',
                    'standstill': 'not_passable'}.get(self.traffic_level)
        if self.water_level:
            return {'none': 'passable', 'gutter': 'passable', 'ankle': 'caution',
                    'knee': 'not_passable', 'waist_or_higher': 'not_passable'}.get(self.water_level)
        return None

    @property
    def resident_status(self):
        """'pending' | 'verified' | 'resolved' | 'rejected'."""
        if any(a.is_resolved for a in self.advisories):
            return 'resolved'
        return 'pending' if self.status in ('pending', 'unverified') else self.status

    @property
    def latest_update_at(self):
        v = self.latest_verification
        return v.decided_at if v else self.created_at

    @property
    def condition_label(self):
        """Human label for the reported water level / traffic level."""
        if self.water_level:
            return {'none': 'No standing water', 'gutter': 'Gutter-deep', 'ankle': 'Ankle-deep',
                    'knee': 'Knee-deep', 'waist_or_higher': 'Waist-deep or higher'}.get(self.water_level, self.water_level)
        if self.traffic_level:
            return {'light': 'Light traffic', 'heavy': 'Heavy traffic',
                    'standstill': 'Standstill'}.get(self.traffic_level, self.traffic_level)
        return None

    @property
    def display_title(self):
        lead = 'Flooding' if self.report_type == 'flood' else 'Road / traffic issue'
        if self.road:
            return f'{lead} near {self.road.name}'
        return f'{lead} in {self.barangay.name}'

    @property
    def first_verified_at(self):
        times = [v.decided_at for v in self.verifications if v.decision == 'verified']
        return min(times) if times else None


class Verification(db.Model):
    __tablename__ = 'verifications'
    verification_id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.report_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    decision = db.Column(db.Enum('verified', 'unverified', 'rejected', name='verification_decisions'), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    decided_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    report = db.relationship('Report', backref='verifications')
    staff = db.relationship('User', backref='verifications')


class ReportUpvote(db.Model):
    """A nearby resident's confirmation of a report (one per user per report)."""
    __tablename__ = 'report_upvotes'
    upvote_id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.report_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('report_id', 'user_id', name='uq_report_upvotes_report_user'),)

    report = db.relationship('Report', backref=db.backref('upvotes', cascade='all, delete-orphan', passive_deletes=True))
    user = db.relationship('User', backref=db.backref('upvotes', passive_deletes=True))


class Advisory(db.Model):
    __tablename__ = 'advisories'
    advisory_id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.report_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangays.barangay_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    road_id = db.Column(db.Integer, db.ForeignKey('roads.road_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    published_by = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    road_status = db.Column(db.Enum('passable', 'caution', 'not_passable', name='road_statuses'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    published_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_resolved = db.Column(db.Boolean, nullable=False, default=False)
    title = db.Column(db.String(200), nullable=False, default='')
    status = db.Column(db.Enum('draft', 'published', 'archived', name='advisory_statuses'),
                       nullable=False, default='published')

    report = db.relationship('Report', backref='advisories')
    road = db.relationship('Road', backref='advisories')
    publisher = db.relationship('User', backref='published_advisories')

    @property
    def reference(self):
        if not self.advisory_id:
            return 'ADV-NEW'
        if not self.published_at:
            return f'ADV-NEW-{self.advisory_id:03d}'
        return f'ADV-{self.published_at:%m%d}-{self.advisory_id:02d}'

    @property
    def status_label(self):
        return self.status.title()


class Notification(db.Model):
    """In-app notification for personnel (e.g. a new report in their barangay)."""
    __tablename__ = 'notifications'
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.report_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')
    report = db.relationship('Report', backref='notifications')

    def to_dict(self):
        from flask import url_for
        endpoint = ('resident.report_detail' if self.user and self.user.role == 'resident'
                    else 'personnel.report_detail')
        return {'id': self.notification_id, 'report_id': self.report_id,
                'url': url_for(endpoint, report_id=self.report_id) if self.report_id else None,
                'message': self.message, 'is_read': self.is_read,
                'created_at': self.created_at.strftime('%d %b · %I:%M %p')}


class ActivityLog(db.Model):
    """Personnel action audit trail. New table, additive."""
    __tablename__ = 'activity_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    barangay_id = db.Column(db.Integer, db.ForeignKey('barangays.barangay_id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    record_type = db.Column(db.String(32), nullable=True)
    record_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='activity_logs')
    barangay = db.relationship('Barangay', backref='activity_logs')


class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                            onupdate=datetime.utcnow)


class DataDisposalRequest(db.Model):
    __tablename__ = 'data_disposal_requests'
    request_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(190), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'completed',
                               name='data_disposal_statuses'), nullable=False, default='pending')
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])