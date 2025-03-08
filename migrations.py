#!/usr/bin/env python
import os
import click
from flask.cli import with_appcontext
from flask_migrate import Migrate, init, migrate, upgrade, current, stamp
from app import create_app, db

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@click.group()
def cli():
    """Database migration commands."""
    pass

@cli.command()
@with_appcontext
def init_migrations():
    """Initialize a new migration repository."""
    init()
    click.echo('Initialized the migration repository.')

@cli.command()
@click.option('--message', '-m', default=None, help='Migration message')
@with_appcontext
def make_migrations(message):
    """Generate a new migration."""
    migrate(message=message)
    click.echo('Generated new migration.')

@cli.command()
@with_appcontext
def upgrade_db():
    """Upgrade the database to the latest revision."""
    upgrade()
    click.echo('Upgraded the database.')

@cli.command()
@with_appcontext
def stamp_db():
    """Stamp the database with the current migration version."""
    stamp()
    click.echo('Stamped the database with the current migration version.')

@cli.command()
@with_appcontext
def current_version():
    """Show current migration version."""
    current()

if __name__ == '__main__':
    cli() 