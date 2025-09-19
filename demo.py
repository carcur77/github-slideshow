#!/usr/bin/env python3
"""
Demo script for the Telegram Crypto Bot
Shows functionality without requiring a live Telegram connection
"""

import sqlite3
import os
from price_monitor import PriceMonitor
from daily_scheduler import DailySummaryScheduler

def demo_database_operations():
    """Demonstrate database operations"""
    print("🗄️  Database Operations Demo")
    print("=" * 40)
    
    # Create a demo database
    db_path = "demo_bot.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
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
    
    # Insert demo data
    cursor.execute(
        'INSERT INTO user_preferences (user_id, username, daily_notifications) VALUES (?, ?, ?)',
        (123456, 'alice_trader', 1)
    )
    
    cursor.execute(
        'INSERT INTO user_preferences (user_id, username, daily_notifications) VALUES (?, ?, ?)',
        (789012, 'bob_investor', 0)
    )
    
    # Add favorite coins for Alice
    for coin in ['BTC', 'ETH', 'ADA']:
        cursor.execute(
            'INSERT INTO favorite_coins (user_id, coin_symbol) VALUES (?, ?)',
            (123456, coin)
        )
    
    # Add favorite coins for Bob
    for coin in ['BTC', 'XRP', 'DOT']:
        cursor.execute(
            'INSERT INTO favorite_coins (user_id, coin_symbol) VALUES (?, ?)',
            (789012, coin)
        )
    
    # Add price alerts
    cursor.execute(
        'INSERT INTO price_alerts (user_id, coin_symbol, price_threshold, alert_type) VALUES (?, ?, ?, ?)',
        (123456, 'BTC', 45000.0, 'price_target')
    )
    
    cursor.execute(
        'INSERT INTO price_alerts (user_id, coin_symbol, price_threshold, alert_type) VALUES (?, ?, ?, ?)',
        (123456, 'ETH', 3000.0, 'price_target')
    )
    
    conn.commit()
    
    # Display data
    print("👥 Users:")
    cursor.execute('SELECT user_id, username, daily_notifications FROM user_preferences')
    for user_id, username, daily in cursor.fetchall():
        daily_status = "✅ Enabled" if daily else "❌ Disabled"
        print(f"  • {username} (ID: {user_id}) - Daily notifications: {daily_status}")
    
    print("\n💰 Favorite Coins:")
    cursor.execute('''
        SELECT up.username, fc.coin_symbol 
        FROM user_preferences up 
        JOIN favorite_coins fc ON up.user_id = fc.user_id
        ORDER BY up.username, fc.coin_symbol
    ''')
    current_user = None
    for username, coin in cursor.fetchall():
        if username != current_user:
            print(f"  • {username}: {coin}", end="")
            current_user = username
        else:
            print(f", {coin}", end="")
    print()
    
    print("\n🔔 Price Alerts:")
    cursor.execute('''
        SELECT up.username, pa.coin_symbol, pa.price_threshold, pa.is_active
        FROM user_preferences up 
        JOIN price_alerts pa ON up.user_id = pa.user_id
        ORDER BY up.username
    ''')
    for username, coin, threshold, active in cursor.fetchall():
        status = "🟢 Active" if active else "🔴 Inactive"
        print(f"  • {username}: {coin} at ${threshold:,.2f} - {status}")
    
    conn.close()
    os.remove(db_path)
    print()

def demo_price_monitoring():
    """Demonstrate price monitoring functionality"""
    print("📊 Price Monitoring Demo")
    print("=" * 40)
    
    monitor = PriceMonitor()
    
    coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'DOGE']
    
    print("Current Prices (Mock Data):")
    for coin in coins:
        price = monitor.get_mock_price(coin)
        print(f"  • {coin}: ${price:,.2f}")
    
    print("\nMarket Summary:")
    summary = monitor.get_market_summary(coins)
    print(summary)
    print()

def demo_daily_scheduler():
    """Demonstrate daily scheduler functionality"""
    print("📅 Daily Scheduler Demo")
    print("=" * 40)
    
    # Create a temporary database for demo
    db_path = "demo_scheduler.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables and insert demo data
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
    
    cursor.execute(
        'INSERT INTO user_preferences (user_id, username, daily_notifications) VALUES (?, ?, ?)',
        (123456, 'daily_user', 1)
    )
    
    for coin in ['BTC', 'ETH', 'XRP']:
        cursor.execute(
            'INSERT INTO favorite_coins (user_id, coin_symbol) VALUES (?, ?)',
            (123456, coin)
        )
    
    conn.commit()
    conn.close()
    
    # Demo scheduler
    scheduler = DailySummaryScheduler()
    scheduler.db_path = db_path
    
    users = scheduler.get_users_with_daily_enabled()
    print(f"Users with daily notifications enabled: {len(users)}")
    
    for user_id, username in users:
        print(f"  • {username} (ID: {user_id})")
        favorites = scheduler.get_user_favorite_coins(user_id)
        print(f"    Favorite coins: {', '.join(favorites)}")
        
        # Generate sample summary
        summary = scheduler.price_monitor.get_market_summary(favorites)
        print("    Sample summary:")
        for line in summary.split('\n'):
            if line.strip():
                print(f"      {line}")
    
    os.remove(db_path)
    print()

def demo_command_examples():
    """Show examples of bot commands"""
    print("🤖 Bot Command Examples")
    print("=" * 40)
    
    commands = [
        ("/start", "Initialize the bot and see welcome message"),
        ("/help", "Show all available commands"),
        ("/setfavorites BTC ETH XRP", "Set your favorite coins"),
        ("/signals", "Get trading signals for all coins"),
        ("/signals favorites", "Get signals only for your favorite coins"),
        ("/setalert BTC 45000", "Set price alert for BTC at $45,000"),
        ("/alerts", "View your active alerts"),
        ("/dailyon", "Enable daily market summaries"),
        ("/dailyoff", "Disable daily market summaries"),
        ("/status", "Check your current settings"),
        ("/testsummary", "Send a test market summary")
    ]
    
    for command, description in commands:
        print(f"  {command:<25} - {description}")
    
    print()

def main():
    """Run the complete demo"""
    print("🚀 Telegram Crypto Bot Demo")
    print("=" * 50)
    print("This demo shows the bot functionality without requiring")
    print("a live Telegram connection.\n")
    
    demo_database_operations()
    demo_price_monitoring()
    demo_daily_scheduler()
    demo_command_examples()
    
    print("✅ Demo completed!")
    print("\nTo use the bot with Telegram:")
    print("1. Get a bot token from @BotFather")
    print("2. Set the token in config.py or environment variable")
    print("3. Run: python bot.py")

if __name__ == '__main__':
    main()