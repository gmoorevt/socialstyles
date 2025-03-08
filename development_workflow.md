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

5. **Initialize the database and migrations**:
   ```bash
   # Initialize the migration repository (first time only)
   flask db init
   
   # Create initial migration
   flask db migrate -m "Initial migration"
   
   # Apply migrations to the database
   flask db upgrade
   ```

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
   # After changing models, generate a new migration
   flask db migrate -m "Description of database changes"
   
   # Review the generated migration script in migrations/versions/
   
   # Apply the migration to update the database schema
   flask db upgrade
   
   # If you need to revert a migration
   flask db downgrade
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

## 7. Database Migration Management

The project uses Flask-Migrate (based on Alembic) for database migrations. This allows you to make changes to your database schema in a controlled and reversible way.

### Migration Commands

1. **Initialize migrations** (only needed once per project):
   ```bash
   flask db init
   ```

2. **Create a new migration** after changing models:
   ```bash
   flask db migrate -m "Description of changes"
   ```

3. **Apply migrations** to update the database:
   ```bash
   flask db upgrade
   ```

4. **Revert migrations** if needed:
   ```bash
   flask db downgrade
   ```

5. **View migration history**:
   ```bash
   flask db history
   ```

6. **View current migration**:
   ```bash
   flask db current
   ```

### Migration Workflow

1. **Make changes to your models** in the application code
2. **Generate a migration** using `flask db migrate -m "Description"`
3. **Review the generated migration script** in the `migrations/versions/` directory
4. **Edit the migration script if necessary** to handle complex changes
5. **Apply the migration** using `flask db upgrade`
6. **Test the changes** to ensure they work as expected
7. **Commit both the model changes and migration scripts** to version control

### Handling Migration Conflicts

If multiple developers are working on the database schema:

1. **Communicate changes** to avoid conflicts
2. **Pull and merge changes** before creating new migrations
3. **Resolve conflicts** in migration scripts if they occur
4. **Test migrations** thoroughly after resolving conflicts

### Production Migrations

When deploying to production:

1. **Always back up the database** before applying migrations
2. **Test migrations** in a staging environment first
3. **Include migrations** in your deployment process
4. **Monitor the migration process** for any errors
5. **Have a rollback plan** in case of issues 