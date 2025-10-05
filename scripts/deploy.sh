#!/bin/bash

# Social Styles - Manual Deployment Script
# For use when GitHub Actions is unavailable
# Usage: ./scripts/deploy.sh [staging|production]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment-specific settings
if [ "$ENVIRONMENT" = "staging" ]; then
    SERVER_HOST="${STAGING_SSH_HOST:-staging.example.com}"
    SERVER_USER="${STAGING_SSH_USER:-root}"
    APP_DIR="/var/www/socialstyles-staging"
    BRANCH="staging"
    PORT="8001"
elif [ "$ENVIRONMENT" = "production" ]; then
    SERVER_HOST="${PROD_SSH_HOST:-134.209.128.212}"
    SERVER_USER="${PROD_SSH_USER:-root}"
    APP_DIR="/var/www/socialstyles"
    BRANCH="main"
    PORT="8000"
else
    echo -e "${RED}Error: Invalid environment. Use 'staging' or 'production'${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Social Styles Manual Deployment     ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo ""
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Server: ${YELLOW}$SERVER_HOST${NC}"
echo -e "Branch: ${YELLOW}$BRANCH${NC}"
echo ""

# Confirmation
read -p "Continue with deployment? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""

# Step 1: Run tests locally
echo -e "${YELLOW}📋 Running tests locally...${NC}"
cd "$PROJECT_DIR"

if python3 test_assessment_math.py && python3 test_team_dashboard.py; then
    echo -e "${GREEN}✅ Tests passed${NC}"
else
    echo -e "${RED}❌ Tests failed${NC}"
    read -p "Continue anyway? (yes/no): " continue_anyway
    if [ "$continue_anyway" != "yes" ]; then
        exit 1
    fi
fi

echo ""

# Step 2: Create deployment tag (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}🏷️  Creating deployment tag...${NC}"
    VERSION=$(date +%Y%m%d.%H%M%S)
    DEPLOY_TAG="v${VERSION}"

    git tag "$DEPLOY_TAG"
    echo -e "Created tag: ${GREEN}$DEPLOY_TAG${NC}"
    echo ""
fi

# Step 3: Deploy to server
echo -e "${YELLOW}🚀 Deploying to $ENVIRONMENT server...${NC}"

ssh "$SERVER_USER@$SERVER_HOST" << EOF
    set -e

    echo "📦 Starting deployment on server..."

    # Navigate to app directory
    cd $APP_DIR

    # Backup database (production only)
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "💾 Creating database backup..."

        BACKUP_DIR="/var/backups/socialstyles"
        mkdir -p \$BACKUP_DIR

        BACKUP_FILE="\$BACKUP_DIR/backup-\$(date +%Y%m%d-%H%M%S).sql.gz"

        source .env
        if [[ \$DATABASE_URL == postgresql://* ]]; then
            export PGPASSWORD=\$(echo \$DATABASE_URL | sed -E 's/.*:\/\/[^:]*:([^@]*).*/\1/')
            DB_HOST=\$(echo \$DATABASE_URL | sed -E 's/.*@([^:]*).*/\1/')
            DB_USER=\$(echo \$DATABASE_URL | sed -E 's/.*:\/\/([^:]*).*/\1/')
            DB_NAME=\$(echo \$DATABASE_URL | sed -E 's/.*\/([^?]*).*/\1/')

            pg_dump -h \$DB_HOST -U \$DB_USER \$DB_NAME | gzip > \$BACKUP_FILE
            echo "✅ Backup created: \$BACKUP_FILE"
        fi
    fi

    # Pull latest code
    echo "📥 Pulling latest code..."
    git fetch origin $BRANCH
    git reset --hard origin/$BRANCH

    # Install dependencies
    echo "📚 Installing dependencies..."
    sudo -u socialstyles venv/bin/pip install -r requirements.txt --quiet

    # Run migrations
    echo "📊 Running database migrations..."
    sudo -u socialstyles venv/bin/flask db upgrade || echo "⚠️  No migrations to run"

    # Restart application
    echo "🔄 Restarting application..."
    sudo systemctl reload socialstyles || sudo systemctl restart socialstyles

    # Wait for startup
    sleep 5

    # Health check
    echo "🏥 Running health check..."

    MAX_RETRIES=5
    RETRY_COUNT=0

    while [ \$RETRY_COUNT -lt \$MAX_RETRIES ]; do
        if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
            echo "✅ Deployment successful!"
            exit 0
        fi

        echo "⏳ Waiting for application... (attempt \$((RETRY_COUNT + 1))/\$MAX_RETRIES)"
        RETRY_COUNT=\$((RETRY_COUNT + 1))
        sleep 3
    done

    echo "❌ Health check failed!"
    exit 1
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   Deployment Successful! 🎉            ║${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo ""

    if [ "$ENVIRONMENT" = "production" ]; then
        echo -e "Tag: ${GREEN}$DEPLOY_TAG${NC}"
        echo ""
        read -p "Push tag to GitHub? (yes/no): " push_tag
        if [ "$push_tag" = "yes" ]; then
            git push origin "$DEPLOY_TAG"
            echo -e "${GREEN}✅ Tag pushed to GitHub${NC}"
        fi
    fi

    echo ""
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "Visit: https://teamsocialstyles.com"
    else
        echo "Visit: https://staging.teamsocialstyles.com"
    fi
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   Deployment Failed! ❌                ║${NC}"
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo ""
    echo "Check logs with: ssh $SERVER_USER@$SERVER_HOST 'journalctl -u socialstyles -f'"
    exit 1
fi
