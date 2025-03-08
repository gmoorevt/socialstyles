# Social Styles Assessment - Digital Ocean Startup Guide

This guide explains how to ensure your Social Styles Assessment application starts automatically on your Digital Ocean server after a reboot.

## Automatic Startup with Systemd

We've created several scripts to help you manage your application on Digital Ocean:

1. **socialstyles.service**: A systemd service file that defines how your application should run.
2. **setup_systemd_service.sh**: A script to install and enable the systemd service on your Digital Ocean server.
3. **check_and_restart_service.sh**: A script to check if your service is running and restart it if needed.
4. **setup_cron_job.sh**: A script to set up a cron job that automatically checks and restarts your service every 5 minutes.

### Step 1: Set Up the Systemd Service

Run the setup script to install and enable the systemd service:

```bash
./setup_systemd_service.sh
```

This script will:
- Copy the service file to your Digital Ocean server
- Install it as a systemd service
- Stop the current supervisor-managed instance
- Enable the systemd service to start on boot
- Start the service

### Step 2: Set Up the Cron Job (Optional but Recommended)

For extra reliability, set up a cron job to check and restart your service if it goes down:

```bash
./setup_cron_job.sh
```

This script will:
- Create a check script on your server
- Set up a cron job to run the check script every 5 minutes
- The check script will automatically restart your service if it's down

### Step 3: Verify the Setup

You can verify that your service is running correctly:

```bash
./check_and_restart_service.sh
```

This will show you the current status of your service.

## After a Reboot

After your Digital Ocean server reboots, the systemd service will automatically start your application. You don't need to do anything manually.

If you want to check that everything is running correctly after a reboot, you can run:

```bash
./check_and_restart_service.sh
```

## Manual Commands

If you need to manually manage your service on the server, you can use these commands:

- **Check status**: `systemctl status socialstyles.service`
- **Start service**: `systemctl start socialstyles.service`
- **Stop service**: `systemctl stop socialstyles.service`
- **Restart service**: `systemctl restart socialstyles.service`
- **View logs**: `journalctl -u socialstyles.service`

These commands need to be run on your Digital Ocean server, so you would SSH in first:

```bash
ssh root@67.205.184.178
```

## Troubleshooting

If the application doesn't start automatically after a reboot:

1. SSH into your server:
   ```bash
   ssh root@67.205.184.178
   ```

2. Check the service status:
   ```bash
   systemctl status socialstyles.service
   ```

3. If the service is not running, try to start it:
   ```bash
   systemctl start socialstyles.service
   ```

4. Check the logs for any errors:
   ```bash
   journalctl -u socialstyles.service -n 50
   ```

5. Make sure the service is enabled to start on boot:
   ```bash
   systemctl is-enabled socialstyles.service
   ```
   If it's not enabled, run:
   ```bash
   systemctl enable socialstyles.service
   ```

## Service Configuration

The systemd service is configured with the following settings:

```ini
[Unit]
Description=Social Styles Assessment Application
After=network.target

[Service]
User=socialstyles
Group=www-data
WorkingDirectory=/var/www/socialstyles
Environment="PATH=/var/www/socialstyles/venv/bin"
ExecStart=/var/www/socialstyles/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
Restart=always
RestartSec=5
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
```

This configuration ensures that:
- The service starts after the network is available
- The service runs as the socialstyles user
- The service automatically restarts if it crashes
- The service starts automatically on boot 

## Deployment Script

You can use the deployment script to deploy your application to Digital Ocean:

```bash
./deploy_to_digitalocean.sh
```

This script will:
- Deploy your application to Digital Ocean
- Set up the necessary environment and configurations
- Ensure your application starts automatically on boot 