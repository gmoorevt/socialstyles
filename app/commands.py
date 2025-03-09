import click
from flask.cli import with_appcontext
from app.models.user import User
from app import db
from initialize_assessment import initialize_assessment

@click.command('init-assessment')
@with_appcontext
def init_assessment():
    """Initialize the assessment with the correct questions."""
    initialize_assessment()


@click.command('make-admin')
@click.argument('email')
@with_appcontext
def make_admin(email):
    """Make a user an admin by email."""
    user = User.query.filter_by(email=email.lower()).first()
    if user is None:
        click.echo(f'Error: No user found with email {email}')
        return
    
    if user.is_admin:
        click.echo(f'User {user.name} is already an admin')
        return
    
    user.is_admin = True
    db.session.commit()
    click.echo(f'User {user.name} is now an admin')

def register_commands(app):
    """Register custom commands with the Flask application."""
    app.cli.add_command(make_admin) 
    app.cli.add_command(init_assessment)