# Troubleshooting Reddit Authentication

You're getting `invalid_grant` error. Here's how to fix it:

## Step 1: Verify You Can Log In Manually

1. Go to reddit.com
2. Log out completely
3. Try logging in with:
   - Username: `StrikingRing1967`
   - Password: (the one you set)
4. **If this fails**, you need to reset your password or the account has issues

## Step 2: Check if Account Has 2FA Enabled

1. While logged in, go to: https://www.reddit.com/settings/privacy
2. Scroll to "TWO-FACTOR AUTHENTICATION"
3. **If it's enabled, DISABLE it** (bot accounts can't use 2FA with password auth)

## Step 3: Verify Your Reddit App Credentials

1. Go to https://www.reddit.com/prefs/apps (must be logged in as the bot account)
2. Find your app (or create a new one if needed)
3. Make sure app type is **"script"**
4. Copy the credentials:
   - **client_id**: The random string under "personal use script"
   - **client_secret**: The "secret" value
5. Update your `.env` file with these exact values

## Step 4: Try a Different Approach - Create Fresh Account

Sometimes it's easier to start fresh:

### Create New Bot Account (Old Reddit Way)

1. **Log out of all Reddit accounts**
2. Go to **old.reddit.com** (not reddit.com!)
3. Click "Sign Up" in top right
4. Fill out:
   - **Username**: `CFBBeltBot` (try to get this if available)
   - **Password**: Create a strong one
   - **Email**: Optional but recommended
5. Complete signup
6. **Important**: Make a test comment somewhere to verify account works
7. Create Reddit app for this new account at old.reddit.com/prefs/apps

### Then Update Your .env
```
REDDIT_USERNAME=CFBBeltBot  # or whatever you got
REDDIT_PASSWORD=your_new_password
```

## Step 5: Reddit App Must Be "Script" Type

When creating the Reddit app:
- **Name**: CFBBeltBot
- **Type**: Select **"script"** (NOT "web app" or "installed app")
- **Description**: Tracks CFB Linear Championship Belt
- **About URL**: https://rutgersstartedthis.com
- **Redirect URI**: http://localhost:8080 (required but not used)

## Step 6: Account Age/Karma Issues

Brand new accounts might be restricted. If account is less than 1 hour old:
- Wait a bit
- Make a test comment on r/test
- Verify email address if you provided one

## Step 7: Still Not Working?

If none of this works, the most reliable solution is:

**Use old.reddit.com to create a completely fresh account** with a traditional signup (not Google/Apple). This gives you:
- Clean username you choose
- Password that definitely works
- No SSO complications

Then:
1. Create Reddit app for that account
2. Update .env with new credentials
3. Test with `python test_auth.py`

## Common Mistakes

❌ Using display name instead of username
✅ Username is the auto-generated one like "StrikingRing1967"

❌ Having 2FA enabled
✅ Bot accounts must have 2FA disabled

❌ Wrong app type (web app instead of script)
✅ Must be "script" type

❌ Password has special characters that need escaping
✅ Try a simple password first to test

## Next Step

Once `python test_auth.py` shows "SUCCESS!", you're ready to run the bot!
