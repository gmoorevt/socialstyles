#!/bin/bash

# Configuration
BACKUP_DIR="/var/backups/socialstyles"
DB_NAME="socialstyles"
DB_USER="socialstyles"
DB_HOST="your-postgres-host"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/socialstyles_$TIMESTAMP.sql"

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

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup the database
print_message "Creating backup of $DB_NAME database..."
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -f $BACKUP_FILE

# Check if backup was successful
if [ $? -eq 0 ]; then
    print_message "Backup created successfully: $BACKUP_FILE"
    
    # Compress the backup
    gzip $BACKUP_FILE
    print_message "Backup compressed: $BACKUP_FILE.gz"
    
    # Remove backups older than 30 days
    find $BACKUP_DIR -name "socialstyles_*.sql.gz" -type f -mtime +30 -delete
    print_message "Old backups cleaned up"
else
    print_error "Backup failed!"
    exit 1
fi

# List current backups
print_message "Current backups:"
ls -lh $BACKUP_DIR 