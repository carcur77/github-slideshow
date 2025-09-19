#!/bin/bash
# Installation script for Telegram Crypto Bot

echo "🤖 Installing Telegram Crypto Bot..."
echo "====================================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "✓ Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Run tests
echo "🧪 Running tests..."
python3 test_bot.py

if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Some tests failed"
    exit 1
fi

# Run demo
echo "🎮 Running demo..."
python3 demo.py

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Get a Telegram bot token from @BotFather"
echo "2. Set your token: export TELEGRAM_BOT_TOKEN='your_token'"
echo "3. Run the bot: python3 bot.py"
echo ""
echo "For more information, see BOT_README.md"