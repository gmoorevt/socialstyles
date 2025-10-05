#!/bin/bash

# Social Styles - Production Rollback Script
# Usage: ./scripts/rollback.sh <version-tag>
# Example: ./scripts/rollback.sh v20250104.120000

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
APP_DIR="/var/www/socialstyles"
BACKUP_DIR="/var/backups/socialstyles"

# Check if version tag is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version tag required${NC}"
    echo "Usage: $0 <version-tag>"
    echo ""
    echo "Available versions:"
    git tag -l | tail -10
    exit 1
fi

VERSION=$1

echo -e "${YELLOW}🔄 Starting rollback to version: $VERSION${NC}"
echo ""

# Navigate to app directory
cd $APP_DIR

# Verify version exists
if ! git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo -e "${RED}Error: Version $VERSION not found${NC}"
    echo ""
    echo "Available versions:"
    git tag -l | tail -10
    exit 1
fi

# Show current version
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
echo -e "Current version: ${YELLOW}$CURRENT_VERSION${NC}"
echo -e "Rolling back to: ${YELLOW}$VERSION${NC}"
echo ""

# Confirmation
read -p "Are you sure you want to rollback? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

echo ""

# Step 1: Checkout version
echo -e "${YELLOW}📦 Checking out version $VERSION...${NC}"
git fetch --all --tags
git checkout $VERSION

# Step 2: Install dependencies
echo -e "${YELLOW}📚 Installing dependencies...${NC}"
sudo -u socialstyles venv/bin/pip install -r requirements.txt --quiet

# Step 3: Database rollback (optional)
echo ""
echo -e "${YELLOW}Database rollback options:${NC}"
echo "1. Keep current database (code-only rollback)"
echo "2. Rollback database to match code version (dangerous!)"
echo "3. Restore from backup file"
read -p "Choose option (1/2/3): " db_option

case $db_option in
    1)
        echo "Keeping current database"
        ;;
    2)
        echo -e "${YELLOW}⚠️  Rolling back database migrations...${NC}"
        # Get migration ID for this version
        # This is risky - only do if you're sure!
        sudo -u socialstyles venv/bin/flask db downgrade
        ;;
    3)
        echo ""
        echo "Available backups:"
        ls -lh $BACKUP_DIR/*.sql.gz 2>/dev/null || echo "No backups found"
        echo ""
        read -p "Enter backup filename (or 'skip'): " backup_file

        if [ "$backup_file" != "skip" ] && [ -f "$BACKUP_DIR/$backup_file" ]; then
            echo -e "${YELLOW}💾 Restoring database from $backup_file...${NC}"

            # Extract database credentials from .env
            source .env
            export PGPASSWORD=$(echo $DATABASE_URL | sed -E 's/.*:\/\/[^:]*:([^@]*).*/\1/')
            DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:]*).*/\1/')
            DB_USER=$(echo $DATABASE_URL | sed -E 's/.*:\/\/([^:]*).*/\1/')
            DB_NAME=$(echo $DATABASE_URL | sed -E 's/.*\/([^?]*).*/\1/')

            # Restore backup
            gunzip -c "$BACKUP_DIR/$backup_file" | psql -h $DB_HOST -U $DB_USER -d $DB_NAME

            echo -e "${GREEN}✅ Database restored${NC}"
        else
            echo "Skipping database restore"
        fi
        ;;
    *)
        echo "Invalid option, keeping current database"
        ;;
esac

# Step 4: Restart application
echo ""
echo -e "${YELLOW}🔄 Restarting application...${NC}"
sudo systemctl restart socialstyles

# Wait for startup
sleep 5

# Step 5: Health check
echo -e "${YELLOW}🏥 Running health check...${NC}"

MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Rollback successful!${NC}"
        echo ""
        echo "Application is now running version: $VERSION"
        echo "Visit: https://teamsocialstyles.com"
        exit 0
    fi

    echo "⏳ Waiting for application... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 3
done

# Rollback failed
echo -e "${RED}❌ Health check failed!${NC}"
echo "Application may not be running correctly"
echo ""
echo "Check logs with: journalctl -u socialstyles -f"
echo ""

exit 1
