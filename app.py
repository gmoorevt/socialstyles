"""
Legacy entry point for compatibility.
This file is maintained for backward compatibility.
Please use wsgi.py as the main entry point for the application.
"""

import os
from app import create_app
from app.websockets import socketio

app = create_app(os.getenv('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
