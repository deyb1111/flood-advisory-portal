import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 8388608))
    app.config.setdefault('PERSONNEL_DEMO', False)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to continue.'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    from app.views.public import public_bp
    from app.views.resident import resident_bp
    from app.views.auth import auth_bp
    from app.views.api import api_bp
    from app.views.personnel import personnel_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(resident_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(personnel_bp, url_prefix='/personnel')

       # Fix for Windows strftime (Windows doesn't support %-d or %-I)
    @app.template_filter('dt')
    def format_datetime(value, format='%d %b %Y'):
        if not value:
            return ''
        # Strip the '-' modifier for Windows compatibility
        safe_format = format.replace('%-', '%')
        return value.strftime(safe_format)

    return app