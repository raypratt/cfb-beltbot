"""Manually reply to the test comment"""
import praw
import config
from commands import CommandHandler

print("Manual reply test...")

reddit = praw.Reddit(
    client_id=config.REDDIT_CLIENT_ID,
    client_secret=config.REDDIT_CLIENT_SECRET,
    username=config.REDDIT_USERNAME,
    password=config.REDDIT_PASSWORD,
    user_agent=config.REDDIT_USER_AGENT
)

handler = CommandHandler()

# Get the comment
comment = reddit.comment("njd793e")
print(f"Found comment: {comment.body}")
print(f"By: u/{comment.author}")

# Generate response
response = handler.handle_command(comment.body)
print(f"\nGenerated response (first 200 chars):")
print(response[:200])

# Check DRY_RUN
if config.DRY_RUN:
    print("\n*** DRY RUN MODE - Would post this response but not actually posting ***")
else:
    print("\nPosting reply...")
    try:
        comment.reply(response)
        print("SUCCESS! Reply posted!")
    except Exception as e:
        print(f"Error: {e}")
