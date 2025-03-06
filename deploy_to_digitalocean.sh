#!/bin/bash

# Social Styles Assessment Application Deployment Script for Digital Ocean
# This script automates the deployment of the Social Styles Assessment application to a Digital Ocean droplet

# Exit on error
set -e

# Configuration variables - CHANGE THESE
DROPLET_IP=""
SSH_USER="root"
APP_NAME="social-styles"
DOMAIN_NAME=""  # Optional: your domain name if you have one
SSH_KEY_PATH="$HOME/.ssh/id_rsa"  # Path to your SSH key

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

check_variables() {
    if [ -z "$DROPLET_IP" ]; then
        print_error "Please set the DROPLET_IP variable in the script"
        exit 1
    fi
}

# Check if required variables are set
check_variables

# Confirm deployment
echo -e "${YELLOW}This script will deploy the Social Styles Assessment application to:${NC}"
echo "  - Droplet IP: $DROPLET_IP"
echo "  - SSH User: $SSH_USER"
echo "  - App Name: $APP_NAME"
if [ ! -z "$DOMAIN_NAME" ]; then
    echo "  - Domain: $DOMAIN_NAME"
fi
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 1: Prepare local files for deployment
print_step "Preparing local files for deployment"

# Create a production .env file
cat > .env.production << EOF
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 24)
FLASK_DEBUG=0
EOF

# Create a requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    print_warning "requirements.txt not found, creating one"
    pip freeze > requirements.txt
fi

# Step 2: Set up the server
print_step "Setting up the server"

ssh -i "$SSH_KEY_PATH" "$SSH_USER@$DROPLET_IP" << 'ENDSSH'
# Update package lists
apt-get update

# Install required packages
apt-get install -y python3-pip python3-venv nginx supervisor

# Create app directory
mkdir -p /var/www/social-styles

# Create a user for the application
if ! id -u social-styles &>/dev/null; then
    useradd -m -s /bin/bash social-styles
    echo "Created user: social-styles"
fi

# Give ownership of the app directory to the new user
chown -R social-styles:social-styles /var/www/social-styles
ENDSSH

# Step 3: Copy application files
print_step "Copying application files to the server"

# Create a temporary directory for files to transfer
mkdir -p deploy_tmp
cp -r app deploy_tmp/
cp -r static deploy_tmp/
cp app.py deploy_tmp/
cp requirements.txt deploy_tmp/
cp .env.production deploy_tmp/.env
cp initialize_assessment.py deploy_tmp/

# Transfer files to the server
rsync -avz --exclude venv --exclude __pycache__ --exclude .git \
    -e "ssh -i $SSH_KEY_PATH" \
    deploy_tmp/ "$SSH_USER@$DROPLET_IP:/var/www/$APP_NAME/"

# Clean up temporary directory
rm -rf deploy_tmp

# Step 4: Set up the Python environment and install dependencies
print_step "Setting up Python environment and installing dependencies"

ssh -i "$SSH_KEY_PATH" "$SSH_USER@$DROPLET_IP" << ENDSSH
# Set up Python virtual environment
cd /var/www/$APP_NAME
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Initialize the database
python initialize_assessment.py

# Set proper permissions
chown -R social-styles:social-styles /var/www/$APP_NAME
ENDSSH

# Step 5: Configure Supervisor
print_step "Configuring Supervisor"

ssh -i "$SSH_KEY_PATH" "$SSH_USER@$DROPLET_IP" << ENDSSH
# Create Supervisor configuration
cat > /etc/supervisor/conf.d/$APP_NAME.conf << EOF
[program:$APP_NAME]
directory=/var/www/$APP_NAME
command=/var/www/$APP_NAME/venv/bin/gunicorn --workers 3 --bind unix:/var/www/$APP_NAME/$APP_NAME.sock -m 007 app:app
user=social-styles
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/$APP_NAME/gunicorn.err.log
stdout_logfile=/var/log/$APP_NAME/gunicorn.out.log
environment=PATH="/var/www/$APP_NAME/venv/bin"
EOF

# Create log directory
mkdir -p /var/log/$APP_NAME
chown -R social-styles:social-styles /var/log/$APP_NAME

# Reload Supervisor
supervisorctl reread
supervisorctl update
supervisorctl restart $APP_NAME
ENDSSH

# Step 6: Configure Nginx
print_step "Configuring Nginx"

if [ -z "$DOMAIN_NAME" ]; then
    # Configuration without domain name
    ssh -i "$SSH_KEY_PATH" "$SSH_USER@$DROPLET_IP" << ENDSSH
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $DROPLET_IP;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/$APP_NAME/$APP_NAME.sock;
    }

    location /static {
        alias /var/www/$APP_NAME/static;
    }
}
EOF
ENDSSH
else
    # Configuration with domain name
    ssh -i "$SSH_KEY_PATH" "$SSH_USER@$DROPLET_IP" << ENDSSH
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/$APP_NAME/$APP_NAME.sock;
    }

    location /static {
        alias /var/www/$APP_NAME/static;
    }
}
EOF
ENDSSH
fi

# Enable the site and restart Nginx
ssh -i "$SSH_KEY_PATH" "$SSH_USER@$DROPLET_IP" << ENDSSH
# Create proxy_params if it doesn't exist
if [ ! -f /etc/nginx/proxy_params ]; then
    cat > /etc/nginx/proxy_params << EOF
proxy_set_header Host \$http_host;
proxy_set_header X-Real-IP \$remote_addr;
proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto \$scheme;
EOF
fi

# Enable the site
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx

# Configure firewall if it's active
if command -v ufw &> /dev/null; then
    ufw allow 'Nginx Full'
fi
ENDSSH

# Step 7: Set up SSL with Let's Encrypt (if domain is provided)
if [ ! -z "$DOMAIN_NAME" ]; then
    print_step "Setting up SSL with Let's Encrypt"
    
    ssh -i "$SSH_KEY_PATH" "$SSH_USER@$DROPLET_IP" << ENDSSH
    # Install Certbot
    apt-get install -y certbot python3-certbot-nginx
    
    # Obtain SSL certificate
    certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME
    
    # Auto-renew cron job
    echo "0 3 * * * certbot renew --quiet" | crontab -
ENDSSH
fi

# Step 8: Final checks
print_step "Performing final checks"

ssh -i "$SSH_KEY_PATH" "$SSH_USER@$DROPLET_IP" << ENDSSH
# Check if Supervisor is running our app
supervisorctl status $APP_NAME

# Check if Nginx is running
systemctl status nginx | grep "Active:" || true
ENDSSH

# Deployment complete
echo ""
echo -e "${GREEN}Deployment complete!${NC}"
if [ -z "$DOMAIN_NAME" ]; then
    echo -e "Your Social Styles Assessment application is now available at: ${YELLOW}http://$DROPLET_IP${NC}"
else
    echo -e "Your Social Styles Assessment application is now available at: ${YELLOW}https://$DOMAIN_NAME${NC}"
fi
echo ""
echo "To make changes to your deployment:"
echo "1. SSH into your server: ssh $SSH_USER@$DROPLET_IP"
echo "2. Navigate to the app directory: cd /var/www/$APP_NAME"
echo "3. Restart the application: sudo supervisorctl restart $APP_NAME"
echo "" 