# Economic Data Discord Bot

A Python-based Discord bot that delivers real-time and scheduled economic/forex news alerts to your Discord server. Designed for trading communities, it supports custom filters, timezone handling, and role tagging for high-impact news events.

## Features
- Automated daily and real-time alerts for key economic news
- Immersive panel-based alerts for imporved user experience
- Customizable currency and impact filters
- Timezone-aware scheduling (EST by default)
- Discord Role tagging for important alerts
- Manual commands for news summaries, settings, and more

## Setup
1. Clone this repo and install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Fill out `config.json` with your Discord bot credentials and channel/role IDs.
3. Place your monthly news CSVs in the `news/` folder.
4. Run the bot:
   ```bash
   python3 bot.py
   ```

## Commands
- `!news` — Show today's filtered news
- `!alerts:USD` — Enable real-time alerts for USD news
- `!alerts:` — Show today's real-time alert schedule
- `!currencies:USD,EUR` — Set news filter currencies
- `!impacts:red,orange` — Set news filter impacts
- `!alertrole:ROLE_ID` — Set which role to tag in alerts

## Credits
This project was built using foundational code from Fizah Khalid, licensed under the MIT License. 

## License
MIT
