# Project Details

I built this bot to solve a problem for trading communities, getting timely, reliable, and relevant economic news directly into Discord. I incorporated enhanced visuals as well as comprehensive time logging to ensure production-ready bot. 



## Features

- **Real-time Alerts**: 5-minute warnings and instant release notifications

- **Smart Filtering**: Customizable currency and impact level filters

- **Timezone Support**: Automatic timezone conversion and scheduling

- **Role Tagging**: Configurable Discord role mentions for alerts

- **Memory Management**: Automatic cleanup to prevent memory leakage

- **Configuration Management**: Centralized config with validation

- **CSV Caching**: Optimized data loading with intelligent caching




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


- `!news` — Show today's filtered news events

- `!today` — Alternative command for today's news

- `!state` — Display current bot configuration and status

- `!currencies:USD,EUR,GBP` — Set currency filters (or `all` for all currencies)

- `!impacts:red,orange` — Set impact level filters

- `!timezone` — Interactive timezone setup

- `!datetime` — Show current date/time in bot's timezone

- `!alerts:USD,EUR` — Enable real-time alerts for specific currencies

- `!alerts:` — Show today's alert schedule

- `!alertrole:ROLE_ID` — Set Discord role to mention in alerts

- `!daily:HH:MM` — Set daily news summary time

- `!ping` — Test bot responsiveness


## Troubleshooting



### Common Issues

1. **Bot won't start**: Check config.json format and required fields

2. **No alerts**: Verify alert_currencies are set and CSV data exists in the correct directory

3. **Permission errors**: Ensure bot has proper Discord permissions by checking channel settings

4. **Memory issues**: Alert cleanup runs automatically every 24 hours




## Credits

This project was built using foundational code from Fizah Khalid, and sources data from their scraper, licensed under the MIT License. 



## License

MIT License - See LICENSE file for details
