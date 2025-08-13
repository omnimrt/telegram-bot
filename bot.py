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
    
    def get_vote_counts_for_film(self, film_id: int, round_id: int = None) -> Dict[str, int]:
        """Get vote counts for a specific film in a round."""
        if round_id is None:
            round_id = self.get_active_round()
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get seen votes
        cursor.execute(
            "SELECT COUNT(*) FROM votes WHERE film_id = ? AND round_id = ? AND seen = 1",
            (film_id, round_id)
        )
        seen_count = cursor.fetchone()[0]
        
        # Get unseen votes
        cursor.execute(
            "SELECT COUNT(*) FROM votes WHERE film_id = ? AND round_id = ? AND seen = 0",
            (film_id, round_id)
        )
        unseen_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'seen': seen_count,
            'unseen': unseen_count,
            'total': seen_count + unseen_count
        }
    
    def delete_film(self, film_id: int) -> bool:
        """Delete a film and all its associated votes."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # First, get the film title for logging
            cursor.execute("SELECT title FROM films WHERE id = ?", (film_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            film_title = result[0]
            
            # Delete all votes for this film
            cursor.execute("DELETE FROM votes WHERE film_id = ?", (film_id,))
            
            # Delete the film
            cursor.execute("DELETE FROM films WHERE id = ?", (film_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Film '{film_title}' (ID: {film_id}) deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting film {film_id}: {e}")
            return False
    
    def get_film_id_by_title(self, title: str) -> int:
        """Get film ID by title (case-insensitive)."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM films WHERE LOWER(title) = LOWER(?)", (title,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None


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
Hi! I'm the Film Voting Bot 🎬

When you type /vote in the group chat, I'll send you a private message with the list of movies. You can vote only once. After you vote, I'll let the group know you've voted (but not what you picked).

**📱 User Commands:**
• `/vote` - Vote for ONE film in the current round
• `/results` - View all films and their scores for current round
• `/winner` - See the top-scoring film for current round
• `/listfilms` - List all available films

**⚙️ Admin Commands:**
• `/addfilm <title>` - Add a new film
• `/deletefilm <title>` - Delete a film from the database
• `/newround <name>` - Create a new voting round
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
    """Send voting interface directly to DM without group notification."""
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
    
    # Create voting interface
    poll_message = f"🎬 **{round_name} - Movie Voting** 🎬\n\n"
    poll_message += "Mark each movie as Seen or Unseen, then vote for ONE movie:\n\n"
    
    keyboard = []
    for i, (film_id, title) in enumerate(films, 1):
        # Add movie option with number
        poll_message += f"**{i}.** 🎭 {title}\n"
        
        # Add Seen/Unseen buttons for this movie
        keyboard.append([
            InlineKeyboardButton(f"Seen ✅", callback_data=f"mark_{film_id}_1"),
            InlineKeyboardButton(f"Unseen ❌", callback_data=f"mark_{film_id}_0")
        ])
        
        # Add separator between movies (except for last one)
        if i < len(films):
            poll_message += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # Add vote button at the bottom
    keyboard.append([
        InlineKeyboardButton("Vote for this movie 🎯", callback_data="submit_vote")
    ])
    
    poll_message += "\n💡 *Mark each movie's status, then click 'Vote for this movie'*"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send voting interface to user's DM
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=poll_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Store the voting session in context
        if 'voting_sessions' not in context.bot_data:
            context.bot_data['voting_sessions'] = {}
        
        context.bot_data['voting_sessions'][user_id] = {
            'round_id': round_id,
            'marks': {},
            'message_id': None,
            'vote_chat_id': update.effective_chat.id
        }
        
    except Exception as e:
        logger.warning(f"Could not send DM to user {user_id}: {e}")
        # Fallback to group chat if DM fails
        await update.message.reply_text(
            poll_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks for voting."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("mark_"):
        # Handle marking movies as Seen/Unseen
        parts = data.split("_")
        film_id = int(parts[1])
        seen = bool(int(parts[2]))
        
        # Get or create voting session
        if 'voting_sessions' not in context.bot_data:
            context.bot_data['voting_sessions'] = {}
        
        if user_id not in context.bot_data['voting_sessions']:
            await query.edit_message_text("❌ Voting session expired. Please use /vote again.")
            return
        
        session = context.bot_data['voting_sessions'][user_id]
        session['marks'][film_id] = seen
        
        # Update the voting interface to show current marks
        await update_voting_interface(query, context, user_id, session)
    
    elif data == "submit_vote":
        # Handle submitting the vote
        if 'voting_sessions' not in context.bot_data or user_id not in context.bot_data['voting_sessions']:
            await query.edit_message_text("❌ Voting session expired. Please use /vote again.")
            return
        
        session = context.bot_data['voting_sessions'][user_id]
        
        if not session['marks']:
            await query.answer("❌ Please mark at least one movie before voting!")
            return
        
        # Check if user has already voted in this round
        if bot.has_user_voted_in_round(user_id, session['round_id']):
            await query.edit_message_text(
                f"❌ **Already Voted!** ❌\n\n"
                f"You have already voted in this round.\n\n"
                f"Use /results to see current standings."
            )
            # Clean up the voting session
            if user_id in context.bot_data['voting_sessions']:
                del context.bot_data['voting_sessions'][user_id]
            return
        
        # Get the first marked movie (user can only vote for one)
        film_id = list(session['marks'].keys())[0]
        seen = session['marks'][film_id]
        
        if bot.add_vote(user_id, film_id, seen):
            film_title = bot.get_film_by_id(film_id)
            round_id, round_name = bot.get_round_info()
            status = "Seen" if seen else "Unseen"
            
            # Get user's name for group notification
            user_name = update.effective_user.first_name
            if update.effective_user.last_name:
                user_name += f" {update.effective_user.last_name}"
            
            # Send confirmation to DM
            confirmation_message = f"✅ **Vote Confirmation - {round_name}** ✅\n\n"
            confirmation_message += f"🎬 **Movie:** {film_title}\n"
            confirmation_message += f"👁️ **Your Vote:** {status}\n\n"
            confirmation_message += "🎉 *Your vote has been recorded successfully!*"
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=confirmation_message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"Could not send confirmation DM to user {user_id}: {e}")
            
            # Update the voting interface to show completion
            await query.edit_message_text(
                f"✅ **Vote Submitted!** ✅\n\n"
                f"🎬 You voted for: **{film_title}**\n"
                f"👁️ Status: **{status}**\n\n"
                f"Check your private messages for confirmation."
            )
            
            # Notify the group (without showing the choice)
            try:
                # Get the original chat where /vote was called
                # We need to store this information when the vote command is called
                if 'vote_chat_id' in session:
                    await context.bot.send_message(
                        chat_id=session['vote_chat_id'],
                        text=f"✅ {user_name} has voted."
                    )
            except Exception as e:
                logger.warning(f"Could not send group notification: {e}")
            
            # Clean up the voting session
            del context.bot_data['voting_sessions'][user_id]
            
        else:
            await query.edit_message_text(
                f"❌ **Already Voted!** ❌\n\n"
                f"You have already voted in this round.\n\n"
                f"Use /results to see current standings."
            )


async def update_voting_interface(query, context, user_id, session):
    """Update the voting interface to show current marks."""
    films = bot.get_all_films()
    round_id, round_name = bot.get_round_info()
    
    poll_message = f"🎬 **{round_name} - Movie Voting** 🎬\n\n"
    poll_message += "Mark each movie as Seen or Unseen, then vote for ONE movie:\n\n"
    
    keyboard = []
    for i, (film_id, title) in enumerate(films, 1):
        # Check if this movie is marked
        mark_status = ""
        if film_id in session['marks']:
            if session['marks'][film_id]:
                mark_status = " ✅"
            else:
                mark_status = " ❌"
        
        # Add movie option with number and mark status
        poll_message += f"**{i}.** 🎭 {title}{mark_status}\n"
        
        # Add Seen/Unseen buttons for this movie
        keyboard.append([
            InlineKeyboardButton(f"Seen ✅", callback_data=f"mark_{film_id}_1"),
            InlineKeyboardButton(f"Unseen ❌", callback_data=f"mark_{film_id}_0")
        ])
        
        # Add separator between movies (except for last one)
        if i < len(films):
            poll_message += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # Add vote button at the bottom
    keyboard.append([
        InlineKeyboardButton("Vote for this movie 🎯", callback_data="submit_vote")
    ])
    
    poll_message += "\n💡 *Mark each movie's status, then click 'Vote for this movie'*"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=poll_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all films with their scores for the current round."""
    round_id, round_name = bot.get_round_info()
    results = bot.get_results(round_id)
    
    if not results:
        await update.message.reply_text("📝 No films available. Ask an admin to add some films!")
        return
    
    message = f"📊 **{round_name} - Voting Results** 📊\n\n"
    
    for i, (title, score) in enumerate(results, 1):
        trophy = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
        message += f"{trophy} **{title}**\n"
        message += f"   📈 **{score:.1f} points**\n"
        
        # Add separator between movies (except for last one)
        if i < len(results):
            message += "━━━━━━━━━━━━━━━━━━━━\n"
    
    message += f"\n💡 *Scoring: Seen = 0.5 points, Unseen = 1.0 points*"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def winner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the top-scoring film for the current round."""
    round_id, round_name = bot.get_round_info()
    winner_title, winner_score = bot.get_winner(round_id)
    
    if not winner_title:
        await update.message.reply_text("📝 No films available. Ask an admin to add some films!")
        return
    
    message = f"🏆 **{round_name} - WINNER** 🏆\n\n"
    message += f"👑 **{winner_title}**\n"
    message += f"📊 **{winner_score:.1f} points**\n\n"
    message += f"🎉 *Congratulations to the winning film!*"
    
    await update.message.reply_text(message, parse_mode='Markdown')


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


async def delete_film(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a film from the database (Admin only)."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Sorry, only admins can delete films.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a film title: /deletefilm <film title>")
        return
    
    film_title = " ".join(context.args)
    film_id = bot.get_film_id_by_title(film_title)
    
    if not film_id:
        await update.message.reply_text(f"❌ Film '{film_title}' not found in the database.")
        return
    
    if bot.delete_film(film_id):
        await update.message.reply_text(f"✅ Film '{film_title}' deleted successfully!")
    else:
        await update.message.reply_text(f"❌ Could not delete film '{film_title}'.")


async def list_films(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all films in the database."""
    films = bot.get_all_films()
    
    if not films:
        await update.message.reply_text("📝 No films available in the database.")
        return
    
    message = "🎬 **Available Films:**\n\n"
    for i, (film_id, title) in enumerate(films, 1):
        message += f"**{i}.** {title}\n"
    
    message += f"\n📊 Total: {len(films)} films"
    
    await update.message.reply_text(message, parse_mode='Markdown')


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addfilm", add_film))
    application.add_handler(CommandHandler("deletefilm", delete_film))
    application.add_handler(CommandHandler("listfilms", list_films))
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
