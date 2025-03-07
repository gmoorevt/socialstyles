#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
DROPLET_IP="67.205.184.178"
SSH_USER="root"
APP_PATH="/var/www/socialstyles"

echo -e "${GREEN}Updating and initializing the application on Digital Ocean droplet...${NC}"

# Copy the latest files to the droplet
echo -e "${YELLOW}Copying latest files to the droplet...${NC}"
rsync -avz --exclude venv --exclude __pycache__ --exclude .git \
    -e "ssh" \
    app app.py config.py gunicorn_config.py initialize_assessment.py requirements.txt wsgi.py \
    $SSH_USER@$DROPLET_IP:$APP_PATH/

# Connect to the droplet and run the database initialization commands
ssh $SSH_USER@$DROPLET_IP << EOF
  echo "Navigating to application directory..."
  cd $APP_PATH
  
  echo "Activating virtual environment..."
  source venv/bin/activate
  
  echo "Creating database tables..."
  python3 -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
  "
  
  echo "Initializing assessment data..."
  FLASK_ENV=production python initialize_assessment.py
  
  echo "Restarting the application..."
  sudo supervisorctl restart socialstyles
  
  echo "Done!"
EOF

echo -e "${GREEN}Update and initialization complete!${NC}"
echo -e "${YELLOW}Your application should now be fully functional at:${NC} http://$DROPLET_IP" 