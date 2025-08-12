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
        
        # Create votes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                film_id INTEGER NOT NULL,
                seen BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, film_id),
                FOREIGN KEY (film_id) REFERENCES films (id)
            )
        ''')
        
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
    
    def has_user_voted(self, user_id: int, film_id: int) -> bool:
        """Check if user has already voted for a film."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM votes WHERE user_id = ? AND film_id = ?",
            (user_id, film_id)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def add_vote(self, user_id: int, film_id: int, seen: bool) -> bool:
        """Add a vote for a film."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO votes (user_id, film_id, seen) VALUES (?, ?, ?)",
                (user_id, film_id, seen)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"User {user_id} has already voted for film {film_id}")
            return False
        except Exception as e:
            logger.error(f"Error adding vote: {e}")
            return False
    
    def get_results(self) -> List[Tuple[str, float]]:
        """Get all films with their scores, sorted by highest first."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
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
            LEFT JOIN votes v ON f.id = v.film_id
            GROUP BY f.id, f.title
            ORDER BY total_score DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_winner(self) -> Tuple[str, float]:
        """Get the top-scoring film."""
        results = self.get_results()
        return results[0] if results else (None, 0.0)


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
• /vote - Vote on films (Seen/Not Seen)
• /results - View all films and their scores
• /winner - See the top-scoring film
• /addfilm <title> - Add a new film (Admin only)

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
    """Show all films with voting buttons."""
    films = bot.get_all_films()
    
    if not films:
        await update.message.reply_text("📝 No films available. Ask an admin to add some films!")
        return
    
    keyboard = []
    for film_id, title in films:
        # Check if user has already voted
        user_id = update.effective_user.id
        has_voted = bot.has_user_voted(user_id, film_id)
        
        if has_voted:
            # Show voted status
            keyboard.append([
                InlineKeyboardButton(f"✅ {title} (Voted)", callback_data=f"voted_{film_id}")
            ])
        else:
            # Show voting buttons
            keyboard.append([
                InlineKeyboardButton("👁️ Seen", callback_data=f"vote_{film_id}_1"),
                InlineKeyboardButton("❌ Not Seen", callback_data=f"vote_{film_id}_0")
            ])
            keyboard.append([
                InlineKeyboardButton(f"📽️ {title}", callback_data=f"info_{film_id}")
            ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎬 Vote on films! Tap 'Seen' or 'Not Seen' for each film:",
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
            status = "Seen" if seen else "Not Seen"
            await query.edit_message_text(
                f"✅ Vote recorded! You marked '{film_title}' as {status}.\n\n"
                f"Use /vote to vote on more films or /results to see current standings."
            )
        else:
            await query.edit_message_text(
                "❌ You have already voted for this film!\n\n"
                f"Use /vote to vote on other films or /results to see current standings."
            )
    
    elif data.startswith("voted_"):
        # User already voted for this film
        await query.edit_message_text(
            "✅ You have already voted for this film!\n\n"
            f"Use /vote to vote on other films or /results to see current standings."
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
    """Show all films with their scores."""
    results = bot.get_results()
    
    if not results:
        await update.message.reply_text("📝 No films available. Ask an admin to add some films!")
        return
    
    message = "🏆 Film Voting Results 🏆\n\n"
    
    for i, (title, score) in enumerate(results, 1):
        trophy = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
        message += f"{trophy} {title}: {score:.1f} points\n"
    
    message += "\n💡 Scoring: Seen = 0.5 points, Not Seen = 1.0 points"
    
    await update.message.reply_text(message)


async def winner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the top-scoring film."""
    winner_title, winner_score = bot.get_winner()
    
    if not winner_title:
        await update.message.reply_text("📝 No films available. Ask an admin to add some films!")
        return
    
    message = f"🏆 WINNER 🏆\n\n"
    message += f"👑 {winner_title}\n"
    message += f"📊 Score: {winner_score:.1f} points\n\n"
    message += f"🎉 Congratulations to the winning film!"
    
    await update.message.reply_text(message)


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
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("Starting Film Voting Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
