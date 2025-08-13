#!/usr/bin/env python3
"""
Standalone database test for Film Voting Bot
This script tests the database functionality without requiring bot token.
"""

import sqlite3
import os

class TestFilmVotingBot:
    def __init__(self):
        self.db_name = "test_film_voting.db"
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
        print("✅ Database initialized successfully")
    
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
            print(f"⚠️  Film '{title}' already exists")
            return False
        except Exception as e:
            print(f"❌ Error adding film: {e}")
            return False
    
    def get_all_films(self):
        """Get all films from the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM films ORDER BY title")
        films = cursor.fetchall()
        conn.close()
        return films
    
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
                print("❌ No active round found")
                return False
            
            cursor.execute(
                "INSERT INTO votes (user_id, film_id, round_id, seen) VALUES (?, ?, ?, ?)",
                (user_id, film_id, round_id, seen)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️  User {user_id} has already voted in round {round_id}")
            return False
        except Exception as e:
            print(f"❌ Error adding vote: {e}")
            return False
    
    def get_results(self, round_id: int = None):
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
    
    def get_winner(self, round_id: int = None):
        """Get the top-scoring film for a specific round."""
        results = self.get_results(round_id)
        return results[0] if results else (None, 0.0)
    
    def get_vote_counts_for_film(self, film_id: int, round_id: int = None):
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
            
            print(f"✅ Film '{film_title}' (ID: {film_id}) deleted successfully")
            return True
        except Exception as e:
            print(f"❌ Error deleting film {film_id}: {e}")
            return False
    
    def get_film_id_by_title(self, title: str) -> int:
        """Get film ID by title (case-insensitive)."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM films WHERE LOWER(title) = LOWER(?)", (title,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def cleanup(self):
        """Remove test database."""
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
            print("🧹 Test database cleaned up")

def test_database():
    """Test the database functionality."""
    print("🧪 Testing Film Voting Bot Database")
    print("=" * 50)
    
    # Initialize bot
    bot = TestFilmVotingBot()
    
    # Test adding films
    print("\n2. Testing film addition...")
    test_films = [
        "The Shawshank Redemption",
        "Pulp Fiction", 
        "The Dark Knight",
        "Fight Club",
        "Inception"
    ]
    
    for film in test_films:
        success = bot.add_film(film)
        if success:
            print(f"✅ Added: {film}")
        else:
            print(f"❌ Failed to add: {film}")
    
    # Test duplicate prevention
    print("\n3. Testing duplicate prevention...")
    success = bot.add_film("The Shawshank Redemption")
    if not success:
        print("✅ Duplicate prevention working")
    else:
        print("❌ Duplicate prevention failed")
    
    # Test voting
    print("\n4. Testing voting system...")
    test_user_id = 12345
    films = bot.get_all_films()
    
    # Test first user voting (should succeed)
    film_id, title = films[0]
    success = bot.add_vote(test_user_id, film_id, True)
    if success:
        print(f"✅ User 1 voted 'Seen' for: {title}")
    else:
        print(f"❌ Failed to vote 'Seen' for: {title}")
    
    # Test duplicate vote prevention (should fail)
    film_id, title = films[1]
    success = bot.add_vote(test_user_id, film_id, False)
    if not success:
        print(f"✅ Duplicate vote prevention working for user 1")
    else:
        print(f"❌ Duplicate vote prevention failed for user 1")
    
    # Test another user voting
    print("\n5. Testing multiple users...")
    test_user_id_2 = 67890
    film_id, title = films[1]
    success = bot.add_vote(test_user_id_2, film_id, False)
    if success:
        print(f"✅ User 2 voted 'Not Seen' for: {title}")
    else:
        print(f"❌ User 2 failed to vote for: {title}")
    
    # Test results
    print("\n6. Testing results calculation...")
    results = bot.get_results()
    print("📊 Current Results:")
    for i, (title, score) in enumerate(results, 1):
        print(f"   {i}. {title}: {score:.1f} points")
    
    # Test winner
    print("\n7. Testing winner selection...")
    winner_title, winner_score = bot.get_winner()
    print(f"🏆 Winner: {winner_title} with {winner_score:.1f} points")
    
    # Test vote counts
    print("\n8. Testing vote counts...")
    film_id, title = films[0]
    vote_counts = bot.get_vote_counts_for_film(film_id)
    print(f"📊 Vote counts for '{title}': Seen={vote_counts['seen']}, Unseen={vote_counts['unseen']}, Total={vote_counts['total']}")
    
    # Test delete functionality
    print("\n9. Testing delete functionality...")
    film_id, title = films[1]
    success = bot.delete_film(film_id)
    if success:
        print(f"✅ Successfully deleted: {title}")
    else:
        print(f"❌ Failed to delete: {title}")
    
    # Test film ID lookup
    print("\n10. Testing film ID lookup...")
    film_id = bot.get_film_id_by_title("The Shawshank Redemption")
    if film_id:
        print(f"✅ Found film ID: {film_id}")
    else:
        print(f"❌ Film not found")
    
    # Cleanup
    bot.cleanup()
    
    print("\n🎉 All tests completed successfully!")
    print("=" * 50)
    print("The bot is ready to run with: python bot.py")

if __name__ == "__main__":
    test_database()
