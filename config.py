"""
Configuration file for the Telegram Crypto Bot
"""

import os

# Bot Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Database Configuration
DATABASE_PATH = 'user_preferences.db'

# API Configuration
CRYPTO_API_URL = 'https://api.coingecko.com/api/v3'

# Timing Configuration
DAILY_SUMMARY_TIME = "09:00"  # UTC time for daily summaries
PRICE_CHECK_INTERVAL = 300    # Check prices every 5 minutes (in seconds)

# Default Settings
DEFAULT_COINS = ['bitcoin', 'ethereum', 'binancecoin', 'ripple', 'cardano']
MAX_FAVORITES = 10
MAX_ALERTS_PER_USER = 20

# Message Templates
HELP_MESSAGE = """
📚 *CryptoBot Help Menu*

*Favorite Coins:*
/setfavorites BTC ETH XRP - Set your favorite coins
/signals favorites - Get signals only for your favorite coins
/signals - Get signals for all coins

*Price Alerts:*
/setalert BTC 30000 - Set alert when BTC reaches $30,000
/alerts - View your active alerts

*Daily Summaries:*
/dailyon - Enable daily market summaries
/dailyoff - Disable daily market summaries

*General:*
/status - Check your current settings
/help - Show this help menu

*Example Usage:*
`/setfavorites BTC ETH ADA DOGE`
`/setalert BTC 45000`
`/signals favorites`
"""

WELCOME_MESSAGE = """
🚀 Welcome to CryptoBot, {name}!

I can help you track cryptocurrency prices and get personalized alerts.

Available commands:
/help - Show all available commands
/setfavorites - Set your favorite coins
/signals - Get trading signals
/setalert - Set price alerts
/dailyon - Enable daily market summaries
/dailyoff - Disable daily market summaries
/status - Check your current settings
"""