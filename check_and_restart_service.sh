#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
DROPLET_IP="67.205.184.178"
SSH_USER="root"

echo -e "${YELLOW}Checking Social Styles application service status...${NC}"

# Connect to the droplet and check service status
ssh $SSH_USER@$DROPLET_IP << EOF
  echo "Checking service status..."
  if systemctl is-active --quiet socialstyles.service; then
    echo -e "${GREEN}Service is running.${NC}"
  else
    echo -e "${RED}Service is not running. Attempting to start...${NC}"
    systemctl start socialstyles.service
    
    # Check if service started successfully
    if systemctl is-active --quiet socialstyles.service; then
      echo -e "${GREEN}Service started successfully.${NC}"
    else
      echo -e "${RED}Failed to start service. Checking logs...${NC}"
      journalctl -u socialstyles.service -n 50 --no-pager
    fi
  fi
  
  echo "Current service status:"
  systemctl status socialstyles.service
EOF

echo -e "${GREEN}Check complete!${NC}" 