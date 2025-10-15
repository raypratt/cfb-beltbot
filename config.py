"""Configuration for CFB Belt Bot"""
import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API Credentials
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME', 'CFBBeltBot')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'CFBBeltBot v1.0')

# Target subreddit
TARGET_SUBREDDIT = os.getenv('TARGET_SUBREDDIT', 'test')

# Data sources
GAMES_CSV_URL = os.getenv('GAMES_CSV_URL')
SCHOOLS_CSV_URL = os.getenv('SCHOOLS_CSV_URL')
SCHEDULE_CSV_URL = os.getenv('SCHEDULE_CSV_URL')

# Website
WEBSITE_URL = os.getenv('WEBSITE_URL', 'https://rutgersstartedthis.com')

# Bot behavior
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
MAX_REPLIES_PER_HOUR = 10
MAX_POSTS_PER_HOUR = 1

# Bot signature
BOT_SIGNATURE = (
    "\n\n---\n"
    f"^(🏆 Rutgers started this | "
    f"[Tracker]({WEBSITE_URL}) | "
    f"[Source](https://github.com/raypratt/cfb-beltbot) | "
    f"!beltbot help for commands)\n\n"
    f"^(Found a bug or incorrect data? [Report it here](https://github.com/raypratt/cfb-beltbot/issues))"
)

# Posting schedule (Eastern Time)
WEEKLY_UPDATE_DAY = 0  # Monday
WEEKLY_UPDATE_HOUR = 10  # 10 AM ET
WEEKLY_UPDATE_MINUTE = 0

# Commands
COMMAND_TRIGGERS = ['!beltbot', '!belt']

# Rate limiting
REPLY_COOLDOWN_SECONDS = 60  # Don't reply to same thread within 60 seconds
