#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi
}

# Function to check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        echo -e "${RED}Error: .env file not found${NC}"
        exit 1
    fi
}

# Function to check if DATABASE_URL exists in .env
check_database_url() {
    if ! grep -q "^DATABASE_URL=" .env; then
        echo -e "${RED}Error: DATABASE_URL not found in .env file${NC}"
        echo -e "${YELLOW}Please add your database URL to .env file:${NC}"
        echo "DATABASE_URL=postgresql://username:password@host:5432/dbname"
        exit 1
    fi
}

# Function to test database connection
test_database_connection() {
    echo -e "${YELLOW}Testing database connection...${NC}"
    
    # Create a temporary Python script to test connection
    cat > test_db.py << 'EOL'
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to database: {str(e)}")
    exit(1)
EOL

    # Run the test script
    python3 test_db.py
    rm test_db.py
}

# Function to build the Docker image
build_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker-compose build
}

# Function to start the containers
start_containers() {
    echo -e "${YELLOW}Starting containers...${NC}"
    docker-compose up -d
}

# Function to stop the containers
stop_containers() {
    echo -e "${YELLOW}Stopping containers...${NC}"
    docker-compose down
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}Showing logs...${NC}"
    docker-compose logs -f
}

# Function to initialize the database
init_database() {
    echo -e "${YELLOW}Initializing database...${NC}"
    docker-compose exec web flask db upgrade
}

# Function to perform full deployment
full_deployment() {
    echo -e "${YELLOW}Starting full deployment...${NC}"
    
    # Check prerequisites
    check_docker
    check_env
    check_database_url
    
    # Test database connection
    test_database_connection
    
    # Build and start containers
    build_image
    start_containers
    
    # Initialize database
    init_database
    
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${YELLOW}You can access the application at http://localhost:5001${NC}"
}

# Main menu
while true; do
    echo -e "\n${YELLOW}Social Styles Docker Deployment Menu${NC}"
    echo "1. Check Docker status"
    echo "2. Check .env file"
    echo "3. Check database URL"
    echo "4. Test database connection"
    echo "5. Build Docker image"
    echo "6. Full deployment"
    echo "7. Start containers"
    echo "8. Stop containers"
    echo "9. Show logs"
    echo "0. Exit"
    
    read -p "Enter your choice (0-9): " choice
    
    case $choice in
        1) check_docker ;;
        2) check_env ;;
        3) check_database_url ;;
        4) test_database_connection ;;
        5) build_image ;;
        6) full_deployment ;;
        7) start_containers ;;
        8) stop_containers ;;
        9) show_logs ;;
        0) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid choice. Please try again.${NC}" ;;
    esac
done 