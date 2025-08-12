#!/bin/bash

echo "🎬 Film Voting Telegram Bot - Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ Python and pip found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Check if bot is configured
if [ ! -f ".env" ] && [ -z "$BOT_TOKEN" ]; then
    echo "🔧 Bot not configured yet. Running setup..."
    python3 setup.py
    echo ""
fi

# Test the bot
echo "🧪 Testing bot functionality..."
python3 test_database.py

if [ $? -ne 0 ]; then
    echo "❌ Bot test failed"
    exit 1
fi

echo ""
echo "🎉 Bot is ready to run!"
echo ""
echo "To start the bot, run:"
echo "  python3 bot.py"
echo ""
echo "Or use this script:"
echo "  ./quick_start.sh run"
echo ""

# If run argument is provided, start the bot
if [ "$1" = "run" ]; then
    echo "🚀 Starting the bot..."
    python3 bot.py
fi
