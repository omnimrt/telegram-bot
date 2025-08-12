# Film Voting Telegram Bot 🎬

A Python Telegram bot for managing film voting with SQLite database storage. Users can vote on films they've seen or haven't seen, and the bot tracks scores to determine the most popular films.

## Features

- **Film Management**: Add films to the database (admin only)
- **Voting System**: Vote on films with "Seen" or "Not Seen" options
- **Duplicate Prevention**: Users can only vote once per film
- **Scoring System**: 
  - Seen films: 0.5 points
  - Not seen films: 1.0 points
- **Results Display**: View all films sorted by score
- **Winner Announcement**: See the top-scoring film with trophy emoji
- **Inline Buttons**: Easy voting with tap-to-vote buttons

## Commands

- `/start` - Welcome message and command list
- `/addfilm <film name>` - Add a new film (Admin only)
- `/vote` - Show all films with voting buttons
- `/results` - Display all films sorted by score
- `/winner` - Show the top-scoring film

## Setup Instructions

### 1. Get Your Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy your bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Admin Setup

The bot uses Telegram's built-in admin system. Any user who is an admin in the chat can add films using the `/addfilm` command. No additional configuration is needed!

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Bot

Set your bot token as an environment variable:

```bash
export BOT_TOKEN="your_bot_token_here"
```

### 5. Test the Bot (Optional)

```bash
python3 test_database.py
```

This will test all database functionality without requiring a bot token.

### 6. Run the Bot

```bash
python bot.py
```

## Quick Start

For the fastest setup, use the provided script:

```bash
# Make the script executable (first time only)
chmod +x quick_start.sh

# Run the quick start script
./quick_start.sh

# Or run the bot directly after setup
./quick_start.sh run
```

This script will:
1. Check Python installation
2. Install dependencies
3. Run the setup wizard (if needed)
4. Test the bot functionality
5. Start the bot (if requested)

## Database Schema

The bot uses SQLite with two tables:

### Films Table
- `id` (INTEGER PRIMARY KEY)
- `title` (TEXT UNIQUE)

### Votes Table
- `id` (INTEGER PRIMARY KEY)
- `user_id` (INTEGER)
- `film_id` (INTEGER)
- `seen` (BOOLEAN)
- `created_at` (TIMESTAMP)

## Scoring Rules

- **Seen films**: 0.5 points per vote
- **Not seen films**: 1.0 points per vote
- **Duplicate prevention**: Users can only vote once per film
- **Results**: Films are sorted by total score (highest first)

## Usage Examples

### Adding Films (Admin)
```
/addfilm The Shawshank Redemption
/addfilm Pulp Fiction
/addfilm The Dark Knight
```

### Voting
1. Type `/vote` to see all available films
2. Tap "👁️ Seen" or "❌ Not Seen" for each film
3. The bot will confirm your vote and update the interface

### Viewing Results
- `/results` - See all films with scores
- `/winner` - See the top-scoring film

## File Structure

```
telegram-bot/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── setup.py           # Interactive setup script
├── test_database.py   # Database functionality test
├── test_admin_simple.py # Admin function test
├── quick_start.sh     # Quick setup and run script
├── README.md          # This file
└── film_voting.db     # SQLite database (created automatically)
```

## Requirements

- Python 3.7+
- python-telegram-bot 20.7+
- SQLite3 (included with Python)

## Troubleshooting

### Bot Token Issues
- Make sure your bot token is correct
- Ensure the environment variable is set: `echo $BOT_TOKEN`

### Admin Privileges
- The bot uses Telegram's built-in admin system
- Any user who is an admin in the chat can add films
- No manual configuration needed

### Database Issues
- The database is created automatically on first run
- If you need to reset, delete `film_voting.db` and restart the bot

### Voting Issues
- Each user can only vote once per film
- Use `/vote` to see your voting status for each film

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.
