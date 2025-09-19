#!/usr/bin/env python3
"""
Telegram Bot for Cryptocurrency Trading with User Customization Features
"""

import logging
import sqlite3
import asyncio
import schedule
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from price_monitor import PriceMonitor
from daily_scheduler import DailySummaryScheduler
from config import BOT_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CryptoBot:
    def __init__(self, token: str):
        self.token = token
        self.db_path = "user_preferences.db"
        self.application = None
        self.price_monitor = None
        self.daily_scheduler = None
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create user preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                daily_notifications INTEGER DEFAULT 0
            )
        ''')
        
        # Create favorite coins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorite_coins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                coin_symbol TEXT,
                FOREIGN KEY (user_id) REFERENCES user_preferences (user_id)
            )
        ''')
        
        # Create price alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                coin_symbol TEXT,
                price_threshold REAL,
                alert_type TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_preferences (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def get_or_create_user(self, user_id: int, username: str = None):
        """Get or create user in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute(
                'INSERT INTO user_preferences (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            conn.commit()
            
        conn.close()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self.get_or_create_user(user.id, user.username)
        
        welcome_message = WELCOME_MESSAGE.format(name=user.first_name)
        await update.message.reply_text(welcome_message)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(HELP_MESSAGE, parse_mode='Markdown')
        
    async def set_favorites_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setfavorites command"""
        user_id = update.effective_user.id
        self.get_or_create_user(user_id, update.effective_user.username)
        
        if not context.args:
            await update.message.reply_text(
                "Please provide coin symbols. Example: /setfavorites BTC ETH XRP"
            )
            return
            
        coins = [coin.upper() for coin in context.args]
        
        # Clear existing favorites
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorite_coins WHERE user_id = ?', (user_id,))
        
        # Add new favorites
        for coin in coins:
            cursor.execute(
                'INSERT INTO favorite_coins (user_id, coin_symbol) VALUES (?, ?)',
                (user_id, coin)
            )
        
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ Your favorite coins have been set to: {', '.join(coins)}"
        )
        
    async def get_user_favorites(self, user_id: int) -> List[str]:
        """Get user's favorite coins"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT coin_symbol FROM favorite_coins WHERE user_id = ?', (user_id,))
        favorites = [row[0] for row in cursor.fetchall()]
        conn.close()
        return favorites
        
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command"""
        user_id = update.effective_user.id
        self.get_or_create_user(user_id, update.effective_user.username)
        
        favorites_only = len(context.args) > 0 and context.args[0].lower() == 'favorites'
        
        if favorites_only:
            favorites = await self.get_user_favorites(user_id)
            if not favorites:
                await update.message.reply_text(
                    "You haven't set any favorite coins yet. Use /setfavorites to set them."
                )
                return
            coins = favorites
            title = "📊 *Trading Signals for Your Favorite Coins:*"
        else:
            coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']  # Default coins
            title = "📊 *Trading Signals for Top Coins:*"
        
        signals_text = f"{title}\n\n"
        
        for coin in coins:
            # Mock trading signal (in real implementation, this would use actual trading algorithms)
            signal = self.generate_mock_signal(coin)
            signals_text += f"*{coin}:* {signal}\n"
        
        await update.message.reply_text(signals_text, parse_mode='Markdown')
        
    def generate_mock_signal(self, coin: str) -> str:
        """Generate mock trading signal for demonstration"""
        import random
        signals = ['🟢 BUY', '🔴 SELL', '🟡 HOLD']
        prices = {
            'BTC': random.randint(40000, 50000),
            'ETH': random.randint(2500, 3500),
            'BNB': random.randint(300, 400),
            'XRP': round(random.uniform(0.5, 1.0), 2),
            'ADA': round(random.uniform(0.3, 0.8), 2)
        }
        
        signal = random.choice(signals)
        price = prices.get(coin, random.randint(1, 100))
        return f"{signal} - ${price}"
        
    async def set_alert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setalert command"""
        user_id = update.effective_user.id
        self.get_or_create_user(user_id, update.effective_user.username)
        
        if len(context.args) != 2:
            await update.message.reply_text(
                "Usage: /setalert <COIN> <PRICE>\nExample: /setalert BTC 45000"
            )
            return
            
        coin = context.args[0].upper()
        try:
            price = float(context.args[1])
        except ValueError:
            await update.message.reply_text("Please provide a valid price number.")
            return
            
        # Store alert in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO price_alerts (user_id, coin_symbol, price_threshold, alert_type) VALUES (?, ?, ?, ?)',
            (user_id, coin, price, 'price_target')
        )
        conn.commit()
        alert_id = cursor.lastrowid
        conn.close()
        
        await update.message.reply_text(
            f"🔔 Alert set! I'll notify you when {coin} reaches ${price:,.2f}\nAlert ID: {alert_id}"
        )
        
    async def daily_on_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dailyon command"""
        user_id = update.effective_user.id
        self.get_or_create_user(user_id, update.effective_user.username)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE user_preferences SET daily_notifications = 1 WHERE user_id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            "📅 Daily market summaries enabled! You'll receive updates every day at 9:00 AM UTC."
        )
        
    async def daily_off_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dailyoff command"""
        user_id = update.effective_user.id
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE user_preferences SET daily_notifications = 0 WHERE user_id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            "📅 Daily market summaries disabled."
        )
        
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user preferences
        cursor.execute('SELECT daily_notifications FROM user_preferences WHERE user_id = ?', (user_id,))
        daily_enabled = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        # Get favorite coins
        favorites = await self.get_user_favorites(user_id)
        
        # Get active alerts
        cursor.execute(
            'SELECT coin_symbol, price_threshold FROM price_alerts WHERE user_id = ? AND is_active = 1',
            (user_id,)
        )
        alerts = cursor.fetchall()
        
        conn.close()
        
        status_text = f"""
📊 *Your CryptoBot Status:*

*Favorite Coins:* {', '.join(favorites) if favorites else 'None set'}

*Daily Summaries:* {'🟢 Enabled' if daily_enabled else '🔴 Disabled'}

*Active Alerts:* {len(alerts)}
        """
        
        if alerts:
            status_text += "\n"
            for coin, price in alerts:
                status_text += f"• {coin}: ${price:,.2f}\n"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
        
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alerts command"""
        user_id = update.effective_user.id
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, coin_symbol, price_threshold, created_at FROM price_alerts WHERE user_id = ? AND is_active = 1',
            (user_id,)
        )
        alerts = cursor.fetchall()
        conn.close()
        
        if not alerts:
            await update.message.reply_text("You have no active alerts.")
            return
            
        alerts_text = "🔔 *Your Active Alerts:*\n\n"
        for alert_id, coin, price, created_at in alerts:
            alerts_text += f"ID {alert_id}: {coin} at ${price:,.2f}\n"
            
        await update.message.reply_text(alerts_text, parse_mode='Markdown')
    
    async def test_summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /testsummary command - for testing daily summaries"""
        user_id = update.effective_user.id
        if self.daily_scheduler:
            self.daily_scheduler.send_test_summary(user_id)
            await update.message.reply_text("📧 Test summary sent!")
        else:
            await update.message.reply_text("❌ Daily scheduler not initialized")
        
    def run(self):
        """Run the bot"""
        self.application = Application.builder().token(self.token).build()
        
        # Initialize monitoring components
        self.price_monitor = PriceMonitor(self.application.bot)
        self.daily_scheduler = DailySummaryScheduler(self.application.bot)
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("setfavorites", self.set_favorites_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CommandHandler("setalert", self.set_alert_command))
        self.application.add_handler(CommandHandler("dailyon", self.daily_on_command))
        self.application.add_handler(CommandHandler("dailyoff", self.daily_off_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("alerts", self.alerts_command))
        self.application.add_handler(CommandHandler("testsummary", self.test_summary_command))
        
        # Start background tasks
        asyncio.create_task(self.price_monitor.start_monitoring())
        asyncio.create_task(self.daily_scheduler.start_scheduler())
        
        # Start the bot
        self.application.run_polling()

if __name__ == '__main__':
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Please set your Telegram bot token in config.py or environment variable")
        print("Get a token from @BotFather on Telegram")
        print("Set environment variable: export TELEGRAM_BOT_TOKEN='your_token'")
        exit(1)
        
    bot = CryptoBot(BOT_TOKEN)
    bot.run()