import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Create the extension objects globally
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 8388608))

    # Initialize extensions with the app  <--- THIS IS THE CRITICAL PART
    db.init_app(app)          # <--- Make sure this line is here!
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register blueprints (make sure these match your actual files)
    from app.views.public import public_bp
    from app.views.resident import resident_bp
    from app.views.auth import auth_bp
    from app.views.api import api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(resident_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    return app