#!/bin/bash

# Script to publish the Social Styles Assessment application to GitHub
# This script initializes a Git repository, adds all files, and pushes to GitHub

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration - CHANGE THESE
GITHUB_USERNAME="gmoorevt"
REPO_NAME="socialstyles"
REPO_DESCRIPTION="A web-based application for taking the Social Styles assessment, built with Flask"

# Helper functions
print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

check_variables() {
    if [ -z "$GITHUB_USERNAME" ]; then
        print_error "Please set the GITHUB_USERNAME variable in the script"
        exit 1
    fi
}

# Check if required variables are set
check_variables

# Confirm publishing
echo -e "${YELLOW}This script will publish the Social Styles Assessment application to GitHub:${NC}"
echo "  - GitHub Username: $GITHUB_USERNAME"
echo "  - Repository Name: $REPO_NAME"
echo "  - Repository Description: $REPO_DESCRIPTION"
echo ""
read -p "Continue with publishing? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing cancelled."
    exit 0
fi

# Step 1: Create .gitignore if it doesn't exist
print_step "Setting up .gitignore"
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# Flask
instance/
.webassets-cache

# SQLite
*.sqlite
*.db

# Environment variables
.env
.env.production

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS specific
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Deployment
deploy_tmp/
EOF
    print_warning "Created .gitignore file"
fi

# Step 2: Initialize Git repository if not already initialized
print_step "Initializing Git repository"
if [ ! -d ".git" ]; then
    git init
    print_warning "Initialized new Git repository"
else
    print_warning "Git repository already exists"
fi

# Step 3: Set remote to existing GitHub repository
print_step "Setting up remote to existing GitHub repository"
if ! git remote | grep -q "origin"; then
    git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    print_warning "Added remote origin"
else
    # Update the remote URL to ensure it's correct
    git remote set-url origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    print_warning "Updated remote origin URL"
fi

# Step 4: Add all files to Git
print_step "Adding files to Git"
git add .

# Step 5: Commit changes
print_step "Committing changes"
git commit -m "Initial commit of Social Styles Assessment application"

# Step 6: Push to GitHub
print_step "Pushing to GitHub"
git push -u origin main || git push -u origin master

# Publishing complete
echo ""
echo -e "${GREEN}Publishing complete!${NC}"
echo -e "Your Social Styles Assessment application is now available at: ${YELLOW}https://github.com/$GITHUB_USERNAME/$REPO_NAME${NC}"
echo ""
echo "To clone this repository on another machine:"
echo "git clone https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo "" 