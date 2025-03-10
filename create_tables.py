from app import create_app, db
from app.models import Team, TeamMember, TeamInvite

app = create_app('development')
with app.app_context():
    # Create tables
    db.create_all()
    print("Tables created successfully!")
    
    # List all tables to verify
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("\nAvailable tables:")
    for table in tables:
        print(f"- {table}") 