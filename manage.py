#!/usr/bin/env python
"""
Management script for database migrations and other management tasks.
This script is primarily used for database migrations with Flask-Migrate.

Usage examples:
  python manage.py db init
  python manage.py db migrate -m "Initial migration"
  python manage.py db upgrade
"""

import os
import click
from flask.cli import FlaskGroup
from app import create_app, db

def create_app_cli():
    return create_app(os.getenv('FLASK_CONFIG') or 'development')

@click.group(cls=FlaskGroup, create_app=create_app_cli)
def cli():
    """Management script for the Social Styles application."""
    pass

if __name__ == '__main__':
    cli() 