# CI/CD Setup Guide - Social Styles Assessment

This guide will help you set up the complete CI/CD pipeline for Social Styles Assessment using GitHub Actions.

## Prerequisites

- ✅ GitHub repository: `gmoorevt/socialstyles`
- ✅ DigitalOcean droplet (production): 134.209.128.212
- ✅ Cloudflare DNS configured
- ✅ SSH access to production server
- ⬜ (Optional) Staging server

---

## Step 1: Set Up GitHub Secrets (5 minutes)

GitHub Actions needs secure access to your servers. Store credentials as secrets.

### 1.1 Generate SSH Key for GitHub Actions

On your local machine:

```bash
# Generate deployment SSH key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key

# Display the private key (copy this)
cat ~/.ssh/github_deploy_key

# Display the public key
cat ~/.ssh/github_deploy_key.pub
```

### 1.2 Add Public Key to Production Server

```bash
# SSH to your server
ssh root@134.209.128.212

# Add the public key to authorized_keys
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys

# Verify permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Test the connection:
```bash
ssh -i ~/.ssh/github_deploy_key root@134.209.128.212 "echo 'Connection successful'"
```

### 1.3 Add Secrets to GitHub

Go to: https://github.com/gmoorevt/socialstyles/settings/secrets/actions

Click "New repository secret" and add:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `PROD_SSH_HOST` | `134.209.128.212` | Production server IP |
| `PROD_SSH_USER` | `root` | SSH user (or deploy user) |
| `PROD_SSH_KEY` | `<contents of ~/.ssh/github_deploy_key>` | Private SSH key (entire file) |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/dbname` | Production database URL |
| `SECRET_KEY` | `<your-flask-secret-key>` | Flask secret key |

**Optional (for staging):**

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `STAGING_SSH_HOST` | `<staging-server-ip>` | Staging server IP |
| `STAGING_SSH_USER` | `root` | Staging SSH user |
| `STAGING_SSH_KEY` | `<staging-ssh-key>` | Staging SSH private key |

---

## Step 2: Set Up GitHub Environment (3 minutes)

GitHub Environments add manual approval gates for production deployments.

### 2.1 Create Production Environment

1. Go to: https://github.com/gmoorevt/socialstyles/settings/environments
2. Click "New environment"
3. Name: `production`
4. Click "Configure environment"

### 2.2 Add Protection Rules

- ✅ **Required reviewers:** Add yourself (or leave empty if solo)
- ✅ **Wait timer:** 0 minutes (or add delay if needed)
- ⬜ **Deployment branches:** Only allow `main` branch

Click "Save protection rules"

---

## Step 3: Create Staging Branch (2 minutes)

The staging branch auto-deploys to a staging server for testing.

```bash
# Create staging branch from main
git checkout main
git pull
git checkout -b staging
git push -u origin staging
```

---

## Step 4: Test the Workflows (5 minutes)

### 4.1 Test the Test Workflow

Create a feature branch and push:

```bash
git checkout -b feature/test-cicd
echo "# CI/CD Test" >> test.txt
git add test.txt
git commit -m "Test CI/CD workflows"
git push -u origin feature/test-cicd
```

Go to: https://github.com/gmoorevt/socialstyles/actions

You should see:
- ✅ "Run Tests" workflow running
- Tests execute automatically
- No deployment happens (feature branch)

### 4.2 Test Staging Deployment (if configured)

```bash
# Merge to staging
git checkout staging
git merge feature/test-cicd
git push origin staging
```

Watch: https://github.com/gmoorevt/socialstyles/actions
- ✅ "Deploy to Staging" workflow runs
- Auto-deploys to staging server
- No manual approval needed

### 4.3 Test Production Deployment

```bash
# Merge staging to main
git checkout main
git merge staging
git push origin main
```

Watch: https://github.com/gmoorevt/socialstyles/actions
- ✅ "Deploy to Production" workflow runs
- ✅ Tests run first
- ⏸️ **Waits for manual approval**
- Click "Review deployments" → "Approve"
- ✅ Deploys to production
- ✅ Creates git tag automatically

---

## Step 5: Set Up Staging Server (Optional, 30 minutes)

### 5.1 Create Staging Droplet

1. Go to: https://cloud.digitalocean.com/droplets
2. Create Droplet:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic - $6/month (1GB RAM)
   - **Region:** Same as production
   - **SSH Key:** Add your SSH key
3. Note the IP address

### 5.2 Configure Staging Server

SSH to the staging server and run:

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3-pip python3-venv nginx git \
    build-essential libssl-dev libffi-dev python3-dev \
    postgresql-client libpq-dev

# Create app user
useradd -m -d /var/www/socialstyles-staging -s /bin/bash socialstyles
usermod -aG www-data socialstyles

# Clone repository
cd /var/www
git clone -b staging https://github.com/gmoorevt/socialstyles.git socialstyles-staging
chown -R socialstyles:www-data socialstyles-staging

# Set up virtual environment
cd socialstyles-staging
python3 -m venv venv
chown -R socialstyles:www-data venv
sudo -u socialstyles venv/bin/pip install -r requirements.txt

# Create .env file
sudo -u socialstyles nano .env
# (Add your staging environment variables)

# Run migrations
sudo -u socialstyles venv/bin/flask db upgrade

# Set up systemd service
cat > /etc/systemd/system/socialstyles-staging.service << 'EOF'
[Unit]
Description=Social Styles Staging
After=network.target

[Service]
User=socialstyles
Group=www-data
WorkingDirectory=/var/www/socialstyles-staging
Environment="PATH=/var/www/socialstyles-staging/venv/bin"
ExecStart=/var/www/socialstyles-staging/venv/bin/gunicorn -w 2 -b 0.0.0.0:8001 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable socialstyles-staging
systemctl start socialstyles-staging

# Set up Nginx
cat > /etc/nginx/sites-available/staging << 'EOF'
server {
    listen 80;
    server_name staging.teamsocialstyles.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/staging /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### 5.3 Configure Cloudflare DNS

1. Go to Cloudflare Dashboard → DNS
2. Add A record:
   - **Type:** A
   - **Name:** staging
   - **IPv4 address:** `<staging-server-ip>`
   - **Proxy status:** Proxied (orange cloud)
   - **TTL:** Auto
3. Save

Wait 2-5 minutes for DNS propagation.

Test: https://staging.teamsocialstyles.com

---

## Step 6: Set Up Monitoring (10 minutes)

### 6.1 Add Health Check Cron Job

On production server:

```bash
# Create health check script
mkdir -p /var/log/socialstyles
cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
LOG_FILE="/var/log/socialstyles/health-check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "[$TIMESTAMP] ❌ Health check failed, restarting..." >> $LOG_FILE
    systemctl restart socialstyles
else
    echo "[$TIMESTAMP] ✅ Healthy" >> $LOG_FILE
fi
EOF

chmod +x /usr/local/bin/health-check.sh

# Add to crontab (runs every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/health-check.sh") | crontab -
```

### 6.2 Set Up UptimeRobot (Free External Monitoring)

1. Go to: https://uptimerobot.com (create free account)
2. Add New Monitor:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Social Styles Production
   - **URL:** https://teamsocialstyles.com/health
   - **Monitoring Interval:** 5 minutes
3. Add email alert

Repeat for staging if configured.

---

## Step 7: Test Complete Workflow (5 minutes)

### 7.1 Make a Code Change

```bash
# Create feature branch
git checkout -b feature/update-homepage
echo "<!-- CI/CD Test -->" >> app/templates/base.html
git add .
git commit -m "Test CI/CD: Update homepage"
git push -u origin feature/update-homepage
```

### 7.2 Create Pull Request to Staging

1. Go to GitHub
2. Create PR: `feature/update-homepage` → `staging`
3. Watch tests run automatically
4. Merge when tests pass

### 7.3 Auto-Deploy to Staging

- Staging auto-deploys immediately
- Visit: https://staging.teamsocialstyles.com
- Verify changes

### 7.4 Create Pull Request to Main

1. Create PR: `staging` → `main`
2. Review changes
3. Merge when ready

### 7.5 Deploy to Production

1. GitHub Actions runs tests
2. **Waits for your approval**
3. Go to Actions → Review deployments → Approve
4. Deploys to production
5. Creates version tag (e.g., `v20250104.143022`)
6. Visit: https://teamsocialstyles.com

---

## Deployment Workflows

### Normal Development Flow

```
1. Create feature branch
   └─> git checkout -b feature/my-feature

2. Make changes, commit, push
   └─> Tests run automatically (no deploy)

3. Create PR to staging
   └─> Tests run
   └─> Merge → Auto-deploy to staging

4. Test on staging
   └─> https://staging.teamsocialstyles.com

5. Create PR from staging to main
   └─> Review changes
   └─> Merge

6. Production deployment starts
   └─> Tests run
   └─> **Manual approval required**
   └─> Approve → Deploy to production
   └─> Tag created automatically

7. Verify production
   └─> https://teamsocialstyles.com
```

### Emergency Hotfix

```bash
# Create hotfix from main
git checkout main
git pull
git checkout -b hotfix/critical-bug

# Fix and commit
git add .
git commit -m "Hotfix: Fix critical bug"

# Push directly to main (bypass staging for emergencies)
git checkout main
git merge hotfix/critical-bug
git push origin main

# Approve deployment in GitHub Actions
```

### Rollback

**Option 1: Via Script (Fastest)**
```bash
ssh root@134.209.128.212
cd /var/www/socialstyles
./scripts/rollback.sh v20250104.120000  # Previous version
```

**Option 2: Via GitHub Actions**
```bash
# Revert commit locally
git revert HEAD
git push origin main

# Or checkout previous tag
git checkout v20250104.120000
git push -f origin main  # Force push (use with caution!)
```

---

## Troubleshooting

### Tests Failing in GitHub Actions

**Check:**
- Test files exist: `test_assessment_math.py`, `test_team_dashboard.py`
- Dependencies installed: `requirements.txt` includes test deps
- Database service running in workflow

**Fix:**
- Update `.github/workflows/test.yml`
- Add missing dependencies
- Check test logs in Actions tab

### Deployment Failing - SSH Issues

**Symptoms:**
- "Permission denied (publickey)"
- "Host key verification failed"

**Fix:**
```bash
# Regenerate SSH key
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy_key

# Add to server
ssh root@134.209.128.212
echo "NEW_PUBLIC_KEY" >> ~/.ssh/authorized_keys

# Update GitHub secret: PROD_SSH_KEY
```

### Health Check Failing

**Check:**
- App is running: `systemctl status socialstyles`
- Port 8000 is open: `netstat -tuln | grep 8000`
- Health endpoint works: `curl http://localhost:8000/health`

**Fix:**
- Restart app: `systemctl restart socialstyles`
- Check logs: `journalctl -u socialstyles -f`

### Database Migration Failing

**Symptoms:**
- "Can't locate revision"
- Migration hangs

**Fix:**
```bash
# On server
cd /var/www/socialstyles

# Check current version
sudo -u socialstyles venv/bin/flask db current

# Force to head (use with caution!)
sudo -u socialstyles venv/bin/flask db stamp head

# Or rollback and reapply
sudo -u socialstyles venv/bin/flask db downgrade
sudo -u socialstyles venv/bin/flask db upgrade
```

---

## Manual Deployment (Fallback)

If GitHub Actions is unavailable:

```bash
# Production
./scripts/deploy.sh production

# Staging
./scripts/deploy.sh staging
```

---

## Security Checklist

- ✅ SSH keys are unique for GitHub Actions (not reused)
- ✅ Private keys stored only in GitHub Secrets (encrypted)
- ✅ Database credentials not in code (in .env and secrets)
- ✅ Production requires manual approval
- ✅ Automated backups before deployment
- ✅ Health checks monitor uptime
- ✅ Rollback process tested and documented

---

## Cost Summary

### Minimal Setup (Current)
- Production server: $12/month
- **Total: $12/month**

### With Staging
- Production server: $12/month
- Staging server: $6/month
- **Total: $18/month**

### Recommended (with Managed DB)
- Production server: $24/month (4GB RAM)
- Staging server: $6/month
- Managed PostgreSQL: $15/month
- **Total: $45/month**

---

## Next Steps

1. ✅ Set up GitHub Secrets (Step 1)
2. ✅ Configure GitHub Environment (Step 2)
3. ✅ Test workflows (Step 4)
4. ⬜ (Optional) Set up staging server (Step 5)
5. ✅ Configure monitoring (Step 6)
6. ✅ Test complete workflow (Step 7)

---

## Support

**Issues?** Create an issue: https://github.com/gmoorevt/socialstyles/issues

**Documentation:**
- Deployment Strategy: `DEPLOYMENT_STRATEGY.md`
- Runbook: `RUNBOOK.md`
- Claude Context: `CLAUDE.md`

---

**Setup complete!** 🎉

Your CI/CD pipeline is now ready. Every push to `main` will trigger automated testing and deployment with your approval.
