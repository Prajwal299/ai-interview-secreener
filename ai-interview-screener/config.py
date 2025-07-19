import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base directory for the project
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Security and Database Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Grok Configuration
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # Application Configuration
    BASE_URL = os.environ.get('BASE_URL', 'http://13.203.2.67:5000')
    
    # Upload Configuration
    UPLOAD_FOLDER = 'instance/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Logging Configuration
    LOG_FILE = 'instance/app.log'
    LOG_LEVEL = 'DEBUG'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5