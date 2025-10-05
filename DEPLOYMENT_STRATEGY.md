# Social Styles - Simple CI/CD Deployment Strategy

## Overview

This is a **simple, repeatable deployment process** designed for a **solo developer** using:
- **GitHub Actions** for CI/CD
- **DigitalOcean Droplets** for hosting
- **Cloudflare** for DNS and SSL
- **PostgreSQL** as the database
- **Zero-downtime deployments** with health checks

---

## Architecture

```
┌─────────────────┐
│   Developer     │
│  (Local Dev)    │
└────────┬────────┘
         │ git push
         ▼
┌─────────────────────────┐
│   GitHub Repository     │
│  - main (production)    │
│  - staging (pre-prod)   │
└──────────┬──────────────┘
           │ triggers
           ▼
┌─────────────────────────────────┐
│      GitHub Actions             │
│  - Run tests                    │
│  - Build Docker image           │
│  - Run migrations (dry-run)     │
│  - Deploy to server             │
└──────────┬──────────────────────┘
           │ SSH deploy
           ▼
┌─────────────────────────────────┐
│   DigitalOcean Droplets         │
│                                 │
│  ┌─────────────────────────┐   │
│  │  Staging (optional)     │   │
│  │  - Test deployments     │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  Production             │   │
│  │  - Nginx                │   │
│  │  - Gunicorn             │   │
│  │  - Flask App            │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  External PostgreSQL Database   │
│  (DigitalOcean Managed DB)      │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│        Cloudflare               │
│  - DNS Management               │
│  - SSL/TLS                      │
│  - DDoS Protection              │
└─────────────────────────────────┘
```

---

## Infrastructure Setup

### 1. Current Production Environment
- **IP:** 134.209.128.212
- **Domain:** teamsocialstyles.com
- **Server:** Ubuntu on DigitalOcean
- **Database:** External PostgreSQL (recommended: DigitalOcean Managed Database)

### 2. Recommended: Add Staging Environment
- **Purpose:** Test deployments before production
- **Setup:** Small DigitalOcean droplet ($6/month)
- **Domain:** staging.teamsocialstyles.com (Cloudflare subdomain)
- **Database:** Share production DB with staging schema OR separate staging DB

### 3. Database Strategy

**Current State:** Using external PostgreSQL
**Recommendation:** Use DigitalOcean Managed PostgreSQL Database

**Why Managed Database?**
- ✅ Automated backups
- ✅ Point-in-time recovery
- ✅ Automatic failover
- ✅ Easy scaling
- ✅ Monitoring built-in
- ✅ No manual maintenance

**Database Migration Strategy:**
```
Production DB:
- Schema: public (production data)
- Schema: staging (optional, for staging environment)

Migration Process:
1. Always test migrations on staging first
2. Backup production DB automatically before migration
3. Run migration with dry-run flag first
4. Apply migration to production
5. Keep rollback scripts ready
```

---

## CI/CD Workflow Design

### Branch Strategy

```
main (production)
  ├── Protected branch
  ├── Requires PR approval
  ├── Auto-deploy to production
  └── Tagged releases (v1.0.0, v1.1.0, etc.)

staging (pre-production)
  ├── Auto-deploy to staging server
  ├── Testing ground
  └── Merge to main when stable

feature/* (development)
  ├── Feature branches
  ├── Run tests only
  └── PR to staging
```

### Deployment Triggers

**Production (`main` branch):**
- ✅ All tests pass
- ✅ Manual approval required (GitHub Environment)
- ✅ Deploy during off-peak hours (configurable)
- ✅ Create git tag automatically

**Staging (`staging` branch):**
- ✅ Auto-deploy on push
- ✅ Run tests
- ✅ No manual approval needed

**Feature branches:**
- ✅ Run tests only
- ❌ No deployment

### Deployment Steps (Automated)

1. **Pre-Deployment Checks**
   - Run unit tests
   - Run integration tests
   - Check code quality (optional: flake8, black)
   - Verify .env variables exist

2. **Build Phase**
   - Build Docker image
   - Tag with commit SHA and version
   - Push to GitHub Container Registry (optional)

3. **Database Migration (Safe)**
   - Backup database automatically
   - Run migration in dry-run mode
   - Apply migration if dry-run succeeds
   - Keep backup for 30 days

4. **Deploy Application**
   - SSH to server
   - Pull latest code
   - Update dependencies
   - Run database migrations
   - Restart services with zero-downtime
   - Run health checks

5. **Post-Deployment**
   - Verify application is running
   - Send notification (optional: Slack, email)
   - Monitor for errors (check logs)

6. **Rollback (if needed)**
   - Revert to previous git tag
   - Restore database backup
   - Restart services

---

## Implementation Plan

### Phase 1: Prepare Infrastructure (1-2 hours)

1. **Set up GitHub Secrets** (Store sensitive data)
   ```
   PROD_SSH_HOST=134.209.128.212
   PROD_SSH_USER=root
   PROD_SSH_KEY=<your-private-ssh-key>
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   SECRET_KEY=<flask-secret-key>
   ```

2. **Optional: Create Staging Server**
   - Create small DO droplet ($6/month)
   - Configure same as production
   - Point staging.teamsocialstyles.com to it

3. **Set up Managed PostgreSQL Database** (Recommended)
   - Create DigitalOcean Managed PostgreSQL
   - Migrate data from current database
   - Update DATABASE_URL in production

### Phase 2: Create GitHub Actions Workflows (2-3 hours)

**File: `.github/workflows/deploy-production.yml`**
- Trigger: Push to `main` branch
- Requires: Manual approval
- Steps: Test → Migrate → Deploy → Health Check

**File: `.github/workflows/deploy-staging.yml`**
- Trigger: Push to `staging` branch
- Auto-deploy without approval

**File: `.github/workflows/test.yml`**
- Trigger: PR to any branch
- Run tests only

### Phase 3: Database Safety (1 hour)

1. **Automated Backups**
   - Use DigitalOcean Managed DB daily backups
   - OR create backup script in workflow

2. **Migration Safety**
   - Always dry-run first
   - Backup before migration
   - Test on staging first

### Phase 4: Deploy Scripts (1 hour)

1. **Create `scripts/deploy.sh`** - Production deployment script
2. **Create `scripts/rollback.sh`** - Rollback to previous version
3. **Create `scripts/health-check.sh`** - Verify deployment success

### Phase 5: Documentation (30 minutes)

1. Update CLAUDE.md with new process
2. Create runbook for common issues
3. Document rollback procedures

---

## Deployment Workflow (End-to-End)

### Normal Development Flow

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes and test locally
docker-compose up -d

# 3. Run tests
python3 test_assessment_math.py

# 4. Commit and push
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 5. Create PR to staging branch
# GitHub Actions runs tests automatically

# 6. Merge to staging (after tests pass)
# Auto-deploys to staging.teamsocialstyles.com

# 7. Test on staging environment
curl https://staging.teamsocialstyles.com/health

# 8. Create PR from staging to main
# Request review (or self-approve if solo)

# 9. Merge to main
# GitHub Actions workflow asks for approval

# 10. Approve deployment
# Workflow deploys to production automatically

# 11. Verify production
curl https://teamsocialstyles.com/health
```

### Emergency Rollback

```bash
# 1. Trigger rollback workflow in GitHub Actions
# OR manually:

# 2. SSH to server
ssh root@134.209.128.212

# 3. Run rollback script
cd /var/www/socialstyles
./scripts/rollback.sh v1.3.0  # Rollback to specific version

# 4. Verify
systemctl status socialstyles
curl http://localhost:8000/health
```

---

## Zero-Downtime Deployment

### Strategy: Blue-Green Deployment (Simple Version)

1. **Current Setup:**
   - Gunicorn running on port 8000
   - Nginx proxying to Gunicorn

2. **Zero-Downtime Process:**
   ```bash
   # 1. Pull new code
   git pull origin main

   # 2. Install dependencies in venv
   venv/bin/pip install -r requirements.txt

   # 3. Run migrations (safe, non-blocking)
   venv/bin/flask db upgrade

   # 4. Graceful restart (Gunicorn handles this well)
   # SIGUSR2: Spawn new workers, then kill old workers
   kill -SIGUSR2 $(cat gunicorn.pid)

   # 5. Health check
   curl http://localhost:8000/health || rollback
   ```

3. **Gunicorn Configuration** (`gunicorn_config.py`):
   ```python
   # Enable graceful restarts
   graceful_timeout = 30
   timeout = 60
   workers = 4  # Adjust based on CPU cores

   # Preload app for faster restarts
   preload_app = True

   # Worker class for WebSocket support
   worker_class = 'eventlet'
   ```

---

## Health Checks & Monitoring

### 1. Application Health Endpoint

Add to `app/main/views.py`:
```python
@main.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'version': app.config.get('VERSION', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

### 2. Monitoring (Simple)

**Option A: DigitalOcean Monitoring** (Built-in)
- CPU, Memory, Disk usage
- Alerts via email
- Free with droplet

**Option B: UptimeRobot** (Free tier)
- External health check every 5 minutes
- Email/SMS alerts on downtime
- Status page

**Option C: Simple Cron Job** (DIY)
```bash
# /etc/cron.d/health-check
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart socialstyles
```

---

## Security Considerations

### 1. Secrets Management
- ✅ Store all secrets in GitHub Secrets
- ✅ Never commit `.env` files
- ✅ Rotate SSH keys quarterly
- ✅ Use read-only database user for app (not superuser)

### 2. SSH Access
- ✅ Use SSH keys (not passwords)
- ✅ Disable root login (create deploy user)
- ✅ Restrict SSH to GitHub Actions IP ranges

### 3. Database Security
- ✅ Use SSL for database connections
- ✅ Restrict database access to app server IP only
- ✅ Regular security updates

---

## Cost Breakdown

### Minimal Setup (Current)
- Production Droplet: $12/month (2GB RAM)
- Domain: $12/year (Cloudflare free tier)
- **Total: ~$12.50/month**

### Recommended Setup (with Staging + Managed DB)
- Production Droplet: $24/month (4GB RAM)
- Staging Droplet: $6/month (1GB RAM)
- Managed PostgreSQL: $15/month (1GB RAM, 10GB storage)
- Domain: $12/year
- **Total: ~$46/month**

### Budget-Friendly Alternative
- Production Droplet: $12/month (2GB RAM)
- External PostgreSQL on same droplet: $0
- No staging (test locally): $0
- **Total: ~$12/month** (same as current)

---

## Quick Start Guide

### Immediate Actions (30 minutes)

1. **Create GitHub Secrets:**
   - Go to repo → Settings → Secrets and variables → Actions
   - Add: `PROD_SSH_HOST`, `PROD_SSH_KEY`, `DATABASE_URL`, `SECRET_KEY`

2. **Create staging branch:**
   ```bash
   git checkout -b staging
   git push -u origin staging
   ```

3. **Test deployment script locally:**
   ```bash
   ./improved_deploy.sh
   # Choose option 11 (Update application only)
   ```

### Next Steps (This Week)

1. Create GitHub Actions workflows (provided in next files)
2. Test staging deployment
3. Set up health checks
4. Configure monitoring
5. Document runbook

---

## Comparison: Current vs. Proposed

| Aspect | Current | Proposed CI/CD |
|--------|---------|----------------|
| **Deployment** | Manual SSH + script | Automated via GitHub Actions |
| **Testing** | Manual local tests | Automated tests on every PR |
| **Database Migrations** | Manual `flask db upgrade` | Automated with safety checks |
| **Rollback** | Manual git revert + redeploy | One-click rollback workflow |
| **Monitoring** | Cron job (basic) | Health checks + alerts |
| **Downtime** | ~30 seconds | Zero-downtime (graceful restart) |
| **Staging** | None | Optional staging environment |
| **Time to Deploy** | 5-10 minutes | 2-3 minutes (automated) |

---

## Decision: What to Implement?

### Option 1: Minimal (Fastest)
**Time: 2-3 hours | Cost: $0 extra**
- ✅ GitHub Actions for main branch only
- ✅ Automated tests
- ✅ Automated deployment to current server
- ✅ Basic health checks
- ❌ No staging environment

### Option 2: Recommended (Best Balance)
**Time: 4-6 hours | Cost: +$21/month**
- ✅ GitHub Actions for staging + production
- ✅ Staging environment ($6/month)
- ✅ Managed PostgreSQL ($15/month)
- ✅ Zero-downtime deployments
- ✅ Automated backups & migrations
- ✅ Monitoring & alerts

### Option 3: Budget-Friendly (Middle Ground)
**Time: 3-4 hours | Cost: $0 extra**
- ✅ GitHub Actions for staging + production
- ✅ Staging uses same server (different port/domain)
- ✅ PostgreSQL on same droplet
- ✅ Automated deployments
- ❌ No managed database benefits

---

## Next Steps

1. **Decide on option** (Minimal, Recommended, or Budget-Friendly)
2. **I'll create the GitHub Actions workflow files** based on your choice
3. **Set up GitHub Secrets** with your credentials
4. **Test deployment** to staging first
5. **Deploy to production** with confidence

**Which option would you prefer?** Let me know and I'll create the specific implementation files!
