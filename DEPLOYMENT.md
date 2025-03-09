# Social Styles Application Deployment Guide

This guide explains how to deploy the Social Styles application to a DigitalOcean droplet using the provided deployment script.

## Prerequisites

Before you begin, make sure you have:

1. A DigitalOcean account and a droplet created
2. SSH access to your droplet
3. A domain name (if you plan to use one)
4. Cloudflare account (optional, for SSL and security)
5. The `deploy_steps.sh` script from this repository

## Configuration

Before running the script, you need to modify the configuration variables at the top of the `deploy_steps.sh` file:

```bash
# Configuration - MODIFY THESE VALUES
DROPLET_IP="134.209.128.212"  # Your droplet's IP address
DOMAIN_NAME="teamsocialstyles.com"  # Your domain name
SSH_KEY_PATH="~/.ssh/id_ed25519"  # Path to your SSH key
APP_NAME="socialstyles"  # Application name
APP_DIR="/var/www/$APP_NAME"  # Application directory on the server
GITHUB_REPO="https://github.com/gmoorevt/socialstyles.git"  # GitHub repository URL
```

## Environment Files

You'll need to create a `.env.production` file in the same directory as the deployment script. This file will be copied to the server as `.env` and should contain your production environment variables:

```
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
# Add other environment variables as needed
```

## Running the Deployment Script

1. Make the script executable:
   ```bash
   chmod +x deploy_steps.sh
   ```

2. Run the script:
   ```bash
   ./deploy_steps.sh
   ```

3. You'll see a menu with various deployment options.

## Deployment Options

The script provides the following options:

### Individual Steps

#### 1. Update server and install dependencies

This step updates the server's package list and installs all necessary dependencies:

```bash
apt-get update && apt-get upgrade -y
apt-get install -y python3-pip python3-venv nginx git supervisor build-essential libssl-dev libffi-dev python3-dev
```

These packages include:
- Python and pip for running the application
- Nginx for serving as a reverse proxy
- Git for pulling code from the repository
- Supervisor for process management
- Build tools and development libraries for compiling dependencies

#### 2. Create application user

Creates a dedicated user for running the application, which is a security best practice:

```bash
useradd -m -d /var/www/socialstyles -s /bin/bash socialstyles
usermod -aG www-data socialstyles
```

This creates a user named 'socialstyles' with:
- A home directory at `/var/www/socialstyles`
- Membership in the www-data group for proper file permissions

#### 3. Clone repository

Clones the application code from GitHub to the server:

```bash
rm -rf /var/www/socialstyles
git clone https://github.com/gmoorevt/socialstyles.git /var/www/socialstyles
chown -R socialstyles:www-data /var/www/socialstyles
```

This step also:
- Removes any existing directory (for clean deployments)
- Sets proper ownership of files to the application user

#### 4. Set up Python virtual environment

Creates an isolated Python environment for the application:

```bash
cd /var/www/socialstyles
python3 -m venv venv
chown -R socialstyles:www-data venv
sudo -u socialstyles venv/bin/pip install --upgrade pip
sudo -u socialstyles venv/bin/pip install -r requirements.txt
```

This ensures:
- Dependencies are isolated from system Python
- The application user has proper permissions
- All required packages are installed

#### 5. Set up production environment

Copies the production environment variables to the server:

```bash
# Copies .env.production from local machine to /var/www/socialstyles/.env on server
chown socialstyles:www-data /var/www/socialstyles/.env
```

This file contains sensitive configuration like:
- Database connection strings
- Secret keys
- API credentials
- Mail server settings

#### 6. Initialize database

Sets up the database schema and initial data:

```bash
cd /var/www/socialstyles
sudo -u socialstyles venv/bin/python initialize_assessment.py
sudo -u socialstyles venv/bin/flask db upgrade
```

This:
- Runs the assessment initialization script
- Applies any pending database migrations

#### 7. Configure Nginx

Sets up Nginx as a reverse proxy with Cloudflare integration:

```bash
# Creates a configuration file at /etc/nginx/sites-available/socialstyles.conf
# Links it to sites-enabled
# Removes default site
# Tests and restarts Nginx
```

The configuration includes:
- Cloudflare IP ranges for proper client IP forwarding
- Proxy settings for the Flask application
- Static file serving
- Domain name configuration

#### 8. Set up systemd service

Creates a systemd service to manage the application process:

```bash
# Creates /etc/systemd/system/socialstyles.service
systemctl daemon-reload
systemctl enable socialstyles.service
systemctl start socialstyles.service
```

The service configuration:
- Runs the application with Gunicorn
- Automatically starts on boot
- Restarts on failure
- Runs as the dedicated application user

#### 9. Set up service monitoring

Configures a cron job to monitor and automatically restart the service if it fails:

```bash
# Creates a monitoring script at /usr/local/bin/check_and_restart_service.sh
# Adds a cron job to run every 5 minutes
```

This ensures high availability by:
- Checking if the service is running
- Automatically restarting it if it's down
- Logging restart events

#### 10. Check deployment status

Verifies that the application is running correctly:

```bash
systemctl status socialstyles.service --no-pager
```

This shows:
- Whether the service is active
- Recent log output
- Any startup errors

#### 11. Show Cloudflare setup instructions

Displays detailed instructions for configuring Cloudflare:
- Setting up DNS records
- Configuring SSL/TLS settings
- Setting up page rules
- Enabling security features

### Combined Steps

#### 12. Run all steps (1-10)

Executes all the individual steps in sequence for a complete initial deployment.

#### 13. Install PostgreSQL driver

Installs the PostgreSQL driver if you're using PostgreSQL instead of SQLite:

```bash
cd /var/www/socialstyles
sudo -u socialstyles venv/bin/pip install psycopg2-binary
```

This is necessary when:
- Using PostgreSQL as your database
- Switching from SQLite to PostgreSQL

#### 14. Run database migrations

Runs database migrations and initializes assessment data:

```bash
cd /var/www/socialstyles
sudo -u socialstyles venv/bin/flask db upgrade
sudo -u socialstyles venv/bin/python initialize_assessment.py
```

This is useful for:
- Applying schema changes
- Updating seed data
- Fixing database issues

#### 15. Full deploy with database setup

Performs a targeted deployment focusing on code and database updates:

```bash
# Clones repository (step 3)
# Sets up Python virtual environment (step 4)
# Sets up production environment (step 5)
# Installs PostgreSQL driver (step 13)
# Runs database migrations (step 14)
# Sets up systemd service (step 8)
# Checks deployment status (step 10)
```

This is ideal for routine updates where you don't need to reconfigure the entire server.

## Common Deployment Scenarios

### Initial Deployment

For the first deployment, you should run option 12 (all steps) to set up everything:

```bash
./deploy_steps.sh
# Then select option 12
```

This will:
1. Update the server and install all dependencies
2. Create the application user
3. Clone the repository
4. Set up the Python environment
5. Configure the production environment
6. Initialize the database
7. Set up Nginx
8. Configure the systemd service
9. Set up monitoring
10. Verify the deployment

### Updating the Application

For subsequent updates, you can use option 15 (Full deploy with database setup):

```bash
./deploy_steps.sh
# Then select option 15
```

This will:
- Pull the latest code from GitHub
- Update the Python dependencies
- Run any new database migrations
- Restart the application

This is more efficient than running all steps again since it focuses only on what needs to be updated.

### Database Changes Only

If you only need to apply database changes:

```bash
./deploy_steps.sh
# Then select option 14
```

This is useful when:
- You've added new database migrations
- You need to update the assessment data
- You're troubleshooting database issues

## Monitoring and Maintenance

### Viewing Logs

To view the application logs:

```bash
ssh -i ~/.ssh/id_ed25519 root@your-droplet-ip
journalctl -u socialstyles.service -f
```

The `-f` flag follows the log in real-time, showing new entries as they occur.

### Restarting the Service

To restart the application:

```bash
ssh -i ~/.ssh/id_ed25519 root@your-droplet-ip
systemctl restart socialstyles.service
```

This is useful after configuration changes or when troubleshooting issues.

## Cloudflare Setup

After deploying, follow these steps to configure Cloudflare:

1. Log in to your Cloudflare account
2. Add your domain if you haven't already
3. Set up an A record for the root domain pointing to your droplet IP
4. Set up another A record for the www subdomain
5. Enable SSL/TLS encryption (Full mode)
6. Enable "Always Use HTTPS"

Cloudflare provides:
- Free SSL certificates
- DDoS protection
- Caching for better performance
- Web application firewall

## Troubleshooting

### Service Won't Start

Check the logs for errors:

```bash
journalctl -u socialstyles.service -n 50
```

Common issues include:
- Missing dependencies
- Configuration errors in .env file
- Database connection problems
- Permission issues

### Database Migration Issues

If database migrations fail, you may need to check:

```bash
ssh -i ~/.ssh/id_ed25519 root@your-droplet-ip
cd /var/www/socialstyles
sudo -u socialstyles venv/bin/flask db history
```

This shows the migration history, which can help identify:
- Failed migrations
- Out-of-order migrations
- Conflicts between branches

### Nginx Configuration Problems

Check Nginx error logs:

```bash
ssh -i ~/.ssh/id_ed25519 root@your-droplet-ip
nginx -t
cat /var/log/nginx/error.log
```

The `nginx -t` command tests the configuration for syntax errors.

## Version History

The deployment script will automatically copy your `version.txt` file to the server, ensuring that the correct version information is available in the deployed application.

This allows you to:
- Track which version is deployed
- Display version information in the application
- Correlate server behavior with specific releases

## Security Considerations

- The script sets up Nginx to work with Cloudflare, which provides additional security
- A dedicated application user is created to run the application
- Service monitoring ensures the application stays running
- Systemd is configured to restart the service if it crashes

Additional security measures to consider:
- Setting up a firewall (UFW)
- Configuring fail2ban to prevent brute force attacks
- Enabling automatic security updates
- Regular backups of your database

## Conclusion

This deployment script provides a comprehensive way to deploy and maintain your Social Styles application on a DigitalOcean droplet. By following this guide, you should be able to deploy your application successfully and keep it running smoothly.

The modular approach allows you to:
- Perform complete deployments for new servers
- Update only what's needed for routine maintenance
- Troubleshoot specific components when issues arise
- Maintain consistent deployments across multiple environments 