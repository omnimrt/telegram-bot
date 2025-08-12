#!/usr/bin/env python3
"""
Simple test for admin functionality
This script tests the admin checking logic without requiring bot token.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

async def is_user_admin(update, context):
    """Check if the user is an admin in the current chat."""
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ('administrator', 'creator')
    except Exception as e:
        print(f"Warning: Error checking admin status: {e}")
        return False

async def test_admin_function():
    """Test the admin checking function with mock data."""
    print("🧪 Testing Admin Function")
    print("=" * 50)
    
    # Create mock update and context
    mock_update = MagicMock()
    mock_context = MagicMock()
    
    # Test case 1: User is admin
    print("\n1. Testing admin user...")
    mock_update.effective_chat.id = 123456
    mock_update.effective_user.id = 789012
    
    # Mock the bot.get_chat_member method
    mock_member = MagicMock()
    mock_member.status = 'administrator'
    mock_context.bot.get_chat_member = AsyncMock(return_value=mock_member)
    
    result = await is_user_admin(mock_update, mock_context)
    if result:
        print("✅ Admin user correctly identified")
    else:
        print("❌ Admin user not identified correctly")
    
    # Test case 2: User is creator
    print("\n2. Testing creator user...")
    mock_member.status = 'creator'
    result = await is_user_admin(mock_update, mock_context)
    if result:
        print("✅ Creator user correctly identified")
    else:
        print("❌ Creator user not identified correctly")
    
    # Test case 3: User is not admin
    print("\n3. Testing non-admin user...")
    mock_member.status = 'member'
    result = await is_user_admin(mock_update, mock_context)
    if not result:
        print("✅ Non-admin user correctly identified")
    else:
        print("❌ Non-admin user not identified correctly")
    
    # Test case 4: Error handling
    print("\n4. Testing error handling...")
    mock_context.bot.get_chat_member = AsyncMock(side_effect=Exception("Test error"))
    result = await is_user_admin(mock_update, mock_context)
    if not result:
        print("✅ Error handling works correctly")
    else:
        print("❌ Error handling not working correctly")
    
    print("\n🎉 Admin function tests completed!")

if __name__ == "__main__":
    asyncio.run(test_admin_function())
