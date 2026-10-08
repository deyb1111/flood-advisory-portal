from flask import Blueprint, redirect, url_for

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/logout')
def logout():
    # TODO Phase 5: real logout via Flask-Login
    return redirect(url_for('public.home'))
