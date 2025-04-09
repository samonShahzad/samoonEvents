import os
from dotenv import load_dotenv


load_dotenv()

class Config:
    # Secret key for session management (should be stored in environment variable)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    
    # SQLALCHEMY_DATABASE_URI = f"mysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST', 'localhost')}/{os.environ.get('DB_NAME')}"
    # SQLite Database URI (uses local file for storage)
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'app.db')}"
    
    # Disable modification tracking
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail server configuration (should be stored in environment variable)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
    MAIL_USE_TLS = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME

    # Define base directory
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Upload folder configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}