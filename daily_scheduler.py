"""
Daily summary scheduler for the Telegram Crypto Bot
"""

import sqlite3
import asyncio
import schedule
import time
import logging
from datetime import datetime
from typing import List
from price_monitor import PriceMonitor
from config import DATABASE_PATH, DAILY_SUMMARY_TIME

logger = logging.getLogger(__name__)

class DailySummaryScheduler:
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.db_path = DATABASE_PATH
        self.price_monitor = PriceMonitor()
        
    def get_users_with_daily_enabled(self) -> List[tuple]:
        """Get all users who have daily notifications enabled"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username 
            FROM user_preferences 
            WHERE daily_notifications = 1
        ''')
        users = cursor.fetchall()
        conn.close()
        return users
    
    def get_user_favorite_coins(self, user_id: int) -> List[str]:
        """Get user's favorite coins"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT coin_symbol FROM favorite_coins WHERE user_id = ?',
            (user_id,)
        )
        favorites = [row[0] for row in cursor.fetchall()]
        conn.close()
        return favorites or ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']  # Default coins if no favorites
    
    async def send_daily_summary(self):
        """Send daily market summary to all subscribed users"""
        users = self.get_users_with_daily_enabled()
        
        if not users:
            logger.info("No users subscribed to daily summaries")
            return
        
        logger.info(f"Sending daily summaries to {len(users)} users")
        
        for user_id, username in users:
            try:
                # Get user's favorite coins for personalized summary
                favorite_coins = self.get_user_favorite_coins(user_id)
                summary = self.price_monitor.get_market_summary(favorite_coins)
                
                if self.bot:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=summary,
                        parse_mode='Markdown'
                    )
                    
                logger.info(f"Daily summary sent to user {user_id}")
                
            except Exception as e:
                logger.error(f"Failed to send daily summary to user {user_id}: {e}")
    
    def schedule_daily_summaries(self):
        """Schedule daily summaries"""
        schedule.every().day.at(DAILY_SUMMARY_TIME).do(
            lambda: asyncio.create_task(self.send_daily_summary())
        )
        logger.info(f"Daily summaries scheduled for {DAILY_SUMMARY_TIME} UTC")
    
    async def start_scheduler(self):
        """Start the scheduling loop"""
        self.schedule_daily_summaries()
        logger.info("Daily summary scheduler started")
        
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    def send_test_summary(self, user_id: int):
        """Send a test summary to a specific user (for testing)"""
        try:
            favorite_coins = self.get_user_favorite_coins(user_id)
            summary = self.price_monitor.get_market_summary(favorite_coins)
            summary = "🧪 *Test Summary*\n\n" + summary
            
            if self.bot:
                asyncio.create_task(
                    self.bot.send_message(
                        chat_id=user_id,
                        text=summary,
                        parse_mode='Markdown'
                    )
                )
                
        except Exception as e:
            logger.error(f"Failed to send test summary to user {user_id}: {e}")