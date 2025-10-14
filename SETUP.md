# CFB Belt Bot - Setup Guide

## Step 1: Create Reddit App

1. Go to https://www.reddit.com/prefs/apps
2. Click "create app" or "create another app"
3. Fill out the form:
   - **name**: CFBBeltBot
   - **type**: Select "script"
   - **description**: Tracks the CFB Linear Championship Belt
   - **about url**: https://rutgersstartedthis.com
   - **redirect uri**: http://localhost:8080 (required but not used)
4. Click "create app"
5. Note your credentials:
   - **client_id**: The string under "personal use script"
   - **client_secret**: The "secret" value

## Step 2: Create Reddit Bot Account

1. Create a new Reddit account for the bot: u/CFBBeltBot
2. Verify the email address
3. Note the username and password

## Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your credentials:
```
REDDIT_CLIENT_ID=your_client_id_from_step1
REDDIT_CLIENT_SECRET=your_secret_from_step1
REDDIT_USERNAME=CFBBeltBot
REDDIT_PASSWORD=your_bot_password
REDDIT_USER_AGENT=CFBBeltBot v1.0 by u/your_actual_username

# Start with test subreddit!
TARGET_SUBREDDIT=test
```

## Step 5: Test the Bot

### Test Data Fetching
```bash
python data_fetcher.py
```

You should see current champion, next game info, etc.

### Test Commands
```bash
python commands.py
```

You should see sample command responses.

### Test Scheduled Posts
```bash
python scheduled_posts.py
```

You should see sample weekly update and game day posts.

### Test Bot (Dry Run)
```bash
# Make sure DRY_RUN=true in .env
python bot.py
```

The bot will run but not actually post anything. Test for a few minutes to make sure no errors.

## Step 6: Test on r/test

1. Change `TARGET_SUBREDDIT=test` in `.env`
2. Set `DRY_RUN=false`
3. Run the bot:
```bash
python bot.py
```

4. Go to r/test and make a comment with `!beltbot`
5. The bot should reply!

## Step 7: Contact r/CFB Moderators

**Before going live on r/CFB**, you MUST get moderator approval!

Send a message to r/CFB modmail with:

```
Subject: Request to run CFBBeltBot - Linear Championship Belt Tracker

Hi r/CFB mods,

I'd like to run a bot on r/CFB called u/CFBBeltBot.

Purpose: Track and announce updates about the CFB Linear Championship Belt
(a mythical championship that has passed from winner to winner since the
first college football game in 1869).

Website: https://rutgersstartedthis.com

What the bot does:
- Posts weekly belt status updates (Mondays, ~10 AM ET)
- Alerts when the belt is on the line (game day posts)
- Announces belt changes/defenses (post-game)
- Responds to user commands (!beltbot for current status)

Frequency:
- 1-2 scheduled posts per week during season
- Responds to user mentions/commands (rate limited)
- All posts are informational, no spam

The bot has been tested on r/test and is working well. I'm happy to adjust
any behavior based on your feedback or requirements.

Source code: [GitHub link if you make it public]

Please let me know if this is okay to run, or if you'd like any changes!

Thanks,
u/[your username]
```

## Step 8: Go Live on r/CFB

Once you get mod approval:

1. Change `TARGET_SUBREDDIT=CFB` in `.env`
2. Run the bot
3. Make an introduction post (see LAUNCH_POST.md for template)

## Step 9: Keep It Running

### Option A: Run Locally
Keep the bot running on your computer. Not recommended for production.

### Option B: Deploy to Cloud

**Heroku** (Free tier available):
```bash
# Install Heroku CLI
# Create Heroku app
heroku create cfb-beltbot

# Set environment variables
heroku config:set REDDIT_CLIENT_ID=xxx
heroku config:set REDDIT_CLIENT_SECRET=xxx
# ... etc for all variables

# Deploy
git push heroku main
```

**Railway.app** (Easier, ~$5/month):
1. Sign up at railway.app
2. Create new project from GitHub
3. Add environment variables in dashboard
4. Deploy!

**DigitalOcean** (~$6/month):
1. Create a droplet
2. SSH in and clone repo
3. Set up systemd service to keep bot running
4. Configure environment variables

## Monitoring

Once running, monitor:
- Bot logs for errors
- Reddit inbox for complaints
- Upvotes/downvotes on posts
- r/CFB mod messages

## Troubleshooting

**Bot not replying to commands:**
- Check bot is running
- Check TARGET_SUBREDDIT is correct
- Check DRY_RUN is false
- Check Reddit API credentials
- Look for errors in console

**Rate limit errors:**
- Reddit has rate limits for new accounts
- Build up karma on bot account first
- Post/comment on other subreddits

**Authentication errors:**
- Double-check client_id and client_secret
- Make sure bot account password is correct
- Verify account email address

## Next Steps

- Add more sophisticated game result detection
- Integration with chaos meter (future)
- User prediction features
- Historical "on this day" posts
- Enhanced statistics

Good luck! 🏆
