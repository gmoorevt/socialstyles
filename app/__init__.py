from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import os
from app.utils import get_version_info
import logging
import sys
from config import config

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

def create_app(config_name):
    """
    Create the Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Bind Socket.IO to the app so socketio.run() / live events work.
    # Without this, wsgi.py's socketio.run(app) crashes (eio is None).
    from app.websockets import init_websockets
    init_websockets(app)

    # Register blueprints
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.assessment import assessment as assessment_blueprint
    app.register_blueprint(assessment_blueprint, url_prefix='/assessment')

    from app.team import team as team_blueprint
    app.register_blueprint(team_blueprint, url_prefix='/team')

    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    # Expose the shared score->position helpers to all templates so every grid
    # renderer derives from one source of truth (app/assessment/geometry.py).
    from app.assessment import geometry
    app.jinja_env.globals.update(
        svg_position=geometry.svg_position,
        percent_position=geometry.percent_position,
        quadrant=geometry.quadrant,
        quadrant_color=geometry.quadrant_color,
        style_color=geometry.style_color,
    )

    # Configure error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
        
    return app
