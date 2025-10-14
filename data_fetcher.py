"""Fetch and process belt data from Google Sheets"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dateutil import parser as date_parser
import config

class BeltDataFetcher:
    def __init__(self):
        self.schools_cache = {}
        self.games_cache = None
        self.schedule_cache = None
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=15)

    def fetch_schools(self) -> Dict[str, str]:
        """Fetch school ID to name mapping"""
        if self.schools_cache:
            return self.schools_cache

        try:
            response = requests.get(config.SCHOOLS_CSV_URL)
            response.raise_for_status()

            lines = response.text.strip().split('\n')
            for line in lines[1:]:  # Skip header
                parts = line.split(',')
                if len(parts) >= 2:
                    school_id = parts[0].strip()
                    school_name = parts[1].strip()
                    self.schools_cache[school_id] = school_name

            return self.schools_cache
        except Exception as e:
            print(f"Error fetching schools: {e}")
            return {}

    def get_school_name(self, school_id: str) -> str:
        """Get school name from ID"""
        schools = self.fetch_schools()
        return schools.get(school_id, school_id)

    def fetch_games(self, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch all historical games"""
        if not force_refresh and self.games_cache is not None:
            if self.cache_timestamp and datetime.now() - self.cache_timestamp < self.cache_duration:
                return self.games_cache

        try:
            df = pd.read_csv(config.GAMES_CSV_URL)
            # Parse dates manually to handle old dates (before 1677)
            df['date'] = df['date'].apply(lambda x: date_parser.parse(x))
            self.games_cache = df
            self.cache_timestamp = datetime.now()
            return df
        except Exception as e:
            print(f"Error fetching games: {e}")
            return pd.DataFrame()

    def fetch_schedule(self, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch future schedule"""
        if not force_refresh and self.schedule_cache is not None:
            if self.cache_timestamp and datetime.now() - self.cache_timestamp < self.cache_duration:
                return self.schedule_cache

        try:
            df = pd.read_csv(config.SCHEDULE_CSV_URL)
            df['start_date'] = pd.to_datetime(df['start_date'], utc=True).dt.tz_localize(None)
            self.schedule_cache = df
            return df
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return pd.DataFrame()

    def get_current_champion(self) -> Tuple[Optional[str], Optional[datetime], int]:
        """
        Returns: (champion_id, reign_start_date, defenses)
        """
        games = self.fetch_games()
        if games.empty:
            return None, None, 0

        # Get most recent completed game with belt_change data
        belt_games = games[games['belt_change'].notna()].copy()
        if belt_games.empty:
            return None, None, 0

        belt_games = belt_games.sort_values('date', ascending=False)

        # Find current champion (last winner in belt games)
        current_champion = belt_games.iloc[0]['winner_id']

        # Count consecutive wins by current champion (going backwards from most recent)
        wins_in_current_reign = []
        for idx, game in belt_games.iterrows():
            if game['winner_id'] == current_champion:
                wins_in_current_reign.append(game)
            else:
                break

        # First win doesn't count as defense
        defenses = len(wins_in_current_reign) - 1

        # Reign started with the earliest win in this streak
        reign_start = wins_in_current_reign[-1]['date'] if wins_in_current_reign else None

        return current_champion, reign_start, defenses

    def get_next_belt_game(self) -> Optional[Dict]:
        """Get the next scheduled belt game"""
        champion, _, _ = self.get_current_champion()
        if not champion:
            return None

        schedule = self.fetch_schedule()
        if schedule.empty:
            return None

        # Filter to future games involving champion
        now = datetime.now()
        future_games = schedule[
            (schedule['start_date'] > now) &
            (schedule['completed'] == False) &
            ((schedule['home_id'] == champion) | (schedule['away_id'] == champion))
        ]

        if future_games.empty:
            return None

        # Get earliest game
        next_game = future_games.sort_values('start_date').iloc[0]

        opponent = next_game['away_id'] if next_game['home_id'] == champion else next_game['home_id']
        location = next_game['venue'] if pd.notna(next_game['venue']) else 'TBD'

        return {
            'date': next_game['start_date'],
            'opponent_id': opponent,
            'opponent_name': self.get_school_name(opponent),
            'location': location,
            'week': next_game.get('week', 'TBD'),
            'home_id': next_game['home_id'],
            'away_id': next_game['away_id']
        }

    def get_team_belt_history(self, team_id: str) -> Dict:
        """Get a team's complete belt history"""
        games = self.fetch_games()
        if games.empty:
            return {
                'total_reigns': 0,
                'total_days': 0,
                'total_defenses': 0,
                'best_reign_days': 0,
                'last_held': None,
                'last_won_from': None,
                'last_lost_to': None
            }

        belt_games = games[games['belt_change'].notna()].copy()
        team_games = belt_games[
            (belt_games['winner_id'] == team_id) |
            (belt_games['loser_id'] == team_id)
        ]

        total_reigns = 0
        total_days = 0
        total_defenses = 0
        best_reign_days = 0
        last_held = None
        last_won_from = None
        last_lost_to = None

        current_reign_start = None
        current_reign_defenses = 0

        for idx, game in team_games.iterrows():
            if game['winner_id'] == team_id:
                if current_reign_start is None:
                    # New reign starting
                    total_reigns += 1
                    current_reign_start = game['date']
                    current_reign_defenses = 0
                    last_won_from = self.get_school_name(game['loser_id'])
                else:
                    # Defense
                    current_reign_defenses += 1
                    total_defenses += 1
            else:
                # Lost the belt
                if current_reign_start is not None:
                    reign_days = (game['date'] - current_reign_start).days
                    total_days += reign_days
                    best_reign_days = max(best_reign_days, reign_days)
                    last_held = game['date']
                    last_lost_to = self.get_school_name(game['winner_id'])
                    current_reign_start = None
                    current_reign_defenses = 0

        # If team currently holds the belt
        if current_reign_start is not None:
            reign_days = (datetime.now() - current_reign_start).days
            total_days += reign_days
            best_reign_days = max(best_reign_days, reign_days)
            last_held = datetime.now()

        return {
            'total_reigns': total_reigns,
            'total_days': total_days,
            'total_defenses': total_defenses,
            'best_reign_days': best_reign_days,
            'last_held': last_held,
            'last_won_from': last_won_from,
            'last_lost_to': last_lost_to
        }

    def get_overall_stats(self) -> Dict:
        """Get overall belt statistics"""
        games = self.fetch_games()
        if games.empty:
            return {}

        belt_games = games[games['belt_change'].notna()]

        return {
            'total_games': len(belt_games),
            'total_changes': len(belt_games[belt_games['belt_change'] == 'yes']),
            'start_date': belt_games.iloc[0]['date'],
            'days_since_start': (datetime.now() - belt_games.iloc[0]['date']).days
        }


if __name__ == '__main__':
    # Test the data fetcher
    fetcher = BeltDataFetcher()

    print("Current Champion:")
    champion, start, defenses = fetcher.get_current_champion()
    if champion:
        print(f"  {fetcher.get_school_name(champion)}")
        print(f"  Since: {start}")
        print(f"  Defenses: {defenses}")

    print("\nNext Game:")
    next_game = fetcher.get_next_belt_game()
    if next_game:
        print(f"  vs {next_game['opponent_name']}")
        print(f"  {next_game['date']}")
        print(f"  at {next_game['location']}")
