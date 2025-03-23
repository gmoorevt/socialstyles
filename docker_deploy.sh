#!/bin/bash

# Social Styles Assessment - Docker Deployment Script
# This script deploys the application using Docker
# Uses external PostgreSQL database service

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create one before continuing."
    exit 1
fi

# Validate DATABASE_URL in .env
if ! grep -q "^DATABASE_URL=" .env; then
    print_error "DATABASE_URL not found in .env file."
    print_message "Please add a valid PostgreSQL connection string to your .env file."
    print_message "Format: DATABASE_URL=postgresql://username:password@hostname:port/database"
    exit 1
fi

# Extract database connection info for validation
DB_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
print_message "Found database connection string in .env file."

# Display menu
show_menu() {
    echo "=== Social Styles Docker Deployment Steps ==="
    echo "1. Build Docker images"
    echo "2. Start Docker containers"
    echo "3. Initialize application database"
    echo "4. Show container logs"
    echo "5. Stop Docker containers"
    echo "6. Full deployment (runs steps 1-3)"
    echo "7. Check container status"
    echo "8. Troubleshoot common issues"
    echo "9. Test database connection"
    echo "0. Exit"
    echo "======================================"
}

# Check if container is running
check_container_running() {
    container_name=$(docker-compose ps --services | grep web)
    if [ -z "$container_name" ]; then
        print_error "Could not find web service in docker-compose.yml"
        return 1
    fi
    
    container_id=$(docker-compose ps -q web)
    if [ -z "$container_id" ]; then
        print_error "Web container is not created. Run option 2 first."
        return 1
    fi
    
    if ! docker ps | grep -q "$container_id"; then
        print_error "The web container exists but is not running."
        print_message "Container ID: $container_id"
        print_message "Container status:"
        docker ps -a | grep "$container_id"
        print_message "You can check container logs with option 4."
        return 1
    fi
    
    print_message "Web container is running with ID: $container_id"
    return 0
}

# Step 1: Build Docker images
step1() {
    print_step "Building Docker images..."
    docker-compose build
    
    if [ $? -eq 0 ]; then
        print_message "Docker images built successfully!"
        return 0
    else
        print_error "Failed to build Docker images."
        return 1
    fi
}

# Step 2: Start Docker containers
step2() {
    print_step "Starting Docker containers..."
    docker-compose up -d
    
    # Wait a moment for containers to start
    print_message "Waiting for containers to start..."
    sleep 5
    
    # Check if container is running
    if docker ps | grep -q "social-styles-web\|social_styles-web"; then
        print_message "Docker containers started successfully!"
        return 0
    else
        print_error "Failed to start Docker containers."
        print_message "Showing logs to help diagnose the issue:"
        docker-compose logs
        return 1
    fi
}

# Step 3: Initialize application database
step3() {
    print_step "Initializing application database..."
    
    # Check if container is running
    if ! check_container_running; then
        print_error "Cannot initialize database because the web container is not running."
        print_message "Please start the containers first with option 2."
        return 1
    fi
    
    # Test container connectivity
    print_message "Testing container connectivity..."
    if ! docker-compose exec -T web echo "Container is responsive"; then
        print_error "Cannot execute commands in the container."
        print_message "Container might be running but not responsive."
        print_message "Check logs with option 4 for more details."
        return 1
    fi
    
    # Check if PostgreSQL is accessible
    print_message "Checking database connection..."
    if ! docker-compose exec -T web python -c "from app import create_app, db; app = create_app('development'); app.app_context().push(); print('Trying to connect to:', db.engine.url); connection = db.engine.connect(); print('Database connection successful')" 2>&1; then
        print_error "Cannot connect to the PostgreSQL database."
        print_message "Please check your DATABASE_URL in the .env file and ensure the database is accessible."
        print_message "You can use option 9 to test the database connection."
        return 1
    fi
    
    # Run migrations with detailed output
    print_message "Running database migrations..."
    docker-compose exec -T web flask db upgrade
    local migrate_status=$?
    
    if [ $migrate_status -ne 0 ]; then
        print_error "Failed to run database migrations."
        print_message "Try running the migrations with more detailed output:"
        docker-compose exec -T web flask db upgrade --verbose
        return 1
    fi
    
    # Initialize assessment
    print_message "Initializing assessment data..."
    docker-compose exec -T web python manage.py init-assessment
    local init_status=$?
    
    if [ $init_status -ne 0 ]; then
        print_error "Failed to initialize assessment data."
        return 1
    fi
    
    print_message "Database initialization completed successfully!"
    return 0
}

# Step 4: Show container logs
step4() {
    print_step "Showing container logs (press Ctrl+C to exit)..."
    docker-compose logs
}

# Step 5: Stop Docker containers
step5() {
    print_step "Stopping Docker containers..."
    docker-compose down
    
    if [ $? -eq 0 ]; then
        print_message "Docker containers stopped successfully!"
        return 0
    else
        print_error "Failed to stop Docker containers."
        return 1
    fi
}

# Step 7: Check container status
step7() {
    print_step "Checking container status..."
    docker ps -a
    
    echo
    print_message "Container details:"
    docker-compose ps
}

# Step 8: Troubleshoot common issues
step8() {
    print_step "Troubleshooting common issues..."
    
    # Check for port conflicts
    print_message "Checking for port conflicts..."
    if lsof -i :5001 >/dev/null 2>&1; then
        print_error "Port 5001 is already in use. This will prevent the Docker container from starting."
        print_message "Running processes using port 5001:"
        lsof -i :5001
        print_message "You can either:"
        print_message "1. Stop the process using port 5001"
        print_message "2. Edit docker-compose.yml to use a different port (e.g., 5002:5000)"
    else
        print_message "Port 5001 is available. ✅"
    fi
    
    # Check Docker daemon status
    print_message "Checking Docker daemon status..."
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running."
        print_message "Try starting the Docker daemon:"
        print_message "sudo systemctl start docker (Linux)"
        print_message "Open Docker Desktop (Mac/Windows)"
    else
        print_message "Docker daemon is running. ✅"
    fi
    
    # Validate database URL
    print_message "Validating DATABASE_URL format..."
    db_url=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
    
    if [[ "$db_url" != postgresql://* ]]; then
        print_error "DATABASE_URL does not appear to be a valid PostgreSQL connection string."
        print_message "It should start with 'postgresql://' and include username, password, host, port, and database name."
    else
        print_message "DATABASE_URL format looks valid. ✅"
    fi
    
    # Check disk space
    print_message "Checking disk space..."
    df -h .
    
    # Check Docker network
    print_message "Checking Docker networks..."
    docker network ls
    
    # Clean up unused resources
    print_message "Do you want to clean up unused Docker resources? (y/n)"
    read -r cleanup
    if [[ $cleanup == "y" ]]; then
        print_message "Cleaning up unused Docker resources..."
        
        # Stop all running containers
        print_message "Stopping all running containers..."
        docker-compose down
        
        # Remove unused containers
        print_message "Removing unused containers..."
        docker container prune -f
        
        # Remove unused images
        print_message "Removing unused images..."
        docker image prune -f
        
        # Remove unused volumes
        print_message "Removing unused volumes..."
        docker volume prune -f
        
        # Remove unused networks
        print_message "Removing unused networks..."
        docker network prune -f
        
        print_message "Cleanup completed. You can now try deploying again."
    fi
}

# Step 9: Test database connection
step9() {
    print_step "Testing database connection..."
    
    # Extract connection details
    db_url=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
    
    if [[ -z "$db_url" ]]; then
        print_error "DATABASE_URL not found in .env file."
        return 1
    fi
    
    # Create a simple Python script to test the connection
    cat > test_db_connection.py << EOF
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Get database URL from environment
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Testing connection to: {db_url.split('@')[1] if '@' in db_url else db_url}")

try:
    # Create engine and attempt connection
    engine = create_engine(db_url)
    connection = engine.connect()
    print("Success: Connection to database established!")
    connection.close()
except SQLAlchemyError as e:
    print(f"Error: Failed to connect to database: {e}")
    sys.exit(1)
EOF
    
    # Run the test script in a temporary container
    print_message "Running database connection test..."
    docker run --rm -v "$(pwd)/test_db_connection.py:/app/test.py" \
               --env-file .env \
               --network=host \
               python:3.11-slim bash -c "pip install sqlalchemy psycopg2-binary && python /app/test.py"
    
    local test_status=$?
    rm -f test_db_connection.py
    
    if [ $test_status -ne 0 ]; then
        print_error "Database connection test failed."
        print_message "Please check your DATABASE_URL in the .env file and ensure the database is accessible."
        return 1
    else
        print_message "Database connection test successful! ✅"
        return 0
    fi
}

# Run all steps
run_all() {
    local failed=0
    
    # Test database connection first
    print_message "Testing database connection before proceeding..."
    step9 || { failed=1; print_error "Database connection test failed. Fix database issues before continuing."; }
    
    if [ $failed -eq 0 ]; then
        step1 || { failed=1; print_error "Step 1 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step2 || { failed=1; print_error "Step 2 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        step3 || { failed=1; print_error "Step 3 failed"; }
    fi
    
    if [ $failed -eq 0 ]; then
        print_message "All steps completed successfully!"
        print_message "Your application should now be running at: http://localhost:5001"
    else
        print_error "Deployment failed. Please check the errors above."
    fi
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (0-9): " choice
    
    case $choice in
        1) step1 ;;
        2) step2 ;;
        3) step3 ;;
        4) step4 ;;
        5) step5 ;;
        6) run_all ;;
        7) step7 ;;
        8) step8 ;;
        9) step9 ;;
        0) exit 0 ;;
        *) print_error "Invalid choice. Please try again." ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
    clear
done 