"""Scheduled post generators for CFB Belt Bot"""
from datetime import datetime, timedelta
from data_fetcher import BeltDataFetcher
import config

class ScheduledPosts:
    def __init__(self):
        self.fetcher = BeltDataFetcher()

    def generate_weekly_update(self) -> str:
        """Generate Monday weekly belt status update"""
        champion_id, reign_start, defenses = self.fetcher.get_current_champion()

        if not champion_id:
            return None

        champion_name = self.fetcher.get_school_name(champion_id)
        days_held = (datetime.now() - reign_start).days if reign_start else 0
        next_game = self.fetcher.get_next_belt_game()

        # Get week number (approximate based on date)
        week_num = self._get_week_number()

        title = f"📢 CFB Linear Championship Belt Update - Week {week_num}"

        body = f"# 🏆 Current Champion: {champion_name}\n\n"
        body += f"**📅 Held Since:** {reign_start.strftime('%B %d, %Y') if reign_start else 'Unknown'}\n\n"
        body += f"**⏱️ Days Held:** {days_held}\n\n"
        body += f"**🛡️ Defenses This Reign:** {defenses}\n\n"

        if next_game:
            next_date = next_game['date']
            is_home = next_game['home_id'] == champion_id
            vs_at = "vs" if is_home else "at"

            body += f"## ⚔️ Next Belt Game\n\n"
            body += f"**Week {next_game['week']}:** {champion_name} {vs_at} {next_game['opponent_name']}\n\n"
            body += f"**📅 Date:** {next_date.strftime('%A, %B %d')}\n\n"
            body += f"**🏟️ Location:** {next_game['location']}\n\n"

            days_until = (next_date - datetime.now()).days
            if days_until <= 3:
                body += f"**🔥 THE BELT IS ON THE LINE THIS WEEK!**\n\n"

        body += "---\n\n"
        body += "## 📖 What is the Linear Championship Belt?\n\n"
        body += "The belt started with the first college football game ever played (Rutgers beat Princeton, 6-4, on November 6, 1869). "
        body += "It passes from winner to winner, like a boxing championship belt. Only the team that beats the current holder can win it!\n\n"

        body += f"📊 [Full Tracker & History]({config.WEBSITE_URL})\n\n"
        body += "🏆 Rutgers started this. We're just tracking it."

        return {"title": title, "body": body}

    def generate_game_day_alert(self) -> str:
        """Generate alert when belt is on the line today"""
        champion_id, _, defenses = self.fetcher.get_current_champion()
        next_game = self.fetcher.get_next_belt_game()

        if not next_game:
            return None

        # Check if game is today
        today = datetime.now().date()
        game_date = next_game['date'].date()

        if game_date != today:
            return None

        champion_name = self.fetcher.get_school_name(champion_id)
        opponent = next_game['opponent_name']
        is_home = next_game['home_id'] == champion_id
        vs_at = "vs" if is_home else "at"

        title = f"⚔️ THE BELT IS ON THE LINE TODAY! ⚔️"

        body = f"# 🏆 {champion_name} {vs_at} {opponent}\n\n"
        body += f"**Current Champion:** {champion_name} ({defenses} defenses this reign)\n\n"
        body += f"**Location:** {next_game['location']}\n\n"
        body += f"**Week:** {next_game['week']}\n\n"

        body += "---\n\n"
        body += f"Will {champion_name} defend the belt, or will {opponent} become the new champion?\n\n"

        body += f"📊 [Live Tracker]({config.WEBSITE_URL})\n\n"
        body += "🏆 Rutgers started this in 1869. Who's got it next?"

        return {"title": title, "body": body}

    def generate_belt_change_announcement(self, new_champion_id: str, old_champion_id: str, score: str = None) -> dict:
        """Generate post when belt changes hands"""
        new_champ_name = self.fetcher.get_school_name(new_champion_id)
        old_champ_name = self.fetcher.get_school_name(old_champion_id)

        # Get old champion's reign info (before the loss)
        old_history = self.fetcher.get_team_belt_history(old_champion_id)

        title = f"🚨 BELT CHANGE! 🚨 {new_champ_name} defeats {old_champ_name}"
        if score:
            title += f" {score}"

        body = f"# 🏆 NEW CHAMPION: {new_champ_name}!\n\n"

        if score:
            body += f"**Final Score:** {new_champ_name} defeats {old_champ_name} {score}\n\n"

        body += f"**Previous Champion:** {old_champ_name}\n\n"
        body += f"**Reign Duration:** {old_history.get('best_reign_days', 0)} days\n\n"
        body += f"**Defenses:** {old_history.get('total_defenses', 0)}\n\n"

        body += "---\n\n"

        # Get new champion's history
        new_history = self.fetcher.get_team_belt_history(new_champion_id)
        ordinal = self._ordinal(new_history['total_reigns'])

        body += f"This is {new_champ_name}'s **{ordinal} time** holding the belt!\n\n"

        if new_history['total_reigns'] > 1:
            body += f"**All-Time:** {new_history['total_days']:,} days held, {new_history['total_defenses']} defenses\n\n"

        body += f"📊 [Updated Tracker]({config.WEBSITE_URL})\n\n"
        body += "🏆 The belt lives on!"

        return {"title": title, "body": body}

    def generate_belt_defense_announcement(self, champion_id: str, challenger_id: str, score: str = None, defenses: int = 0) -> dict:
        """Generate post when champion successfully defends"""
        champion_name = self.fetcher.get_school_name(champion_id)
        challenger_name = self.fetcher.get_school_name(challenger_id)

        title = f"🛡️ BELT DEFENDED! 🛡️ {champion_name} defeats {challenger_name}"
        if score:
            title += f" {score}"

        body = f"# 🏆 {champion_name} retains the belt!\n\n"

        if score:
            body += f"**Final Score:** {champion_name} defeats {challenger_name} {score}\n\n"

        body += f"**Defenses This Reign:** {defenses}\n\n"

        # Get next game
        next_game = self.fetcher.get_next_belt_game()
        if next_game:
            body += f"**Next Defense:** Week {next_game['week']} vs {next_game['opponent_name']} on {next_game['date'].strftime('%B %d')}\n\n"

        body += f"📊 [Updated Tracker]({config.WEBSITE_URL})\n\n"
        body += f"🏆 {champion_name} keeps the belt!"

        return {"title": title, "body": body}

    def _get_week_number(self) -> int:
        """Approximate current week of CFB season"""
        now = datetime.now()
        # Assume season starts around late August/early September
        # This is approximate - could be enhanced with actual week data
        season_start = datetime(now.year, 8, 25)
        if now < season_start:
            # Off-season or previous season
            season_start = datetime(now.year - 1, 8, 25)

        weeks = (now - season_start).days // 7
        return max(0, min(weeks, 15))  # Cap at week 15

    def _ordinal(self, n: int) -> str:
        """Convert number to ordinal string (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"


if __name__ == '__main__':
    # Test scheduled posts
    posts = ScheduledPosts()

    print("=== Weekly Update ===")
    weekly = posts.generate_weekly_update()
    if weekly:
        print(f"Title: {weekly['title']}")
        print(f"\nBody:\n{weekly['body']}")

    print("\n\n=== Game Day Alert ===")
    gameday = posts.generate_game_day_alert()
    if gameday:
        print(f"Title: {gameday['title']}")
        print(f"\nBody:\n{gameday['body']}")
    else:
        print("No game today")
