"""Command handlers for CFB Belt Bot"""
from datetime import datetime
from typing import Optional
from data_fetcher import BeltDataFetcher
import config

class CommandHandler:
    def __init__(self):
        self.fetcher = BeltDataFetcher()

    def handle_command(self, command_text: str) -> str:
        """Route command to appropriate handler"""
        parts = command_text.lower().strip().split()

        if len(parts) == 0:
            return self.get_current_status()

        # Determine if a trigger was used
        trigger_used = parts[0] in config.COMMAND_TRIGGERS
        subcommand = parts[0] if not trigger_used else (parts[1] if len(parts) > 1 else '')

        if subcommand == 'help':
            return self.get_help()
        elif subcommand == 'next':
            return self.get_next_game()
        elif subcommand == 'stats':
            return self.get_stats()
        elif subcommand == 'history':
            # Extract team name based on whether trigger was used
            if trigger_used:
                team_name = ' '.join(parts[2:]) if len(parts) > 2 else None
            else:
                team_name = ' '.join(parts[1:]) if len(parts) > 1 else None
            return self.get_team_history(team_name)
        else:
            return self.get_current_status()

    def get_current_status(self) -> str:
        """Get current belt holder status"""
        champion_id, reign_start, defenses = self.fetcher.get_current_champion()

        if not champion_id:
            return "Unable to fetch belt data right now. Try again later!" + config.BOT_SIGNATURE

        champion_name = self.fetcher.get_school_name(champion_id)
        days_held = (datetime.now() - reign_start).days if reign_start else 0

        next_game = self.fetcher.get_next_belt_game()

        response = f"🏆 **CFB Linear Championship Belt Status**\n\n"
        response += f"**Current Champion:** {champion_name}\n\n"
        response += f"**Held Since:** {reign_start.strftime('%B %d, %Y') if reign_start else 'Unknown'} ({days_held} days)\n\n"
        response += f"**Defenses This Reign:** {defenses}\n\n"

        if next_game:
            next_date = next_game['date']
            is_home = next_game['home_id'] == champion_id
            vs_at = "vs" if is_home else "at"

            response += f"**Next Game:** Week {next_game['week']} - "
            response += f"{next_date.strftime('%B %d')} {vs_at} {next_game['opponent_name']}\n\n"
        else:
            response += f"**Next Game:** Schedule TBD\n\n"

        response += f"[View full tracker]({config.WEBSITE_URL})"
        response += config.BOT_SIGNATURE

        return response

    def get_help(self) -> str:
        """Show available commands"""
        response = "🏆 **CFB Belt Bot Commands**\n\n"
        response += "**Available Commands:**\n\n"
        response += "• `!beltbot` - Current belt status\n\n"
        response += "• `!beltbot next` - Next belt game\n\n"
        response += "• `!beltbot stats` - Overall belt statistics\n\n"
        response += "• `!beltbot history [team]` - Team's belt history\n\n"
        response += "• `!beltbot help` - This help message\n\n"
        response += "---\n\n"
        response += "**Need Help?**\n\n"
        response += f"• Full Tracker: {config.WEBSITE_URL}\n\n"
        response += "• Report bugs or data issues: [GitHub Issues](https://github.com/raypratt/cfb-beltbot/issues)\n\n"
        response += "• Source code: [GitHub](https://github.com/raypratt/cfb-beltbot)"
        response += config.BOT_SIGNATURE

        return response

    def get_next_game(self) -> str:
        """Get next belt game info"""
        champion_id, _, defenses = self.fetcher.get_current_champion()

        if not champion_id:
            return "Unable to fetch belt data right now. Try again later!" + config.BOT_SIGNATURE

        champion_name = self.fetcher.get_school_name(champion_id)
        next_game = self.fetcher.get_next_belt_game()

        if not next_game:
            return f"🏆 **Next Belt Game**\n\n{champion_name} holds the belt, but no upcoming games are scheduled yet." + config.BOT_SIGNATURE

        next_date = next_game['date']
        is_home = next_game['home_id'] == champion_id
        vs_at = "vs" if is_home else "at"

        response = f"🏆 **Next Belt Game**\n\n"
        response += f"**{champion_name}** ({defenses} defenses) {vs_at} **{next_game['opponent_name']}**\n\n"
        response += f"📅 {next_date.strftime('%A, %B %d, %Y')}\n\n"
        response += f"🏟️ {next_game['location']}\n\n"
        response += f"Week {next_game['week']}\n\n"

        days_until = (next_date - datetime.now()).days
        if days_until == 0:
            response += "🔥 **THE BELT IS ON THE LINE TODAY!**\n\n"
        elif days_until == 1:
            response += "⏰ Tomorrow!\n\n"
        elif days_until > 1:
            response += f"⏰ {days_until} days away\n\n"

        response += f"[Live tracker]({config.WEBSITE_URL})"
        response += config.BOT_SIGNATURE

        return response

    def get_stats(self) -> str:
        """Get overall belt statistics"""
        champion_id, reign_start, defenses = self.fetcher.get_current_champion()
        stats = self.fetcher.get_overall_stats()

        if not stats:
            return "Unable to fetch belt statistics right now. Try again later!" + config.BOT_SIGNATURE

        champion_name = self.fetcher.get_school_name(champion_id) if champion_id else "Unknown"
        days_since_start = stats.get('days_since_start', 0)
        total_games = stats.get('total_games', 0)
        total_changes = stats.get('total_changes', 0)

        response = f"📊 **CFB Linear Championship Belt Statistics**\n\n"
        response += f"**Current Champion:** {champion_name} ({defenses} defenses)\n\n"
        response += f"**Belt Established:** November 6, 1869 (Rutgers beat Princeton 6-4)\n\n"
        response += f"**Days Since Start:** {days_since_start:,}\n\n"
        response += f"**Total Belt Games:** {total_games:,}\n\n"
        response += f"**Belt Changes:** {total_changes:,}\n\n"
        response += f"**Defenses:** {total_games - total_changes:,}\n\n"
        response += f"[Full statistics]({config.WEBSITE_URL})"
        response += config.BOT_SIGNATURE

        return response

    def get_team_history(self, team_name: Optional[str]) -> str:
        """Get a team's belt history"""
        if not team_name:
            return "Please specify a team! Example: `!beltbot history Michigan`" + config.BOT_SIGNATURE

        # Find team using the improved search with aliases
        result = self.fetcher.find_team_by_name(team_name)

        if not result:
            return f"Couldn't find a team matching '{team_name}'. Try a different spelling!" + config.BOT_SIGNATURE

        team_id, actual_team_name = result
        history = self.fetcher.get_team_belt_history(team_id)

        if history['total_reigns'] == 0:
            return f"📊 **{actual_team_name} Belt History**\n\n{actual_team_name} has never held the belt... yet! 🏆" + config.BOT_SIGNATURE

        response = f"📊 **{actual_team_name} Belt History**\n\n"
        response += f"**Total Reigns:** {history['total_reigns']}\n\n"
        response += f"**Total Days Held:** {history['total_days']:,}\n\n"
        response += f"**Total Defenses:** {history['total_defenses']}\n\n"
        response += f"**Longest Reign:** {history['best_reign_days']:,} days\n\n"

        if history['last_held']:
            if isinstance(history['last_held'], datetime):
                last_held_str = history['last_held'].strftime('%B %d, %Y')
            else:
                last_held_str = str(history['last_held'])
            response += f"**Last Held:** {last_held_str}\n\n"

        if history['last_won_from']:
            response += f"**Last Won From:** {history['last_won_from']}\n\n"

        if history['last_lost_to']:
            response += f"**Last Lost To:** {history['last_lost_to']}\n\n"

        response += f"[Full history]({config.WEBSITE_URL})"
        response += config.BOT_SIGNATURE

        return response


if __name__ == '__main__':
    # Test commands
    handler = CommandHandler()

    print("=== Test: Current Status ===")
    print(handler.get_current_status())
    print("\n=== Test: Help ===")
    print(handler.get_help())
    print("\n=== Test: Next Game ===")
    print(handler.get_next_game())
    print("\n=== Test: Stats ===")
    print(handler.get_stats())
