"""
Legacy entry point for compatibility.
This file is maintained for backward compatibility.
Please use wsgi.py as the main entry point for the application.
"""

import os
from wsgi import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
