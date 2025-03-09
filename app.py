import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from initialize_assessment import initialize_assessment
import logging
import sys

# Set up logging
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Print environment variables for debugging
logger.info("Environment variables loaded:")
logger.info(f"USE_SES: {os.environ.get('USE_SES')}")
logger.info(f"AWS_REGION: {os.environ.get('AWS_REGION')}")
logger.info(f"AWS_ACCESS_KEY_ID: {os.environ.get('AWS_ACCESS_KEY_ID', 'Not set')[:4] if os.environ.get('AWS_ACCESS_KEY_ID') else 'Not set'}...")
logger.info(f"MAIL_DEFAULT_SENDER: {os.environ.get('MAIL_DEFAULT_SENDER')}")

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///social_styles.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # CSRF Configuration
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_SSL_STRICT'] = False  # Disable strict referrer checking
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600   # 1 hour token expiration
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'yes', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # AWS SES Configuration
    use_ses = os.environ.get('USE_SES', 'False').lower() in ['true', 'yes', '1']
    app.config['USE_SES'] = use_ses
    app.config['AWS_REGION'] = os.environ.get('AWS_REGION')
    app.config['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID')
    app.config['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    # Log configuration
    logger.info(f"App configuration:")
    logger.info(f"USE_SES: {use_ses}")
    logger.info(f"AWS_REGION: {app.config.get('AWS_REGION')}")
    logger.info(f"AWS_ACCESS_KEY_ID: {app.config.get('AWS_ACCESS_KEY_ID', 'Not set')[:4] if app.config.get('AWS_ACCESS_KEY_ID') else 'Not set'}...")
    logger.info(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)
    csrf.init_app(app)
    
    # Register blueprints
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.assessment import assessment as assessment_blueprint
    app.register_blueprint(assessment_blueprint, url_prefix='/assessment')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Create the application instance
app = create_app()
migrate = Migrate(app, db)

# Import models after app is created to avoid circular imports
from app.models import User, Assessment, AssessmentResult

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Assessment=Assessment, AssessmentResult=AssessmentResult)

@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@app.cli.command()  
def init_assessment():
    """Initialize the assessment with the correct questions."""
    initialize_assessment()



if __name__ == '__main__':
    app.run(debug=True)
