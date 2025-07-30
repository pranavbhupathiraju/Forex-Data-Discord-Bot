import json
import requests
import asyncio
import aiofiles
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
from constants import DEFAULT_TIMEOUT, CURRENCY_FLAGS
from timezone_manager import timezone_manager
from error_handler import error_handler


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
        await error_handler.handle_error(e, "fetching quote")
        await message.channel.send("Sorry, couldn't fetch a quote right now.")
        return None
    except Exception as e:
        await error_handler.handle_error(e, "sending quote")
        await message.channel.send("An error occurred while fetching the quote.")
        return None


async def handle_timezone_message(client, message):
    """Handle timezone setup with improved error handling"""
    select_timezone = "Please select timezone from UTC-12 to UTC+14"
    await message.channel.send(select_timezone)

    def check(m):
        return m.author == message.author and m.channel == message.channel and m.content.strip().startswith('UTC')

    try:
        reply = await client.wait_for('message', timeout=DEFAULT_TIMEOUT, check=check)

    except asyncio.TimeoutError:
        await message.channel.send("Sorry, you took too long to reply.")
    else:
        timezone_name, message_for_timezone = find_timezone_name_using_offset(
            reply.content)
        if timezone_name:
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
        hour = daily_update.get('hour', '7')
        minute = str(daily_update.get('minute', '0')).zfill(2)
        message_str += f"**Time:** `{hour}:{minute}`\n\n"

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

    except Exception as e:
        await error_handler.handle_error(e, "displaying bot state")
        await message.channel.send("Error retrieving bot state.")


async def handle_datetime_command(message):
    """Handle datetime command with improved timezone handling"""
    try:
        data = await get_database()
        if 'timezone' in data.keys():
            timezone_dict = data['timezone']
            timezone_name = timezone_dict['name']
            offset = timezone_dict['offset']

            tz = timezone_manager.get_timezone_object(timezone_name)
            now = datetime.now(tz)

            await message.channel.send(
                f"**Current Date/Time:**\n"
                f"**Timezone:** {timezone_name} ({offset})\n"
                f"**Date:** {now.strftime('%Y-%m-%d')}\n"
                f"**Time:** {now.strftime('%H:%M:%S')}"
            )
        else:
            await message.channel.send("No timezone configured. Use `!timezone` to set one.")

    except Exception as e:
        await error_handler.handle_error(e, "handling datetime command")
        await message.channel.send("Error getting current datetime.")


async def set_allowed_currencies(message):
    """Set allowed currencies with improved validation"""
    try:
        content = message.content.replace('!currencies:', '').strip()
        if content.lower() == 'all':
            currencies = ['USD', 'EUR', 'JPY', 'GBP',
                          'AUD', 'CAD', 'CHF', 'NZD', 'CNY']
        else:
            currencies = [c.strip().upper()
                          for c in content.split(',') if c.strip()]

        if not currencies:
            await message.channel.send("Please specify currencies or 'all'")
            return

        database = await get_database()
        database['currencies'] = currencies
        from config_manager import config_manager
        await config_manager.save_database(database)

        await message.channel.send(f"Currencies set to: {', '.join(currencies)}")

    except Exception as e:
        await error_handler.handle_error(e, "setting currencies")
        await message.channel.send("Error setting currencies.")


async def set_allowed_impacts(message):
    """Set allowed impacts with improved validation"""
    try:
        content = message.content.replace('!impacts:', '').strip()
        impacts = [i.strip().lower() for i in content.split(',') if i.strip()]

        if not impacts:
            await message.channel.send("Please specify impact levels")
            return

        database = await get_database()
        database['impacts'] = impacts
        from config_manager import config_manager
        await config_manager.save_database(database)

        await message.channel.send(f"Impacts set to: {', '.join(impacts)}")

    except Exception as e:
        await error_handler.handle_error(e, "setting impacts")
        await message.channel.send("Error setting impacts.")


async def set_daily_update_time(message):
    """Set daily update time with improved validation"""
    try:
        content = message.content.replace('!daily:', '').strip()
        time_parts = content.split(':')

        if len(time_parts) != 2:
            await message.channel.send("Please use format HH:MM (e.g., 07:00)")
            return

        try:
            hour = int(time_parts[0])
            minute = int(time_parts[1])
        except ValueError:
            await message.channel.send("Invalid time format. Use HH:MM")
            return

        # Check if hour and minute are within valid ranges (0-23 for hour, 0-59 for minute)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            database = await get_database()
            database['daily_update'] = {
                'hour': str(hour),
                'minute': str(minute)
            }
            from config_manager import config_manager
            await config_manager.save_database(database)

            await message.channel.send(f"Daily update time set to {hour:02d}:{minute:02d}")
        else:
            await message.channel.send("Invalid time. Hour should be between 0 and 23, and minute should be between 0 and 59.")

    except Exception as e:
        await error_handler.handle_error(e, "setting daily update time")
        await message.channel.send("Error setting daily update time.")


async def today_news(message):
    """Display today's news with improved error handling"""
    try:
        from csv_manager import csv_manager

        # Get today's events using the centralized CSV manager
        events = await csv_manager.get_today_events()

        if not events:
            await message.channel.send("No news events found for today.")
            return

        # Format events for display
        news_text = ""
        for event in events:
            currency = event.get('currency', 'Unknown')
            impact = event.get('impact', 'gray')
            time = event.get('time', 'Unknown')
            event_name = event.get('event', 'Unknown Event')

            event_line = f"{form_emoji(impact)} {CURRENCY_FLAGS.get(currency, '')} {currency} **{time}** - {event_name}\n"

            # Check if adding this line would exceed Discord's limit
            if len(news_text + event_line) > 1900:  # Leave some buffer
                # Send current chunk and start new one
                if news_text:
                    await message.channel.send(news_text)
                news_text = event_line
            else:
                news_text += event_line

        # Send any remaining text
        if news_text:
            await message.channel.send(news_text)
        else:
            await message.channel.send("No news events found for today.")

    except Exception as e:
        await error_handler.handle_error(e, "displaying today's news")
        await message.channel.send("Error retrieving today's news.")


async def set_alert_currencies(message):
    """Set alert currencies with improved validation"""
    try:
        content = message.content.replace('!alerts:', '').strip()

        if not content:
            # Show current alert schedule
            database = await get_database()
            alert_currencies = database.get('alert_currencies', [])

            # Get today's events for alert currencies
            from csv_manager import csv_manager
            events = await csv_manager.get_high_impact_events()

            if alert_currencies:
                message_str = f"**Current Alert Currencies:** {', '.join(alert_currencies)}\n\n"

                # Filter events for alert currencies
                alert_events = [e for e in events if e.get(
                    'currency') in alert_currencies]

                if alert_events:
                    message_str += "**Today's Alert Schedule:**\n"
                    for event in alert_events[:10]:  # Show first 10 events
                        time = event.get('time', 'Unknown')
                        currency = event.get('currency', 'Unknown')
                        impact = event.get('impact', 'gray')
                        event_name = event.get('event', 'Unknown Event')
                        message_str += f"{form_emoji(impact)} {CURRENCY_FLAGS.get(currency, '')} {currency} **{time}** - {event_name}\n"

                    if len(alert_events) > 10:
                        message_str += f"\n... and {len(alert_events) - 10} more events"
                else:
                    message_str += "No alert events scheduled for today for the selected currencies."
            else:
                message_str = "No alert currencies set. Use `!alerts:USD,EUR` to set them."

            await message.channel.send(message_str)
            return

        if content.lower() == 'all':
            currencies = ['USD', 'EUR', 'JPY', 'GBP',
                          'AUD', 'CAD', 'CHF', 'NZD', 'CNY']
        else:
            currencies = [c.strip().upper()
                          for c in content.split(',') if c.strip()]

        if not currencies:
            await message.channel.send("Please specify currencies or 'all'")
            return

        database = await get_database()
        database['alert_currencies'] = currencies
        from config_manager import config_manager
        await config_manager.save_database(database)

        await message.channel.send(f"Alert currencies set to: {', '.join(currencies)}")

    except Exception as e:
        await error_handler.handle_error(e, "setting alert currencies")
        await message.channel.send("Error setting alert currencies.")


async def refresh_data(message):
    """Force refresh CSV data and clear caches"""
    try:
        from csv_manager import csv_manager
        from cache_manager import cache_manager

        # Clear all caches
        cache_manager.clear()
        csv_manager.force_refresh_cache()

        # Test loading fresh data
        events = await csv_manager.get_today_events(force_refresh=True)

        await message.channel.send(f"✅ Cache refreshed! Found {len(events)} events for today.")

    except Exception as e:
        await error_handler.handle_error(e, "refreshing data")
        await message.channel.send("Error refreshing data.")


async def debug_time(message):
    """Debug current time and event times"""
    try:
        from csv_manager import csv_manager
        from timezone_manager import timezone_manager
        import pandas as pd

        # Get current time
        now = await timezone_manager.get_current_datetime()
        current_timezone = await timezone_manager.get_current_timezone()

        # Get raw CSV data
        df = csv_manager.load_latest_csv(force_refresh=True)

        debug_msg = f"**🔍 Debug Info**\n\n"
        debug_msg += f"**Current Time:** {now.strftime('%H:%M:%S')}\n"
        debug_msg += f"**Timezone:** {current_timezone}\n"
        debug_msg += f"**Today's Date:** {now.strftime('%d/%m/%Y')}\n\n"

        if df is not None:
            debug_msg += f"**CSV File Info:**\n"
            debug_msg += f"• Total rows: {len(df)}\n"
            debug_msg += f"• Columns: {list(df.columns)}\n\n"

            # Show today's events from raw CSV
            today_str = now.strftime('%d/%m/%Y')
            today_events = df[df['date'].astype(str).str.strip() == today_str]
            debug_msg += f"**Today's Events (Raw CSV):**\n"
            debug_msg += f"• Found {len(today_events)} events for {today_str}\n\n"

            for idx, row in today_events.head(10).iterrows():
                time_val = row.get('time', 'Unknown')
                date_val = row.get('date', 'Unknown')
                event_val = row.get('event', 'Unknown')
                currency_val = row.get('currency', 'Unknown')
                impact_val = row.get('impact', 'Unknown')

                debug_msg += f"• Time: `{time_val}` | Date: `{date_val}` | {currency_val} | {impact_val} | {event_val}\n"

        # Get filtered high impact events
        events = await csv_manager.get_high_impact_events()
        debug_msg += f"\n**High Impact Events (Filtered):**\n"
        for event in events[:10]:
            time_str = event.get('time', 'Unknown')
            event_name = event.get('event', 'Unknown')
            currency = event.get('currency', 'Unknown')
            impact = event.get('impact', 'Unknown')
            debug_msg += f"• {time_str} - {currency} ({impact}) - {event_name}\n"

        await message.channel.send(debug_msg)

    except Exception as e:
        await error_handler.handle_error(e, "debug time")
        await message.channel.send(f"Error in debug command: {str(e)}")
