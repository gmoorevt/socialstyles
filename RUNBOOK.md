# Social Styles Deployment Runbook

## Quick Reference

### Emergency Contacts
- **Developer:** Solo team
- **Hosting:** DigitalOcean Support (support ticket system)
- **DNS:** Cloudflare Support
- **Database:** DigitalOcean Managed Database Support

### Critical URLs
- **Production:** https://teamsocialstyles.com
- **Staging:** https://staging.teamsocialstyles.com (if configured)
- **Server IP:** 134.209.128.212
- **GitHub:** https://github.com/gmoorevt/socialstyles

---

## Common Operations

### 1. Deploy to Production

**Via GitHub Actions (Recommended):**
```bash
# Merge staging to main
git checkout main
git merge staging
git push origin main

# Approve deployment in GitHub Actions
# Go to: https://github.com/gmoorevt/socialstyles/actions
# Click on workflow → Review deployments → Approve
```

**Manual Deployment (Fallback):**
```bash
# SSH to server
ssh root@134.209.128.212

# Navigate to app directory
cd /var/www/socialstyles

# Pull latest code
git pull origin main

# Install dependencies
sudo -u socialstyles venv/bin/pip install -r requirements.txt

# Run migrations
sudo -u socialstyles venv/bin/flask db upgrade

# Restart application
systemctl restart socialstyles

# Verify
curl http://localhost:8000/health
```

### 2. Rollback Deployment

**Emergency Rollback (Manual):**
```bash
# SSH to server
ssh root@134.209.128.212

# Navigate to app
cd /var/www/socialstyles

# Find previous version tag
git tag -l | tail -5

# Rollback to specific version
git checkout v1.3.0  # or whichever version

# Reinstall dependencies (in case they changed)
sudo -u socialstyles venv/bin/pip install -r requirements.txt

# Rollback database (if migration issues)
sudo -u socialstyles venv/bin/flask db downgrade

# Restart
systemctl restart socialstyles

# Verify
curl http://localhost:8000/health
systemctl status socialstyles
```

**Restore Database Backup:**
```bash
# List available backups
ls -lh /backups/

# Restore from backup
pg_restore -h <db-host> -U <db-user> -d social_styles /backups/backup-20250104.dump

# Or if using DigitalOcean Managed DB:
# Go to DigitalOcean Dashboard → Databases → Backups → Restore
```

### 3. View Logs

```bash
# Application logs (systemd)
journalctl -u socialstyles -f

# Application logs (file-based, if configured)
tail -f /var/www/socialstyles/logs/app.log

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log

# Database logs (if local PostgreSQL)
tail -f /var/log/postgresql/postgresql-14-main.log
```

### 4. Restart Services

```bash
# Restart application
systemctl restart socialstyles

# Restart Nginx
systemctl restart nginx

# Restart both
systemctl restart socialstyles nginx

# Check status
systemctl status socialstyles
systemctl status nginx
```

### 5. Database Migrations

**Create Migration:**
```bash
# Locally
flask db migrate -m "Description of changes"
git add migrations/
git commit -m "Add migration: Description"
git push

# Staging will auto-deploy and run migration
```

**Apply Migration Manually:**
```bash
# SSH to server
ssh root@134.209.128.212

cd /var/www/socialstyles

# Backup first!
sudo -u socialstyles venv/bin/python scripts/backup_db.py

# Dry-run (check for issues)
sudo -u socialstyles venv/bin/flask db upgrade --sql > migration.sql
cat migration.sql  # Review changes

# Apply migration
sudo -u socialstyles venv/bin/flask db upgrade

# Verify
sudo -u socialstyles venv/bin/flask db current
```

**Rollback Migration:**
```bash
cd /var/www/socialstyles

# Show current revision
sudo -u socialstyles venv/bin/flask db current

# Downgrade one step
sudo -u socialstyles venv/bin/flask db downgrade

# Or downgrade to specific revision
sudo -u socialstyles venv/bin/flask db downgrade abc123

# Restart app
systemctl restart socialstyles
```

### 6. Check Application Health

```bash
# Health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"1.4.0","timestamp":"2025-01-04T..."}

# Check database connection
curl http://localhost:8000/health | jq .

# Check from outside (via Cloudflare)
curl https://teamsocialstyles.com/health
```

### 7. Update Dependencies

```bash
# SSH to server
ssh root@134.209.128.212

cd /var/www/socialstyles

# Update requirements.txt locally first, then deploy
# Or update directly on server:

sudo -u socialstyles venv/bin/pip install <package>==<version>
sudo -u socialstyles venv/bin/pip freeze | grep <package>

# Update requirements.txt
sudo -u socialstyles venv/bin/pip freeze > requirements.txt

# Restart
systemctl restart socialstyles
```

---

## Troubleshooting

### Issue: Application Not Responding

**Symptoms:**
- 502 Bad Gateway
- Nginx shows "upstream timed out"
- `curl http://localhost:8000` fails

**Diagnosis:**
```bash
# Check if application is running
systemctl status socialstyles

# Check Gunicorn processes
ps aux | grep gunicorn

# Check port 8000
netstat -tuln | grep 8000
```

**Fix:**
```bash
# Restart application
systemctl restart socialstyles

# If still failing, check logs
journalctl -u socialstyles -n 50

# Common issues:
# 1. Port already in use → kill process on 8000
# 2. Import errors → reinstall dependencies
# 3. Database connection → check DATABASE_URL in .env
```

### Issue: Database Connection Failed

**Symptoms:**
- "could not connect to server" error
- Health check returns unhealthy
- Application logs show database errors

**Diagnosis:**
```bash
# Test database connection
cd /var/www/socialstyles

# Check DATABASE_URL
grep DATABASE_URL .env

# Test connection
sudo -u socialstyles venv/bin/python << EOF
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connection successful!')
EOF
```

**Fix:**
```bash
# 1. Check if database is running (if local)
systemctl status postgresql

# 2. Check firewall rules
ufw status

# 3. Verify DATABASE_URL format
# Should be: postgresql://user:pass@host:5432/dbname

# 4. If using DO Managed DB, check connection pooling
# Go to DO Dashboard → Databases → Connection Details

# 5. Restart application
systemctl restart socialstyles
```

### Issue: Migrations Failing

**Symptoms:**
- "Can't locate revision" error
- "Target database is not up to date"
- Migration hangs

**Diagnosis:**
```bash
cd /var/www/socialstyles

# Check current migration version
sudo -u socialstyles venv/bin/flask db current

# Check migration history
sudo -u socialstyles venv/bin/flask db history

# Compare with codebase
ls -la migrations/versions/
```

**Fix:**
```bash
# Option 1: Force to latest (dangerous!)
sudo -u socialstyles venv/bin/flask db stamp head

# Option 2: Manually fix migration table
# Connect to database and inspect alembic_version table

# Option 3: Reset migrations (ONLY for development/staging)
# Drop all tables and reinitialize
sudo -u socialstyles venv/bin/flask db downgrade base
sudo -u socialstyles venv/bin/flask db upgrade

# Always backup first!
```

### Issue: High CPU/Memory Usage

**Symptoms:**
- Slow response times
- Server unresponsive
- Out of memory errors

**Diagnosis:**
```bash
# Check resource usage
top
htop  # if installed

# Check Gunicorn workers
ps aux | grep gunicorn

# Check memory
free -h

# Check disk space
df -h
```

**Fix:**
```bash
# 1. Adjust Gunicorn workers
# Edit gunicorn_config.py:
# workers = (2 * CPU_CORES) + 1

# 2. Restart application
systemctl restart socialstyles

# 3. If memory leak suspected:
# Enable graceful timeout in gunicorn_config.py
# graceful_timeout = 30
# max_requests = 1000  # Restart workers after 1000 requests

# 4. Upgrade droplet if needed
# DigitalOcean Dashboard → Resize Droplet
```

### Issue: SSL/TLS Errors (Cloudflare)

**Symptoms:**
- ERR_SSL_PROTOCOL_ERROR
- "Too many redirects"
- Mixed content warnings

**Diagnosis:**
```bash
# Test direct connection (bypass Cloudflare)
curl -I http://134.209.128.212

# Test via Cloudflare
curl -I https://teamsocialstyles.com

# Check Nginx configuration
nginx -t
cat /etc/nginx/sites-enabled/socialstyles.conf
```

**Fix:**
```bash
# 1. Cloudflare SSL/TLS mode should be "Flexible"
# Dashboard → SSL/TLS → Overview → Flexible

# 2. Ensure Nginx listens on port 80 (not 443)
# Cloudflare handles SSL, not your server

# 3. Check X-Forwarded-Proto header
# In Nginx config, ensure:
# proxy_set_header X-Forwarded-Proto $scheme;

# 4. Restart Nginx
systemctl restart nginx

# 5. Clear Cloudflare cache
# Dashboard → Caching → Purge Everything
```

### Issue: GitHub Actions Deployment Failing

**Symptoms:**
- Workflow shows red X
- "Permission denied" errors
- SSH connection failures

**Diagnosis:**
```bash
# Check GitHub Actions logs
# Go to: https://github.com/gmoorevt/socialstyles/actions

# Verify secrets are set
# Settings → Secrets and variables → Actions

# Test SSH key locally
ssh -i ~/.ssh/deploy_key root@134.209.128.212
```

**Fix:**
```bash
# 1. Regenerate SSH key if needed
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/deploy_key

# 2. Add public key to server
ssh-copy-id -i ~/.ssh/deploy_key.pub root@134.209.128.212

# 3. Update GitHub secret with private key
cat ~/.ssh/deploy_key | pbcopy  # macOS
# Paste into GitHub Secrets → PROD_SSH_KEY

# 4. Re-run workflow
# GitHub Actions → Failed workflow → Re-run jobs
```

---

## Monitoring & Alerts

### Health Check Script

Create `/usr/local/bin/health-check.sh`:
```bash
#!/bin/bash

HEALTH_URL="http://localhost:8000/health"
ALERT_EMAIL="your-email@example.com"

# Check health endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -ne 200 ]; then
    echo "Application unhealthy! HTTP $response" | \
        mail -s "ALERT: Social Styles Down" $ALERT_EMAIL
    systemctl restart socialstyles
fi
```

Add to crontab:
```bash
*/5 * * * * /usr/local/bin/health-check.sh
```

### Log Rotation

Create `/etc/logrotate.d/socialstyles`:
```
/var/www/socialstyles/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 socialstyles www-data
    sharedscripts
    postrotate
        systemctl reload socialstyles > /dev/null 2>&1 || true
    endscript
}
```

---

## Backup & Recovery

### Automated Database Backup

Create `/usr/local/bin/backup-database.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d-%H%M%S)
DB_NAME="social_styles"

# Load database URL
source /var/www/socialstyles/.env

# Extract connection details
DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:]*).*/\1/')
DB_USER=$(echo $DATABASE_URL | sed -E 's/.*:\/\/([^:]*).*/\1/')
DB_PASS=$(echo $DATABASE_URL | sed -E 's/.*:\/\/[^:]*:([^@]*).*/\1/')

# Backup
export PGPASSWORD="$DB_PASS"
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | \
    gzip > $BACKUP_DIR/backup-$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup-*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup-$DATE.sql.gz"
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-database.sh
```

### Restore from Backup

```bash
# List backups
ls -lh /backups/

# Restore specific backup
gunzip -c /backups/backup-20250104-020000.sql.gz | \
    psql -h $DB_HOST -U $DB_USER -d $DB_NAME
```

---

## Security Checklist

### Regular Security Tasks

**Weekly:**
- [ ] Review application logs for errors
- [ ] Check disk space: `df -h`
- [ ] Verify backups exist: `ls -lh /backups/`

**Monthly:**
- [ ] Update system packages: `apt update && apt upgrade`
- [ ] Review Cloudflare security settings
- [ ] Check SSL certificate expiry
- [ ] Review user access logs

**Quarterly:**
- [ ] Rotate SSH keys
- [ ] Update Python dependencies: `pip list --outdated`
- [ ] Review database performance: slow queries
- [ ] Security audit: check for vulnerabilities

### Security Incident Response

**If Compromised:**
1. **Immediately:** Disable Cloudflare proxy (go to DNS, turn off orange cloud)
2. **Isolate:** Shutdown application: `systemctl stop socialstyles nginx`
3. **Investigate:** Check logs for unauthorized access
4. **Rotate:** Change all passwords, SSH keys, database credentials
5. **Restore:** From clean backup if needed
6. **Update:** Patch vulnerabilities
7. **Monitor:** Watch logs closely for 48 hours

---

## Maintenance Windows

### Planned Maintenance

**Best Times:**
- **Production:** Sunday 2-4 AM EST (lowest traffic)
- **Staging:** Anytime

**Communication:**
- Add banner to application: "Scheduled maintenance on [DATE] at [TIME]"
- Update status page (if configured)

**Process:**
1. Announce maintenance 48 hours in advance
2. Create database backup
3. Enable maintenance mode (optional: custom Nginx 503 page)
4. Perform maintenance
5. Run health checks
6. Disable maintenance mode
7. Monitor for 1 hour

---

## Contacts & Resources

### Documentation
- **This Runbook:** `/Users/gmoore/dev/social-styles/RUNBOOK.md`
- **Deployment Strategy:** `/Users/gmoore/dev/social-styles/DEPLOYMENT_STRATEGY.md`
- **Claude Context:** `/Users/gmoore/dev/social-styles/CLAUDE.md`

### External Resources
- **Flask Docs:** https://flask.palletsprojects.com/
- **Gunicorn Docs:** https://docs.gunicorn.org/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **DigitalOcean Tutorials:** https://www.digitalocean.com/community/tutorials
- **Cloudflare Docs:** https://developers.cloudflare.com/

### Support Channels
- **DigitalOcean Support:** https://cloud.digitalocean.com/support/tickets
- **Cloudflare Support:** https://dash.cloudflare.com/support
- **GitHub Issues:** https://github.com/gmoorevt/socialstyles/issues

---

## Appendix: Useful Commands

### Server Management
```bash
# SSH to server
ssh root@134.209.128.212

# Check server uptime
uptime

# Check system resources
htop
df -h
free -h

# Check running services
systemctl list-units --type=service --state=running

# Reboot server (last resort!)
reboot
```

### Git Operations
```bash
# Check current branch
git branch

# View recent commits
git log --oneline -10

# Create and push tag
git tag v1.4.1
git push origin v1.4.1

# Delete remote tag
git push --delete origin v1.4.0
```

### Database Operations
```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# List databases
\l

# List tables
\dt

# Describe table
\d users

# Run query
SELECT COUNT(*) FROM users;

# Exit
\q
```

### Docker Operations (if used)
```bash
# List containers
docker ps

# View logs
docker logs socialstyles_web

# Restart container
docker-compose restart

# Rebuild
docker-compose up -d --build

# Execute command in container
docker-compose exec web flask db upgrade
```

---

**Last Updated:** January 4, 2025
**Maintainer:** Solo Developer
**Version:** 1.0
