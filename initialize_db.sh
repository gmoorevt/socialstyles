#!/bin/bash

# Initialize the database for Social Styles Assessment
# This script creates all necessary database tables and initializes with default data

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

echo -e "${GREEN}Initializing database...${NC}"

# Create database tables
echo -e "${YELLOW}Creating database tables...${NC}"
flask shell << EOF
from app import db
db.create_all()
print("Database tables created successfully.")
exit()
EOF

# Initialize assessment data
echo -e "${YELLOW}Initializing assessment data...${NC}"
python initialize_assessment.py

echo -e "${GREEN}Database initialization complete!${NC}"
echo -e "You can now run the application with ${YELLOW}./run_dev.sh${NC}" 