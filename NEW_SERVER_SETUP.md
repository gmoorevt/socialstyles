# New Production Server Setup Guide

This guide walks you through creating a brand new production server for Social Styles Assessment.

---

## Overview

**Goal:** Create a fresh DigitalOcean production server with CI/CD ready to go

**Time Required:** 30-45 minutes

**What You'll Get:**
- Fresh Ubuntu server optimized for production
- Automated deployment via GitHub Actions
- Zero-downtime deployments
- Automatic backups
- Health monitoring

---

## Step 1: Create DigitalOcean Droplet (5 minutes)

### 1.1 Go to DigitalOcean

Visit: https://cloud.digitalocean.com/droplets/new

### 1.2 Configure Droplet

**Choose an image:**
- ✅ Ubuntu 22.04 LTS x64

**Choose Size:**
- **Recommended:** Regular - $24/month (4GB RAM, 2 vCPUs, 80GB SSD)
  - Good for production with room to grow
  - Can handle multiple concurrent users
- **Budget:** Basic - $12/month (2GB RAM, 1 vCPU, 50GB SSD)
  - Minimum for production
  - Fine for low traffic

**Choose a datacenter region:**
- Select closest to your users
- Recommended: New York 1, San Francisco 3, or Toronto 1

**Authentication:**
- ✅ SSH Key (recommended)
- Select your existing SSH key OR create a new one
- If creating new:
  ```bash
  # On your Mac
  ssh-keygen -t ed25519 -C "digitalocean-production"
  cat ~/.ssh/id_ed25519.pub  # Copy this
  ```
  Then paste into DigitalOcean

**Choose a hostname:**
- `socialstyles-prod` or `teamsocialstyles`

**Add tags (optional):**
- `production`
- `socialstyles`

### 1.3 Create Droplet

Click **Create Droplet**

Wait 1-2 minutes for provisioning.

**Note the IP address!** You'll need this for DNS and deployment.

---

## Step 2: Initial Server Connection (2 minutes)

### 2.1 Get Server IP

From DigitalOcean dashboard, copy the new droplet's IP address.

Example: `157.230.45.123`

### 2.2 Connect via SSH

```bash
# Replace with your actual IP
ssh root@157.230.45.123
```

Accept the host key fingerprint when prompted (type `yes`)

You should see a welcome message from Ubuntu.

---

## Step 3: Run Automated Setup Script (5 minutes)

### 3.1 Download and Run Setup Script

On the server, run:

```bash
# Download setup script
curl -o setup.sh https://raw.githubusercontent.com/gmoorevt/socialstyles/main/scripts/setup-production-server.sh

# Make executable
chmod +x setup.sh

# Run setup
./setup.sh
```

This script will:
- ✅ Update system packages
- ✅ Install Python, Nginx, PostgreSQL client
- ✅ Create application user
- ✅ Clone your GitHub repository
- ✅ Set up Python virtual environment
- ✅ Configure systemd service
- ✅ Configure Nginx
- ✅ Set up firewall
- ✅ Create backup directories

**Time:** 3-5 minutes

### 3.2 Script Output

You'll see progress messages like:
```
[1/10] Updating system packages...
✅ System updated

[2/10] Installing dependencies...
✅ Dependencies installed

...

╔════════════════════════════════════════╗
║   Server Setup Complete! 🎉            ║
╚════════════════════════════════════════╝
```

---

## Step 4: Configure Database (10 minutes)

You have two options:

### Option A: DigitalOcean Managed Database (Recommended - $15/month)

**Pros:**
- Automated backups
- Point-in-time recovery
- High availability
- No maintenance

**Setup:**

1. **Create Managed Database:**
   - Go to: https://cloud.digitalocean.com/databases/new
   - Choose: PostgreSQL 14
   - Plan: Basic - $15/month (1GB RAM, 10GB storage)
   - Same region as your droplet
   - Click **Create Database Cluster**

2. **Get Connection Details:**
   - Wait 3-5 minutes for database to provision
   - Click **Connection Details**
   - Copy the **Connection String**
   - Example: `postgresql://doadmin:PASS@db-postgresql-nyc1-12345.db.ondigitalocean.com:25060/defaultdb?sslmode=require`

3. **Add Droplet to Trusted Sources:**
   - In database dashboard → Settings → Trusted Sources
   - Add your droplet's IP address
   - Click **Save**

### Option B: PostgreSQL on Same Server (Free - Not Recommended)

**Setup:**

```bash
# Install PostgreSQL
apt-get install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE social_styles;
CREATE USER social_user WITH PASSWORD 'CHANGE_THIS_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE social_styles TO social_user;
\q
EOF

# Connection string will be:
# postgresql://social_user:CHANGE_THIS_PASSWORD@localhost:5432/social_styles
```

---

## Step 5: Configure Application (5 minutes)

### 5.1 Edit .env File

```bash
cd /var/www/socialstyles
nano .env
```

### 5.2 Update These Values

**Required:**

```bash
# Generate a secure secret key
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Update DATABASE_URL with your actual connection string
# Option A (Managed Database):
DATABASE_URL=postgresql://doadmin:PASS@db-postgresql-nyc1-12345.db.ondigitalocean.com:25060/defaultdb?sslmode=require

# Option B (Local):
DATABASE_URL=postgresql://social_user:YOUR_PASSWORD@localhost:5432/social_styles
```

**Optional (Email):**

```bash
# If using Gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password  # NOT your regular password

MAIL_DEFAULT_SENDER=noreply@teamsocialstyles.com
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

### 5.3 Verify .env File

```bash
# Test database connection
cd /var/www/socialstyles
source .env
echo $DATABASE_URL  # Should show your connection string (without password visible)
```

---

## Step 6: Initialize Database (3 minutes)

```bash
cd /var/www/socialstyles

# Run database migrations
sudo -u socialstyles venv/bin/flask db upgrade

# Initialize assessment questions
sudo -u socialstyles venv/bin/python initialize_assessment.py
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade...
✅ Assessment initialized successfully
```

---

## Step 7: Start Application (2 minutes)

```bash
# Start the service
systemctl start socialstyles

# Check status
systemctl status socialstyles
```

**Expected output:**
```
● socialstyles.service - Social Styles Assessment Application
     Loaded: loaded
     Active: active (running)
```

### Test Locally

```bash
# Test health endpoint
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.4.0",
  "timestamp": "2025-01-04T..."
}
```

---

## Step 8: Update Cloudflare DNS (5 minutes)

### 8.1 Get New Server IP

```bash
# On the server
curl ifconfig.me
```

Example output: `157.230.45.123`

### 8.2 Update DNS Records

1. Go to Cloudflare Dashboard: https://dash.cloudflare.com
2. Select your domain: `teamsocialstyles.com`
3. Click **DNS** in the left menu
4. Find the existing A records for:
   - `teamsocialstyles.com` (or `@`)
   - `www.teamsocialstyles.com`

5. **Edit each record:**
   - Click **Edit**
   - Update **IPv4 address** to your new server IP
   - Ensure **Proxy status** is **Proxied** (orange cloud)
   - Click **Save**

### 8.3 Wait for DNS Propagation

- Typically: 2-5 minutes
- Max: 15 minutes

### 8.4 Test

```bash
# From your local machine
curl https://teamsocialstyles.com/health
```

---

## Step 9: Set Up GitHub Actions (10 minutes)

### 9.1 Add GitHub Deploy Key to Server

```bash
# On your LOCAL machine
cat ~/.ssh/github_deploy_key.pub

# Copy the output, then on the SERVER:
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 9.2 Test SSH Connection

```bash
# On your LOCAL machine
ssh -i ~/.ssh/github_deploy_key root@NEW_SERVER_IP "echo 'Connection successful!'"
```

### 9.3 Add GitHub Secrets

1. Go to: https://github.com/gmoorevt/socialstyles/settings/secrets/actions

2. Click **New repository secret**

3. Add these secrets:

| Secret Name | Value | Where to Get It |
|-------------|-------|-----------------|
| `PROD_SSH_HOST` | `157.230.45.123` | Your new server IP |
| `PROD_SSH_USER` | `root` | Default user |
| `PROD_SSH_KEY` | `<private key>` | `cat ~/.ssh/github_deploy_key` |

To get the private key:
```bash
# On your LOCAL machine
cat ~/.ssh/github_deploy_key
```

Copy the entire output including:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

### 9.4 Create GitHub Production Environment

1. Go to: https://github.com/gmoorevt/socialstyles/settings/environments
2. Click **New environment**
3. Name: `production`
4. Click **Configure environment**
5. Check **Required reviewers** (add yourself)
6. Click **Save protection rules**

---

## Step 10: Test Deployment (5 minutes)

### 10.1 Make a Test Change

```bash
# On your LOCAL machine
cd /Users/gmoore/dev/social-styles

git checkout main
git pull

# Make small change
echo "<!-- Server migrated $(date) -->" >> README.md

git add README.md
git commit -m "Test deployment to new server"
git push origin main
```

### 10.2 Watch GitHub Actions

1. Go to: https://github.com/gmoorevt/socialstyles/actions
2. You'll see **"Deploy to Production"** workflow running
3. It will:
   - ✅ Run tests
   - ⏸️ Wait for your approval

### 10.3 Approve Deployment

1. Click on the running workflow
2. Click **Review deployments**
3. Check **production**
4. Click **Approve and deploy**

### 10.4 Monitor Deployment

Watch the logs as it:
- ✅ Backs up database
- ✅ Pulls latest code
- ✅ Installs dependencies
- ✅ Runs migrations
- ✅ Restarts application
- ✅ Runs health check
- ✅ Creates version tag

### 10.5 Verify Production

```bash
# From your local machine
curl https://teamsocialstyles.com/health
```

Visit: https://teamsocialstyles.com

You should see your application running!

---

## Step 11: Clean Up Old Server (Optional)

### 11.1 Verify New Server

- ✅ Application works at https://teamsocialstyles.com
- ✅ Can log in and create assessments
- ✅ Database working
- ✅ GitHub Actions deployment works

### 11.2 Backup Old Server Data (if needed)

If you have important data on the old server:

```bash
# SSH to OLD server (134.209.128.212)
ssh root@134.209.128.212

# Backup database
cd /var/www/socialstyles
source .env
pg_dump $DATABASE_URL | gzip > ~/backup-old-server.sql.gz

# Download to local machine
# On your LOCAL machine:
scp root@134.209.128.212:~/backup-old-server.sql.gz ~/Downloads/
```

### 11.3 Destroy Old Droplet

1. Go to DigitalOcean dashboard
2. Find droplet with IP `134.209.128.212`
3. Click **Destroy**
4. Confirm destruction

**Savings:** Whatever the old droplet cost per month

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
journalctl -u socialstyles -n 50

# Common issues:
# 1. Database connection - check DATABASE_URL in .env
# 2. Port already in use - restart server
# 3. Import errors - reinstall dependencies
```

### Can't Access via Domain

```bash
# Check if Nginx is running
systemctl status nginx

# Check if application is running
systemctl status socialstyles

# Test locally first
curl http://localhost:8000/health

# If local works but domain doesn't:
# - Wait for DNS propagation (up to 15 min)
# - Check Cloudflare is set to "Proxied"
# - Check Cloudflare SSL/TLS mode is "Flexible"
```

### GitHub Actions Deployment Fails

```bash
# Test SSH connection manually
ssh -i ~/.ssh/github_deploy_key root@NEW_SERVER_IP

# Check GitHub Secrets are correct:
# - PROD_SSH_HOST matches new server IP
# - PROD_SSH_KEY is the complete private key
# - PROD_SSH_USER is "root"
```

---

## Summary Checklist

- [ ] Created DigitalOcean droplet
- [ ] Ran setup script on server
- [ ] Configured database (managed or local)
- [ ] Updated .env file with credentials
- [ ] Ran database migrations
- [ ] Started application service
- [ ] Updated Cloudflare DNS
- [ ] Added GitHub deploy key to server
- [ ] Configured GitHub Secrets
- [ ] Created GitHub production environment
- [ ] Tested deployment via GitHub Actions
- [ ] Verified application works at domain
- [ ] (Optional) Destroyed old server

---

## Next Steps

✅ **Server is ready!** You now have:
- Fresh production server
- Automated CI/CD deployments
- Zero-downtime updates
- Health monitoring
- Automatic backups

**Future deployments:**
```bash
git checkout main
git merge staging  # or make changes directly
git push origin main

# Approve in GitHub Actions
# Done! 🎉
```

---

## Server Details

| Item | Value |
|------|-------|
| **Server IP** | [Your new IP] |
| **Domain** | https://teamsocialstyles.com |
| **SSH** | `ssh root@[IP]` |
| **App Directory** | `/var/www/socialstyles` |
| **Service** | `systemctl status socialstyles` |
| **Logs** | `journalctl -u socialstyles -f` |
| **Health Check** | `curl http://localhost:8000/health` |

---

**Setup complete!** 🎉 Your new production server is ready for CI/CD deployments.
