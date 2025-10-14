# Reddit Password for Google/Apple Login Users

If you signed up with Google/Apple, you don't have a traditional password. You need to set one for API access.

## Set a Password for Your Bot Account

### Option 1: Set Password (Recommended)
1. Log into your bot account on reddit.com
2. Go to https://www.reddit.com/settings/account
3. Scroll down to "Change Password" section
4. Click "Set Password" or "Change Password"
5. Set a new password (doesn't affect Google login)
6. Save it

Now you can use this password in the `.env` file while still logging in via Google on the website!

### Option 2: Use OAuth2 Flow (More Complex)

If you don't want to set a password, you can use Reddit's OAuth2 flow. This requires code changes:

**Not recommended for now** - just set a password, it's way easier!

## Verification

After setting a password, test it:

1. Open an incognito/private browser window
2. Go to reddit.com
3. Try logging in with:
   - Username: [your auto-generated username]
   - Password: [the password you just set]
4. If it works, you're good!

## Update .env

```env
REDDIT_USERNAME=your-auto-generated-username
REDDIT_PASSWORD=the-password-you-just-set
```

## Alternative: Create a Fresh Bot Account

If you're having trouble, you can create a brand new bot account the old-fashioned way:

1. **Log out of Reddit completely**
2. Go to **old.reddit.com** (important!)
3. Click "Sign Up" in the top right
4. Fill out:
   - Username: `CFBBeltBot` (if available)
   - Password: [create one]
   - Email: [optional but recommended]
5. Verify email if you provided one
6. Done!

This gives you a clean username and password from the start.

## Which Should You Do?

**If you can set a password on your existing account:** Do that! It's quickest.

**If it won't let you set a password:** Create a new account on old.reddit.com with a clean username like "CFBBeltBot"

Either way works fine!

## Summary

You need:
- ✅ Username (the auto-generated one OR a new clean one)
- ✅ Password (set one in account settings OR create new account)
- ✅ Client ID (from Reddit app - Step 1 of SETUP.md)
- ✅ Client Secret (from Reddit app - Step 1 of SETUP.md)
