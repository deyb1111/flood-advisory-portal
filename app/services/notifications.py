from app import db
from app.models import Notification, User


def notify_new_report(report):
    """Queue a notification for every active staff member of the report's barangay.
    Caller must flush (report_id needed) and commit."""
    staff = User.query.filter_by(barangay_id=report.barangay_id,
                                 role='staff', is_active=True).all()
    where = ', '.join(p for p in (report.road.name if report.road else None,
                                  report.barangay.name) if p)
    msg = f'New {report.report_type_label.lower()} report {report.short_ref} · {where}'[:255]
    for s in staff:
        db.session.add(Notification(user_id=s.user_id,
                                    report_id=report.report_id, message=msg))

# Staff are told at these confirmation counts only, so a busy report doesn't flood them.
STAFF_NOTIFY_AT = (1, 3, 5, 10)


def _add_once(user_id, report_id, msg):
    """Queue a notification unless an identical one exists (blocks vote on/off spam)."""
    msg = msg[:255]
    if not Notification.query.filter_by(user_id=user_id, report_id=report_id,
                                        message=msg).first():
        db.session.add(Notification(user_id=user_id, report_id=report_id, message=msg))


def notify_upvote(report, count):
    """A nearby resident confirmed `report` (now `count` confirmations).
    Tells the owner every time and barangay staff at STAFF_NOTIFY_AT milestones.
    Voter identity is never included. Caller must commit."""
    where = ', '.join(p for p in (report.road.name if report.road else None,
                                  report.barangay.name) if p)
    noun = 'confirmation' if count == 1 else 'confirmations'
    if report.user and report.user.is_active:
        _add_once(report.user_id, report.report_id,
                  f'Nearby residents confirmed your report {report.short_ref} · {where} ({count} {noun})')
    if count in STAFF_NOTIFY_AT:
        staff = User.query.filter_by(barangay_id=report.barangay_id,
                                     role='staff', is_active=True).all()
        for s in staff:
            _add_once(s.user_id, report.report_id,
                      f'Report {report.short_ref} · {where} now has {count} community {noun}')
