"""Main CFB Belt Bot"""
import praw
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import re

import config
from commands import CommandHandler
from data_fetcher import BeltDataFetcher
from scheduled_posts import ScheduledPosts

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
        self.fetcher = BeltDataFetcher()
        self.scheduled_posts = ScheduledPosts()

        # Track recent replies and posts to avoid spam
        self.recent_replies = {}
        self.commented_threads = {}  # Track which game/postgame threads we've commented on
        self.last_post_time = {}  # Track when we last made each type of post

        # Scheduler for automated posts
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone('US/Eastern'))

    def start(self):
        """Start the bot"""
        print(f"Starting bot on r/{config.TARGET_SUBREDDIT}...")

        if config.DRY_RUN:
            print("DRY RUN MODE - No posts will be made")

        # Schedule automated posts and comments
        self._schedule_posts()

        # Start the scheduler
        self.scheduler.start()

        print("Bot is running! Press Ctrl+C to stop.")
        print("Monitoring for mentions, commands, and game threads...")

        try:
            # Main loop - monitor for mentions and commands
            while True:
                self._check_mentions()
                self._check_commands()
                self._check_game_threads()
                self._check_postgame_threads()
                time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\nStopping bot...")
            self.scheduler.shutdown()
            print("Bot stopped.")

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

    def _schedule_posts(self):
        """Schedule automated posts"""
        # "On This Day" posts - Saturday at 10 AM ET
        self.scheduler.add_job(
            self._post_on_this_day,
            CronTrigger(day_of_week='sat', hour=10, minute=0),
            id='on_this_day'
        )

        # Belt Chase Updates - Sunday at 10 AM ET
        self.scheduler.add_job(
            self._post_belt_chase,
            CronTrigger(day_of_week='sun', hour=10, minute=0),
            id='belt_chase'
        )

        # Check for longest reign milestones - daily at 9 AM ET
        self.scheduler.add_job(
            self._check_longest_reign,
            CronTrigger(hour=9, minute=0),
            id='longest_reign_check'
        )

        print("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            print(f"  - {job.id}")

    def _check_game_threads(self):
        """Check for new game threads involving the belt holder"""
        try:
            champion_id, _, _ = self.fetcher.get_current_champion()
            if not champion_id:
                return

            champion_name = self.fetcher.get_school_name(champion_id)

            # Look for new submissions by CFB_Referee
            for submission in self.subreddit.new(limit=10):
                # Skip if not by CFB_Referee
                if submission.author.name != 'CFB_Referee':
                    continue

                # Check if it's a game thread
                if not submission.title.startswith('[Game Thread]'):
                    continue

                # Skip if we already commented
                if submission.id in self.commented_threads:
                    continue

                # Check if champion is in the game
                if champion_name.lower() not in submission.title.lower():
                    continue

                # This is a belt game thread!
                self._comment_on_game_thread(submission, champion_name)

        except Exception as e:
            print(f"Error checking game threads: {e}")

    def _check_postgame_threads(self):
        """Check for new post-game threads involving the belt holder"""
        try:
            champion_id, _, _ = self.fetcher.get_current_champion()
            if not champion_id:
                return

            champion_name = self.fetcher.get_school_name(champion_id)

            # Look for new submissions by CFB_Referee
            for submission in self.subreddit.new(limit=10):
                # Skip if not by CFB_Referee
                if submission.author.name != 'CFB_Referee':
                    continue

                # Check if it's a postgame thread
                if not submission.title.startswith('[Postgame Thread]'):
                    continue

                # Skip if we already commented
                if submission.id in self.commented_threads:
                    continue

                # Check if champion is in the game
                if champion_name.lower() not in submission.title.lower():
                    continue

                # This is a belt postgame thread!
                self._comment_on_postgame_thread(submission, champion_id, champion_name)

        except Exception as e:
            print(f"Error checking postgame threads: {e}")

    def _comment_on_game_thread(self, submission, champion_name):
        """Post a comment on a game thread where belt is on the line"""
        print(f"Found belt game thread: {submission.title}")

        comment_body = f"🏆 **The Belt is on the line in this game!** 🏆\n\n"
        comment_body += f"**Current holder:** {champion_name}\n\n"
        comment_body += f"[Live belt tracker]({config.WEBSITE_URL})"
        comment_body += config.BOT_SIGNATURE

        if config.DRY_RUN:
            print(f"DRY RUN - Would comment on game thread:\n{comment_body}")
        else:
            try:
                submission.reply(comment_body)
                print(f"Commented on game thread: {submission.id}")
            except Exception as e:
                print(f"Error commenting on game thread: {e}")

        self.commented_threads[submission.id] = time.time()

    def _comment_on_postgame_thread(self, submission, champion_id, champion_name):
        """Post a comment on a postgame thread for a belt game"""
        print(f"Found belt postgame thread: {submission.title}")

        # Parse the title to determine winner
        # Format: [Postgame Thread] Winner Defeats Loser Score-Score
        title = submission.title
        match = re.search(r'\[Postgame Thread\]\s+(.+?)\s+Defeats\s+(.+?)\s+\d', title)

        if not match:
            print(f"Could not parse postgame thread title: {title}")
            return

        winner_name = match.group(1).strip()
        loser_name = match.group(2).strip()

        # Determine if belt changed hands or was defended
        belt_changed = champion_name.lower() in loser_name.lower()

        if belt_changed:
            comment_body = f"🚨 **BELT CHANGED HANDS!** 🚨\n\n"
            comment_body += f"**New Champion:** {winner_name}\n\n"
            comment_body += f"**Previous Champion:** {champion_name}\n\n"
        else:
            comment_body = f"🛡️ **BELT DEFENDED!** 🛡️\n\n"
            comment_body += f"**{champion_name}** successfully defended the belt!\n\n"

        comment_body += f"[Updated belt tracker]({config.WEBSITE_URL})"
        comment_body += config.BOT_SIGNATURE

        if config.DRY_RUN:
            print(f"DRY RUN - Would comment on postgame thread:\n{comment_body}")
        else:
            try:
                submission.reply(comment_body)
                print(f"Commented on postgame thread: {submission.id}")
            except Exception as e:
                print(f"Error commenting on postgame thread: {e}")

        self.commented_threads[submission.id] = time.time()

    def _post_on_this_day(self):
        """Post historical belt moments (Saturdays)"""
        print("Generating 'On This Day' post...")

        post_data = self.scheduled_posts.generate_on_this_day()

        if not post_data:
            print("No belt games on this day in history")
            return

        self._make_post(post_data['title'], post_data['body'], 'on_this_day')

    def _post_belt_chase(self):
        """Post weekly belt chase update (Sundays)"""
        print("Generating Belt Chase Update...")

        post_data = self.scheduled_posts.generate_belt_chase_update()

        if not post_data:
            print("No belt chase data available")
            return

        self._make_post(post_data['title'], post_data['body'], 'belt_chase')

    def _check_longest_reign(self):
        """Check if current reign has entered top 10"""
        print("Checking for longest reign milestones...")

        try:
            champion_id, reign_start, _ = self.fetcher.get_current_champion()
            if not champion_id or not reign_start:
                return

            # Get longest reigns
            longest_reigns = self.fetcher.get_longest_reigns(10)

            # Find current reign in the list
            current_rank = None
            for i, reign in enumerate(longest_reigns, 1):
                if reign.get('current', False):
                    current_rank = i
                    break

            if not current_rank or current_rank > 10:
                # Not in top 10
                return

            # Check if we already posted about this rank
            milestone_key = f"longest_reign_rank_{current_rank}"
            if milestone_key in self.last_post_time:
                # Already posted about this rank
                return

            print(f"Current reign is #{current_rank} all-time!")

            post_data = self.scheduled_posts.generate_longest_reign_alert(current_rank)

            if post_data:
                self._make_post(post_data['title'], post_data['body'], milestone_key)

        except Exception as e:
            print(f"Error checking longest reign: {e}")

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
