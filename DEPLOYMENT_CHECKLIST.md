# Social Styles Assessment Deployment Checklist

Use this checklist to ensure a smooth deployment process when using the `improved_deploy.sh` script.

## Pre-Deployment Preparation

- [ ] Ensure all code changes are committed and pushed to the repository
- [ ] Update version information in `version.txt`
- [ ] Create or update `.env.production` file with proper configuration
- [ ] Test the application locally with similar settings to production

## Script Configuration

- [ ] Update `DROPLET_IP` in improved_deploy.sh with your server's IP
- [ ] Update `DOMAIN_NAME` with your application domain
- [ ] Set `SSH_KEY_PATH` to point to your correct SSH key file
- [ ] Verify `GITHUB_REPO` and `GITHUB_BRANCH` settings
- [ ] Confirm PostgreSQL settings (`DB_USER` and `DB_NAME`)

## Server Prerequisites

- [ ] DigitalOcean droplet is created and running
- [ ] SSH key is set up for server access
- [ ] Domain name is registered and DNS is configured
- [ ] PostgreSQL database is created and accessible

## Deployment Environment Variables Check

- [ ] `FLASK_APP` is set to `wsgi.py`
- [ ] `FLASK_ENV` is set to `production`
- [ ] `FLASK_DEBUG` is set to `0`
- [ ] `SECRET_KEY` is set to a secure random value
- [ ] `DATABASE_URL` points to the PostgreSQL database with correct credentials
- [ ] Email configuration is properly set up (AWS SES or SMTP)

## Deployment Steps

- [ ] Make script executable: `chmod +x improved_deploy.sh`
- [ ] Run the script: `./improved_deploy.sh`
- [ ] For new deployments, choose Option 1 (Full Deployment)
- [ ] For updates, choose Option 2 (Update Application Only)
- [ ] For database changes, choose Option 3 (Database Setup/Migration)
- [ ] Verify each step completes successfully

## Post-Deployment Verification

- [ ] Application is accessible via domain name
- [ ] Systemd service is running (`systemctl status socialstyles.service`)
- [ ] Nginx is correctly configured (`nginx -t`)
- [ ] Database migrations have been applied successfully
- [ ] Static files are being served correctly
- [ ] Email functionality is working
- [ ] Assessment creation and completion works as expected
- [ ] User registration and login functions properly

## Cloudflare Setup

- [ ] Domain added to Cloudflare
- [ ] DNS records configured (A records for @ and www)
- [ ] SSL/TLS set to Full mode
- [ ] Always Use HTTPS option enabled
- [ ] Cache settings configured as needed

## Security Checks

- [ ] Firewall is configured to allow only necessary ports
- [ ] Fail2ban is set up for SSH protection (if needed)
- [ ] All services run with minimum required permissions
- [ ] Debug mode is disabled in production
- [ ] Secret keys and sensitive information are properly secured

## Backup Plan

- [ ] Database backup procedure is established (Option 10 in improved_deploy.sh)
- [ ] Code backup/version control is in place
- [ ] Restore procedure is documented and tested (Option 11 in improved_deploy.sh)

## Documentation

- [ ] Deployment details are documented (server info, URLs, credentials location)
- [ ] Update procedures are documented
- [ ] Rollback procedures are documented
- [ ] Monitoring and alert system is in place

## Performance Testing

- [ ] Application loads quickly
- [ ] Database queries perform efficiently
- [ ] Resource usage (CPU, memory) is at acceptable levels
- [ ] Application can handle expected user load 