Here is the full revised README for your Economic Data Discord Bot, incorporating a more human and engaging tone while keeping the important technical details and formatting.

Economic Data Discord Bot: Your Server's Personal Financial Analyst
I built this bot to solve a problem for trading communities: getting timely, reliable, and relevant economic news directly into Discord. This is more than just a data dump; it's a robust and reliable system for anyone who needs to stay on top of the financial markets.

Key Features
Real-time Alerts: Get instant notifications and a 5-minute heads-up for critical news releases.

Smart Filtering: Don't get overwhelmed. You can filter alerts by specific currencies and impact levels.

Timezone Support: The bot automatically converts and schedules alerts, so you're always on time, no matter where your community is.

Discord Integration: I included configurable role tagging, so you can mention the right people for the right alerts.

Robust & Reliable: I focused on building a bot with strong error handling and automated memory management to ensure it's always running smoothly.

Clean Architecture: The code is modular and easy to maintain, and I've implemented intelligent caching for optimized data loading.

Prerequisites
Python 3.8 or higher

Discord bot token and permissions

Economic news CSV data files (the scraper generates these for you)

Getting Started
Clone the repository and install dependencies:

Bash

git clone <repository-url>
cd economic-discord-bot
pip install -r requirements.txt
Configure the bot:
Make sure your config.json file is set up with all the necessary keys and IDs:

JSON

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

***To ddd news data:***
Place your monthly CSV files in the news/ directory


**Available Commands**
!news — Show today's filtered news events
!today — Alternative command for today's news
!state — Display the bot's current configuration and status
!currencies:USD,EUR,GBP — Set currency filters (or all for all currencies)
!impacts:red,orange — Set impact level filters
!timezone — Interactive timezone setup
!datetime — Show current date/time in bot's timezone
!alerts:USD,EUR — Enable real-time alerts for specific currencies
!alerts: — Show today's alert schedule
!alertrole:ROLE_ID — Set the Discord role to mention in alerts
!daily:HH:MM — Set a daily news summary time
!ping — Test bot responsiveness


**Common Issues**

1. Bot won't start: Double-check your config.json format and all required fields.
2. No alerts: Make sure your alert_currencies are set and the news CSV data is in place.
3. Permission errors: Ensure the bot has the necessary permissions in your Discord server.
4. Memory issues: The bot automatically cleans up alerts every 24 hours to prevent memory leaks.

**Recent Improvements**
- Squashed some memory leaks in the alert system.
- Added comprehensive error handling for smoother operation.
- Built a modular architecture for easy maintenance.
- Implemented configuration validation to prevent common setup errors.
- Optimized CSV processing with a new caching system.
- Fixed a timezone conversion bug that caused redundancy.
- Improved the command parsing system for better user experience.

Credits
This project was built upon foundational code by Fizah Khalid, licensed under the MIT License. I've enhanced and refactored it for production-grade reliability and use.

License
MIT License - See the LICENSE file for details.
