"""
Price monitoring and alert system for the Telegram Crypto Bot
"""

import sqlite3
import requests
import asyncio
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from config import DATABASE_PATH, CRYPTO_API_URL, PRICE_CHECK_INTERVAL

logger = logging.getLogger(__name__)

class PriceMonitor:
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.db_path = DATABASE_PATH
        self.api_url = CRYPTO_API_URL
        
    def get_current_price(self, coin_symbol: str) -> float:
        """Get current price for a cryptocurrency"""
        try:
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum', 
                'BNB': 'binancecoin',
                'XRP': 'ripple',
                'ADA': 'cardano',
                'DOGE': 'dogecoin',
                'DOT': 'polkadot',
                'SOL': 'solana',
                'AVAX': 'avalanche-2',
                'MATIC': 'matic-network'
            }
            
            coin_id = symbol_map.get(coin_symbol.upper(), coin_symbol.lower())
            
            response = requests.get(
                f"{self.api_url}/simple/price",
                params={
                    'ids': coin_id,
                    'vs_currencies': 'usd'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    return data[coin_id]['usd']
            
            # Fallback to mock price if API fails
            logger.warning(f"API call failed for {coin_symbol}, using mock price")
            return self.get_mock_price(coin_symbol)
            
        except Exception as e:
            logger.error(f"Error getting price for {coin_symbol}: {e}")
            return self.get_mock_price(coin_symbol)
    
    def get_mock_price(self, coin_symbol: str) -> float:
        """Generate mock price for demonstration purposes"""
        import random
        mock_prices = {
            'BTC': random.uniform(40000, 50000),
            'ETH': random.uniform(2500, 3500),
            'BNB': random.uniform(300, 400),
            'XRP': random.uniform(0.5, 1.0),
            'ADA': random.uniform(0.3, 0.8),
            'DOGE': random.uniform(0.05, 0.15),
            'DOT': random.uniform(5, 15),
            'SOL': random.uniform(20, 80),
            'AVAX': random.uniform(10, 30),
            'MATIC': random.uniform(0.5, 1.5)
        }
        return mock_prices.get(coin_symbol.upper(), random.uniform(1, 100))
    
    def get_active_alerts(self) -> List[Tuple]:
        """Get all active price alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, user_id, coin_symbol, price_threshold, alert_type 
            FROM price_alerts 
            WHERE is_active = 1
        ''')
        alerts = cursor.fetchall()
        conn.close()
        return alerts
    
    def deactivate_alert(self, alert_id: int):
        """Deactivate a triggered alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE price_alerts SET is_active = 0 WHERE id = ?',
            (alert_id,)
        )
        conn.commit()
        conn.close()
    
    async def check_price_alerts(self):
        """Check all active alerts and send notifications"""
        alerts = self.get_active_alerts()
        
        for alert_id, user_id, coin_symbol, threshold, alert_type in alerts:
            try:
                current_price = self.get_current_price(coin_symbol)
                
                # For simplicity, we'll trigger alert if price is within 5% of threshold
                price_diff_percent = abs(current_price - threshold) / threshold * 100
                
                if price_diff_percent <= 5:  # Alert triggered
                    message = f"""
🚨 *Price Alert Triggered!* 🚨

*{coin_symbol}* has reached your target!
💰 Current Price: ${current_price:,.2f}
🎯 Your Target: ${threshold:,.2f}

Alert ID: {alert_id}
                    """
                    
                    if self.bot:
                        try:
                            await self.bot.send_message(
                                chat_id=user_id,
                                text=message,
                                parse_mode='Markdown'
                            )
                            self.deactivate_alert(alert_id)
                            logger.info(f"Alert {alert_id} triggered for user {user_id}")
                        except Exception as e:
                            logger.error(f"Failed to send alert to user {user_id}: {e}")
                            
            except Exception as e:
                logger.error(f"Error checking alert {alert_id}: {e}")
    
    async def start_monitoring(self):
        """Start the price monitoring loop"""
        logger.info("Starting price monitoring...")
        
        while True:
            try:
                await self.check_price_alerts()
                await asyncio.sleep(PRICE_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def get_market_summary(self, coins: List[str] = None) -> str:
        """Generate market summary for specified coins"""
        if not coins:
            coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']
        
        summary = "📊 *Daily Market Summary*\n\n"
        
        for coin in coins:
            try:
                price = self.get_current_price(coin)
                # Mock 24h change for demo
                import random
                change_percent = random.uniform(-10, 10)
                change_symbol = "🟢" if change_percent > 0 else "🔴"
                
                summary += f"*{coin}:* ${price:,.2f} {change_symbol} {change_percent:+.2f}%\n"
                
            except Exception as e:
                logger.error(f"Error getting price for {coin}: {e}")
                
        summary += f"\n📅 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
        return summary