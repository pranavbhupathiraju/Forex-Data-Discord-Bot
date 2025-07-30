# Economic Data Discord Bot

A robust Python-based Discord bot that delivers real-time and scheduled economic/forex news alerts to your Discord server. Designed for trading communities with enterprise-grade reliability, comprehensive logging, and advanced alert management.

## Features
- **Real-time Alerts**: 5-minute warnings and instant release notifications
- **Smart Filtering**: Customizable currency and impact level filters
- **Timezone Support**: Automatic timezone conversion and scheduling
- **Role Tagging**: Configurable Discord role mentions for alerts
- **Memory Management**: Automatic cleanup to prevent memory leaks
- **Comprehensive Logging**: Detailed logs with rotation and error tracking
- **Robust Error Handling**: Graceful degradation and recovery
- **Modular Architecture**: Clean, maintainable code structure
- **Configuration Management**: Centralized config with validation
- **CSV Caching**: Optimized data loading with intelligent caching

## Quick Setup

### Prerequisites
- Python 3.8 or higher
- Discord bot token and permissions
- Economic news CSV data files(run scraper)

### Installation
1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd economic-discord-bot
   pip install -r requirements.txt
   ```

2. **Configure the bot:**
   your config.json should have as follows:

{
 "public_key":"Your Public Key",
 "application_id":"Your Application ID",
 "client_id":"Your Client ID",
 "client_secret":"Your Client Secret",
 "token": "Your token",
 "news_channel_id": channel_id,
 "operations_channel_id": channel_id,
 "test_news_channel_id": channel_id,
 "test_operations_channel_id": channel_id,
 "alert_role_id": role_id,
 "testing": true,
 "authorized_users": ["discord_username"]
}


3. **Add news data:**
   ```bash
   # Place your monthly CSV files in the news/ directory
   # Format: MonthName_news.csv (e.g., July_news.csv)
   ```



## Commands

### News & Information
- `!news` — Show today's filtered news events
- `!today` — Alternative command for today's news
- `!state` — Display current bot configuration and status

### Configuration
- `!currencies:USD,EUR,GBP` — Set currency filters (or `all` for all currencies)
- `!impacts:red,orange` — Set impact level filters
- `!timezone` — Interactive timezone setup
- `!datetime` — Show current date/time in bot's timezone

### Alerts
- `!alerts:USD,EUR` — Enable real-time alerts for specific currencies
- `!alerts:` — Show today's alert schedule
- `!alertrole:ROLE_ID` — Set Discord role to mention in alerts
- `!daily:HH:MM` — Set daily news summary time

### System
- `!ping` — Test bot responsiveness


## Monitoring & Logs

- Logs are automatically created in the `logs/` directory
- Daily log rotation with detailed error tracking
- Performance metrics and alert statistics
- Configurable log levels for debugging

## Troubleshooting

### Common Issues
1. **Bot won't start**: Check `config.json` format and required fields
2. **No alerts**: Verify `alert_currencies` are set and CSV data exists
3. **Permission errors**: Ensure bot has proper Discord permissions
4. **Memory issues**: Alert cleanup runs automatically every 24 hours

### Debug Mode
Set logging level to DEBUG in `logger.py` for detailed troubleshooting.

## 🚀 Recent Improvements

- ✅ Fixed memory leaks in alert system
- ✅ Added comprehensive error handling
- ✅ Implemented modular architecture
- ✅ Added configuration validation
- ✅ Optimized CSV processing with caching
- ✅ Enhanced logging and monitoring
- ✅ Fixed timezone conversion redundancy
- ✅ Improved command parsing system

## 📝 Credits
This project was built using foundational code from Fizah Khalid, licensed under the MIT License.
Enhanced and refactored for production use with enterprise-grade reliability.

## 📄 License
MIT License - See LICENSE file for details
