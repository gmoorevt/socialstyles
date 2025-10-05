# 🚀 Deployment Quick Reference

One-page cheat sheet for Social Styles deployment operations.

---

## 📋 Common Commands

### Deploy to Production
```bash
# Via GitHub (Recommended)
git checkout main
git merge staging
git push origin main
# → Approve in GitHub Actions

# Manual (Fallback)
./scripts/deploy.sh production
```

### Deploy to Staging
```bash
git checkout staging
git merge feature/my-feature
git push origin staging
# → Auto-deploys automatically
```

### Rollback Production
```bash
# Find version to rollback to
git tag -l | tail -10

# Option 1: Manual script
ssh root@134.209.128.212
cd /var/www/socialstyles
./scripts/rollback.sh v20250104.120000

# Option 2: GitHub Actions
# Go to Actions → Rollback Production → Run workflow
```

### View Logs
```bash
# Application logs
ssh root@134.209.128.212 "journalctl -u socialstyles -f"

# Nginx logs
ssh root@134.209.128.212 "tail -f /var/log/nginx/error.log"

# Health check logs
ssh root@134.209.128.212 "tail -f /var/log/socialstyles/health-check.log"
```

### Check Status
```bash
# Health check
curl https://teamsocialstyles.com/health

# Service status
ssh root@134.209.128.212 "systemctl status socialstyles"

# Version info
curl https://teamsocialstyles.com/health | jq .version
```

### Database Operations
```bash
# Connect to database
ssh root@134.209.128.212
cd /var/www/socialstyles
source .env
psql $DATABASE_URL

# Run migration
sudo -u socialstyles venv/bin/flask db upgrade

# Rollback migration
sudo -u socialstyles venv/bin/flask db downgrade

# Backup database
pg_dump $DATABASE_URL | gzip > backup.sql.gz
```

---

## 🔄 Normal Workflow

```
1. Feature → Staging → Production

   git checkout -b feature/my-feature
   # Make changes
   git push origin feature/my-feature
   # Create PR to staging → Merge
   # Test on staging
   # Create PR to main → Merge
   # Approve in GitHub Actions
```

---

## 🆘 Emergency Procedures

### Application Down
```bash
# 1. Check if running
ssh root@134.209.128.212 "systemctl status socialstyles"

# 2. Restart
ssh root@134.209.128.212 "systemctl restart socialstyles"

# 3. Check logs
ssh root@134.209.128.212 "journalctl -u socialstyles -n 50"
```

### Database Issues
```bash
# 1. Test connection
ssh root@134.209.128.212
cd /var/www/socialstyles
source .env
psql $DATABASE_URL -c "SELECT 1;"

# 2. Restore from backup
gunzip -c /var/backups/socialstyles/backup-20250104.sql.gz | \
    psql $DATABASE_URL
```

### Rollback Emergency
```bash
# Quick rollback to previous version
ssh root@134.209.128.212
cd /var/www/socialstyles
git tag -l | tail -5  # Find previous version
git checkout v20250104.120000
systemctl restart socialstyles
```

---

## 📊 Monitoring

### Health Endpoints
- **Production:** https://teamsocialstyles.com/health
- **Staging:** https://staging.teamsocialstyles.com/health
- **Direct:** http://134.209.128.212/health

### Expected Response
```json
{
  "status": "healthy",
  "version": "1.4.0",
  "timestamp": "2025-01-04T21:30:00Z"
}
```

### Monitoring Tools
- **UptimeRobot:** External monitoring (5min intervals)
- **Cron Job:** Internal health check (5min intervals)
- **GitHub Actions:** Deployment monitoring

---

## 🔐 GitHub Secrets

Required secrets in GitHub repository settings:

| Secret | Value | Used By |
|--------|-------|---------|
| `PROD_SSH_HOST` | `134.209.128.212` | Production workflows |
| `PROD_SSH_USER` | `root` | Production workflows |
| `PROD_SSH_KEY` | SSH private key | Production workflows |
| `STAGING_SSH_HOST` | Staging IP | Staging workflows |
| `STAGING_SSH_USER` | `root` | Staging workflows |
| `STAGING_SSH_KEY` | SSH private key | Staging workflows |

---

## 📁 Important Files

### Configuration
- `.env` - Environment variables (local)
- `.env.production` - Production env vars (on server)
- `config.py` - Flask configuration classes

### Deployment
- `.github/workflows/deploy-production.yml` - Production CI/CD
- `.github/workflows/deploy-staging.yml` - Staging CI/CD
- `.github/workflows/test.yml` - Test automation
- `.github/workflows/rollback.yml` - Rollback workflow

### Scripts
- `scripts/deploy.sh` - Manual deployment
- `scripts/rollback.sh` - Manual rollback
- `scripts/health-check.sh` - Health monitoring

### Documentation
- `DEPLOYMENT_STRATEGY.md` - Overall strategy
- `SETUP_CICD.md` - Setup instructions
- `RUNBOOK.md` - Operational procedures
- `DEPLOYMENT_QUICK_REFERENCE.md` - This file

---

## 🌐 URLs

| Environment | URL | Server |
|-------------|-----|--------|
| Production | https://teamsocialstyles.com | 134.209.128.212 |
| Staging | https://staging.teamsocialstyles.com | TBD |
| GitHub | https://github.com/gmoorevt/socialstyles | - |
| GitHub Actions | https://github.com/gmoorevt/socialstyles/actions | - |

---

## 🔧 Troubleshooting Quick Fixes

### 502 Bad Gateway
```bash
systemctl restart socialstyles nginx
```

### Database Connection Failed
```bash
# Check .env file
grep DATABASE_URL /var/www/socialstyles/.env

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Migration Failed
```bash
# Force to current state (careful!)
flask db stamp head

# Or rollback and retry
flask db downgrade
flask db upgrade
```

### High CPU/Memory
```bash
# Check resources
htop

# Restart with fresh workers
systemctl restart socialstyles
```

### SSL/Cloudflare Issues
```bash
# Check Cloudflare SSL mode: Should be "Flexible"
# Check Nginx config
nginx -t

# Restart Nginx
systemctl restart nginx

# Clear Cloudflare cache in dashboard
```

---

## 📞 Support Contacts

- **DigitalOcean Support:** https://cloud.digitalocean.com/support/tickets
- **Cloudflare Support:** https://dash.cloudflare.com/support
- **GitHub Issues:** https://github.com/gmoorevt/socialstyles/issues

---

## 🎯 Quick Decisions

### Should I rollback?
**YES if:**
- ❌ Health check fails repeatedly
- ❌ Critical feature broken
- ❌ Database errors
- ❌ Users reporting issues

**NO if:**
- ✅ Minor UI issue (push hotfix instead)
- ✅ Isolated edge case
- ✅ Can be fixed with config change

### Staging vs. Direct to Production?
**Use Staging:**
- ✅ Major features
- ✅ Database schema changes
- ✅ Dependency updates
- ✅ Refactoring

**Skip Staging (with caution):**
- ⚠️ Hotfixes for critical bugs
- ⚠️ Documentation updates
- ⚠️ Minor CSS/text changes

---

**Last Updated:** January 4, 2025
**Version:** 1.0

---

## 💡 Pro Tips

1. **Always test on staging first** - Even for "small" changes
2. **Tag releases consistently** - Use date-based tags (v20250104.HHMMSS)
3. **Keep backups** - Automated daily backups to /var/backups
4. **Monitor after deploy** - Watch logs for 5-10 minutes post-deploy
5. **Document incidents** - Note what went wrong and how you fixed it
6. **Health checks are your friend** - Always verify after changes
7. **Don't deploy on Fridays** - Unless you enjoy weekend debugging 😅
