#!/bin/bash

# Run Social Styles Assessment with Flask development server
# This script runs the application with Flask for local development

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

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

echo -e "${GREEN}Starting Social Styles Assessment with Flask development server...${NC}"
echo -e "${YELLOW}The application will be available at:${NC} http://localhost:8080"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Run with Flask development server
flask run --host=0.0.0.0 --port=8080 