#!/usr/bin/env python3
"""
Test script for the Telegram Crypto Bot
"""

import sqlite3
import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from price_monitor import PriceMonitor
from daily_scheduler import DailySummaryScheduler

class TestCryptoBot(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db_path = self.test_db.name
        self.test_db.close()
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def init_test_db(self):
        """Initialize test database with schema"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE user_preferences (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                daily_notifications INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE favorite_coins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                coin_symbol TEXT,
                FOREIGN KEY (user_id) REFERENCES user_preferences (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE price_alerts (
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
    
    def test_database_initialization(self):
        """Test database schema creation"""
        self.init_test_db()
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn('user_preferences', tables)
        self.assertIn('favorite_coins', tables)
        self.assertIn('price_alerts', tables)
        
        conn.close()
    
    def test_user_creation(self):
        """Test user creation in database"""
        self.init_test_db()
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Insert test user
        cursor.execute(
            'INSERT INTO user_preferences (user_id, username) VALUES (?, ?)',
            (123456, 'testuser')
        )
        conn.commit()
        
        # Verify user exists
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (123456,))
        user = cursor.fetchone()
        
        self.assertIsNotNone(user)
        self.assertEqual(user[0], 123456)
        self.assertEqual(user[1], 'testuser')
        
        conn.close()
    
    def test_favorite_coins(self):
        """Test favorite coins functionality"""
        self.init_test_db()
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Insert test user
        cursor.execute(
            'INSERT INTO user_preferences (user_id, username) VALUES (?, ?)',
            (123456, 'testuser')
        )
        
        # Insert favorite coins
        coins = ['BTC', 'ETH', 'XRP']
        for coin in coins:
            cursor.execute(
                'INSERT INTO favorite_coins (user_id, coin_symbol) VALUES (?, ?)',
                (123456, coin)
            )
        
        conn.commit()
        
        # Retrieve favorite coins
        cursor.execute('SELECT coin_symbol FROM favorite_coins WHERE user_id = ?', (123456,))
        favorites = [row[0] for row in cursor.fetchall()]
        
        self.assertEqual(len(favorites), 3)
        self.assertIn('BTC', favorites)
        self.assertIn('ETH', favorites)
        self.assertIn('XRP', favorites)
        
        conn.close()
    
    def test_price_alerts(self):
        """Test price alerts functionality"""
        self.init_test_db()
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Insert test user
        cursor.execute(
            'INSERT INTO user_preferences (user_id, username) VALUES (?, ?)',
            (123456, 'testuser')
        )
        
        # Insert price alert
        cursor.execute(
            'INSERT INTO price_alerts (user_id, coin_symbol, price_threshold, alert_type) VALUES (?, ?, ?, ?)',
            (123456, 'BTC', 45000.0, 'price_target')
        )
        
        conn.commit()
        
        # Retrieve alerts
        cursor.execute(
            'SELECT coin_symbol, price_threshold FROM price_alerts WHERE user_id = ? AND is_active = 1',
            (123456,)
        )
        alerts = cursor.fetchall()
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0][0], 'BTC')
        self.assertEqual(alerts[0][1], 45000.0)
        
        conn.close()
    
    @patch('price_monitor.requests.get')
    def test_price_monitor(self, mock_get):
        """Test price monitoring functionality"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'bitcoin': {'usd': 45000}}
        mock_get.return_value = mock_response
        
        monitor = PriceMonitor()
        price = monitor.get_current_price('BTC')
        
        self.assertEqual(price, 45000)
    
    def test_mock_price_generation(self):
        """Test mock price generation"""
        monitor = PriceMonitor()
        
        # Test mock prices for different coins
        btc_price = monitor.get_mock_price('BTC')
        eth_price = monitor.get_mock_price('ETH')
        
        self.assertGreater(btc_price, 0)
        self.assertGreater(eth_price, 0)
        self.assertNotEqual(btc_price, eth_price)  # Should be different
    
    def test_daily_scheduler_users(self):
        """Test daily scheduler user retrieval"""
        self.init_test_db()
        
        # Patch the db_path in scheduler
        scheduler = DailySummaryScheduler()
        scheduler.db_path = self.test_db_path
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Insert test users
        cursor.execute(
            'INSERT INTO user_preferences (user_id, username, daily_notifications) VALUES (?, ?, ?)',
            (123456, 'user1', 1)
        )
        cursor.execute(
            'INSERT INTO user_preferences (user_id, username, daily_notifications) VALUES (?, ?, ?)',
            (789012, 'user2', 0)
        )
        
        conn.commit()
        conn.close()
        
        # Get users with daily notifications enabled
        users = scheduler.get_users_with_daily_enabled()
        
        self.assertEqual(len(users), 1)  # Only one user has notifications enabled
        self.assertEqual(users[0][0], 123456)

def run_tests():
    """Run all tests"""
    print("Running Telegram Crypto Bot Tests...")
    print("=" * 50)
    
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_tests()