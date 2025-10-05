#!/bin/bash

# Social Styles - Production Server Setup Script
# This script sets up a fresh DigitalOcean droplet for production deployment
# Run this on the SERVER after creating the droplet

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Social Styles Production Server Setup ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Configuration
APP_NAME="socialstyles"
APP_DIR="/var/www/$APP_NAME"
GITHUB_REPO="https://github.com/gmoorevt/socialstyles.git"
GITHUB_BRANCH="main"

# Step 1: Update system
echo -e "${YELLOW}[1/10] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq
echo -e "${GREEN}✅ System updated${NC}"
echo ""

# Step 2: Install dependencies
echo -e "${YELLOW}[2/10] Installing dependencies...${NC}"
apt-get install -y -qq \
    python3-pip \
    python3-venv \
    nginx \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    postgresql-client \
    libpq-dev \
    curl \
    htop \
    ufw

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 3: Create application user
echo -e "${YELLOW}[3/10] Creating application user...${NC}"
if id "$APP_NAME" &>/dev/null; then
    echo "User $APP_NAME already exists"
else
    useradd -m -d "$APP_DIR" -s /bin/bash "$APP_NAME"
    usermod -aG www-data "$APP_NAME"
    echo -e "${GREEN}✅ User created: $APP_NAME${NC}"
fi
echo ""

# Step 4: Clone repository
echo -e "${YELLOW}[4/10] Cloning repository...${NC}"
if [ -d "$APP_DIR" ]; then
    echo "Directory $APP_DIR already exists, backing up..."
    mv "$APP_DIR" "${APP_DIR}.backup.$(date +%Y%m%d%H%M%S)"
fi

git clone -b "$GITHUB_BRANCH" "$GITHUB_REPO" "$APP_DIR"
chown -R "$APP_NAME:www-data" "$APP_DIR"
echo -e "${GREEN}✅ Repository cloned${NC}"
echo ""

# Step 5: Set up Python virtual environment
echo -e "${YELLOW}[5/10] Setting up Python virtual environment...${NC}"
cd "$APP_DIR"
python3 -m venv venv
chown -R "$APP_NAME:www-data" venv
sudo -u "$APP_NAME" venv/bin/pip install --upgrade pip -q
sudo -u "$APP_NAME" venv/bin/pip install -r requirements.txt -q
echo -e "${GREEN}✅ Virtual environment ready${NC}"
echo ""

# Step 6: Create .env file template
echo -e "${YELLOW}[6/10] Creating .env file template...${NC}"
cat > "$APP_DIR/.env" << 'EOF'
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=CHANGE-ME-TO-RANDOM-STRING
FLASK_DEBUG=0

# Database configuration (REQUIRED)
# Format: postgresql://user:password@host:port/database
DATABASE_URL=postgresql://user:password@localhost:5432/social_styles

# Mail configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# AWS SES configuration (optional)
USE_SES=False
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

MAIL_DEFAULT_SENDER=noreply@teamsocialstyles.com

# Application configuration
APP_NAME=Social Styles Assessment
ADMIN_EMAIL=admin@teamsocialstyles.com
EOF

chown "$APP_NAME:www-data" "$APP_DIR/.env"
chmod 640 "$APP_DIR/.env"

echo -e "${GREEN}✅ .env template created${NC}"
echo -e "${YELLOW}⚠️  IMPORTANT: Edit $APP_DIR/.env with your actual credentials!${NC}"
echo ""

# Step 7: Set up systemd service
echo -e "${YELLOW}[7/10] Setting up systemd service...${NC}"
cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Social Styles Assessment Application
After=network.target

[Service]
Type=notify
User=$APP_NAME
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"

# Using gunicorn with eventlet worker class for WebSocket support
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --bind 0.0.0.0:8000 \\
    --workers 4 \\
    --worker-class eventlet \\
    --timeout 60 \\
    --graceful-timeout 30 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --access-logfile - \\
    --error-logfile - \\
    wsgi:app

Restart=always
RestartSec=5
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${APP_NAME}.service
echo -e "${GREEN}✅ Systemd service configured${NC}"
echo ""

# Step 8: Set up Nginx
echo -e "${YELLOW}[8/10] Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/${APP_NAME} << 'EOF'
server {
    listen 80;
    server_name teamsocialstyles.com www.teamsocialstyles.com;

    # Real IP from Cloudflare
    real_ip_header CF-Connecting-IP;

    # Cloudflare IP ranges (IPv4) - update periodically
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

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;

        # Cloudflare specific headers
        proxy_set_header CF-Connecting-IP $http_cf_connecting_ip;
        proxy_set_header CF-IPCountry $http_cf_ipcountry;
        proxy_set_header CF-Ray $http_cf_ray;
        proxy_set_header CF-Visitor $http_cf_visitor;
    }

    location /static {
        alias /var/www/socialstyles/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:8000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_buffering off;
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
systemctl enable nginx

echo -e "${GREEN}✅ Nginx configured${NC}"
echo ""

# Step 9: Set up firewall
echo -e "${YELLOW}[9/10] Configuring firewall...${NC}"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
echo -e "${GREEN}✅ Firewall configured${NC}"
echo ""

# Step 10: Create backup directory
echo -e "${YELLOW}[10/10] Setting up backup directory...${NC}"
mkdir -p /var/backups/${APP_NAME}
chown -R "$APP_NAME:www-data" /var/backups/${APP_NAME}

# Create log directory
mkdir -p /var/log/${APP_NAME}
chown -R "$APP_NAME:www-data" /var/log/${APP_NAME}

echo -e "${GREEN}✅ Backup and log directories created${NC}"
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Server Setup Complete! 🎉            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo -e "${YELLOW}1. Edit the .env file with your credentials:${NC}"
echo "   nano $APP_DIR/.env"
echo ""
echo -e "${YELLOW}2. Set up your database:${NC}"
echo "   - Update DATABASE_URL in .env"
echo "   - Run migrations:"
echo "     cd $APP_DIR"
echo "     sudo -u $APP_NAME venv/bin/flask db upgrade"
echo "     sudo -u $APP_NAME venv/bin/python initialize_assessment.py"
echo ""
echo -e "${YELLOW}3. Generate a secure SECRET_KEY:${NC}"
echo "   python3 -c 'import secrets; print(secrets.token_hex(32))'"
echo ""
echo -e "${YELLOW}4. Start the application:${NC}"
echo "   systemctl start ${APP_NAME}"
echo "   systemctl status ${APP_NAME}"
echo ""
echo -e "${YELLOW}5. Test the application:${NC}"
echo "   curl http://localhost:8000/health"
echo ""
echo -e "${YELLOW}6. Update Cloudflare DNS:${NC}"
echo "   - Point teamsocialstyles.com to this server's IP"
echo "   - Point www.teamsocialstyles.com to this server's IP"
echo ""
echo -e "${BLUE}Server IP:${NC} $(curl -s ifconfig.me)"
echo ""
echo -e "${GREEN}Setup script completed successfully!${NC}"
