#!/usr/bin/env python3
"""
Film Voting Telegram Bot
A bot for managing film voting with SQLite database storage.

Setup Instructions:
1. Get your bot token from @BotFather on Telegram
2. Set your bot token as an environment variable: export BOT_TOKEN="your_token_here"
3. Install dependencies: pip install -r requirements.txt
4. Run the bot: python bot.py

Admin Setup:
- The bot uses Telegram's built-in admin system
- Any user who is an admin in the chat can add films
- No manual configuration needed
"""

import os
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
)

# Configuration
# Try to load from .env file first
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue with environment variables

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Please set BOT_TOKEN environment variable or create a .env file")

# Admin check will be done dynamically using Telegram's admin system

# Database setup
DATABASE_NAME = "film_voting.db"

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class FilmVotingBot:
    def __init__(self):
        self.db_name = DATABASE_NAME
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create films table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS films (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Create rounds table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create votes table with round support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                film_id INTEGER NOT NULL,
                round_id INTEGER NOT NULL,
                seen BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, round_id),
                FOREIGN KEY (film_id) REFERENCES films (id),
                FOREIGN KEY (round_id) REFERENCES rounds (id)
            )
        ''')
        
        # Create default active round if none exists
        cursor.execute('SELECT COUNT(*) FROM rounds WHERE is_active = 1')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO rounds (name, is_active) VALUES (?, ?)', ('Round 1', 1))
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def add_film(self, title: str) -> bool:
        """Add a film to the database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO films (title) VALUES (?)", (title,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Film '{title}' already exists")
            return False
        except Exception as e:
            logger.error(f"Error adding film: {e}")
            return False
    
    def get_all_films(self) -> List[Tuple[int, str]]:
        """Get all films from the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM films ORDER BY title")
        films = cursor.fetchall()
        conn.close()
        return films
    
    def get_film_by_id(self, film_id: int) -> str:
        """Get film title by ID."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM films WHERE id = ?", (film_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_active_round(self) -> int:
        """Get the currently active round ID."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM rounds WHERE is_active = 1")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def has_user_voted_in_round(self, user_id: int, round_id: int) -> bool:
        """Check if user has already voted in the current round."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM votes WHERE user_id = ? AND round_id = ?",
            (user_id, round_id)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def add_vote(self, user_id: int, film_id: int, seen: bool) -> bool:
        """Add a vote for a film in the current round."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Get active round
            round_id = self.get_active_round()
            if not round_id:
                logger.error("No active round found")
                return False
            
            cursor.execute(
                "INSERT INTO votes (user_id, film_id, round_id, seen) VALUES (?, ?, ?, ?)",
                (user_id, film_id, round_id, seen)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"User {user_id} has already voted in round {round_id}")
            return False
        except Exception as e:
            logger.error(f"Error adding vote: {e}")
            return False
    
    def get_results(self, round_id: int = None) -> List[Tuple[str, float]]:
        """Get all films with their scores for a specific round, sorted by highest first."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if round_id is None:
            round_id = self.get_active_round()
        
        cursor.execute('''
            SELECT f.title, 
                   COALESCE(SUM(
                       CASE 
                           WHEN v.seen = 1 THEN 0.5
                           WHEN v.seen = 0 THEN 1.0
                           ELSE 0
                       END
                   ), 0) as total_score
            FROM films f
            LEFT JOIN votes v ON f.id = v.film_id AND v.round_id = ?
            GROUP BY f.id, f.title
            ORDER BY total_score DESC
        ''', (round_id,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_winner(self, round_id: int = None) -> Tuple[str, float]:
        """Get the top-scoring film for a specific round."""
        results = self.get_results(round_id)
        return results[0] if results else (None, 0.0)
    
    def create_new_round(self, name: str) -> bool:
        """Create a new round and deactivate the current one."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Deactivate current active round
            cursor.execute("UPDATE rounds SET is_active = 0 WHERE is_active = 1")
            
            # Create new round
            cursor.execute("INSERT INTO rounds (name, is_active) VALUES (?, 1)", (name,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating new round: {e}")
            return False
    
    def get_round_info(self, round_id: int = None) -> Tuple[int, str]:
        """Get round information."""
        if round_id is None:
            round_id = self.get_active_round()
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM rounds WHERE id = ?", (round_id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else (None, None)


# Global bot instance
bot = FilmVotingBot()


async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the current chat."""
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ('administrator', 'creator')
    except Exception as e:
        logger.warning(f"Error checking admin status: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_text = """
🎬 Welcome to the Film Voting Bot! 🎬

I help you vote on films and track which ones are most popular.

Available commands:
• /vote - Vote for ONE film in the current round
• /results - View all films and their scores for current round
• /winner - See the top-scoring film for current round
• /addfilm <title> - Add a new film (Admin only)
• /newround <name> - Create a new voting round (Admin only)

Get started by typing /vote to see available films!
    """
    
    await update.message.reply_text(welcome_text.strip())


async def add_film(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a film to the database (Admin only)."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Sorry, only admins can add films.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a film title: /addfilm <film name>")
        return
    
    film_title = " ".join(context.args)
    
    if bot.add_film(film_title):
        await update.message.reply_text(f"✅ Film '{film_title}' added successfully!")
    else:
        await update.message.reply_text(f"❌ Film '{film_title}' already exists or could not be added.")


async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all films with voting buttons for the current round."""
    films = bot.get_all_films()
    
    if not films:
        await update.message.reply_text("📝 No films available. Ask an admin to add some films!")
        return
    
    # Get current round info
    round_id, round_name = bot.get_round_info()
    user_id = update.effective_user.id
    
    # Check if user has already voted in this round
    has_voted_in_round = bot.has_user_voted_in_round(user_id, round_id)
    
    if has_voted_in_round:
        # User already voted in this round
        await update.message.reply_text(
            f"✅ You have already voted in {round_name}!\n\n"
            f"Use /results to see current standings or wait for the next round."
        )
        return
    
    keyboard = []
    for film_id, title in films:
        # Show voting buttons for each film
        keyboard.append([
            InlineKeyboardButton("👁️ Seen", callback_data=f"vote_{film_id}_1"),
            InlineKeyboardButton("❌ Not Seen", callback_data=f"vote_{film_id}_0")
        ])
        keyboard.append([
            InlineKeyboardButton(f"📽️ {title}", callback_data=f"info_{film_id}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🎬 Vote for {round_name}!\n\n"
        f"Choose ONE film to vote on. Tap 'Seen' or 'Not Seen':",
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks for voting."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("vote_"):
        # Handle voting
        parts = data.split("_")
        film_id = int(parts[1])
        seen = bool(int(parts[2]))
        
        if bot.add_vote(user_id, film_id, seen):
            film_title = bot.get_film_by_id(film_id)
            round_id, round_name = bot.get_round_info()
            status = "Seen" if seen else "Not Seen"
            
            # Send confirmation via private message
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Vote Confirmation for {round_name}!\n\n"
                         f"🎬 Film: {film_title}\n"
                         f"👁️ Status: {status}\n\n"
                         f"Your vote has been recorded successfully!"
                )
                
                # Update the group message to show vote was recorded
                await query.edit_message_text(
                    f"✅ Vote recorded for {round_name}!\n\n"
                    f"📱 Check your private messages for confirmation.\n\n"
                    f"Use /results to see current standings."
                )
            except Exception as e:
                # If private message fails, show confirmation in group
                logger.warning(f"Could not send private message to user {user_id}: {e}")
                await query.edit_message_text(
                    f"✅ Vote recorded for {round_name}!\n\n"
                    f"🎬 Film: {film_title}\n"
                    f"👁️ Status: {status}\n\n"
                    f"Use /results to see current standings."
                )
        else:
            await query.edit_message_text(
                f"❌ You have already voted in this round!\n\n"
                f"Use /results to see current standings."
            )
    
    elif data.startswith("info_"):
        # Show film info
        film_id = int(data.split("_")[1])
        film_title = bot.get_film_by_id(film_id)
        await query.edit_message_text(
            f"📽️ {film_title}\n\n"
            f"Tap 'Seen' or 'Not Seen' to vote!"
        )


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all films with their scores for the current round."""
    round_id, round_name = bot.get_round_info()
    results = bot.get_results(round_id)
    
    if not results:
        await update.message.reply_text("📝 No films available. Ask an admin to add some films!")
        return
    
    message = f"🏆 Film Voting Results - {round_name} 🏆\n\n"
    
    for i, (title, score) in enumerate(results, 1):
        trophy = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
        message += f"{trophy} {title}: {score:.1f} points\n"
    
    message += f"\n💡 Scoring: Seen = 0.5 points, Not Seen = 1.0 points"
    
    await update.message.reply_text(message)


async def winner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the top-scoring film for the current round."""
    round_id, round_name = bot.get_round_info()
    winner_title, winner_score = bot.get_winner(round_id)
    
    if not winner_title:
        await update.message.reply_text("📝 No films available. Ask an admin to add some films!")
        return
    
    message = f"🏆 WINNER - {round_name} 🏆\n\n"
    message += f"👑 {winner_title}\n"
    message += f"📊 Score: {winner_score:.1f} points\n\n"
    message += f"🎉 Congratulations to the winning film!"
    
    await update.message.reply_text(message)


async def new_round(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new voting round (Admin only)."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Sorry, only admins can create new rounds.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a round name: /newround <round name>")
        return
    
    round_name = " ".join(context.args)
    
    if bot.create_new_round(round_name):
        await update.message.reply_text(f"✅ New round '{round_name}' created successfully!\n\nUsers can now vote again with /vote")
    else:
        await update.message.reply_text(f"❌ Could not create new round '{round_name}'.")


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addfilm", add_film))
    application.add_handler(CommandHandler("vote", vote))
    application.add_handler(CommandHandler("results", results))
    application.add_handler(CommandHandler("winner", winner))
    application.add_handler(CommandHandler("newround", new_round))
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("Starting Film Voting Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
