from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
import os

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Create upload directory
    upload_dir = os.path.join(app.instance_path, 'Uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Register API routes
    from app.rest_api import register_routes
    register_routes(app)
    
    # Ensure all models are imported for database creation
    with app.app_context():
        from app.models import User, Campaign, Candidate, InterviewQuestion, Interview, UploadedCSV
        db.create_all()
    
    return app