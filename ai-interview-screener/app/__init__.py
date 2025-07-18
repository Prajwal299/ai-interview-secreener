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
from config import Config

db = SQLAlchemy()
jwt = JWTManager()
api = Api()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
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

    db.init_app(app)
    jwt.init_app(app)
    api.init_app(app)

    with app.app_context():
        from .rest_api import register_routes
        register_routes(app)  # Correctly calls register_routes with only app
        db.create_all()

    return app
