"""
Entry point for the web application.
This file is used for application deployment with WSGI servers like Gunicorn.
"""

import os
from app import create_app
from app.websockets import socketio

# Create the application instance using the configuration from environment
app = create_app(os.getenv('FLASK_CONFIG', 'production'))

if __name__ == '__main__':
    # Run the development server with socketio support
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
