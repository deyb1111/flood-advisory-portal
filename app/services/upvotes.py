"""Community upvote rules: nearby residents confirm a pending report.

"Nearby" = the voter's home barangay matches the report's barangay (users have
no stored location). Upvotes are a signal for personnel, never a verification.
"""
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import ReportUpvote

OPEN_STATUSES = ('pending', 'unverified')


def block_reason(report, user):
    """Return why `user` may not vote on `report`, or None if allowed."""
    if user.role != 'resident' or not user.is_active:
        return 'Only resident accounts can confirm reports.'
    if report.user_id == user.user_id:
        return 'You cannot confirm your own report.'
    if report.barangay_id != user.barangay_id:
        return 'Only residents of the report\'s barangay can confirm it.'
    if report.status not in OPEN_STATUSES:
        return 'Confirmations are closed once personnel have reviewed a report.'
    return None


def toggle_upvote(report, user):
    """Add or remove the user's single upvote. Returns True if now upvoted.
    The (report_id, user_id) unique key makes concurrent double-votes safe."""
    existing = ReportUpvote.query.filter_by(report_id=report.report_id,
                                            user_id=user.user_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return False
    db.session.add(ReportUpvote(report_id=report.report_id, user_id=user.user_id))
    try:
        db.session.commit()
    except IntegrityError:      # lost a race with our own duplicate request
        db.session.rollback()
    return True
