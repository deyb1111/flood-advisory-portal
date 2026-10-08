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

    report = db.relationship('Report', backref='advisories')
    road = db.relationship('Road', backref='advisories')
    publisher = db.relationship('User', backref='published_advisories')