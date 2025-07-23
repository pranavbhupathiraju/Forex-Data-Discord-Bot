import json
import requests
import asyncio
import aiofiles
import pytz
import pandas as pd
import os
from datetime import datetime
from utils import (
    find_timezone_name_using_offset,
    set_user_timezone,
    get_database,
    form_emoji,
    write_json,
    get_datetime_by_offset)

# SEND RANDOM QUOTE


async def send_qoute(message):
    """Send a random quote (keeping original function name for compatibility)"""
    from logger import logger

    try:
        response = requests.get('https://zenquotes.io/api/random', timeout=10)
        response.raise_for_status()

        json_data = response.json()
        if json_data and len(json_data) > 0:
            quote = json_data[0]['q'] + " - " + json_data[0]['a']
            await message.channel.send(quote)
            logger.debug("Quote sent successfully")
            return quote
        else:
            await message.channel.send("Sorry, couldn't fetch a quote right now.")
            return None

    except requests.RequestException as e:
        logger.error(f"Error fetching quote: {e}")
        await message.channel.send("Sorry, couldn't fetch a quote right now.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in send_qoute: {e}", exc_info=True)
        await message.channel.send("An error occurred while fetching the quote.")
        return None


async def handle_timezone_message(client, message):
    select_timezone = "Please select timezone from UTC-12 to UTC+14"
    await message.channel.send(select_timezone)

    def check(m):
        return m.author == message.author and m.channel == message.channel and m.content.strip().startswith('UTC')
    try:
        reply = await client.wait_for('message', timeout=60.0, check=check)

    except asyncio.TimeoutError:
        await message.channel.send("Sorry, you took too long to reply.")
    else:
        timezone_name, message_for_timezone = find_timezone_name_using_offset(
            reply.content)
        if not timezone_name:
            await set_user_timezone(timezone_name, reply.content, message.channel)
        else:
            await message.channel.send(message_for_timezone)


async def state(message):
    """Show current bot state and configuration"""
    from config_manager import config_manager
    from alert_manager import alert_manager
    from logger import logger

    try:
        database = await config_manager.load_database()
        config = await config_manager.load_config()

        message_str = "**🤖 Bot Status**\n\n"

        # Filter settings
        message_str += "**📊 FILTERS**\n"
        message_str += f"**Currencies:** `{' | '.join(database.get('currencies', []))}`\n"
        message_str += f"**Impacts:** `{' | '.join(database.get('impacts', []))}`\n\n"

        # Daily updates
        daily_update = database.get('daily_update', {})
        message_str += "**📅 DAILY UPDATES**\n"
        message_str += f"**Status:** `{'✅ Updated' if database.get('updated', False) else '❌ Pending'}`\n"
        message_str += f"**Time:** `{daily_update.get('hour', '7')}:{daily_update.get('minute', '0').zfill(2)}`\n\n"

        # Alert settings
        message_str += "**🚨 ALERTS**\n"
        alert_currencies = database.get('alert_currencies', [])
        message_str += f"**Alert Currencies:** `{' | '.join(alert_currencies) if alert_currencies else 'None'}`\n"
        message_str += f"**Active Alerts:** `{alert_manager.get_alert_count()}`\n"
        message_str += f"**Timezone:** `{database.get('timezone', {}).get('offset', 'UTC-5')}`\n\n"

        # System info
        message_str += "**⚙️ SYSTEM**\n"
        message_str += f"**Mode:** `{'🧪 Testing' if config.get('testing', False) else '🚀 Production'}`\n"

        await message.channel.send(message_str)
        logger.info(f"State information sent to {message.author.name}")

    except Exception as e:
        logger.error(f"Error getting state: {e}", exc_info=True)
        await message.channel.send("Error retrieving bot state.")


async def handle_datetime_command(message):
    existing_data = await get_database()
    if not existing_data:
        await message.channel.send(f"Database is empty !")
        return
    data = existing_data

    if 'timezone' in data.keys():
        timezone_dict = data['timezone']
        offset = timezone_dict['offset']

        dt = get_datetime_by_offset(offset)
        if dt:
            time_str = dt.time().strftime('%H:%M')
            tz = pytz.timezone(timezone_dict['name'])
            now = datetime.now(tz)
            timezoneOffset = timezone_dict['offset']
        else:
            now = datetime.now()
            time_str = now.strftime('%H:%M')
            timezoneOffset = None
    else:
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        timezoneOffset = None
    # send the confirmation message with the current date and time
    await message.channel.send(f"Date: `{now.strftime('%d-%m-%Y')}`\nTime: `{time_str}`\nTimezone: `{timezoneOffset}`")


async def set_allowed_currencies(message):
    msg = message.content
    database = await get_database()
    currencies = msg.split(":")[-1]
    if currencies.lower().strip() == "all":
        filtered = database['all_currencies']
    else:
        filtered = []
        currencies = currencies.split(",")
        for currency in currencies:
            if currency in database['all_currencies']:
                filtered.append(currency)

    database['currencies'] = filtered
    await write_json('database.json', database)
    await message.channel.send(f"Updated Currencies Filter to Include these currencies: {filtered}")


async def set_allowed_impacts(message):
    impacts = message.content.split("impacts:")[-1].split(",")
    print("Impacts: ", impacts)
    if impacts != ['']:
        database = await get_database()
        database['impacts'] = impacts
        await write_json('database.json', database)
        await message.channel.send(f"Updated Impacts Filter to Include these impacts: {'-'.join([form_emoji(impact) for impact in impacts])}")
    else:
        await message.channel.send("You are trying to set empty impacts, it cannot be empty")


async def set_daily_update_time(message):
    update_time = message.content.split(":")

    if len(update_time) == 3:
        hour = update_time[-2].zfill(2)  # Ensure two-digit hour format
        minute = update_time[-1].zfill(2)  # Ensure two-digit minute format

        # Check if hour and minute are valid integers
        if hour.isdigit() and minute.isdigit():
            hour = int(hour)
            minute = int(minute)

            # Check if hour and minute are within valid ranges (0-23 for hour, 0-59 for minute)
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                database = await get_database()
                database["daily_update"]["hour"] = str(hour)
                database["daily_update"]["minute"] = str(minute)
                await write_json('database.json', database)
                await message.channel.send(f"News Daily Update Time changed to {hour:02d}:{minute:02d}")
            else:
                await message.channel.send("Invalid hour or minute value. Hour should be between 0 and 23, and minute should be between 0 and 59.")
        else:
            await message.channel.send("Invalid hour or minute format. Please use two-digit format, e.g., !daily:03:03")
    else:
        await message.channel.send("Invalid command format. Please use !daily:hh:mm")


async def today_news(message):
    """Show today's news events"""
    from csv_manager import csv_manager
    from logger import logger

    try:
        # Get today's events
        events = csv_manager.get_today_events(timezone='US/Eastern')

        if not events:
            await message.channel.send("No news events scheduled for today.")
            return

        # Format message
        msg = "**Today's Forex News Events:**\n"
        for event in events:
            time_str = event.get('time', 'Unknown')
            currency = event.get('currency', 'Unknown')
            impact = event.get('impact', 'unknown').capitalize()
            event_name = event.get('event', 'Unknown Event')

            msg += f"- {time_str} | {currency} | {impact} | {event_name}\n"

        # Split message if too long
        if len(msg) > 2000:
            chunks = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
            for chunk in chunks:
                await message.channel.send(chunk)
        else:
            await message.channel.send(msg)

        logger.info(f"Today's news sent to {message.author.name}")

    except Exception as e:
        logger.error(f"Error sending today's news: {e}", exc_info=True)
        await message.channel.send("Error retrieving today's news events.")


async def set_alert_currencies(message):
    msg = message.content
    database = await get_database()
    if ':' in msg:
        currencies = msg.split(':', 1)[-1]
        import pandas as pd
        import os
        from datetime import datetime
        import pytz
        est = pytz.timezone('US/Eastern')
        today = datetime.now(est).strftime('%d/%m/%Y')
        news_dir = os.path.join(os.path.dirname(__file__), 'news')
        csv_files = [f for f in os.listdir(news_dir) if f.endswith('.csv')]
        if not csv_files:
            await message.channel.send("No news data available.")
            return
        latest_csv = max(csv_files, key=lambda f: os.path.getmtime(
            os.path.join(news_dir, f)))
        df = pd.read_csv(os.path.join(news_dir, latest_csv))
        # Debug prints removed for production
        alert_currencies = [c.strip().upper()
                            for c in currencies.split(',') if c.strip()]
        # Robust filtering
        filtered_events = df[
            (df['date'].astype(str).str.strip() == today) &
            (df['impact'].astype(str).str.lower().str.strip().isin(['red', 'orange'])) &
            (df['currency'].astype(str).str.upper(
            ).str.strip().isin(alert_currencies))
        ]
        if currencies.strip() == '':
            # Show all red/orange events for today, regardless of alert_currencies
            today_events = df[
                (df['date'].astype(str).str.strip() == today) &
                (df['impact'].astype(str).str.lower(
                ).str.strip().isin(['red', 'orange']))
            ]
            if today_events.empty:
                await message.channel.send("No real-time alerts scheduled for today.")
                return
            msg_str = "**Today's Real-Time Alert News Events:**\n"
            for _, row in today_events.iterrows():
                msg_str += f"- {row['time']} | {row['currency']} | {row['impact'].capitalize()} | {row['event']}\n"
            await message.channel.send(msg_str)
            return
        # Otherwise, update alert_currencies and show only those
        database['alert_currencies'] = alert_currencies
        await write_json('database.json', database)
        if filtered_events.empty:
            await message.channel.send(
                f"Real-time alerts enabled for: {', '.join(alert_currencies)}\nNo real-time alerts scheduled for today for the selected currencies."
            )
        else:
            msg_str = f"Real-time alerts enabled for: {', '.join(alert_currencies)}\n"
            msg_str += "**Today's Real-Time Alert News Events (for selected currencies):**\n"
            for _, row in filtered_events.iterrows():
                msg_str += f"- {row['time']} | {row['currency']} | {row['impact'].capitalize()} | {row['event']}\n"
            await message.channel.send(msg_str)
    else:
        await message.channel.send("Please use the format !alerts:USD,EUR or !alerts: to show today's alert schedule.")
