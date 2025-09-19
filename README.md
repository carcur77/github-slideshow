# Your GitHub Learning Lab Repository for Introducing GitHub

Welcome to **your** repository for your GitHub Learning Lab course. This repository will be used during the different activities that I will be guiding you through. See a word you don't understand? We've included an emoji 📖 next to some key terms. Click on it to see its definition.

Oh! I haven't introduced myself...

I'm the GitHub Learning Lab bot and I'm here to help guide you in your journey to learn and master the various topics covered in this course. I will be using Issue and Pull Request comments to communicate with you. In fact, I already added an issue for you to check out.

![issue tab](https://lab.github.com/public/images/issue_tab.png)

I'll meet you over there, can't wait to get started!

This course is using the :sparkles: open source project [reveal.js](https://github.com/hakimel/reveal.js/). In some cases we’ve made changes to the history so it would behave during class, so head to the original project repo to learn more about the cool people behind this project.
---

## 🤖 Telegram Crypto Bot

This repository also includes a **Telegram Crypto Bot** with advanced user customization features for cryptocurrency trading and monitoring.

### Features

- **Favorite Coins**: Set and manage your favorite cryptocurrencies
- **Price Alerts**: Get notified when coins reach target prices
- **Daily Market Summaries**: Receive personalized daily reports
- **Trading Signals**: Get trading recommendations for your portfolio

### Quick Start

1. **Install dependencies**:
   ```bash
   ./install.sh
   ```

2. **Set up your bot**:
   - Get a token from [@BotFather](https://t.me/botfather)
   - Set your token: `export TELEGRAM_BOT_TOKEN='your_token'`

3. **Run the bot**:
   ```bash
   python3 bot.py
   ```

4. **Test the functionality**:
   ```bash
   python3 demo.py
   ```

### Bot Commands

- `/setfavorites BTC ETH XRP` - Set your favorite coins
- `/signals favorites` - Get signals for your favorites
- `/setalert BTC 45000` - Set price alerts
- `/dailyon` - Enable daily summaries
- `/status` - Check your settings

For detailed documentation, see [BOT_README.md](BOT_README.md)
