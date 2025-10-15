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

    def generate_on_this_day(self) -> dict:
        """Generate 'On This Day' historical post (Saturdays)"""
        now = datetime.now()
        games = self.fetcher.get_games_on_this_day(now.month, now.day)

        if not games:
            return None

        # Pick the most recent/interesting game
        featured_game = games[0]  # Most recent

        title = f"📅 On This Day in Belt History - {now.strftime('%B %d')}"

        body = f"# {featured_game['year']}: {featured_game['winner_name']} defeated {featured_game['loser_name']}\n\n"

        if featured_game['winner_score'] != 'N/A' and featured_game['loser_score'] != 'N/A':
            body += f"**Final Score:** {featured_game['winner_score']}-{featured_game['loser_score']}\n\n"

        years_ago = now.year - featured_game['year']
        body += f"**{years_ago} years ago**, {featured_game['winner_name']} "

        # Determine if they won or defended the belt
        # (Would need more context to know if this was a belt change or defense)
        body += f"won the CFB Linear Championship Belt!\n\n"

        # Show other games on this date if any
        if len(games) > 1:
            body += "---\n\n"
            body += f"**Other belt games on {now.strftime('%B %d')}:**\n\n"
            for game in games[1:4]:  # Show up to 3 more
                body += f"• **{game['year']}**: {game['winner_name']} beat {game['loser_name']}"
                if game['winner_score'] != 'N/A':
                    body += f" {game['winner_score']}-{game['loser_score']}"
                body += "\n\n"

        body += f"📊 [Full Belt History]({config.WEBSITE_URL})\n\n"
        body += "🏆 Rutgers started this in 1869. We're still tracking it!"

        return {"title": title, "body": body}

    def generate_longest_reign_alert(self, current_rank: int) -> dict:
        """Generate post when current reign enters top 10"""
        champion_id, reign_start, defenses = self.fetcher.get_current_champion()
        if not champion_id:
            return None

        champion_name = self.fetcher.get_school_name(champion_id)
        reign_days = (datetime.now() - reign_start).days if reign_start else 0

        ordinal_rank = self._ordinal(current_rank)

        title = f"🚨 HISTORIC REIGN ALERT! 🚨 {champion_name} reaches #{current_rank} all-time"

        body = f"# {champion_name}'s reign is now the {ordinal_rank} longest in belt history!\n\n"
        body += f"**Current Reign:** {reign_days:,} days\n\n"
        body += f"**Defenses:** {defenses}\n\n"
        body += f"**Started:** {reign_start.strftime('%B %d, %Y')}\n\n"

        # Get top 10 for context
        top_reigns = self.fetcher.get_longest_reigns(10)

        body += "---\n\n"
        body += "**Top 10 Longest Reigns:**\n\n"

        for i, reign in enumerate(top_reigns, 1):
            is_current = reign.get('current', False)
            marker = "**👑 " if is_current else ""
            end_marker = "**" if is_current else ""

            body += f"{i}. {marker}{reign['champion_name']}: {reign['days']:,} days{end_marker}"
            if is_current:
                body += " (CURRENT)"
            else:
                body += f" ({reign['start_date'].year})"
            body += "\n\n"

        # Next milestone
        if current_rank > 1:
            next_reign = top_reigns[current_rank - 2]
            days_to_next = next_reign['days'] - reign_days
            body += f"**Next Milestone:** {days_to_next} more days to reach #{current_rank - 1}\n\n"

        next_game = self.fetcher.get_next_belt_game()
        if next_game:
            body += f"**Next Game:** {next_game['date'].strftime('%B %d')} vs {next_game['opponent_name']}\n\n"

        body += f"📊 [Live Tracker]({config.WEBSITE_URL})\n\n"
        body += f"🏆 Can {champion_name} keep it going?"

        return {"title": title, "body": body}

    def generate_belt_chase_update(self) -> dict:
        """Generate weekly belt chase update (Sundays)"""
        champion_id, reign_start, defenses = self.fetcher.get_current_champion()
        if not champion_id:
            return None

        champion_name = self.fetcher.get_school_name(champion_id)
        week_num = self._get_week_number()

        # Compute all teams that can win the belt this season
        chase_teams = self.fetcher.compute_belt_chase_teams()

        title = f"🎯 Belt Chase Update - Week {week_num}"

        body = f"# Who Can Win the Belt This Season?\n\n"
        body += f"Current Champion: {champion_name} ({defenses} defenses)\n\n"

        if not chase_teams:
            body += f"No upcoming games scheduled. {champion_name} holds the belt for now!\n\n"
        else:
            body += f"{len(chase_teams)} teams can still win the belt this season!\n\n"
            body += "---\n\n"

            # Group teams by how many games away they are
            teams_by_distance = {}
            for team_info in chase_teams:
                distance = team_info['games_away']
                if distance not in teams_by_distance:
                    teams_by_distance[distance] = []
                teams_by_distance[distance].append(team_info)

            # Show direct path (1 game away)
            if 1 in teams_by_distance:
                body += "## Direct Path (1 game away)\n\n"
                body += "These teams play the champion next and can win the belt directly:\n\n"
                for team in sorted(teams_by_distance[1], key=lambda x: x['earliest_week']):
                    body += f"- {team['name']} (Week {team['earliest_week']})\n"
                body += "\n"

            # Show 2 games away
            if 2 in teams_by_distance:
                body += "## Two Steps Away (2 games)\n\n"
                body += "These teams need someone to beat the champion first, then beat that team:\n\n"
                for team in sorted(teams_by_distance[2], key=lambda x: x['earliest_week'])[:10]:
                    body += f"- {team['name']} (earliest: Week {team['earliest_week']})\n"
                if len(teams_by_distance[2]) > 10:
                    body += f"\n...and {len(teams_by_distance[2]) - 10} more teams\n"
                body += "\n"

            # Show 3+ games away summary
            distant_teams = sum(len(teams) for dist, teams in teams_by_distance.items() if dist >= 3)
            if distant_teams > 0:
                body += f"## Long Shot Teams (3+ games away)\n\n"
                body += f"{distant_teams} teams could theoretically win the belt, but need multiple games to break their way.\n\n"

        body += "---\n\n"
        body += f"Current Reign: {(datetime.now() - reign_start).days if reign_start else 0} days\n\n"
        body += f"Last Belt Change: {reign_start.strftime('%B %d, %Y') if reign_start else 'Unknown'}\n\n"
        body += f"Full Chase Tree: {config.WEBSITE_URL}\n\n"
        body += "Rutgers started this in 1869. Who's next?"

        return {"title": title, "body": body}


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
