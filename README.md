# CFB Belt Bot 🏆

A Reddit bot for r/CFB that tracks and announces the CFB Linear Championship Belt

**Website:** [rutgersstartedthis.com](https://rutgersstartedthis.com)
**Reddit:** u/CFBBeltBot

## What It Does

- 📅 Posts weekly belt status updates every Monday
- ⚔️ Alerts when the belt is on the line
- 🚨 Announces belt changes and defenses
- 💬 Responds to user commands
- 📊 Provides belt statistics and history

## Commands

- `!beltbot` - Get current belt status
- `!beltbot history [team]` - Get a team's belt history
- `!beltbot next` - When is the next belt game
- `!beltbot stats` - Overall belt statistics
- `!beltbot help` - Show all commands

## Setup

### Prerequisites
- Python 3.9+
- Reddit account (for the bot)
- Reddit API credentials

### Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file with your credentials:
```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=CFBBeltBot
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=CFBBeltBot v1.0 by u/your_username
```

4. Run the bot:
```bash
python bot.py
```

## Development

### Project Structure
```
cfb-beltbot/
├── bot.py              # Main bot entry point
├── commands.py         # Command handlers
├── scheduled_posts.py  # Automated posting logic
├── data_fetcher.py     # Fetch data from Google Sheets
├── utils.py            # Helper functions
├── config.py           # Configuration
├── requirements.txt
├── .env               # Not committed - add your credentials
└── README.md
```

### Testing
```bash
python -m pytest tests/
```

## Deployment

Can be deployed to:
- Heroku (with scheduler addon)
- Railway.app
- DigitalOcean
- AWS Lambda

## Contributing

Issues and pull requests welcome!

## License

MIT

---

🏆 Rutgers started this. We're just tracking it.
