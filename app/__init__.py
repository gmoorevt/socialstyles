from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app(config_name='default'):
    app = Flask(__name__)
    
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
    
    # Register custom commands
    from app.commands import register_commands
    register_commands(app)
    
    # Add version info to template context
    from app.utils import get_version_info
    
    @app.context_processor
    def inject_version():
        return get_version_info()
    
    return app
