#!/bin/bash
set -e

# Simple deploy: push to main, SSH to server, pull & restart
# Usage: ./deploy.sh

SERVER="root@134.199.243.119"
APP_DIR="/var/www/socialstyles"

echo "==> Running tests..."
source venv/bin/activate 2>/dev/null || true
python test_assessment_math.py

echo "==> Pushing to GitHub..."
git push origin main

echo "==> Deploying to production..."
ssh "$SERVER" << 'EOF'
set -e
cd /var/www/socialstyles

# Pull latest
git fetch origin main
git reset --hard origin/main

# Install deps & migrate
sudo -u socialstyles venv/bin/pip install -r requirements.txt --quiet
sudo -u socialstyles FLASK_APP=wsgi.py FLASK_CONFIG=production venv/bin/flask db upgrade

# Restart
sudo systemctl restart socialstyles
sleep 3

# Health check
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "Deploy successful!"
else
    echo "Health check failed!" >&2
    exit 1
fi
EOF

echo "==> Done! https://teamsocialstyles.com"
