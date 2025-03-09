import click
from flask.cli import with_appcontext
from app.models.user import User
from app.models.assessment import Assessment, AssessmentResult
from app import db
from initialize_assessment import initialize_assessment
import random
from datetime import datetime, timedelta
import uuid
import re

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

@click.command('create-test-data')
@click.option('--users', default=10, help='Number of test users to create')
@click.option('--results-per-user', default=2, help='Number of assessment results per user')
@with_appcontext
def create_test_data(users, results_per_user):
    """Generate test users with assessment results."""
    # Check if we have any assessments
    assessments = Assessment.query.all()
    if not assessments:
        click.echo('Error: No active assessments found. Please create at least one assessment first.')
        return
    
    social_styles = ['DRIVER', 'EXPRESSIVE', 'AMIABLE', 'ANALYTICAL']
    created_users = 0
    
    for i in range(users):
        # Create a unique email
        unique_id = str(uuid.uuid4())[:8]
        email = f'testuser{i}_{unique_id}@example.com'
        
        # Create user
        user = User(
            email=email,
            name=f'Test User {i+1}',
            password='password123',  # This would be hashed by the User model
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
            last_login=datetime.utcnow() - timedelta(days=random.randint(0, 30))
        )
        db.session.add(user)
        db.session.flush()  # Get the user ID without committing
        
        # Create assessment results for this user
        for j in range(results_per_user):
            # Pick a random assessment
            assessment = random.choice(assessments)
            
            # Create a result with random social style
            result = AssessmentResult(
                user_id=user.id,
                assessment_id=assessment.id,
                social_style=random.choice(social_styles),
                assertiveness_score=random.uniform(1.0, 10.0),
                responsiveness_score=random.uniform(1.0, 10.0),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(result)
        
        created_users += 1
    
    db.session.commit()
    click.echo(f'Successfully created {created_users} test users with {results_per_user} assessment results each.')

@click.command('delete-test-data')
@click.option('--confirm', is_flag=True, help='Confirm deletion without prompting')
@with_appcontext
def delete_test_data(confirm):
    """Delete all test users and their assessment results."""
    # Find all test users (matching the pattern testuser*@example.com)
    test_users = User.query.filter(User.email.like('testuser%@example.com')).all()
    
    if not test_users:
        click.echo('No test users found.')
        return
    
    user_count = len(test_users)
    
    if not confirm:
        click.confirm(f'This will delete {user_count} test users and all their assessment results. Continue?', abort=True)
    
    # Get IDs of all test users
    test_user_ids = [user.id for user in test_users]
    
    # Delete all assessment results for these users
    result_count = AssessmentResult.query.filter(AssessmentResult.user_id.in_(test_user_ids)).delete(synchronize_session=False)
    
    # Delete the test users
    for user in test_users:
        db.session.delete(user)
    
    db.session.commit()
    click.echo(f'Successfully deleted {user_count} test users and {result_count} assessment results.')

def register_commands(app):
    """Register custom commands with the Flask application."""
    app.cli.add_command(make_admin) 
    app.cli.add_command(init_assessment)
    app.cli.add_command(create_test_data)
    app.cli.add_command(delete_test_data)