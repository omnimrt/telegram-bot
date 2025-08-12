#!/usr/bin/env python3
"""
Setup script for Film Voting Telegram Bot
This script helps you configure the bot with your token and user ID.
"""

import os
import re

def get_bot_token():
    """Get bot token from user input."""
    print("🔑 Bot Token Setup")
    print("=" * 50)
    print("1. Go to @BotFather on Telegram")
    print("2. Send /newbot and follow instructions")
    print("3. Copy your bot token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)")
    print()
    
    while True:
        token = input("Enter your bot token: ").strip()
        if re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
            return token
        else:
            print("❌ Invalid token format. Please try again.")

def get_user_id():
    """Get user ID from user input (for reference only)."""
    print("\n👤 User ID Setup (Optional)")
    print("=" * 50)
    print("Note: The bot now uses Telegram's built-in admin system.")
    print("You don't need to configure a specific user ID.")
    print("Any user who is an admin in the chat can add films.")
    print()
    
    response = input("Do you want to continue? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        return None
    else:
        print("Setup cancelled.")
        exit(0)

def update_bot_file(token, user_id):
    """Update bot.py with the provided token."""
    try:
        # No need to update bot.py for user ID anymore
        # The bot now uses Telegram's built-in admin system
        print("✅ bot.py is already configured for dynamic admin checking!")
        return True
    except Exception as e:
        print(f"❌ Error updating bot.py: {e}")
        return False

def create_env_file(token):
    """Create .env file with bot token."""
    try:
        with open('.env', 'w') as f:
            f.write(f'BOT_TOKEN="{token}"\n')
        print("✅ .env file created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    """Main setup function."""
    print("🎬 Film Voting Telegram Bot Setup")
    print("=" * 50)
    print()
    
    # Get bot token and user ID
    token = get_bot_token()
    user_id = get_user_id()
    
    print("\n⚙️  Configuration")
    print("=" * 50)
    
    # Update bot.py
    if update_bot_file(token, user_id):
        print(f"✅ Bot configured for dynamic admin checking")
    
    # Create .env file
    if create_env_file(token):
        print(f"✅ Bot token saved to .env file")
    
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the bot: python bot.py")
    print("3. Start chatting with your bot on Telegram!")
    print()
    print("💡 Tip: You can also set the token as an environment variable:")
    print(f"   export BOT_TOKEN='{token}'")

if __name__ == "__main__":
    main()
