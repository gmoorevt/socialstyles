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

echo -e "${GREEN}Setting up systemd service for Social Styles application...${NC}"

# Copy the service file to the droplet
echo -e "${YELLOW}Copying service file to the droplet...${NC}"
scp socialstyles.service $SSH_USER@$DROPLET_IP:/tmp/

# Connect to the droplet and set up the service
ssh $SSH_USER@$DROPLET_IP << EOF
  echo "Moving service file to systemd directory..."
  mv /tmp/socialstyles.service /etc/systemd/system/
  
  echo "Reloading systemd daemon..."
  systemctl daemon-reload
  
  echo "Stopping supervisor service..."
  supervisorctl stop socialstyles
  
  echo "Disabling supervisor service on boot..."
  # Remove from supervisor config
  sed -i '/socialstyles/d' /etc/supervisor/conf.d/socialstyles.conf
  supervisorctl reread
  supervisorctl update
  
  echo "Enabling systemd service..."
  systemctl enable socialstyles.service
  
  echo "Starting systemd service..."
  systemctl start socialstyles.service
  
  echo "Checking service status..."
  systemctl status socialstyles.service
  
  echo "Done!"
EOF

echo -e "${GREEN}Systemd service setup complete!${NC}"
echo -e "${YELLOW}Your application will now start automatically on reboot.${NC}"
echo -e "${YELLOW}To check status: ssh $SSH_USER@$DROPLET_IP 'systemctl status socialstyles.service'${NC}"
echo -e "${YELLOW}To restart: ssh $SSH_USER@$DROPLET_IP 'systemctl restart socialstyles.service'${NC}" 