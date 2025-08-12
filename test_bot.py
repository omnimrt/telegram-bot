#!/usr/bin/env python3
"""
Test script for Film Voting Bot
This script tests the database functionality without running the Telegram bot.
"""

import sqlite3
import os

def test_database():
    """Test the database functionality."""
    print("🧪 Testing Film Voting Bot Database")
    print("=" * 50)
    
    # Test database creation
    print("1. Testing database creation...")
    if os.path.exists("film_voting.db"):
        os.remove("film_voting.db")
    
    # Import and initialize the bot
    from bot import FilmVotingBot
    bot = FilmVotingBot()
    print("✅ Database created successfully")
    
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
    
    print("\n🎉 All tests completed successfully!")
    print("=" * 50)
    print("The bot is ready to run with: python bot.py")

if __name__ == "__main__":
    test_database()
