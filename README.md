# Film Voting Telegram Bot 🎬

A Python Telegram bot for managing film voting with SQLite database storage. Users can vote on films they've seen or haven't seen, and the bot tracks scores to determine the most popular films.

## Features

- **Clean Poll Interface**: Movies displayed as clear, visually separated poll options
- **DM-Only Voting**: All voting interactions take place in private messages
- **Round-Based Voting**: Each user can vote for ONE film per round
- **Vote Counts**: Real-time vote counts shown in confirmations
- **Film Management**: Add and delete films from the database (admin only)
- **Scoring System**: 
  - Seen films: 0.5 points
  - Unseen films: 1.0 points
- **Results Display**: Clean, formatted results with separators and emojis
- **Winner Announcement**: See the top-scoring film with trophy emoji
- **Round Management**: Admins can create new voting rounds
- **Intuitive UI**: Proper spacing, separators, and visual hierarchy

## Commands

- `/start` - Welcome message and command list
- `/vote` - Vote for ONE film in the current round (sent to DM)
- `/results` - Display all films sorted by score for current round
- `/winner` - Show the top-scoring film for current round
- `/listfilms` - List all available films in the database

**Admin Commands:**
- `/addfilm <film name>` - Add a new film
- `/deletefilm <film name>` - Delete a film from the database
- `/newround <name>` - Create a new voting round

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

The bot uses SQLite with three tables:

### Films Table
- `id` (INTEGER PRIMARY KEY)
- `title` (TEXT UNIQUE)

### Rounds Table
- `id` (INTEGER PRIMARY KEY)
- `name` (TEXT)
- `is_active` (BOOLEAN)
- `created_at` (TIMESTAMP)

### Votes Table
- `id` (INTEGER PRIMARY KEY)
- `user_id` (INTEGER)
- `film_id` (INTEGER)
- `round_id` (INTEGER)
- `seen` (BOOLEAN)
- `created_at` (TIMESTAMP)

## Scoring Rules

- **Seen films**: 0.5 points per vote
- **Not seen films**: 1.0 points per vote
- **Round-based voting**: Users can only vote once per round
- **Results**: Films are sorted by total score for current round (highest first)

## Usage Examples

### Adding Films (Admin)
```
/addfilm The Shawshank Redemption
/addfilm Pulp Fiction
/addfilm The Dark Knight
```

### Complete Voting Flow
```
Admin: /addfilm The Shawshank Redemption
Admin: /newround "Movie Night 2024"
User: /vote
Bot: [In group] "📱 Poll sent to your private messages! Check your DM to vote for Movie Night 2024."
Bot: [In DM] "🎬 Movie Night 2024 - Movie Voting Poll 🎬

Choose ONE movie to vote on:

1. 🎭 The Shawshank Redemption
━━━━━━━━━━━━━━━━━━━━
2. 🎭 Pulp Fiction
━━━━━━━━━━━━━━━━━━━━
3. 🎭 The Dark Knight

💡 You can only vote for ONE movie per round

[Inline buttons: "👁️ Seen" | "❌ Unseen" for each movie]"

User: [Taps "👁️ Seen" for The Shawshank Redemption]
Bot: [In DM] "✅ Vote Confirmation - Movie Night 2024 ✅

🎬 Movie: The Shawshank Redemption
👁️ Your Vote: Seen

📊 Current Vote Counts:
   👁️ Seen: 1 votes
   ❌ Unseen: 0 votes
   📈 Total: 1 votes

🎉 Your vote has been recorded successfully!"
```

### Voting Process
1. Type `/vote` in the group chat
2. Check your private messages (DM) for the poll
3. Choose ONE movie and tap "👁️ Seen" or "❌ Unseen"
4. Get confirmation with current vote counts
5. You can only vote once per round

### Film Management
- `/addfilm <title>` - Add new films to the database
- `/deletefilm <title>` - Remove films from the database
- `/listfilms` - View all available films

### Round Management
- `/newround <name>` - Create a new voting round (Admin only)
- Users can vote again when a new round is created

### Viewing Results
- `/results` - See all films with scores for current round
- `/winner` - See the top-scoring film for current round

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
- Each user can only vote once per round
- Vote confirmations are sent via private message
- If private message fails, confirmation will be shown in the group
- Use `/vote` to see available films for the current round

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.
