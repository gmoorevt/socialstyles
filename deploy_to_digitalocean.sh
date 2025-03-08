#!/bin/bash

# Social Styles Assessment - DigitalOcean Deployment Script
# This script deploys the Social Styles Assessment application to a DigitalOcean droplet

set -e  # Exit on error

# Configuration - MODIFY THESE VALUES
DROPLET_IP="134.209.128.212"  # e.g., "67.205.184.178"
DOMAIN_NAME="teamsocialstyles.com"
SSH_KEY_PATH="~/.ssh/id_ed25519"  # Updated to use your actual SSH key
APP_NAME="socialstyles"
APP_DIR="/var/www/$APP_NAME"
GITHUB_REPO="https://github.com/gmoorevt/socialstyles.git"
USE_CLOUDFLARE=true           # Using Cloudflare for DNS and SSL
USE_SSL=false                 # Set to false since Cloudflare will handle SSL

# SSH options to make connections more reliable
SSH_OPTS="-o ConnectTimeout=30 -o ServerAliveInterval=60 -o ServerAliveCountMax=30"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required variables are set
if [ "$DROPLET_IP" = "your_droplet_ip" ]; then
    print_error "Please set your DROPLET_IP in the script"
    exit 1
fi

# Function to run commands on the remote server
run_remote() {
    ssh $SSH_OPTS -i "$SSH_KEY_PATH" root@"$DROPLET_IP" "$1"
}

# Function to copy files to the remote server
copy_to_remote() {
    scp $SSH_OPTS -i "$SSH_KEY_PATH" "$1" root@"$DROPLET_IP":"$2"
}

# Main deployment process
print_message "Starting deployment to DigitalOcean droplet at $DROPLET_IP"
print_message "Domain: $DOMAIN_NAME (using Cloudflare)"

# 1. Update the server and install dependencies
print_message "Updating server and installing dependencies..."
run_remote "apt-get update && apt-get upgrade -y && \
            apt-get install -y python3-pip python3-venv nginx git supervisor \
            build-essential libssl-dev libffi-dev python3-dev"

# 2. Create application user
print_message "Creating application user..."
run_remote "id -u $APP_NAME &>/dev/null || useradd -m -d $APP_DIR -s /bin/bash $APP_NAME && \
            usermod -aG www-data $APP_NAME"

# 3. Clone the repository
print_message "Cloning the repository..."
run_remote "rm -rf $APP_DIR && \
            git clone $GITHUB_REPO $APP_DIR && \
            chown -R $APP_NAME:www-data $APP_DIR"

# Copy version.txt file to ensure it's available
copy_to_remote "version.txt" "$APP_DIR/version.txt"
run_remote "chown $APP_NAME:www-data $APP_DIR/version.txt"

# 4. Set up Python virtual environment
print_message "Setting up Python virtual environment..."
run_remote "cd $APP_DIR && \
            python3 -m venv venv && \
            chown -R $APP_NAME:www-data venv && \
            sudo -u $APP_NAME venv/bin/pip install --upgrade pip && \
            sudo -u $APP_NAME venv/bin/pip install -r requirements.txt"

# 5. Copy production environment file
print_message "Setting up production environment..."
copy_to_remote ".env.production" "$APP_DIR/.env"
run_remote "chown $APP_NAME:www-data $APP_DIR/.env"

# 6. Initialize the database
print_message "Initializing the database..."
run_remote "cd $APP_DIR && \
            sudo -u $APP_NAME venv/bin/python initialize_assessment.py"

# 7. Set up Nginx for Cloudflare
print_message "Configuring Nginx for Cloudflare..."

# Create Nginx config for Cloudflare
cat > nginx_config.conf << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    # Real IP from Cloudflare
    real_ip_header CF-Connecting-IP;
    
    # Cloudflare IP ranges (IPv4)
    # These are Cloudflare's IP ranges as of the script creation
    # You may need to update these: https://www.cloudflare.com/ips-v4
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 131.0.72.0/22;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Cloudflare specific headers
        proxy_set_header CF-Connecting-IP \$http_cf_connecting_ip;
        proxy_set_header CF-IPCountry \$http_cf_ipcountry;
        proxy_set_header CF-Ray \$http_cf_ray;
        proxy_set_header CF-Visitor \$http_cf_visitor;
    }
    
    location /static {
        alias $APP_DIR/app/static;
        expires 30d;
    }
}
EOF

# Copy and enable Nginx config
copy_to_remote "nginx_config.conf" "/etc/nginx/sites-available/$APP_NAME.conf"
run_remote "ln -sf /etc/nginx/sites-available/$APP_NAME.conf /etc/nginx/sites-enabled/ && \
            rm -f /etc/nginx/sites-enabled/default && \
            nginx -t && \
            systemctl restart nginx"
rm nginx_config.conf

# 8. Create systemd service file
print_message "Setting up systemd service..."
cat > socialstyles.service << EOF
[Unit]
Description=Social Styles Assessment Application
After=network.target

[Service]
User=$APP_NAME
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
Restart=always
RestartSec=5
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
EOF

copy_to_remote "socialstyles.service" "/etc/systemd/system/socialstyles.service"
run_remote "systemctl daemon-reload && \
            systemctl enable socialstyles.service && \
            systemctl start socialstyles.service"
rm socialstyles.service

# 9. Create a script to check and restart the service if needed
print_message "Setting up service monitoring..."
cat > check_and_restart_service.sh << EOF
#!/bin/bash
SERVICE_NAME="socialstyles.service"
if ! systemctl is-active --quiet \$SERVICE_NAME; then
    echo "\$(date): \$SERVICE_NAME is down, restarting..." >> /var/log/socialstyles_monitor.log
    systemctl restart \$SERVICE_NAME
else
    echo "\$(date): \$SERVICE_NAME is running" >> /var/log/socialstyles_monitor.log
fi
EOF

copy_to_remote "check_and_restart_service.sh" "/usr/local/bin/check_and_restart_service.sh"
run_remote "chmod +x /usr/local/bin/check_and_restart_service.sh && \
            (crontab -l 2>/dev/null; echo '*/5 * * * * /usr/local/bin/check_and_restart_service.sh') | crontab -"
rm check_and_restart_service.sh

# 10. Final status check
print_message "Checking deployment status..."
run_remote "systemctl status socialstyles.service --no-pager"

print_message "Deployment completed successfully!"
print_message "Your application should now be running at: http://$DROPLET_IP"
print_message "Once you configure Cloudflare, it will be available at: https://$DOMAIN_NAME"

# Instructions for Cloudflare setup
cat << EOF

=== CLOUDFLARE SETUP INSTRUCTIONS ===
1. Log in to your Cloudflare account
2. Add your domain (teamsocialstyles.com) if you haven't already
3. Set up an A record:
   - Name: @ (or leave blank for root domain)
   - IPv4 address: $DROPLET_IP
   - Proxy status: Proxied (orange cloud)

4. Set up another A record for www subdomain:
   - Name: www
   - IPv4 address: $DROPLET_IP
   - Proxy status: Proxied (orange cloud)

5. In Cloudflare SSL/TLS settings:
   - Set SSL/TLS encryption mode to "Full" (not "Full (strict)")
   - Enable "Always Use HTTPS" in the Edge Certificates section

6. In Cloudflare Page Rules, consider adding:
   - URL pattern: http://$DOMAIN_NAME/*
   - Setting: Always Use HTTPS

=== UPDATING THE APPLICATION ===
To update your application in the future, run:

ssh -i $SSH_KEY_PATH root@$DROPLET_IP
cd $APP_DIR
git pull
sudo -u $APP_NAME venv/bin/pip install -r requirements.txt
sudo systemctl restart socialstyles.service

=== MONITORING LOGS ===
To view application logs:

ssh -i $SSH_KEY_PATH root@$DROPLET_IP
journalctl -u socialstyles.service -f

EOF 