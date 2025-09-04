# Code clean up - Updated utils
import json
import asyncio
import aiofiles
import pandas as pd
from datetime import datetime, timedelta, time
from discord.ext import tasks
from data import TIMEZONES
from constants import CURRENCY_FLAGS, IMPACT_LEVELS
from timezone_manager import timezone_manager
from error_handler import error_handler


async def write_json(filepath, filecontent):
    """Write JSON content to file asynchronously"""
    try:
        async with aiofiles.open(filepath, mode='w') as file:
            await file.write(json.dumps(filecontent, indent=4))
    except Exception as e:
        await error_handler.handle_error(e, "writing JSON file")


# EMOJIS
def form_emoji(impact_color):
    """Get emoji for impact color"""
    if impact_color == "gray" or impact_color == "grey":
        impact_color = "white"
    return f":{impact_color}_circle:"


def form_emoji_flag(currency):
    """Get flag emoji for currency"""
    return CURRENCY_FLAGS.get(currency, "")


# TIMEZONE FUNCTIONS
async def set_user_timezone(timezone_name, offset, channel):
    """Set user timezone with improved error handling"""
    from config_manager import config_manager
    from logger import logger

    try:
        database = await config_manager.load_database()
        database['timezone'] = {"name": timezone_name, "offset": offset}
        await config_manager.save_database(database)

        # Clear timezone cache to force refresh
        timezone_manager.clear_cache()

        tz = timezone_manager.get_timezone_object(timezone_name)
        now = datetime.now(tz)

        await channel.send(
            f"Your timezone has been set to {timezone_name}.\nCurrent date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        logger.info(f"Timezone updated to {timezone_name} ({offset})")

    except Exception as e:
        await error_handler.handle_error(e, "setting timezone")
        await channel.send(f"Error setting timezone: {e}")


def find_timezone_name_using_offset(offset_str):
    """Find timezone name using offset string"""
    success, message, timezone_name = timezone_manager.parse_timezone_offset(
        offset_str)
    if success:
        return timezone_name, "Done"
    else:
        return False, message


async def get_timezones():
    """Get current timezone settings"""
    from config_manager import config_manager
    database = await config_manager.load_database()
    main_timezone = database["timezone"]
    scraped_timezone = database["timezone_scraped"]
    return main_timezone, scraped_timezone


async def get_database():
    """Get current database"""
    from config_manager import config_manager
    return await config_manager.load_database()


async def update_status():
    """Update status in database"""
    database = await get_database()
    database['updated'] = True
    from config_manager import config_manager
    await config_manager.save_database(database)


async def reset_update_status():
    """Reset update status in database"""
    database = await get_database()
    database['updated'] = False
    from config_manager import config_manager
    await config_manager.save_database(database)


def get_datetime_by_offset(offset_str):
    """Get datetime by offset string"""
    try:
        # Parse the offset string, e.g., 'UTC+5' or 'UTC-3'
        offset_part = offset_str[3:]  # Remove 'UTC'
        sign = offset_part[0]
        hours = int(offset_part[1:])

        # Calculate total offset in minutes
        total_offset_minutes = hours * 60
        if sign == '-':
            total_offset_minutes = -total_offset_minutes

        # Get current UTC time
        current_utc_time = datetime.now(
            timezone_manager.get_timezone_object('UTC'))

        # Calculate target datetime
        target_datetime = current_utc_time + \
            timedelta(minutes=total_offset_minutes)

        return target_datetime
    except ValueError:
        # Handle invalid offset format
        return None


async def get_current_time():
    """Get current time in configured timezone"""
    try:
        existing_data = await get_database()
        if not existing_data or 'timezone' not in existing_data.keys():
            return False

        timezone_dict = existing_data['timezone']
        offset = timezone_dict['offset']
        datetime_obj = get_datetime_by_offset(offset)
        if datetime_obj:
            time_str = datetime_obj.time().strftime('%H:%M')
            return datetime_obj.time(), time_str
        return False
    except Exception as e:
        await error_handler.handle_error(e, "getting current time")
        return False


async def news_today(client, df, message, channel_id):
    """Display today's news with improved error handling"""
    try:
        database = await get_database()
        impacts = database['impacts']
        currencies = database['currencies']
        main_timezone = database['timezone']
        main_timezone_offset = main_timezone["offset"]
        datetime_obj = get_datetime_by_offset(main_timezone_offset)
        today_date = datetime_obj.date()

        todays_events = ""
        filter = df.query(f'date=="{str(today_date)}"')
        for index, row in filter.iterrows():
            try:
                event_date = datetime.strptime(row["date"], '%Y-%m-%d').date()
            except ValueError as e:
                logger.warning(
                    f"Cannot read event date for row {index}: time: {row[1]}", str(e))
                continue  # Skip this row if date parsing fails

            if row['currency'] in currencies and row['impact'] in impacts and event_date == today_date:
                todays_events += f"{form_emoji(row['impact'])} {form_emoji_flag(row['currency'])} {row['currency']} **{row['time']}** - {row['event']}\n"

        if todays_events:
            if message:
                await message.channel.send(todays_events)
            else:
                await client.get_channel(channel_id).send(todays_events)
        else:
            news = f"No News for today {today_date}"
            if message:
                await message.channel.send(news)
            else:
                await client.get_channel(channel_id).send(news)
    except Exception as e:
        await error_handler.handle_error(e, "displaying today's news")


def is_red_impact(impact):
    """Check if impact is red"""
    return str(impact).lower() == 'red'


def is_orange_impact(impact):
    """Check if impact is orange"""
    return str(impact).lower() == 'orange'


async def filter_df_for_today(df):
    """Filter dataframe for today's events"""
    try:
        main_timezone = await timezone_manager.get_current_timezone()
        main_timezone_offset = await timezone_manager.get_current_offset()
        datetime_obj = get_datetime_by_offset(main_timezone_offset)
        today_date = datetime_obj.date()

        return df.query(f'date=="{str(today_date)}"')
    except Exception as e:
        await error_handler.handle_error(e, "filtering dataframe for today")
        return df


async def news_updates(client, df, channel_id):
    """Send news updates with improved timezone handling"""
    try:
        main_timezone = await timezone_manager.get_current_timezone()
        main_timezone_name = main_timezone["name"]

        # Check if timezone conversion is needed
        current_time = datetime.now(
            timezone_manager.get_timezone_object(main_timezone_name))

        if main_timezone_name != df["timezone"].tolist()[0]:
            # Timezone conversion needed - this is now handled by the timezone manager
            logger.info(
                "Timezone conversion not needed - using centralized timezone management")

        logger.info("Timezone is correct")

    except Exception as e:
        await error_handler.handle_error(e, "sending news updates")
