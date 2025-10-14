"""Test Reddit authentication"""
import praw
import config

print("Testing Reddit API authentication...")
print(f"Username: {config.REDDIT_USERNAME}")
print(f"Client ID: {config.REDDIT_CLIENT_ID[:5]}..." if config.REDDIT_CLIENT_ID else "NOT SET")
print(f"Client Secret: {config.REDDIT_CLIENT_SECRET[:5]}..." if config.REDDIT_CLIENT_SECRET else "NOT SET")
print(f"User Agent: {config.REDDIT_USER_AGENT}")
print()

try:
    reddit = praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        username=config.REDDIT_USERNAME,
        password=config.REDDIT_PASSWORD,
        user_agent=config.REDDIT_USER_AGENT
    )

    print("Attempting to authenticate...")
    me = reddit.user.me()
    print(f"✅ SUCCESS! Logged in as: u/{me}")
    print(f"Display name: {me.name}")
    print(f"Link karma: {me.link_karma}")
    print(f"Comment karma: {me.comment_karma}")

except Exception as e:
    print(f"❌ AUTHENTICATION FAILED!")
    print(f"Error: {e}")
    print()
    print("Common issues:")
    print("1. Wrong username - Make sure it's the actual username (like 'StrikingRing1967'), not display name")
    print("2. Wrong password - Try logging in manually at reddit.com first")
    print("3. Wrong CLIENT_ID or CLIENT_SECRET from reddit.com/prefs/apps")
    print("4. Account has 2FA enabled (bot accounts should disable 2FA)")
    print("5. Account is too new (try posting a comment first to verify it)")
