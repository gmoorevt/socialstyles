#!/bin/bash

# Social Styles Assessment - Improved DigitalOcean Deployment Script
# This script provides a streamlined process for deploying the application to DigitalOcean

# Configuration - MODIFY THESE VALUES
DROPLET_IP="159.89.95.194"
DOMAIN_NAME="teamsocialstyles.com"
SSH_KEY_PATH="~/.ssh/id_ed25519"
APP_NAME="socialstyles"
APP_DIR="/var/www/$APP_NAME"
GITHUB_REPO="https://github.com/gmoorevt/socialstyles.git"
GITHUB_BRANCH="feature/team-dimension"  # The branch to deploy
DB_USER="social_user"                   # PostgreSQL database user
DB_NAME="social_styles"                 # PostgreSQL database name

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to run commands on the remote server with improved error handling
run_remote() {
    local command="$1"
    local result
    
    print_message "Running remote command: $command"
    result=$(ssh -i "$SSH_KEY_PATH" root@"$DROPLET_IP" "$command" 2>&1)
    local status=$?
    
    if [ $status -ne 0 ]; then
        print_error "Remote command failed with exit code $status"
        print_error "Output: $result"
        return $status
    else
        echo "$result"
        return 0
    fi
}

# Function to copy files to the remote server with improved error handling
copy_to_remote() {
    local source="$1"
    local destination="$2"
    
    print_message "Copying $source to $destination on remote server"
    scp -i "$SSH_KEY_PATH" "$source" root@"$DROPLET_IP":"$destination"
    local status=$?
    
    if [ $status -ne 0 ]; then
        print_error "Failed to copy file to remote server"
        return $status
    else
        print_message "File copied successfully"
        return 0
    fi
}

# Function to check git repository details
check_git_repo() {
    print_message "Checking git repository details..."
    
    # Check if we can access the repository
    print_message "Testing repository access locally..."
    if ! git ls-remote --heads "$GITHUB_REPO" > /dev/null 2>&1; then
        print_error "Cannot access repository: $GITHUB_REPO"
        print_message "Make sure:"
        print_message "1. The repository URL is correct"
        print_message "2. The repository is public or you have proper SSH keys configured"
        print_message "3. Your network allows the connection"
        return 1
    fi
    
    # Check if the specified branch exists
    print_message "Checking if branch '$GITHUB_BRANCH' exists..."
    if ! git ls-remote --heads "$GITHUB_REPO" "$GITHUB_BRANCH" | grep -q "$GITHUB_BRANCH"; then
        print_error "Branch '$GITHUB_BRANCH' does not exist in repository"
        print_message "Available branches:"
        git ls-remote --heads "$GITHUB_REPO" | awk '{print $2}' | sed 's/refs\/heads\///'
        return 1
    fi
    
    print_message "Repository and branch confirmed accessible"
    return 0
}

# Function to validate .env file before uploading
validate_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create one before continuing."
        return 1
    fi
    
    # Check for essential variables
    local missing_vars=()
    
    # PostgreSQL database connection should be configured
    if ! grep -q "DATABASE_URL=" .env; then
        missing_vars+=("DATABASE_URL")
    fi
    
    # Check for other essential variables
    if ! grep -q "SECRET_KEY=" .env; then
        missing_vars+=("SECRET_KEY")
    fi
    
    if ! grep -q "FLASK_APP=" .env; then
        missing_vars+=("FLASK_APP")
    fi
    
    # If any essential variables are missing, print error and return
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Essential variables missing from .env file:"
        for var in "${missing_vars[@]}"; do
            print_error "- $var"
        done
        print_message "Please add these variables to your .env file before continuing."
        return 1
    fi
    
    # Ensure DATABASE_URL is using PostgreSQL
    if ! grep -q "DATABASE_URL=postgresql://" .env; then
        print_warning "DATABASE_URL does not appear to be a PostgreSQL connection string."
        print_warning "Make sure it's in the format: postgresql://username:password@hostname:port/database"
        read -p "Continue anyway? (y/n) " continue_anyway
        if [[ $continue_anyway != "y" ]]; then
            return 1
        fi
    fi
    
    # Ensure FLASK_APP is set to wsgi.py
    if ! grep -q "FLASK_APP=wsgi.py" .env; then
        print_warning "FLASK_APP should be set to wsgi.py for production."
        sed -i '' "s/FLASK_APP=.*/FLASK_APP=wsgi.py/" .env || print_warning "Could not automatically fix FLASK_APP"
    fi
    
    # Ensure FLASK_ENV is set to production
    if grep -q "FLASK_ENV=development" .env; then
        print_warning "FLASK_ENV is set to development. Changing to production."
        sed -i '' "s/FLASK_ENV=development/FLASK_ENV=production/" .env || print_warning "Could not automatically fix FLASK_ENV"
    fi
    
    print_message ".env file validation passed."
    return 0
}

# Display menu
show_menu() {
    echo "=== Social Styles Improved Deployment Steps ==="
    echo "1. Check prerequisites and setup"
    echo "2. Update server and install dependencies"
    echo "3. Set up PostgreSQL database"
    echo "4. Clone repository and set up environment"
    echo "5. Initialize application database"
    echo "6. Configure Nginx and SSL"
    echo "7. Set up systemd service"
    echo "8. Set up service monitoring"
    echo "9. Test deployment"
    echo "10. Full deployment (runs all steps 1-9)"
    echo "11. Update application only (code and database)"
    echo "0. Exit"
    echo "======================================"
}

# Step 1: Check prerequisites and setup
step1() {
    print_step "Checking prerequisites and setup..."
    
    # Check if SSH key exists
    if [ ! -f "$SSH_KEY_PATH" ]; then
        print_error "SSH key not found at $SSH_KEY_PATH"
        print_message "Generate an SSH key with: ssh-keygen -t ed25519"
        return 1
    fi
    
    # Check if we can connect to the server
    print_message "Testing SSH connection to server..."
    if ! ssh -i "$SSH_KEY_PATH" root@"$DROPLET_IP" "echo Connection successful" > /dev/null 2>&1; then
        print_error "Cannot connect to server. Please check:"
        print_message "1. The server IP address is correct"
        print_message "2. The SSH key is correctly configured"
        print_message "3. The server is running and accessible"
        return 1
    fi
    
    # Check Git repository access
    if ! check_git_repo; then
        return 1
    fi
    
    # Validate .env file
    if ! validate_env_file; then
        return 1
    fi
    
    print_message "All prerequisites checked successfully!"
    return 0
}

# Step 2: Update server and install dependencies
step2() {
    print_step "Updating server and installing dependencies..."
    
    run_remote "apt-get update && apt-get upgrade -y"
    
    # Install Python and web server dependencies
    run_remote "apt-get install -y python3-pip python3-venv nginx git supervisor \
                build-essential libssl-dev libffi-dev python3-dev"
    
    # Install PostgreSQL client libraries
    run_remote "apt-get install -y postgresql-client libpq-dev"
    
    # Create application user
    run_remote "id -u $APP_NAME &>/dev/null || useradd -m -d $APP_DIR -s /bin/bash $APP_NAME && \
                usermod -aG www-data $APP_NAME"
    
    print_message "Server updated and dependencies installed successfully!"
    return 0
}

# Step 3: Set up PostgreSQL database
step3() {
    print_step "Setting up PostgreSQL database (checking connection)..."
    
    # Check database connectivity using values from .env
    local db_url=$(grep "DATABASE_URL=" .env | cut -d '=' -f2-)
    
    # Try to connect to the database
    run_remote "apt-get install -y postgresql-client && \
                echo 'Testing database connection...' && \
                export PGPASSWORD=\$(echo '$db_url' | sed -E 's/.*:([^@]*)@.*/\1/') && \
                psql \$(echo '$db_url' | sed -E 's/postgresql:\/\/([^:]*):([^@]*)@([^:]*):([^\/]*)\/([^?]*).*/\5 -h \3 -p \4 -U \1/') -c 'SELECT 1;' && \
                echo 'Database connection successful!'"
    
    if [ $? -ne 0 ]; then
        print_error "Database connection failed. Please check your DATABASE_URL in .env"
        print_error "Make sure the PostgreSQL database is properly set up and accessible from your server"
        return 1
    fi
    
    print_message "PostgreSQL database connection verified successfully!"
    return 0
}

# Step 4: Clone repository and set up environment
step4() {
    print_step "Cloning repository and setting up environment..."
    
    # Remove existing directory if it exists
    run_remote "rm -rf $APP_DIR"
    
    # Clone the repository
    run_remote "git clone -b $GITHUB_BRANCH $GITHUB_REPO $APP_DIR && \
                chown -R $APP_NAME:www-data $APP_DIR"
    
    # Set up Python virtual environment
    run_remote "cd $APP_DIR && \
                python3 -m venv venv && \
                chown -R $APP_NAME:www-data venv && \
                sudo -u $APP_NAME venv/bin/pip install --upgrade pip && \
                sudo -u $APP_NAME venv/bin/pip install -r requirements.txt"
    
    # Upload .env file
    print_message "Uploading .env file..."
    copy_to_remote ".env" "$APP_DIR/.env"
    run_remote "chown $APP_NAME:www-data $APP_DIR/.env"
    
    print_message "Repository cloned and environment set up successfully!"
    return 0
}

# Step 5: Initialize application database
step5() {
    print_step "Initializing application database..."
    
    # Initialize migrations directory if needed
    run_remote "cd $APP_DIR && \
                export FLASK_APP=wsgi.py && \
                if [ ! -d 'migrations' ] || [ ! -f 'migrations/env.py' ]; then \
                    echo 'Initializing migrations directory...' && \
                    sudo -u $APP_NAME venv/bin/flask db init; \
                fi"
    
    # Run database migrations
    run_remote "cd $APP_DIR && \
                export FLASK_APP=wsgi.py && \
                sudo -u $APP_NAME venv/bin/flask db migrate -m 'initial migration' && \
                sudo -u $APP_NAME venv/bin/flask db upgrade"
    
    # Initialize assessment data
    run_remote "cd $APP_DIR && \
                export FLASK_APP=wsgi.py && \
                sudo -u $APP_NAME venv/bin/python initialize_assessment.py"
    
    print_message "Database initialization completed successfully!"
    return 0
}

# Step 6: Configure Nginx and SSL
step6() {
    print_step "Configuring Nginx..."
    
    # Create Nginx config file
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
    
    print_message "Nginx configuration completed successfully!"
    print_message "Note: SSL will be handled by Cloudflare."
    return 0
}

# Step 7: Set up systemd service
step7() {
    print_step "Setting up systemd service..."
    
    # Create systemd service file
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
    
    print_message "systemd service set up successfully!"
    return 0
}

# Step 8: Set up service monitoring
step8() {
    print_step "Setting up service monitoring..."
    
    # Create service monitoring script
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
    
    print_message "Service monitoring set up successfully!"
    return 0
}

# Step 9: Test deployment
step9() {
    print_step "Testing deployment..."
    
    # Check if the service is running
    run_remote "systemctl status socialstyles.service --no-pager"
    
    # Check if Nginx is running and configured correctly
    run_remote "systemctl status nginx --no-pager && \
                nginx -t"
    
    # Try to access the application
    run_remote "curl -I http://localhost:8000/ || echo 'Warning: Could not access application directly'"
    
    print_message "Deployment test completed!"
    echo
    print_message "Your application should now be running at: http://$DROPLET_IP"
    print_message "Once you configure Cloudflare, it will be available at: https://$DOMAIN_NAME"
    echo
    print_message "Cloudflare setup instruction:"
    print_message "1. Add an A record for @ pointing to $DROPLET_IP"
    print_message "2. Add an A record for www pointing to $DROPLET_IP"
    print_message "3. Set SSL/TLS encryption mode to Full"
    print_message "4. Enable Always Use HTTPS in Edge Certificates section"
    
    return 0
}

# Run all steps
run_all() {
    local failed=0
    
    step1 || { failed=1; print_error "Step 1 failed"; }
    
    if [ $failed -eq 0 ]; then
        step2 || { failed=1; print_error "Step 2 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step3 || { failed=1; print_error "Step 3 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step4 || { failed=1; print_error "Step 4 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step5 || { failed=1; print_error "Step 5 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step6 || { failed=1; print_error "Step 6 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step7 || { failed=1; print_error "Step 7 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step8 || { failed=1; print_error "Step 8 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step9 || { failed=1; print_error "Step 9 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        print_message "All steps completed successfully!"
    else
        print_error "Deployment failed. Please check the errors above."
    fi
}

# Update application only
update_app() {
    print_step "Updating application only (code and database)..."
    
    # Update repository
    run_remote "cd $APP_DIR && \
                git pull && \
                chown -R $APP_NAME:www-data $APP_DIR"
    
    # Update dependencies
    run_remote "cd $APP_DIR && \
                sudo -u $APP_NAME venv/bin/pip install -r requirements.txt"
    
    # Run database migrations
    run_remote "cd $APP_DIR && \
                export FLASK_APP=wsgi.py && \
                sudo -u $APP_NAME venv/bin/flask db upgrade"
    
    # Restart service
    run_remote "systemctl restart socialstyles.service"
    
    print_message "Application updated successfully!"
    return 0
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (0-11): " choice
    
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
        10) run_all ;;
        11) update_app ;;
        0) exit 0 ;;
        *) print_error "Invalid choice. Please try again." ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
    clear
done 