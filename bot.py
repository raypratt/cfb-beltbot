"""Main CFB Belt Bot"""
import praw
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

import config
from commands import CommandHandler
from scheduled_posts import ScheduledPosts
from data_fetcher import BeltDataFetcher

class CFBBeltBot:
    def __init__(self):
        """Initialize the bot"""
        print("Initializing CFB Belt Bot...")

        # Initialize Reddit connection
        self.reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            username=config.REDDIT_USERNAME,
            password=config.REDDIT_PASSWORD,
            user_agent=config.REDDIT_USER_AGENT
        )

        print(f"Logged in as: {self.reddit.user.me()}")

        self.subreddit = self.reddit.subreddit(config.TARGET_SUBREDDIT)
        self.command_handler = CommandHandler()
        self.scheduled_posts = ScheduledPosts()
        self.fetcher = BeltDataFetcher()

        # Track recent replies to avoid spam
        self.recent_replies = {}
        self.last_post_time = {}

        # Scheduler for automated posts
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone('US/Eastern'))

    def start(self):
        """Start the bot"""
        print(f"Starting bot on r/{config.TARGET_SUBREDDIT}...")

        if config.DRY_RUN:
            print("DRY RUN MODE - No posts will be made")

        # Schedule automated posts
        self._schedule_posts()

        # Start the scheduler
        self.scheduler.start()

        print("Bot is running! Press Ctrl+C to stop.")
        print("Monitoring for mentions and commands...")

        try:
            # Main loop - monitor for mentions and commands
            while True:
                self._check_mentions()
                self._check_commands()
                time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\nStopping bot...")
            self.scheduler.shutdown()
            print("Bot stopped.")

    def _schedule_posts(self):
        """Schedule automated posts"""
        # Weekly update every Monday at 10 AM ET
        self.scheduler.add_job(
            self._post_weekly_update,
            CronTrigger(
                day_of_week=config.WEEKLY_UPDATE_DAY,
                hour=config.WEEKLY_UPDATE_HOUR,
                minute=config.WEEKLY_UPDATE_MINUTE
            ),
            id='weekly_update'
        )

        # Check for game day alerts daily at 8 AM ET
        self.scheduler.add_job(
            self._check_game_day,
            CronTrigger(hour=8, minute=0),
            id='game_day_check'
        )

        # Check for game results every hour during season
        self.scheduler.add_job(
            self._check_game_results,
            'interval',
            hours=1,
            id='game_results'
        )

        print("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            print(f"  - {job.id}")

    def _post_weekly_update(self):
        """Post weekly belt status update"""
        print("Generating weekly update...")

        post_data = self.scheduled_posts.generate_weekly_update()

        if not post_data:
            print("No data for weekly update")
            return

        self._make_post(post_data['title'], post_data['body'], 'weekly_update')

    def _check_game_day(self):
        """Check if belt is on the line today and post alert"""
        print("Checking for game day...")

        post_data = self.scheduled_posts.generate_game_day_alert()

        if post_data:
            print("Belt game today! Posting alert...")
            self._make_post(post_data['title'], post_data['body'], 'game_day_alert')
        else:
            print("No belt game today")

    def _check_game_results(self):
        """Check if a belt game has been completed and post results"""
        print("Checking for game results...")
        # TODO: Implement result checking logic
        # This would compare current champion with previous check
        # If changed, post belt change announcement
        pass

    def _check_mentions(self):
        """Check for username mentions"""
        try:
            for mention in self.reddit.inbox.mentions(limit=10):
                if mention.id in self.recent_replies:
                    continue

                # Check if already replied
                mention.refresh()
                for reply in mention.replies:
                    if reply.author == self.reddit.user.me():
                        self.recent_replies[mention.id] = time.time()
                        break
                else:
                    # No reply yet, process it
                    self._handle_mention(mention)

        except Exception as e:
            print(f"Error checking mentions: {e}")

    def _check_commands(self):
        """Check for command triggers in new comments"""
        try:
            for comment in self.subreddit.comments(limit=25):
                # Skip our own comments!
                if comment.author == self.reddit.user.me():
                    continue

                # Check if comment contains command trigger
                if not any(trigger in comment.body.lower() for trigger in config.COMMAND_TRIGGERS):
                    continue

                # Check if we've already replied
                if comment.id in self.recent_replies:
                    continue

                # Check cooldown
                comment_time = datetime.fromtimestamp(comment.created_utc)
                if (datetime.now() - comment_time).total_seconds() > 600:  # Skip comments older than 10 min
                    continue

                # Check if we already replied
                comment.refresh()
                for reply in comment.replies:
                    if reply.author == self.reddit.user.me():
                        self.recent_replies[comment.id] = time.time()
                        break
                else:
                    # No reply yet, process it
                    self._handle_command_comment(comment)

        except Exception as e:
            print(f"Error checking commands: {e}")

    def _handle_mention(self, mention):
        """Handle a username mention"""
        print(f"Handling mention from u/{mention.author}: {mention.body[:50]}...")

        response = self.command_handler.handle_command(mention.body)

        if config.DRY_RUN:
            print(f"DRY RUN - Would reply:\n{response}")
        else:
            try:
                mention.reply(response)
                print(f"Replied to mention {mention.id}")
            except Exception as e:
                print(f"Error replying to mention: {e}")

        self.recent_replies[mention.id] = time.time()

    def _handle_command_comment(self, comment):
        """Handle a comment with command trigger"""
        print(f"Handling command from u/{comment.author}: {comment.body[:50]}...")

        response = self.command_handler.handle_command(comment.body)

        if config.DRY_RUN:
            print(f"DRY RUN - Would reply:\n{response}")
        else:
            try:
                comment.reply(response)
                print(f"Replied to command {comment.id}")
            except Exception as e:
                print(f"Error replying to command: {e}")

        self.recent_replies[comment.id] = time.time()

    def _make_post(self, title: str, body: str, post_type: str):
        """Make a post to the subreddit"""
        # Check rate limiting
        now = time.time()
        if post_type in self.last_post_time:
            time_since_last = now - self.last_post_time[post_type]
            if time_since_last < 3600:  # Don't post same type more than once per hour
                print(f"Rate limited: Last {post_type} was {time_since_last/60:.1f} minutes ago")
                return

        if config.DRY_RUN:
            print(f"DRY RUN - Would post:")
            print(f"Title: {title}")
            print(f"Body:\n{body}")
        else:
            try:
                submission = self.subreddit.submit(title, selftext=body)
                print(f"Posted: {title}")
                print(f"URL: {submission.url}")
                self.last_post_time[post_type] = now
            except Exception as e:
                print(f"Error making post: {e}")

    def _cleanup_old_replies(self):
        """Clean up old entries from recent_replies dict"""
        now = time.time()
        cutoff = now - config.REPLY_COOLDOWN_SECONDS
        self.recent_replies = {k: v for k, v in self.recent_replies.items() if v > cutoff}


def main():
    """Main entry point"""
    # Check if credentials are set
    if not config.REDDIT_CLIENT_ID or not config.REDDIT_CLIENT_SECRET:
        print("Error: Reddit API credentials not set!")
        print("Please create a .env file with your credentials.")
        print("See .env.example for template.")
        return

    bot = CFBBeltBot()
    bot.start()


if __name__ == '__main__':
    main()
