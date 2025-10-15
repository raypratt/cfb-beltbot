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

        # Team name aliases for common alternate names
        self.team_aliases = {
            'usc': 'USC',
            'southern cal': 'USC',
            'southern california': 'USC',
            'ole miss': 'Ole Miss',
            'mississippi': 'Ole Miss',
            'miami': 'Miami',
            'miami fl': 'Miami',
            'the u': 'Miami',
            'tcu': 'TCU',
            'texas christian': 'TCU',
            'smu': 'SMU',
            'southern methodist': 'SMU',
            'byu': 'BYU',
            'ucf': 'UCF',
            'central florida': 'UCF',
            'lsu': 'LSU',
            'pitt': 'Pitt',
            'pittsburgh': 'Pitt',
            'boston college': 'Boston College',
            'bc': 'Boston College',
            'nc state': 'NC State',
            'north carolina state': 'NC State',
            'va tech': 'Virginia Tech',
            'vt': 'Virginia Tech',
            'virginia polytechnic institute': 'Virginia Tech',
        }

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

    def get_school_name(self, school_id) -> str:
        """Get school name from ID"""
        schools = self.fetch_schools()
        # Convert to string if it's numeric (handles pandas int/float types)
        if school_id is None:
            return "Unknown"
        school_id_str = str(int(school_id)) if isinstance(school_id, (int, float)) or hasattr(school_id, 'item') else str(school_id)
        return schools.get(school_id_str, school_id_str)

    def find_team_by_name(self, team_name: str) -> Optional[Tuple[str, str]]:
        """
        Find team ID and official name by searching for the team name.
        Returns (team_id, official_name) or None if not found.
        Handles aliases and fuzzy matching.
        """
        if not team_name:
            return None

        schools = self.fetch_schools()
        team_name_lower = team_name.lower().strip()

        # First, check aliases
        if team_name_lower in self.team_aliases:
            canonical_name = self.team_aliases[team_name_lower]
            # Find the school with this canonical name
            for school_id, school_name in schools.items():
                if school_name.lower() == canonical_name.lower():
                    return (school_id, school_name)

        # Exact match
        for school_id, school_name in schools.items():
            if school_name.lower() == team_name_lower:
                return (school_id, school_name)

        # Partial match
        for school_id, school_name in schools.items():
            if team_name_lower in school_name.lower():
                return (school_id, school_name)

        return None

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

        # Get most recent completed game with belt_change data (where belt changed hands)
        belt_games = games[games['belt_change'].notna()].copy()
        if belt_games.empty:
            return None, None, 0

        belt_games = belt_games.sort_values('date', ascending=False)

        # Find current champion (winner of most recent belt change game)
        current_champion = belt_games.iloc[0]['winner_id']
        reign_start = belt_games.iloc[0]['date']

        # Now count all wins by current champion since they won the belt
        # This includes both belt change games and regular wins
        all_games = games.sort_values('date', ascending=True)

        # Get all games after the reign started, but only completed games (in the past)
        now = datetime.now()
        games_since_reign_start = all_games[
            (all_games['date'] >= reign_start) &
            (all_games['date'] <= now)
        ]

        # Count wins by the champion (excluding the initial win that started the reign)
        defenses = 0
        for idx, game in games_since_reign_start.iterrows():
            if game['winner_id'] == current_champion:
                if game['date'] > reign_start:  # Don't count the initial win
                    defenses += 1
            elif game['loser_id'] == current_champion:
                # Champion lost - reign is over, but this shouldn't happen if data is correct
                break

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

        # Convert IDs to strings for school lookup
        home_id = str(int(next_game['home_id'])) if pd.notna(next_game['home_id']) else None
        away_id = str(int(next_game['away_id'])) if pd.notna(next_game['away_id']) else None
        champion_str = str(int(champion)) if pd.notna(champion) else None

        opponent = away_id if home_id == champion_str else home_id
        location = next_game['venue'] if pd.notna(next_game['venue']) else 'TBD'

        return {
            'date': next_game['start_date'],
            'opponent_id': opponent,
            'opponent_name': self.get_school_name(opponent),
            'location': location,
            'week': next_game.get('week', 'TBD'),
            'home_id': home_id,
            'away_id': away_id,
            'home_name': self.get_school_name(home_id),
            'away_name': self.get_school_name(away_id)
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

        # Convert team_id to int for comparison with pandas data
        team_id_int = int(team_id)

        # Trace through all games chronologically to find this team's belt history
        all_games_sorted = games.sort_values('date')

        total_reigns = 0
        total_days = 0
        total_defenses = 0
        best_reign_days = 0
        last_held = None
        last_won_from = None
        last_lost_to = None

        current_champion = None
        current_reign_start = None

        for idx, game in all_games_sorted.iterrows():
            # Check if this is a belt change game
            if pd.notna(game['belt_change']):
                winner_id = game['winner_id']
                loser_id = game['loser_id']

                # If team won the belt
                if winner_id == team_id_int:
                    total_reigns += 1
                    current_champion = team_id_int
                    current_reign_start = game['date']
                    last_won_from = self.get_school_name(loser_id)

                # If team lost the belt
                elif loser_id == team_id_int and current_champion == team_id_int:
                    reign_days = (game['date'] - current_reign_start).days
                    total_days += reign_days
                    best_reign_days = max(best_reign_days, reign_days)
                    last_held = game['date']
                    last_lost_to = self.get_school_name(winner_id)
                    current_champion = winner_id
                    current_reign_start = None

                # Belt changed to someone else
                else:
                    current_champion = winner_id

            # Check for defensive wins
            elif current_champion == team_id_int:
                if game['winner_id'] == team_id_int:
                    # Team defended the belt
                    total_defenses += 1

        # If team currently holds the belt
        if current_champion == team_id_int and current_reign_start is not None:
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

        # Games where belt changed hands
        belt_change_games = games[games['belt_change'].notna()]
        total_belt_changes = len(belt_change_games)

        # Now trace through ALL games chronologically to count belt games and defenses
        all_games_sorted = games.sort_values('date')

        current_champion = None
        total_belt_games = 0
        total_defenses = 0
        start_date = None

        for idx, game in all_games_sorted.iterrows():
            # Check if this is a belt change game
            if pd.notna(game['belt_change']):
                # Belt changed hands
                total_belt_games += 1
                current_champion = game['winner_id']

                if start_date is None:
                    start_date = game['date']
            elif current_champion is not None:
                # Check if current champion played
                if game['winner_id'] == current_champion:
                    # Champion won - this is a defense
                    total_belt_games += 1
                    total_defenses += 1
                elif game['loser_id'] == current_champion:
                    # Champion lost - belt should have changed, but might be missing data
                    # This shouldn't happen in clean data
                    pass

        return {
            'total_games': total_belt_games,
            'total_changes': total_belt_changes,
            'total_defenses': total_defenses,
            'start_date': start_date,
            'days_since_start': (datetime.now() - start_date).days if start_date else 0
        }

    def get_games_on_this_day(self, month: int, day: int) -> List[Dict]:
        """Get belt games that happened on this date in history"""
        games = self.fetch_games()
        if games.empty:
            return []

        belt_games = games[games['belt_change'].notna()].copy()

        # Filter to games on this month/day
        matching_games = []
        for idx, game in belt_games.iterrows():
            if game['date'].month == month and game['date'].day == day:
                matching_games.append({
                    'date': game['date'],
                    'year': game['date'].year,
                    'winner_id': game['winner_id'],
                    'winner_name': self.get_school_name(game['winner_id']),
                    'loser_id': game['loser_id'],
                    'loser_name': self.get_school_name(game['loser_id']),
                    'winner_score': game.get('winner_score', 'N/A'),
                    'loser_score': game.get('loser_score', 'N/A')
                })

        return sorted(matching_games, key=lambda x: x['year'], reverse=True)

    def compute_belt_chase_teams(self) -> List[Dict]:
        """
        Compute all teams that can still win the belt this season.
        Returns list of teams with their earliest path to the belt.
        """
        champion_id, _, _ = self.get_current_champion()
        if not champion_id:
            return []

        schedule = self.fetch_schedule()
        if schedule.empty:
            return []

        # Filter to incomplete games only
        now = datetime.now()
        upcoming_games = schedule[
            (schedule['completed'] == False) &
            (schedule['start_date'] > now) &
            (schedule['home_id'].notna()) &
            (schedule['away_id'].notna())
        ].copy()

        if upcoming_games.empty:
            return []

        # Convert IDs to int for comparison
        champion_id_int = int(champion_id)

        # Build a map of team -> their upcoming games
        from collections import defaultdict
        team_games = defaultdict(list)

        for idx, game in upcoming_games.iterrows():
            home_id = int(game['home_id'])
            away_id = int(game['away_id'])
            week = int(game['week']) if pd.notna(game['week']) else 999

            game_info = {
                'week': week,
                'home_id': home_id,
                'away_id': away_id
            }

            team_games[home_id].append(game_info)
            team_games[away_id].append(game_info)

        # Sort each team's games by week
        for team_id in team_games:
            team_games[team_id].sort(key=lambda x: x['week'])

        # BFS to find all possible paths to the belt
        belt_paths = {}
        queue = [{
            'holder': champion_id_int,
            'week': 0,
            'games_deep': 0
        }]

        visited = set()

        while queue:
            state = queue.pop(0)
            holder = state['holder']
            week = state['week']
            games_deep = state['games_deep']

            state_key = f"{holder}-{week}"
            if state_key in visited:
                continue
            visited.add(state_key)

            # Find the next game for the current belt holder
            holder_games = team_games.get(holder, [])
            next_game = None
            for game in holder_games:
                if game['week'] > week:
                    next_game = game
                    break

            if not next_game:
                # No more games for this holder
                continue

            game_week = next_game['week']
            opponent = next_game['away_id'] if next_game['home_id'] == holder else next_game['home_id']

            # Scenario 1: Opponent wins (gets the belt)
            if opponent not in belt_paths:
                belt_paths[opponent] = {
                    'team_id': opponent,
                    'name': self.get_school_name(str(opponent)),
                    'games_away': games_deep + 1,
                    'earliest_week': game_week
                }
            else:
                # Update if this is an earlier path
                if games_deep + 1 < belt_paths[opponent]['games_away']:
                    belt_paths[opponent]['games_away'] = games_deep + 1
                if game_week < belt_paths[opponent]['earliest_week']:
                    belt_paths[opponent]['earliest_week'] = game_week

            # Continue the path if opponent wins
            queue.append({
                'holder': opponent,
                'week': game_week,
                'games_deep': games_deep + 1
            })

            # Scenario 2: Current holder wins (keeps the belt)
            queue.append({
                'holder': holder,
                'week': game_week,
                'games_deep': games_deep
            })

        return list(belt_paths.values())

    def get_longest_reigns(self, limit: int = 10) -> List[Dict]:
        """Get the longest belt reigns in history"""
        games = self.fetch_games()
        if games.empty:
            return []

        belt_games = games[games['belt_change'].notna()].sort_values('date')

        reigns = []
        current_champion = None
        reign_start = None

        for idx, game in belt_games.iterrows():
            winner = game['winner_id']
            game_date = game['date']

            if current_champion != winner:
                # New reign starting
                if current_champion is not None and reign_start is not None:
                    # End previous reign
                    reign_days = (game_date - reign_start).days
                    reigns.append({
                        'champion_id': current_champion,
                        'champion_name': self.get_school_name(current_champion),
                        'start_date': reign_start,
                        'end_date': game_date,
                        'days': reign_days
                    })

                current_champion = winner
                reign_start = game_date

        # Add current reign if ongoing
        if current_champion is not None and reign_start is not None:
            reign_days = (datetime.now() - reign_start).days
            reigns.append({
                'champion_id': current_champion,
                'champion_name': self.get_school_name(current_champion),
                'start_date': reign_start,
                'end_date': None,
                'days': reign_days,
                'current': True
            })

        # Sort by days and return top N
        reigns.sort(key=lambda x: x['days'], reverse=True)
        return reigns[:limit]


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
