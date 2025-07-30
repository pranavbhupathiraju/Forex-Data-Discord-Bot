"""
Centralized timezone management for the Economic Data Discord Bot
Handles all timezone conversions and timezone-aware operations
"""

import pytz
from datetime import datetime
from typing import Optional, Tuple
from logger import logger
from constants import DEFAULT_TIMEZONE, DEFAULT_TIMEZONE_OFFSET


class TimezoneManager:
    """Centralized timezone management"""

    def __init__(self):
        self._current_timezone = None
        self._current_offset = None
        self._timezone_cache = {}

    async def get_current_timezone(self) -> str:
        """Get the currently configured timezone"""
        if not self._current_timezone:
            from config_manager import config_manager
            try:
                database = await config_manager.load_database()
                self._current_timezone = database.get(
                    'timezone', {}).get('name', DEFAULT_TIMEZONE)
            except Exception as e:
                logger.error(f"Error loading timezone: {e}")
                self._current_timezone = DEFAULT_TIMEZONE
        return self._current_timezone

    async def get_current_offset(self) -> str:
        """Get the currently configured timezone offset"""
        if not self._current_offset:
            from config_manager import config_manager
            try:
                database = await config_manager.load_database()
                self._current_offset = database.get('timezone', {}).get(
                    'offset', DEFAULT_TIMEZONE_OFFSET)
            except Exception as e:
                logger.error(f"Error loading timezone offset: {e}")
                self._current_offset = DEFAULT_TIMEZONE_OFFSET
        return self._current_offset

    def get_timezone_object(self, timezone_name: str) -> pytz.timezone:
        """Get pytz timezone object with caching"""
        if timezone_name not in self._timezone_cache:
            self._timezone_cache[timezone_name] = pytz.timezone(timezone_name)
        return self._timezone_cache[timezone_name]

    async def get_current_datetime(self) -> datetime:
        """Get current datetime in configured timezone"""
        timezone_name = await self.get_current_timezone()
        tz = self.get_timezone_object(timezone_name)
        return datetime.now(tz)

    async def get_current_date_str(self) -> str:
        """Get current date string in configured timezone"""
        current_dt = await self.get_current_datetime()
        return current_dt.strftime('%d/%m/%Y')

    def parse_timezone_offset(self, offset_str: str) -> Tuple[bool, str, Optional[str]]:
        """
        Parse timezone offset string (e.g., 'UTC+5', 'UTC-3')
        Returns: (success, message, timezone_name)
        """
        try:
            if not offset_str.startswith('UTC'):
                return False, "Invalid format. Use UTC+/-offset format.", None

            # Extract sign and number
            offset_part = offset_str[3:]  # Remove 'UTC'
            if not offset_part:
                return False, "Invalid offset. Please use format 'UTC+/-offset'.", None

            sign = offset_part[0]
            if sign not in ['+', '-']:
                return False, "Invalid sign. Use + or - after UTC.", None

            try:
                hours = int(offset_part[1:])
            except ValueError:
                return False, "Invalid offset number. Must be a valid integer.", None

            if not (0 <= hours <= 14):
                return False, "Offset must be between 0 and 14 hours.", None

            # Convert to total minutes
            total_minutes = hours * 60
            if sign == '-':
                total_minutes = -total_minutes

            # Find matching timezone
            timezone_name = self._find_timezone_by_offset(total_minutes)
            if not timezone_name:
                return False, f"No timezone found for offset {offset_str}.", None

            return True, "Timezone found successfully.", timezone_name

        except Exception as e:
            logger.error(f"Error parsing timezone offset: {e}")
            return False, f"Error parsing timezone offset: {str(e)}", None

    def _find_timezone_by_offset(self, total_minutes: int) -> Optional[str]:
        """Find timezone name by offset in minutes"""
        from data import TIMEZONES

        target_offset_str = f'{total_minutes:+03d}00'

        for tz_name in TIMEZONES:
            try:
                tz = self.get_timezone_object(tz_name)
                current_offset = datetime.now(tz).strftime('%z')
                if current_offset == target_offset_str:
                    return tz_name
            except Exception:
                continue

        return None

    def convert_time_by_offset(self, input_time: str, source_offset: str, target_offset: str) -> str:
        """
        Convert time between different UTC offsets
        Args:
            input_time: Time string in format 'HH:MM' or 'HH:MMAM/PM'
            source_offset: Source timezone offset (e.g., 'UTC-5')
            target_offset: Target timezone offset (e.g., 'UTC+3')
        Returns:
            Converted time string
        """
        try:
            if not input_time or not input_time.strip():
                return input_time

            # Parse input time
            time_formats = ['%I:%M%p', '%H:%M']
            time_obj = None

            for fmt in time_formats:
                try:
                    time_obj = datetime.strptime(input_time, fmt)
                    break
                except ValueError:
                    continue

            if not time_obj:
                return input_time

            # Parse offsets
            source_hours = int(source_offset.split('UTC')[1])
            target_hours = int(target_offset.split('UTC')[1])

            # Create timezone objects
            source_tz = pytz.FixedOffset(source_hours * 60)
            target_tz = pytz.FixedOffset(target_hours * 60)

            # Convert time
            localized_time = source_tz.localize(time_obj)
            converted_time = localized_time.astimezone(target_tz)

            return converted_time.strftime('%H:%M')

        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(f"Error converting time {input_time}: {e}")
            return input_time
        except Exception as e:
            logger.error(f"Unexpected error converting time: {e}")
            return input_time

    def clear_cache(self):
        """Clear timezone cache"""
        self._timezone_cache.clear()
        self._current_timezone = None
        self._current_offset = None
        logger.debug("Timezone cache cleared")


# Global timezone manager instance
timezone_manager = TimezoneManager()
