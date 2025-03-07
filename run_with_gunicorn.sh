#!/bin/bash

# Run Social Styles Assessment with Gunicorn
# This script runs the application with Gunicorn for local testing

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}WARNING:${NC} Virtual environment not activated. Activating now..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}ERROR:${NC} Virtual environment not found. Please create one first:"
        echo "python -m venv venv && source venv/bin/activate"
        exit 1
    fi
fi

# Check if gunicorn is installed
if ! pip show gunicorn > /dev/null 2>&1; then
    echo -e "${YELLOW}Installing Gunicorn...${NC}"
    pip install gunicorn
fi

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
export GUNICORN_WORKERS=4  # Override the default in config
export GUNICORN_LOG_LEVEL=info

# Kill any existing gunicorn processes
pkill -f "gunicorn" || true

echo -e "${GREEN}Starting Social Styles Assessment with Gunicorn...${NC}"
echo -e "${YELLOW}The application will be available at:${NC} http://localhost:8000"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Run with gunicorn using the config file
# Using wsgi.py as the entry point
gunicorn -c gunicorn_config.py wsgi:app 