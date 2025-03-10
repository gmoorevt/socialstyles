#!/bin/bash

# Social Styles Assessment - DigitalOcean Deployment Steps
# This script contains individual steps to deploy the application to DigitalOcean

# Configuration - MODIFY THESE VALUES
DROPLET_IP="159.89.95.194"
DOMAIN_NAME="teamsocialstyles.com"
SSH_KEY_PATH="~/.ssh/id_ed25519"
APP_NAME="socialstyles"
APP_DIR="/var/www/$APP_NAME"
GITHUB_REPO="https://github.com/gmoorevt/socialstyles.git"

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

# Function to run commands on the remote server
run_remote() {
    ssh -i "$SSH_KEY_PATH" root@"$DROPLET_IP" "$1"
}

# Function to copy files to the remote server
copy_to_remote() {
    scp -i "$SSH_KEY_PATH" "$1" root@"$DROPLET_IP":"$2"
}

# Display menu
show_menu() {
    echo "=== Social Styles Deployment Steps ==="
    echo "1. Update server and install dependencies"
    echo "2. Create application user"
    echo "3. Clone repository"
    echo "4. Set up Python virtual environment"
    echo "5. Set up production environment"
    echo "6. Initialize database"
    echo "7. Configure Nginx"
    echo "8. Set up systemd service"
    echo "9. Set up service monitoring"
    echo "10. Check deployment status"
    echo "11. Show Cloudflare setup instructions"
    echo "12. Run all steps (1-10)"
    echo "13. Install PostgreSQL driver"
    echo "14. Run database migrations"
    echo "15. Full deploy with database setup"
    echo "16. Update database only"
    echo "17. Initialize migrations directory"
    echo "18. Run migration diagnostics"
    echo "19. Direct fix for migrations"
    echo "0. Exit"
    echo "=================================="
}

# Step 1: Update server and install dependencies
step1() {
    print_message "Updating server and installing dependencies..."
    run_remote "apt-get update && apt-get upgrade -y && \
                apt-get install -y python3-pip python3-venv nginx git supervisor \
                build-essential libssl-dev libffi-dev python3-dev"
}

# Step 2: Create application user
step2() {
    print_message "Creating application user..."
    run_remote "id -u $APP_NAME &>/dev/null || useradd -m -d $APP_DIR -s /bin/bash $APP_NAME && \
                usermod -aG www-data $APP_NAME"
}

# Step 3: Clone repository
step3() {
    print_message "Cloning the repository..."
    run_remote "rm -rf $APP_DIR && \
                git clone -b feature/team-dimension $GITHUB_REPO $APP_DIR && \
                chown -R $APP_NAME:www-data $APP_DIR"
    
    # Copy version.txt file to ensure it's available
    copy_to_remote "version.txt" "$APP_DIR/version.txt"
    run_remote "chown $APP_NAME:www-data $APP_DIR/version.txt"
}

# Step 4: Set up Python virtual environment
step4() {
    print_message "Setting up Python virtual environment..."
    run_remote "cd $APP_DIR && \
                python3 -m venv venv && \
                chown -R $APP_NAME:www-data venv && \
                sudo -u $APP_NAME venv/bin/pip install --upgrade pip && \
                sudo -u $APP_NAME venv/bin/pip install -r requirements.txt"
}

# Step 5: Set up production environment
step5() {
    print_message "Setting up production environment..."
    print_message "Uploading .env file..."
    copy_to_remote ".env" "$APP_DIR/.env"
    run_remote "chown $APP_NAME:www-data $APP_DIR/.env"
}

# Step 6: Initialize database
step6() {
    print_message "Initializing the database..."
    run_remote "cd $APP_DIR && \
                sudo -u $APP_NAME venv/bin/python initialize_assessment.py"
                
    print_message "Running database migrations..."
    run_remote "cd $APP_DIR && \
                sudo -u $APP_NAME venv/bin/flask db upgrade"
}

# Step 7: Configure Nginx
step7() {
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
}

# Step 8: Set up systemd service
step8() {
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
}

# Step 9: Set up service monitoring
step9() {
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
}

# Step 10: Check deployment status
step10() {
    print_message "Checking deployment status..."
    run_remote "systemctl status socialstyles.service --no-pager"
    
    print_message "Deployment completed successfully!"
    print_message "Your application should now be running at: http://$DROPLET_IP"
    print_message "Once you configure Cloudflare, it will be available at: https://$DOMAIN_NAME"
}

# Step 11: Show Cloudflare setup instructions
step11() {
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
}

# Step 13: Install PostgreSQL driver
step13() {
    print_message "Installing PostgreSQL driver..."
    run_remote "cd $APP_DIR && \
                sudo -u $APP_NAME venv/bin/pip install psycopg2-binary"
}

# Step 13b: Initialize migrations directory
step13b() {
    print_message "Checking and initializing migrations directory if needed..."
    run_remote "cd $APP_DIR && \
                if [ ! -f migrations/env.py ]; then \
                  print_message 'Migrations directory not found or incomplete. Initializing...' && \
                  sudo -u $APP_NAME venv/bin/flask db init && \
                  chown -R $APP_NAME:www-data migrations; \
                fi"
}

# Step 14: Run database migrations
step14() {
    print_message "Checking migrations directory first..."
    step13b
    
    print_message "Running database migrations..."
    run_remote "cd $APP_DIR && \
                sudo -u $APP_NAME venv/bin/flask db upgrade"
    
    print_message "Initializing assessment data..."
    run_remote "cd $APP_DIR && \
                sudo -u $APP_NAME venv/bin/python initialize_assessment.py"
}

# Step 15: Full deploy with database setup
step15() {
    step3  # Clone repository
    step4  # Set up Python virtual environment
    # step5 is skipped to prevent updating the .env file
    step13 # Install PostgreSQL driver
    step14 # Run database migrations
    step8  # Set up systemd service (restart application)
    step10 # Check deployment status
}

# Step 16: Update database only
step16() {
    print_message "Updating database only..."
    step5  # Upload correct .env file
    step13 # Install PostgreSQL driver
    step14 # Run database migrations
    print_message "Restarting application service..."
    run_remote "systemctl restart socialstyles.service"
    step10 # Check deployment status
}

# Step 17: Initialize migrations directory
step17() {
    print_message "Initializing migrations directory..."
    step5  # Upload correct .env file
    step13 # Install PostgreSQL driver
    step13b # Initialize migrations
    print_message "Migrations directory initialized successfully."
}

# Step 18: Run detailed migration diagnostics
step18() {
    print_message "Running detailed migration diagnostics..."
    run_remote "cd $APP_DIR && \
                echo '=== ENV FILE CONTENTS ===' && \
                cat .env | grep -v SECRET && \
                echo '=== PYTHON VERSION ===' && \
                python3 --version && \
                echo '=== APP STRUCTURE ===' && \
                ls -la && \
                echo '=== MIGRATIONS DIRECTORY ===' && \
                ls -la migrations 2>/dev/null || echo 'Migrations directory does not exist' && \
                echo '=== FLASK CONFIG ===' && \
                sudo -u $APP_NAME venv/bin/python -c 'import os; print(\"FLASK_APP = \" + os.environ.get(\"FLASK_APP\", \"Not set\"))' && \
                echo '=== MANUALLY INITIALIZING MIGRATIONS ===' && \
                export FLASK_APP=wsgi.py && \
                cd $APP_DIR && \
                sudo -u $APP_NAME venv/bin/flask db init && \
                echo '=== MIGRATIONS AFTER INIT ===' && \
                ls -la migrations 2>/dev/null || echo 'Migrations directory still does not exist'"
    
    print_message "Diagnostics complete. Check the output for details."
}

# Step 19: Direct fix for migrations
step19() {
    print_message "Applying direct fix for migrations..."
    run_remote "cd $APP_DIR && \
                # Ensure correct environment variables are set
                export FLASK_APP=wsgi.py && \
                # Create migrations directory if it doesn't exist
                mkdir -p migrations && \
                chown -R $APP_NAME:www-data migrations && \
                # Force initialize migrations
                sudo -u $APP_NAME venv/bin/flask db init --force && \
                # Create a blank migration
                sudo -u $APP_NAME venv/bin/flask db migrate -m 'initial migration' && \
                # Apply the migration
                sudo -u $APP_NAME venv/bin/flask db upgrade && \
                # Run application initialization
                sudo -u $APP_NAME venv/bin/python initialize_assessment.py && \
                # Restart the service
                systemctl restart socialstyles.service"
    
    print_message "Direct migration fix applied."
}

# Run all steps
run_all() {
    step1
    step2
    step3
    step4
    step5
    step6
    step7
    step8
    step9
    step10
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (0-19): " choice
    
    case $choice in
        1) step1 ;;
        2) step2 ;;
        3) step3 ;;
        4) step4 ;;
        5) step5 ;;
        6) step6 ;;
        7) step7 ;;
        8) step8 ;;
        9) step9 ;;
        10) step10 ;;
        11) step11 ;;
        12) run_all ;;
        13) step13 ;;
        14) step14 ;;
        15) step15 ;;
        16) step16 ;;
        17) step17 ;;
        18) step18 ;;
        19) step19 ;;
        0) exit 0 ;;
        *) print_error "Invalid choice. Please try again." ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
    clear
done 