"""
Entry point for the web application.
This file is used for application deployment with WSGI servers like Gunicorn.
"""

import os
from app import create_app

# Create the application instance using the configuration from environment
app = create_app(os.getenv('FLASK_CONFIG', 'production'))

if __name__ == '__main__':
    # Run the development server if this file is executed directly
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
