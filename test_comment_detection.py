"""Test if bot can see the comment on r/test"""
import praw
import config

print("Testing comment detection...")
print(f"Looking at r/{config.TARGET_SUBREDDIT}")

reddit = praw.Reddit(
    client_id=config.REDDIT_CLIENT_ID,
    client_secret=config.REDDIT_CLIENT_SECRET,
    username=config.REDDIT_USERNAME,
    password=config.REDDIT_PASSWORD,
    user_agent=config.REDDIT_USER_AGENT
)

subreddit = reddit.subreddit(config.TARGET_SUBREDDIT)

print("\nChecking last 10 comments for command triggers...")
for comment in subreddit.comments(limit=10):
    body = comment.body.lower()
    has_trigger = any(trigger in body for trigger in config.COMMAND_TRIGGERS)

    print(f"\n- u/{comment.author}: {comment.body[:50]}...")
    print(f"  Has trigger: {has_trigger}")

    if has_trigger:
        print(f"  *** FOUND COMMAND! ***")
        print(f"  Comment ID: {comment.id}")
        print(f"  Full text: {comment.body}")
