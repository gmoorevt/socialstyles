#!/bin/bash

# Social Styles - Health Check Script
# Checks application health and optionally restarts if unhealthy

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
LOG_FILE="${LOG_FILE:-/var/log/socialstyles/health-check.log}"
AUTO_RESTART="${AUTO_RESTART:-false}"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Function to log
log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Function to check health
check_health() {
    # Try to get health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null)

    if [ "$response" = "200" ]; then
        # Get detailed health info
        health_data=$(curl -s "$HEALTH_URL" 2>/dev/null)

        if [ $? -eq 0 ]; then
            version=$(echo "$health_data" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
            status=$(echo "$health_data" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

            log "✅ Application healthy - Status: $status, Version: $version"
            return 0
        fi
    fi

    log "❌ Application unhealthy - HTTP status: $response"
    return 1
}

# Function to restart application
restart_app() {
    log "🔄 Restarting application..."

    systemctl restart socialstyles

    # Wait for restart
    sleep 5

    # Check if restart was successful
    if check_health; then
        log "✅ Application restarted successfully"
        return 0
    else
        log "❌ Application still unhealthy after restart"
        return 1
    fi
}

# Main health check
if check_health; then
    exit 0
else
    # Application is unhealthy
    if [ "$AUTO_RESTART" = "true" ]; then
        restart_app
        exit $?
    else
        log "⚠️  Application is unhealthy but AUTO_RESTART is disabled"
        exit 1
    fi
fi
