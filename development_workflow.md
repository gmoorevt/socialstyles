# Development Workflow for Social Styles Project

This document outlines the recommended development workflow for the Social Styles project, from local development to deployment on DigitalOcean.

## 1. Local Development Environment

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/gmoorevt/socialstyles.git
   cd social-styles
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Create a `.env` file for local development
   - Include database connection, secret key, and other configuration

### Development Cycle

1. **Run the application locally**:
   ```bash
   flask run --debug
   ```
   This will start the development server with hot reloading.

2. **Make code changes**:
   - Modify code in your preferred editor
   - Changes will be automatically detected and the server will reload

3. **Database migrations** (when changing models):
   ```bash
   flask db migrate -m "Description of changes"
   flask db upgrade
   ```

4. **Testing**:
   ```bash
   pytest
   ```

## 2. Version Control Workflow

### Feature Development

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. **Make commits with descriptive messages**:
   ```bash
   git add .
   git commit -m "Add feature X that does Y"
   ```

3. **Push changes to GitHub**:
   ```bash
   git push origin feature/new-feature-name
   ```

4. **Create a pull request** on GitHub to merge into main

### Version Management

1. **Update version number** in `version.txt` when making significant changes:
   - For minor changes: increment the third number (1.0.0 → 1.0.1)
   - For new features: increment the second number (1.0.1 → 1.1.0)
   - For major changes: increment the first number (1.1.0 → 2.0.0)

2. **Create a tag for each release**:
   ```bash
   git tag -a v1.0.1 -m "Description of this release"
   git push origin v1.0.1
   ```

## 3. Deployment to DigitalOcean

### Preparing for Deployment

1. **Merge changes to main branch**:
   ```bash
   git checkout main
   git merge feature/new-feature-name
   git push origin main
   ```

2. **Run tests on the main branch**:
   ```bash
   pytest
   ```

3. **Update version information**:
   - Update `version.txt` with the new version number and release notes
   - Commit and push the changes
   ```bash
   git add version.txt
   git commit -m "Bump version to X.Y.Z"
   git push origin main
   ```

4. **Create a release tag**:
   ```bash
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   git push origin vX.Y.Z
   ```

### Deployment Options

#### Option 1: Using the Deployment Script

1. **Run the deployment script**:
   ```bash
   ./deploy_to_digitalocean.sh
   ```
   This script will:
   - Clone the repository on the server
   - Set up the environment
   - Configure Nginx
   - Restart the application

#### Option 2: Step-by-Step Deployment

1. **Run the step-by-step deployment script**:
   ```bash
   ./deploy_steps.sh
   ```
   This allows you to:
   - Execute each deployment step individually
   - Troubleshoot issues at each stage
   - Skip steps that don't need to be repeated

#### Option 3: Manual Deployment

For smaller updates, you can manually update the server:

1. **SSH into the server**:
   ```bash
   ssh -i ~/.ssh/id_ed25519 root@134.209.128.212
   ```

2. **Update the code**:
   ```bash
   cd /var/www/socialstyles
   git pull
   ```

3. **Install any new dependencies**:
   ```bash
   sudo -u socialstyles venv/bin/pip install -r requirements.txt
   ```

4. **Run database migrations if needed**:
   ```bash
   sudo -u socialstyles venv/bin/flask db upgrade
   ```

5. **Restart the application**:
   ```bash
   systemctl restart socialstyles.service
   ```

## 4. Post-Deployment Verification

1. **Check application status**:
   ```bash
   ssh -i ~/.ssh/id_ed25519 root@134.209.128.212 "systemctl status socialstyles.service"
   ```

2. **View application logs**:
   ```bash
   ssh -i ~/.ssh/id_ed25519 root@134.209.128.212 "journalctl -u socialstyles.service -f"
   ```

3. **Verify the site is accessible**:
   - Visit http://134.209.128.212 and https://teamsocialstyles.com
   - Check that the version number in the footer is correct

## 5. Troubleshooting

### Common Issues

1. **Connection issues with Cloudflare**:
   - Check Cloudflare DNS settings
   - Verify SSL/TLS mode is set to "Flexible"
   - Temporarily disable Cloudflare proxy to test direct connection

2. **Application not starting**:
   - Check logs: `journalctl -u socialstyles.service -n 50`
   - Verify environment variables are set correctly
   - Check permissions on files and directories

3. **Database issues**:
   - Check database connection in the .env file
   - Verify migrations have been applied

## 6. Best Practices

1. **Always test locally before deploying**
2. **Use feature branches for development**
3. **Update version numbers for significant changes**
4. **Create tags for each release**
5. **Keep deployment scripts updated**
6. **Monitor logs after deployment**
7. **Back up the database regularly** 