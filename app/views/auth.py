from flask import Blueprint, redirect, render_template_string, request, url_for, flash
from flask_login import login_user, logout_user
from urllib.parse import urlparse
from flask_login import current_user

from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

# A simple built-in login page so you can test the system.
_LOGIN_HTML = """
<!doctype html><html><head><title>Sign in</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
</head><body class="bg-light">
<div class="container" style="max-width:420px;margin-top:80px;">
  <div class="card"><div class="card-body p-4">
    <h1 class="h4 mb-3">Bantay Daan Pasig — Sign in</h1>
    {% with msgs = get_flashed_messages() %}{% if msgs %}
      <div class="alert alert-warning">{{ msgs[0] }}</div>
    {% endif %}{% endwith %}
    <form method="post">
      <!-- This is the corrected line: calling csrf_token() with parentheses -->
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div class="mb-3"><label class="form-label">Email</label>
        <input type="email" name="email" class="form-control" required autofocus></div>
      <div class="mb-3"><label class="form-label">Password</label>
        <input type="password" name="password" class="form-control" required></div>
      <button class="btn btn-primary w-100">Sign in</button>
    </form>
  </div></div>
</div></body></html>
"""

def _is_safe_next(target):
    if not target or not target.startswith('/') or '\\' in target:
        return False
    p = urlparse(target)
    return not p.scheme and not p.netloc

def _home_for(user):
    if user.role == 'admin':
        return url_for('admin.overview')
    if user.role == 'staff':
        return url_for('personnel.dashboard')
    return url_for('public.home')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user and user.is_active and user.check_password(password):
            login_user(user)
            nxt = request.args.get('next')
            return redirect(nxt if _is_safe_next(nxt) else _home_for(user))
        flash('Invalid email or password.', 'warning')
    return render_template_string(_LOGIN_HTML)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('public.home'))