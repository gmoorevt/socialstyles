# Social Styles Assessment Deployment Checklist

Use this checklist to ensure a smooth deployment process.

## Pre-Deployment Preparation

- [ ] Ensure all code changes are committed and pushed to the repository
- [ ] Update version information in `version.txt`
- [ ] Create or update `.env` file with proper configuration
- [ ] Test the application locally with similar settings to production

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

- [ ] Run Improved Deployment Script
  - [ ] Step 1: Check prerequisites and setup
  - [ ] Step 2: Update server and install dependencies
  - [ ] Step 3: Set up PostgreSQL database connection
  - [ ] Step 4: Clone repository and set up environment
  - [ ] Step 5: Initialize application database
  - [ ] Step 6: Configure Nginx and SSL
  - [ ] Step 7: Set up systemd service
  - [ ] Step 8: Set up service monitoring
  - [ ] Step 9: Test deployment

## Post-Deployment Verification

- [ ] Application is accessible via IP address
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

- [ ] Database backup procedure is established
- [ ] Code backup/version control is in place
- [ ] Restore procedure is documented and tested

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