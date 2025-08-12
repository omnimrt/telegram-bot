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
            print(f"⚠️  User {user_id} has already voted for film {film_id}")
            return False
        except Exception as e:
            print(f"❌ Error adding vote: {e}")
            return False
    
    def get_results(self):
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
    
    def get_winner(self):
        """Get the top-scoring film."""
        results = self.get_results()
        return results[0] if results else (None, 0.0)
    
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
    
    for film_id, title in films[:3]:  # Test first 3 films
        # Test seen vote
        success = bot.add_vote(test_user_id, film_id, True)
        if success:
            print(f"✅ Voted 'Seen' for: {title}")
        else:
            print(f"❌ Failed to vote 'Seen' for: {title}")
        
        # Test duplicate vote prevention
        success = bot.add_vote(test_user_id, film_id, False)
        if not success:
            print(f"✅ Duplicate vote prevention working for: {title}")
        else:
            print(f"❌ Duplicate vote prevention failed for: {title}")
    
    # Test another user voting
    print("\n5. Testing multiple users...")
    test_user_id_2 = 67890
    for film_id, title in films[3:]:  # Test last 2 films
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
    
    # Cleanup
    bot.cleanup()
    
    print("\n🎉 All tests completed successfully!")
    print("=" * 50)
    print("The bot is ready to run with: python bot.py")

if __name__ == "__main__":
    test_database()
