"""
WSGI entry point for Gunicorn
"""
from app import create_app

# Create the application instance
application = create_app()

# For Gunicorn
app = application

if __name__ == '__main__':
    application.run() 