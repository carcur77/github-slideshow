# Telegram Crypto Bot

A Telegram bot for cryptocurrency trading with user customization features.

## Features

### 1. Favorite Coins
- Set favorite coins with `/setfavorites BTC ETH XRP`
- Get signals only for favorite coins using `/signals favorites`
- User-specific data storage

### 2. Price Alerts
- Set price alerts for specific coins with `/setalert BTC 30000`
- Bot notifies when price reaches threshold
- View active alerts with `/alerts`

### 3. Daily Market Summary
- Automatic daily market summaries at 9:00 AM UTC
- Enable with `/dailyon`, disable with `/dailyoff`
- Personalized summaries based on favorite coins

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Get a Telegram bot token from [@BotFather](https://t.me/botfather)

4. Set your bot token in `bot.py` or use environment variable:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token_here"
   ```

## Usage

Run the bot:
```bash
python bot.py
```

## Commands

- `/start` - Start the bot and see welcome message
- `/help` - Show all available commands
- `/setfavorites <coins>` - Set favorite coins (e.g., `/setfavorites BTC ETH XRP`)
- `/signals [favorites]` - Get trading signals for all coins or favorites only
- `/setalert <coin> <price>` - Set price alert (e.g., `/setalert BTC 45000`)
- `/alerts` - View your active alerts
- `/dailyon` - Enable daily market summaries
- `/dailyoff` - Disable daily market summaries
- `/status` - Check your current settings

## Technical Details

- **Storage**: SQLite database for user preferences, favorites, and alerts
- **APIs**: CoinGecko API for real-time price data (with fallback to mock data)
- **Scheduling**: Automatic daily summaries and price monitoring
- **Error Handling**: Comprehensive error handling and logging

## File Structure

- `bot.py` - Main bot application
- `config.py` - Configuration settings
- `price_monitor.py` - Price monitoring and alert system
- `daily_scheduler.py` - Daily summary scheduling
- `requirements.txt` - Python dependencies
- `user_preferences.db` - SQLite database (created automatically)

## Configuration

Edit `config.py` to customize:
- Daily summary time
- Price check intervals
- API endpoints
- Default coins
- Message templates

## Examples

```
/setfavorites BTC ETH ADA DOGE
/setalert BTC 45000
/signals favorites
/dailyon
```

## Error Handling

The bot includes comprehensive error handling for:
- API failures (falls back to mock data)
- Database errors
- Network issues
- Invalid user input

## Contributing

Feel free to submit issues and enhancement requests!