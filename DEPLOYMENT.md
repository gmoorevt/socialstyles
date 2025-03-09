# Social Styles Application Deployment Guide

This document outlines the process for deploying the Social Styles application to production, including prerequisites, deployment steps, database migration guidelines, and troubleshooting tips.

## Prerequisites

Before deploying, ensure you have:

1. SSH access to the production server
2. Proper credentials for the PostgreSQL database
3. The latest code committed and pushed to the main branch
4. Updated version.txt with the correct version number
5. Updated requirements.txt with all necessary dependencies

## Pre-Deployment Checklist

- [ ] Update version.txt with the new version number
- [ ] Update requirements.txt with any new dependencies
- [ ] Ensure all code changes are committed and pushed to the repository
- [ ] Create a Git tag for the new version
- [ ] Test the application locally with the production configuration
- [ ] Verify database migrations work correctly
- [ ] Check that the PostgreSQL connection string in .env.production is correct

## Deployment Steps

### 1. Environment Setup

```bash
# SSH into the server
ssh -i ~/.ssh/id_ed25519 root@134.209.128.212

# Pull the latest changes
cd /var/www/socialstyles
git pull

# Install any new dependencies
sudo -u socialstyles venv/bin/pip install -r requirements.txt

# Ensure PostgreSQL driver is installed
sudo -u socialstyles venv/bin/pip install psycopg2-binary
```

### 2. Database Migration

```bash
# Run database migrations
cd /var/www/socialstyles
sudo -u socialstyles venv/bin/flask db upgrade

# If needed, initialize assessment data
sudo -u socialstyles venv/bin/python initialize_assessment.py
```

### 3. Application Deployment

```bash
# Restart the application service
systemctl restart socialstyles.service

# Check the status of the application
systemctl status socialstyles.service
```

### 4. Verify Deployment

- Check the application logs for any errors:
  ```bash
  journalctl -u socialstyles.service -n 50
  ```
- Test the application by accessing it in a browser
- Verify key functionality (login, registration, assessments, etc.)

## Database Migration Guidelines

### When Switching Database Systems (e.g., SQLite to PostgreSQL)

1. Update the DATABASE_URL in the .env file on the server
2. Install the appropriate database driver (e.g., psycopg2-binary for PostgreSQL)
3. Run the database initialization script to create the necessary tables
4. Restart the application service

### For Regular Schema Updates

1. Create a migration locally:
   ```bash
   flask db migrate -m "Description of changes"
   ```
2. Review the generated migration script
3. Apply the migration locally to test it
4. Commit the migration script to the repository
5. On the server, run `flask db upgrade` to apply the migration

## Rollback Procedures

If issues occur during deployment:

1. Roll back to the previous version:
   ```bash
   git checkout <previous-tag>
   ```
2. Restore the database from backup if necessary
3. Restart the application service

## Environment Variables

Ensure these environment variables are correctly set in the .env file on the server:

- `FLASK_APP=wsgi.py`
- `FLASK_ENV=production`
- `SECRET_KEY=your-strong-production-secret-key`
- `DATABASE_URL=postgresql://username:password@host/dbname`
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, etc.

## Common Issues and Solutions

### Database Connection Issues

- **Issue**: "No module named 'psycopg2'"
  - **Solution**: Install the PostgreSQL driver with `pip install psycopg2-binary`

- **Issue**: "permission denied for schema public"
  - **Solution**: Grant the necessary permissions to the database user

- **Issue**: "no such table: users"
  - **Solution**: Run the database initialization script or migrations

### Application Startup Issues

- **Issue**: "ImportError: cannot import name 'app' from 'app'"
  - **Solution**: Update wsgi.py to use the create_app factory pattern

### Deployment Script Issues

- **Issue**: Interactive prompts in deployment script
  - **Solution**: Use non-interactive commands or provide input via pipes

## Monitoring and Logging

- Monitor application logs: `journalctl -u socialstyles.service -f`
- Check system resources: `htop`
- Monitor database performance as needed

## Security Considerations

- Keep the .env file secure with restricted permissions
- Use strong, unique passwords for database access
- Regularly update dependencies to patch security vulnerabilities
- Ensure proper HTTPS configuration through Cloudflare 