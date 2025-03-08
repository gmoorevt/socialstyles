#!/usr/bin/env python
import os
from app import create_app, db
from flask_migrate import Migrate, MigrateCommand, upgrade
from app.models import User, Assessment, Question, Result

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Import all models here to make them available to Flask-Migrate
# This ensures all models are included in migrations

@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, Assessment=Assessment, 
                Question=Question, Result=Result)

if __name__ == '__main__':
    # This script can be used for database migrations and other management tasks
    # Example: python manage.py db init
    # Example: python manage.py db migrate -m "Initial migration"
    # Example: python manage.py db upgrade
    app.run() 