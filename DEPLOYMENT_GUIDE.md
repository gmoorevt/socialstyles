# Social Styles Assessment Deployment Guide

This guide provides detailed instructions for deploying the Social Styles Assessment application to a DigitalOcean server using our `improved_deploy.sh` script.

## Prerequisites

Before starting the deployment process, ensure you have the following:

1. A DigitalOcean droplet running Ubuntu (recommended: 20.04 LTS)
2. A domain name pointing to the server's IP address
3. SSH access to the server (using SSH key authentication)
4. A local copy of the application codebase
5. A PostgreSQL database (can be a managed service like DigitalOcean's)

## Quick Deployment Overview

To deploy the application:

1. Configure the script variables at the top of `improved_deploy.sh`
2. Set up your `.env.production` file with necessary environment variables
3. Run the script: `./improved_deploy.sh`
4. Select the appropriate deployment option from the menu

## Configuration Setup

### Step 1: Update Script Configuration

Edit the configuration variables at the top of the `improved_deploy.sh` file:

```bash
# Configuration - MODIFY THESE VALUES
DROPLET_IP="your-droplet-ip"
DOMAIN_NAME="your-domain.com"
SSH_KEY_PATH="$HOME/.ssh/your-key-file"
APP_NAME="socialstyles"
APP_DIR="/var/www/$APP_NAME"
GITHUB_REPO="https://github.com/yourusername/socialstyles.git"
GITHUB_BRANCH="main"  # The branch to deploy
DB_USER="social_user" # PostgreSQL database user
DB_NAME="social_styles" # PostgreSQL database name
```

### Step 2: Set Up Environment Variables

Create a `.env.production` file in the same directory as the deployment script. This file will be copied to the server as `.env` and should contain your production environment variables:

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

## Deployment Options

The `improved_deploy.sh` script provides several options for deployment. Here are the main ones:

### Full Deployment (Option 1)

This option performs a complete deployment including:
- Server setup and dependency installation
- PostgreSQL configuration
- Application deployment and configuration
- Nginx setup with SSL
- Systemd service configuration
- Monitoring setup

Recommended for first-time deployments or when setting up a new server.

### Update Application Only (Option 2)

This option updates the application code without changing server configuration:
- Pulls the latest code from the repository
- Updates dependencies
- Runs database migrations
- Restarts the application

Ideal for regular updates after the initial setup.

### Database Setup/Migration (Option 3)

This option focuses on database operations:
- Sets up the database connection
- Runs migrations
- Initializes application data

Useful when you've made database schema changes.

### Manual Steps

The script also offers individual steps that can be run separately:
- Update server packages
- Install dependencies
- Set up PostgreSQL
- Clone/update repository
- Set up Python environment
- Configure Nginx
- Set up systemd service
- Set up monitoring

## Deployment Process

### Running the Script

1. Make the script executable:
   ```bash
   chmod +x improved_deploy.sh
   ```

2. Run the script:
   ```bash
   ./improved_deploy.sh
   ```

3. Select the appropriate option from the menu.

4. The script will execute the selected operations and provide feedback on each step.

### Post-Deployment Verification

After deployment completes, verify that:

1. The application is accessible at your domain
2. The systemd service is running: `systemctl status socialstyles.service`
3. Nginx is configured correctly: `nginx -t`
4. You can log in and use the application

## Cloudflare Setup

For added security and performance, set up Cloudflare:

1. Add your domain to Cloudflare
2. Set up DNS records pointing to your DigitalOcean server
3. Configure SSL/TLS settings
4. Enable Always Use HTTPS

The `improved_deploy.sh` script includes Cloudflare-ready Nginx configurations.

## Troubleshooting

If you encounter issues during deployment:

### Connection Issues
- Verify your SSH key path and permissions
- Check that you can manually SSH to the server
- Ensure the server IP is correct

### Database Issues
- Check your PostgreSQL connection string
- Verify that the database and user exist
- Ensure the database is accessible from your server

### Application Not Starting
- Check logs: `journalctl -u socialstyles.service`
- Verify environment variables in the `.env` file
- Ensure all dependencies are installed

### Nginx Issues
- Check configuration: `nginx -t`
- View logs: `/var/log/nginx/error.log`
- Verify that ports are not blocked by a firewall

## Backup and Restore

The `improved_deploy.sh` script includes utilities for database backups:

1. To create a backup, use option 10 in the menu
2. The backup will be stored on the server and can be downloaded
3. To restore from a backup, use option 11

For automated backups, consider setting up a cron job on the server.

## Service Management

The `improved_deploy.sh` script configures your application as a systemd service that starts automatically on server boot. Here's how to manage the service:

### Checking Service Status

```bash
ssh -i ~/.ssh/your-key root@your-server-ip "systemctl status socialstyles.service"
```

### Manual Service Control

If you need to manually manage the service:

- **Start the service**:
  ```bash
  systemctl start socialstyles.service
  ```

- **Stop the service**:
  ```bash
  systemctl stop socialstyles.service
  ```

- **Restart the service**:
  ```bash
  systemctl restart socialstyles.service
  ```

- **View service logs**:
  ```bash
  journalctl -u socialstyles.service -n 100
  ```

### Automatic Service Monitoring

The deployment script sets up a monitoring cron job that automatically checks if your service is running and restarts it if needed. This provides additional reliability for your application.

### After Server Reboot

After your DigitalOcean server reboots, the systemd service will automatically start your application. You don't need to take any manual actions.

## Security Considerations

The deployment script implements several security best practices:
- Proper file permissions
- Running the application as a dedicated user
- Setting up SSL with Nginx
- Configuring firewalls

## Advanced Usage

### Custom Branch Deployment

To deploy a specific branch, update the `GITHUB_BRANCH` variable in the script before running.

### Custom Domain Configuration

The script automatically configures Nginx for your domain. If you need to use multiple domains, you can modify the Nginx configuration template in the script.

## Need Help?

If you encounter issues not covered in this guide:
- Check the script's built-in help (option 12 in the menu)
- Consult the project documentation
- Review the script for specific commands being run 