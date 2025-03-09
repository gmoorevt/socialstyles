import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Load environment variables
load_dotenv()

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
    app.config['USE_SES'] = os.environ.get('USE_SES', 'False').lower() in ['true', 'yes', '1']
    app.config['AWS_REGION'] = os.environ.get('AWS_REGION')
    app.config['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID')
    app.config['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
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
def init_db():
    """Initialize the database with default assessment."""
    with app.app_context():
        db.create_all()
        
        # Check if assessment already exists
        if Assessment.query.first() is None:
            # Create the Social Styles assessment
            import json
            
            questions = [
                {"id": 1, "text": "I tend to be direct and straightforward when dealing with others.", "category": "assertiveness"},
                {"id": 2, "text": "I tend to speak quickly and state my views forcefully.", "category": "assertiveness"},
                {"id": 3, "text": "I tend to be competitive and results-oriented.", "category": "assertiveness"},
                {"id": 4, "text": "I tend to be decisive and quick to make decisions.", "category": "assertiveness"},
                {"id": 5, "text": "I tend to be strong-willed and determined.", "category": "assertiveness"},
                {"id": 6, "text": "I tend to be assertive and take charge in group situations.", "category": "assertiveness"},
                {"id": 7, "text": "I tend to be focused on tasks rather than people.", "category": "assertiveness"},
                {"id": 8, "text": "I tend to be confrontational when I disagree with others.", "category": "assertiveness"},
                {"id": 9, "text": "I tend to be impatient when things move too slowly.", "category": "assertiveness"},
                {"id": 10, "text": "I tend to be blunt and tell it like it is.", "category": "assertiveness"},
                {"id": 11, "text": "I tend to show my emotions openly.", "category": "responsiveness"},
                {"id": 12, "text": "I tend to be warm and friendly in my interactions.", "category": "responsiveness"},
                {"id": 13, "text": "I tend to be enthusiastic and expressive.", "category": "responsiveness"},
                {"id": 14, "text": "I tend to be people-oriented rather than task-oriented.", "category": "responsiveness"},
                {"id": 15, "text": "I tend to be collaborative and seek consensus.", "category": "responsiveness"},
                {"id": 16, "text": "I tend to be supportive and encouraging of others.", "category": "responsiveness"},
                {"id": 17, "text": "I tend to be relationship-focused in my work.", "category": "responsiveness"},
                {"id": 18, "text": "I tend to be empathetic and sensitive to others' feelings.", "category": "responsiveness"},
                {"id": 19, "text": "I tend to be talkative and sociable.", "category": "responsiveness"},
                {"id": 20, "text": "I tend to be open and share personal information.", "category": "responsiveness"}
            ]
            
            assessment = Assessment(
                name="Social Styles Assessment",
                description="This assessment helps identify your social style based on assertiveness and responsiveness dimensions.",
                questions=json.dumps(questions)
            )
            
            db.session.add(assessment)
            db.session.commit()
            
            print("Database initialized with Social Styles Assessment.")

if __name__ == '__main__':
    app.run(debug=True)
