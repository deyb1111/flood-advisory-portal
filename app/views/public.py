from flask import Blueprint, render_template

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def home():
    return render_template('public/home.html', active_page='home')

@public_bp.route('/advisories')
def advisories():
    return render_template('public/advisories.html', active_page='advisories')

@public_bp.route('/advisories/<int:advisory_id>')
def advisory_detail(advisory_id):
    return render_template('public/advisory_detail.html',
                           active_page='advisories',
                           advisory_id=advisory_id)

@public_bp.route('/map')
def map_view():
    return render_template('public/map.html', active_page='map')