# CFB Belt Bot - Oracle Cloud Free Tier Deployment Guide

This guide will help you deploy the CFB Belt Bot on Oracle Cloud's Always Free tier, giving you a VM that runs 24/7 at no cost.

## Prerequisites

- GitHub account (for your bot code)
- Credit card (for Oracle verification - won't be charged)
- Reddit API credentials (client ID, secret, username, password)
- Google Sheets CSV URLs for your data

---

## Step 1: Create Oracle Cloud Account

1. Go to https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill out the form:
   - Email address
   - Country
   - Cloud Account Name (choose something memorable)
4. Verify your email
5. Complete account setup:
   - Add credit card (for verification only - won't be charged)
   - Verify your phone number
6. Wait for account approval (usually instant, sometimes takes a few hours)

---

## Step 2: Create an Always Free VM

1. Log into Oracle Cloud Console: https://cloud.oracle.com/
2. Click **"Create a VM Instance"** or navigate to **Compute > Instances**
3. Configure your VM:
   - **Name:** cfb-belt-bot (or any name you like)
   - **Compartment:** Leave as default (root)
   - **Image:**
     - Click "Change Image"
     - Select **Ubuntu 22.04 (Minimal)**
     - Make sure it says "Always Free Eligible"
   - **Shape:**
     - Click "Change Shape"
     - Select **VM.Standard.A1.Flex** (ARM-based - this is free!)
     - Set OCPUs: 2
     - Set Memory: 12 GB
     - (You get 4 OCPUs and 24 GB RAM free total, we're using half)
   - **Networking:**
     - Leave VCN and subnet as default
     - Make sure "Assign a public IPv4 address" is checked
   - **SSH Keys:**
     - Select "Generate a key pair for me"
     - Click "Save Private Key" - SAVE THIS FILE! You'll need it to connect
     - Click "Save Public Key" (optional, but recommended)

4. Click **"Create"**
5. Wait for instance to provision (about 2-3 minutes)
6. Note your **Public IP Address** (you'll see it on the instance details page)

---

## Step 3: Configure Firewall

Oracle Cloud blocks most ports by default. We don't need to open any ports for the bot (it makes outbound connections only), but let's verify:

1. On your instance page, click your **Subnet** name
2. Click **Default Security List**
3. You should see:
   - Ingress (incoming): Port 22 (SSH) allowed
   - Egress (outgoing): All traffic allowed ✓
4. This is perfect for our bot - it can connect out to Reddit, but nothing can connect in

---

## Step 4: Connect to Your VM

### On Windows (using PuTTY):

1. Download PuTTY: https://www.putty.org/
2. Download PuTTYgen: https://www.puttygen.com/
3. Convert your private key:
   - Open PuTTYgen
   - Click "Load" and select your downloaded private key (.key file)
   - Click "Save private key" as a .ppk file
4. Connect with PuTTY:
   - Open PuTTY
   - Host Name: `ubuntu@YOUR_PUBLIC_IP`
   - Port: 22
   - Connection > SSH > Auth > Browse and select your .ppk file
   - Click "Open"

### On Mac/Linux:

```bash
# Move your private key to a safe location
mkdir -p ~/.ssh
mv ~/Downloads/ssh-key-*.key ~/.ssh/oracle-cfb-bot.key

# Set correct permissions
chmod 600 ~/.ssh/oracle-cfb-bot.key

# Connect to your VM
ssh -i ~/.ssh/oracle-cfb-bot.key ubuntu@YOUR_PUBLIC_IP
```

---

## Step 5: Set Up the Server

Once connected to your VM, run these commands:

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and tools
sudo apt install -y python3 python3-pip python3-venv git

# Install system dependencies
sudo apt install -y build-essential libssl-dev libffi-dev

# Create app directory
mkdir -p ~/cfb-belt-bot
cd ~/cfb-belt-bot

# Clone your bot repository
git clone https://github.com/YOUR_USERNAME/cfb-beltbot.git .
# OR if you don't have it on GitHub yet, we'll upload files manually

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install praw python-dotenv pandas apscheduler python-dateutil pytz
```

---

## Step 6: Upload Bot Files (If Not Using Git)

If you haven't pushed to GitHub yet, upload your files:

### On Windows (using WinSCP):
1. Download WinSCP: https://winscp.net/
2. Connect using:
   - Protocol: SFTP
   - Host: YOUR_PUBLIC_IP
   - Username: ubuntu
   - Private key: Your .ppk file
3. Upload all your .py files to `/home/ubuntu/cfb-belt-bot/`

### On Mac/Linux:
```bash
# From your local machine (not the VM)
scp -i ~/.ssh/oracle-cfb-bot.key -r /path/to/cfb-beltbot/* ubuntu@YOUR_PUBLIC_IP:~/cfb-belt-bot/
```

---

## Step 7: Configure Environment Variables

On your VM:

```bash
cd ~/cfb-belt-bot

# Create .env file
nano .env
```

Add your configuration:

```env
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_bot_username
REDDIT_PASSWORD=your_bot_password
REDDIT_USER_AGENT=CFBBeltBot v1.0

# Target subreddit
TARGET_SUBREDDIT=CFB

# Data sources
GAMES_CSV_URL=https://docs.google.com/spreadsheets/d/.../export?format=csv&gid=0
SCHOOLS_CSV_URL=https://docs.google.com/spreadsheets/d/.../export?format=csv&gid=1
SCHEDULE_CSV_URL=https://docs.google.com/spreadsheets/d/.../export?format=csv&gid=2

# Website
WEBSITE_URL=https://rutgersstartedthis.com

# Bot behavior
DRY_RUN=false
```

Save and exit (Ctrl+X, then Y, then Enter)

---

## Step 8: Test the Bot

```bash
# Activate virtual environment
cd ~/cfb-belt-bot
source venv/bin/activate

# Test the bot (dry run mode)
python3 bot.py
```

You should see:
- "Initializing CFB Belt Bot..."
- "Logged in as: [your bot username]"
- "Bot is running! Press Ctrl+C to stop."

Press Ctrl+C to stop after testing.

---

## Step 9: Set Up as System Service (Auto-Start)

Create a systemd service to keep the bot running 24/7:

```bash
# Create service file
sudo nano /etc/systemd/system/cfb-belt-bot.service
```

Add this content:

```ini
[Unit]
Description=CFB Belt Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/cfb-belt-bot
Environment="PATH=/home/ubuntu/cfb-belt-bot/venv/bin"
ExecStart=/home/ubuntu/cfb-belt-bot/venv/bin/python3 /home/ubuntu/cfb-belt-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, Y, Enter)

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable cfb-belt-bot

# Start the service
sudo systemctl start cfb-belt-bot

# Check status
sudo systemctl status cfb-belt-bot
```

You should see "active (running)" in green!

---

## Step 10: Useful Commands

### Check if bot is running:
```bash
sudo systemctl status cfb-belt-bot
```

### View live logs:
```bash
sudo journalctl -u cfb-belt-bot -f
```

### View last 100 log lines:
```bash
sudo journalctl -u cfb-belt-bot -n 100
```

### Restart the bot:
```bash
sudo systemctl restart cfb-belt-bot
```

### Stop the bot:
```bash
sudo systemctl stop cfb-belt-bot
```

### Update bot code:
```bash
cd ~/cfb-belt-bot
git pull  # If using git
sudo systemctl restart cfb-belt-bot
```

---

## Troubleshooting

### Bot won't start:
```bash
# Check logs for errors
sudo journalctl -u cfb-belt-bot -n 50

# Common issues:
# 1. Missing .env file or wrong credentials
# 2. Python package not installed
# 3. Wrong file paths in service file
```

### Bot keeps restarting:
```bash
# Check logs
sudo journalctl -u cfb-belt-bot -n 100

# Look for Python errors
# Usually means:
# - Bad Reddit credentials
# - Can't reach CSV URLs
# - Python dependency missing
```

### Can't connect to VM:
- Check that you're using the correct private key
- Verify the public IP hasn't changed
- Make sure your home IP hasn't been blocked (Oracle sometimes blocks suspicious IPs)

### Bot uses too much memory:
```bash
# Check memory usage
free -h

# If needed, reduce bot's polling frequency
# Edit bot.py and change time.sleep(30) to time.sleep(60)
```

---

## Monitoring

### Set up email alerts (optional):

1. Install mailutils:
```bash
sudo apt install -y mailutils
```

2. Create a monitoring script:
```bash
nano ~/check-bot.sh
```

Add:
```bash
#!/bin/bash
if ! systemctl is-active --quiet cfb-belt-bot; then
    echo "CFB Belt Bot is down!" | mail -s "Bot Alert" your-email@example.com
fi
```

3. Make executable and add to crontab:
```bash
chmod +x ~/check-bot.sh
crontab -e
```

Add:
```
*/5 * * * * /home/ubuntu/check-bot.sh
```

---

## Cost

**Total cost: $0/month**

Oracle's Always Free tier includes:
- 2 AMD-based VMs OR 4 ARM-based VMs (24 GB total RAM)
- 200 GB block storage
- 10 TB outbound data transfer/month
- No credit card charges as long as you stay in Always Free tier

Your bot uses minimal resources, so you'll stay well within the free limits!

---

## Security Best Practices

1. **Keep system updated:**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Don't share your private key** - treat it like a password

3. **Use strong credentials** in your .env file

4. **Enable automatic security updates:**
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

5. **Monitor your bot logs** regularly for errors or suspicious activity

---

## Backup

### Back up your configuration:
```bash
# From your local machine
scp -i ~/.ssh/oracle-cfb-bot.key ubuntu@YOUR_PUBLIC_IP:~/cfb-belt-bot/.env ~/cfb-bot-backup.env
```

### Keep your GitHub repo updated:
```bash
# On the VM
cd ~/cfb-belt-bot
git add .
git commit -m "Update configuration"
git push
```

---

## Getting Help

- **Bot not working?** Check logs: `sudo journalctl -u cfb-belt-bot -f`
- **Oracle Cloud issues?** https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm
- **Bot bugs?** Create an issue: https://github.com/raypratt/cfb-beltbot/issues

---

## You're Done! 🎉

Your CFB Belt Bot is now running 24/7 for free on Oracle Cloud!

The bot will:
- ✅ Auto-start when the VM boots
- ✅ Auto-restart if it crashes
- ✅ Run scheduled posts (Saturdays & Sundays)
- ✅ Respond to commands and mentions
- ✅ Comment on game threads automatically

Enjoy your fully automated belt bot!
