import os
from dotenv import load_dotenv

# Load environment variables from .env files
# First try .env.local if it exists (for local overrides)
# Then fall back to standard .env file
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
else:
    load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration class with settings common to all environments"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'yes', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # AWS SES Configuration - only loaded if USE_SES is True
    USE_SES = os.environ.get('USE_SES', 'False').lower() in ['true', 'yes', '1']
    AWS_REGION = os.environ.get('AWS_REGION')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    # CSRF settings
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_SSL_STRICT = False  # Disable strict referrer checking for better compatibility
    WTF_CSRF_TIME_LIMIT = 3600   # 1 hour token expiration
    
    # Application specific settings
    APP_NAME = os.environ.get('APP_NAME', 'Social Styles Assessment')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    
    @staticmethod
    def init_app(app):
        """Initialize the application with environment-specific settings"""
        pass


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "social_styles_dev.db")}'


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'  # In-memory database
    WTF_CSRF_ENABLED = False  # Disable CSRF during testing


class ProductionConfig(Config):
    """Production environment configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "social_styles.db")}'
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        # Log to stderr for production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


# Config dictionary maps environment names to config classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 