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

echo -e "${GREEN}Setting up cron job to check and restart Social Styles application...${NC}"

# Create the check script on the server
ssh $SSH_USER@$DROPLET_IP << 'EOF'
  echo "Creating service check script..."
  cat > /usr/local/bin/check_socialstyles.sh << 'SCRIPT'
#!/bin/bash

# Check if the service is running
if ! systemctl is-active --quiet socialstyles.service; then
  # Service is not running, restart it
  systemctl restart socialstyles.service
  
  # Log the restart
  echo "$(date): Social Styles service was down and has been restarted." >> /var/log/socialstyles_restarts.log
fi
SCRIPT

  # Make the script executable
  chmod +x /usr/local/bin/check_socialstyles.sh
  
  echo "Setting up cron job..."
  # Add cron job to check every 5 minutes
  (crontab -l 2>/dev/null | grep -v "check_socialstyles.sh"; echo "*/5 * * * * /usr/local/bin/check_socialstyles.sh") | crontab -
  
  echo "Cron job installed. Checking crontab:"
  crontab -l
EOF

echo -e "${GREEN}Cron job setup complete!${NC}"
echo -e "${YELLOW}The service will be checked every 5 minutes and restarted if it's down.${NC}" 