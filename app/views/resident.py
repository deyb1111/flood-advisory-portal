from flask import Blueprint, render_template, redirect, url_for

resident_bp = Blueprint('resident', __name__)

@resident_bp.route('/report', methods=['GET'])
def report():
    return render_template('resident/report_form.html', active_page='report')

@resident_bp.route('/report', methods=['POST'])
def report_submit():
    # TODO Phase 5: validate + insert into DB
    return redirect(url_for('resident.report_submitted'))

@resident_bp.route('/report/submitted')
def report_submitted():
    return render_template('resident/report_submitted.html', active_page='report')

@resident_bp.route('/my-reports')
def my_reports():
    return render_template('resident/my_reports.html', active_page='my_reports')

@resident_bp.route('/my-reports/<int:report_id>')
def report_detail(report_id):
    return render_template('resident/report_detail.html',
                           active_page='my_reports',
                           report_id=report_id)

@resident_bp.route('/profile')
def profile():
    return render_template('resident/profile.html', active_page='profile')