# Social Styles Assessment Deployment Guide

This guide provides detailed instructions for deploying the Social Styles Assessment application to a DigitalOcean server using our improved deployment script.

## Prerequisites

Before starting the deployment process, ensure you have the following:

1. A DigitalOcean droplet running Ubuntu (recommended: 20.04 LTS)
2. A domain name pointing to the server's IP address
3. SSH access to the server (using SSH key authentication)
4. A local copy of the application codebase
5. A PostgreSQL database (can be a managed service like DigitalOcean's)

## Environment Setup

The application requires a `.env` file containing all necessary environment variables. Before deployment, create a `.env` file in the project root with the following variables:

```
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=0

# AWS SES configuration (if using)
USE_SES=True/False
AWS_REGION=region-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

MAIL_DEFAULT_SENDER=your-email@example.com

# Application configuration
APP_NAME=Social Styles Assessment
ADMIN_EMAIL=admin@example.com

# Database configuration
DATABASE_URL=postgresql://username:password@hostname:port/database?sslmode=require
```

Replace the placeholder values with your actual configuration. The `DATABASE_URL` should point to your PostgreSQL database.

## Deployment Steps

The deployment process is handled by the `improved_deploy.sh` script, which breaks down the process into manageable steps. Here's an overview of each step:

### 1. Check Prerequisites and Setup

Verifies that all prerequisites are in place:
- SSH key exists and is accessible
- Server is reachable
- Git repository is accessible
- `.env` file is correctly configured

### 2. Update Server and Install Dependencies

Updates the server and installs all necessary packages:
- Python and development tools
- Nginx web server
- PostgreSQL client
- Git and other utilities

### 3. Set up PostgreSQL Database

Verifies the connection to the PostgreSQL database using the credentials in the `.env` file.

### 4. Clone Repository and Set up Environment

- Clones the application repository
- Sets up a Python virtual environment
- Installs all dependencies
- Uploads the `.env` file

### 5. Initialize Application Database

- Initializes the Flask database migrations
- Runs migrations to create database schema
- Populates initial assessment data

### 6. Configure Nginx and SSL

Sets up Nginx as a reverse proxy:
- Creates a server block for the domain
- Configures Cloudflare integration
- Sets up static file serving

### 7. Set up Systemd Service

Creates a systemd service to manage the application:
- Automatic startup on system boot
- Restart on failure
- Running with correct permissions

### 8. Set up Service Monitoring

Adds a monitoring script and cron job to ensure the application stays running.

### 9. Test Deployment

Tests the deployment by:
- Checking service status
- Testing Nginx configuration
- Verifying application accessibility

## Cloudflare Setup

After deploying the application, set up Cloudflare for added security and performance:

1. Add your domain to Cloudflare
2. Create DNS records:
   - A record for root domain @ pointing to your server IP
   - A record for www subdomain pointing to your server IP
3. Enable SSL/TLS with Full mode
4. Enable Always Use HTTPS option

## Updating the Application

To update the application after making changes to the codebase:

1. Run option 11 from the deployment script menu ("Update application only")
2. The script will:
   - Pull the latest changes from the git repository
   - Update dependencies
   - Run database migrations
   - Restart the application

## Troubleshooting

If you encounter issues during deployment:

1. **SSH Connection Issues**: 
   - Verify your SSH key is correctly set up
   - Check that the server IP is correct
   - Ensure the server's firewall allows SSH connections

2. **Database Connection Issues**:
   - Verify the database connection string
   - Check if the database server accepts connections from your application server
   - Ensure the database user has appropriate permissions

3. **Application Not Starting**:
   - Check the application logs with: `journalctl -u socialstyles.service`
   - Verify the `.env` file contains all required variables
   - Check that the virtual environment is correctly set up

4. **Nginx Configuration Issues**:
   - Test the Nginx configuration with: `nginx -t`
   - Check Nginx error logs: `/var/log/nginx/error.log`
   - Verify that the application is running and accessible locally

## Custom Database Setup

If you need to set up a new PostgreSQL database, follow these steps:

1. Install PostgreSQL on your server or use a managed service
2. Create a new database and user:
   ```sql
   CREATE DATABASE social_styles;
   CREATE USER social_user WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE social_styles TO social_user;
   ```

3. Update your `.env` file with the appropriate connection string
4. Run the deployment script starting from step 5 (Initialize Application Database)

## Backup and Restore

It's important to regularly back up your database:

1. To backup:
   ```bash
   pg_dump -U username -h hostname database_name > backup_filename.sql
   ```

2. To restore:
   ```bash
   psql -U username -h hostname database_name < backup_filename.sql
   ```

For automation, consider setting up a cron job to run the backup regularly.

## Security Considerations

For enhanced security:

1. Implement a firewall (ufw) to restrict access
2. Configure fail2ban to prevent brute force attacks
3. Regularly update the server with security patches
4. Use strong, unique passwords for all services
5. Consider setting up automatic security updates

## Performance Optimization

For better performance:

1. Configure caching in Nginx for static files
2. Consider adding a CDN for static assets
3. Optimize database queries where possible
4. Scale vertically (bigger droplet) or horizontally (multiple servers) as needed

## Need Help?

If you encounter issues not covered in this guide, consult:
- The project's internal documentation
- The Flask, Nginx, or PostgreSQL documentation
- DigitalOcean's community tutorials
- Open an issue in the project repository 