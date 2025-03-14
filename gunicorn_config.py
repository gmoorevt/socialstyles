"""
Gunicorn configuration file for Social Styles Assessment application
"""
import multiprocessing
import os

# Bind to 0.0.0.0:8000 for development, use unix socket for production
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# Number of worker processes
# For development, use 2-4 workers
# For production, use (2 * CPU cores) + 1
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker class - use eventlet for WebSocket support
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "eventlet")

# Maximum number of simultaneous clients
max_requests = 1000
max_requests_jitter = 50

# Timeout for worker processes (seconds)
timeout = 30

# Restart workers after this many seconds
graceful_timeout = 30

# Log level
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Access log format
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Enable auto-reload for development
reload = os.getenv("FLASK_ENV", "production") == "development"

# Process name
proc_name = "socialstyles"

# Preload application for better performance
preload_app = True

# Security settings
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190 