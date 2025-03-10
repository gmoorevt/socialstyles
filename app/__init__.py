from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import os
from app.utils import get_version_info
import logging
import sys

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# Set up logging
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def create_app(config_name=None):
    """Application factory pattern for creating Flask app"""
    app = Flask(__name__)
    
    # Determine config based on environment if not explicitly provided
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        if config_name == 'production':
            config_name = 'production'
        else:
            config_name = 'development'
    
    # Import configuration
    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
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
    
    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from app.team import team as team_blueprint
    app.register_blueprint(team_blueprint, url_prefix='/team')
    
    # Register custom commands
    from app.commands import register_commands
    register_commands(app)
    
    # Add version info to template context
    @app.context_processor
    def inject_version():
        return get_version_info()
    
    # Shell context processor for Flask CLI
    @app.shell_context_processor
    def make_shell_context():
        # Import all models here to make them available in shell context
        from app.models.user import User
        from app.models.assessment import Assessment, AssessmentResult
        from app.models.team import Team
        
        return {
            'db': db, 
            'User': User, 
            'Assessment': Assessment, 
            'AssessmentResult': AssessmentResult,
            'Team': Team
        }
        
    return app
