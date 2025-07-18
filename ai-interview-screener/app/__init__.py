# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_jwt_extended import JWTManager
# from flask_cors import CORS
# from flask_restful import Api
# import logging
# from logging.handlers import RotatingFileHandler
# from config import Config

# db = SQLAlchemy()
# jwt = JWTManager()
# api = Api()

# def create_app():
#     app = Flask(__name__)
#     app.config.from_object(Config)
    
#     # Enable CORS for all origins and all routes
#     CORS(app, resources={r"/*": {"origins": "*"}})

#     # Set up logging
#     logging.basicConfig(level=app.config['LOG_LEVEL'])
#     logger = logging.getLogger(__name__)
#     file_handler = RotatingFileHandler(
#         app.config['LOG_FILE'],
#         maxBytes=app.config['LOG_MAX_BYTES'],
#         backupCount=app.config['LOG_BACKUP_COUNT']
#     )
#     file_handler.setFormatter(logging.Formatter(
#         '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
#     ))
#     app.logger.addHandler(file_handler)
#     logger.info("Flask application initialized")

#     db.init_app(app)
#     jwt.init_app(app)
#     api.init_app(app)

#     with app.app_context():
#         from .rest_api import register_routes
#         register_routes(app)
#         db.create_all()

#     return app


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restful import Api
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
jwt = JWTManager()
api = Api()

def create_app():
    app = Flask(__name__)
    
    # Configure Flask app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/ubuntu/ai-interview-secreener/ai-interview-screener/instance/your_database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    app.config['BASE_DIR'] = os.path.dirname(os.path.abspath(__file__))
    app.config['LOG_LEVEL'] = logging.INFO
    app.config['LOG_FILE'] = os.path.join(app.config['BASE_DIR'], 'instance', 'app.log')
    app.config['LOG_MAX_BYTES'] = 10000000  # 10MB
    app.config['LOG_BACKUP_COUNT'] = 5
    
    # Ensure the instance directory exists
    instance_dir = os.path.join(app.config['BASE_DIR'], 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    # Enable CORS for all origins and all routes
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Set up logging
    logging.basicConfig(level=app.config['LOG_LEVEL'])
    logger = logging.getLogger(__name__)
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT']
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)
    logger.info("Flask application initialized")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    api.init_app(app)

    # Register blueprints
    from app.api.interview_routes import interview_bp
    from app.rest_api import register_routes
    
    app.register_blueprint(interview_bp)
    register_routes(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app