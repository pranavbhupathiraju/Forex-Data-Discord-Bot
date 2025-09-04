# Code clean up - Updated alert manager
import asyncio
import discord
import hashlib
from datetime import datetime, timedelta
from typing import Set, Dict, List, Optional, Any
from logger import logger
from config_manager import config_manager
from csv_manager import csv_manager
from timezone_manager import timezone_manager
from constants import ALERT_TIMINGS, INVALID_TIME_STRINGS, TIME_FORMATS
from error_handler import error_handler
import pandas as pd


class AlertManager:
    """Manages real-time news alerts with memory cleanup"""

    def __init__(self):
        self.alerted_events: Set[str] = set()
        self.last_cleanup = datetime.now()
        self.cleanup_interval_hours = ALERT_TIMINGS['CLEANUP_INTERVAL']

    async def start_alert_monitoring(self, client):
        """Start the background alert monitoring task with adaptive timing"""
        logger.info("Starting alert monitoring system")

        while not client.is_closed():
            try:
                # Check if we're within 10 minutes of any news event
                should_check_frequently = await self._should_check_frequently()

                if should_check_frequently:
                    # Within 10 minutes of news - check every 1 second for precise timing
                    await self._process_alerts(client)
                    await asyncio.sleep(1)
                else:
                    # Outside 10-minute window - check every 5 minutes to save resources
                    await self._process_alerts(client)
                    await self._cleanup_old_alerts()
                    await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                await error_handler.handle_error(e, "alert monitoring")

    async def _process_alerts(self, client):
        """Process and send alerts for upcoming events"""
        try:
            # Get configuration
            config = await config_manager.load_config()
            database = await config_manager.load_database()
            channel_ids = await config_manager.get_channel_ids()

            # Get alert currencies
            alert_currencies = database.get('alert_currencies', [])
            if not alert_currencies:
                return

            # Get news channel
            try:
                news_channel = await client.fetch_channel(channel_ids['news_channel'])
            except discord.NotFound:
                logger.error(
                    f"News channel not found: {channel_ids['news_channel']}")
                return
            except discord.Forbidden:
                logger.error(
                    f"No permission to access news channel: {channel_ids['news_channel']}")
                return

            # Get today's high impact events
            current_timezone = await timezone_manager.get_current_timezone()
            events = await csv_manager.get_high_impact_events(
                timezone=current_timezone,
                currency_filter=alert_currencies
            )

            # Process each event for alerts
            now = await timezone_manager.get_current_datetime()

            for event in events:
                await self._check_event_for_alerts(event, now, news_channel, config)

        except Exception as e:
            await error_handler.handle_error(e, "processing alerts")

    async def _check_event_for_alerts(self, event: Dict[str, Any], now: datetime,
                                      news_channel, config: Dict[str, Any]):
        """Check if an event needs alerts and send them"""
        try:
            event_time_str = str(event.get('time', ''))

            # Skip events without valid times
            if event_time_str in INVALID_TIME_STRINGS:
                return

            # Parse event time
            event_time = await self._parse_event_time(event, event_time_str)
            if not event_time:
                return

            # Check for 5-minute alert
            await self._check_5min_alert(event, event_time, now, news_channel, config)

            # Check for release alert
            await self._check_release_alert(event, event_time, now, news_channel, config)

        except Exception as e:
            await error_handler.handle_error(e, "checking event for alerts")

    async def _parse_event_time(self, event: Dict[str, Any], time_str: str) -> Optional[datetime]:
        """Parse event time string into datetime object"""
        try:
            # Skip invalid time strings
            if time_str in INVALID_TIME_STRINGS or pd.isna(time_str):
                logger.debug(f"Skipping invalid time: {time_str}")
                return None

            current_timezone = await timezone_manager.get_current_timezone()
            tz = timezone_manager.get_timezone_object(current_timezone)
            date_str = event.get('date', '')

            if not date_str or pd.isna(date_str):
                logger.warning(
                    f"No date found for event: {event.get('event', 'Unknown')}")
                return None

            # Try different time formats
            for time_format in TIME_FORMATS:
                try:
                    event_time = datetime.strptime(
                        f"{date_str} {time_str}", time_format)
                    return tz.localize(event_time)
                except ValueError:
                    continue

            logger.warning(f"Could not parse time: {date_str} {time_str}")
            return None

        except Exception as e:
            await error_handler.handle_error(e, "parsing event time")
            return None

    async def _check_5min_alert(self, event: Dict[str, Any], event_time: datetime,
                                now: datetime, news_channel, config: Dict[str, Any]):
        """Check and send 5-minute warning alert"""
        time_diff = (event_time - now).total_seconds()

        # Debug logging
        logger.debug(
            f"Checking 5min alert for {event.get('event')} at {event.get('time')} - diff: {time_diff:.1f}s")

        # 5-minute alert (exactly 300 seconds before - precise timing)
        if 299 <= time_diff <= 301:  # 1-second window for precise timing
            alert_id = self._generate_alert_id(event, "5min")

            if alert_id not in self.alerted_events:
                await self._send_alert(event, news_channel, config, "5 minutes before")
                self.alerted_events.add(alert_id)
                logger.info(
                    f"Sent 5-minute alert for {event.get('currency')} {event.get('event')}")

    async def _check_release_alert(self, event: Dict[str, Any], event_time: datetime,
                                   now: datetime, news_channel, config: Dict[str, Any]):
        """Check and send release alert"""
        time_diff = (now - event_time).total_seconds()

        # Debug logging
        logger.debug(
            f"Checking release alert for {event.get('event')} at {event.get('time')} - diff: {time_diff:.1f}s")

        # Release alert (within 30 seconds after event time for more reliable timing)
        if 0 <= time_diff <= 30:
            alert_id = self._generate_alert_id(event, "release")

            if alert_id not in self.alerted_events:
                await self._send_alert(event, news_channel, config, "NOW!")
                self.alerted_events.add(alert_id)
                logger.info(
                    f"Sent release alert for {event.get('currency')} {event.get('event')}")

    def _generate_alert_id(self, event: Dict[str, Any], alert_type: str) -> str:
        """Generate unique alert ID using hash"""
        event_str = f"{event.get('date')}_{event.get('time')}_{event.get('currency')}_{event.get('event')}_{alert_type}"
        return hashlib.md5(event_str.encode()).hexdigest()

    async def _send_alert(self, event: Dict[str, Any], news_channel,
                          config: Dict[str, Any], alert_text: str):
        """Send alert embed to news channel"""
        try:
            # Determine embed color based on impact
            impact = str(event.get('impact', '')).lower()
            from constants import IMPACT_LEVELS
            color = IMPACT_LEVELS.get(impact, IMPACT_LEVELS['gray'])

            # Create embed
            embed = discord.Embed(
                title=f"{impact.capitalize()} Impact News Alert",
                description=event.get('event', 'Unknown Event'),
                color=color
            )

            embed.add_field(
                name="Currency",
                value=event.get('currency', 'Unknown'),
                inline=True
            )
            embed.add_field(
                name="Time",
                value=event.get('time', 'Unknown'),
                inline=True
            )
            embed.add_field(
                name="Alert",
                value=alert_text,
                inline=False
            )

            # Get role mention
            role_mention = ""
            role_id = config.get('alert_role_id')
            if role_id:
                role_mention = f"<@&{role_id}>"

            # Send alert
            await news_channel.send(content=role_mention, embed=embed)

        except Exception as e:
            await error_handler.handle_error(e, "sending alert")

    async def _cleanup_old_alerts(self):
        """Clean up old alert IDs to prevent memory leaks"""
        try:
            now = datetime.now()

            # Only cleanup once per cleanup interval
            if (now - self.last_cleanup).total_seconds() < (self.cleanup_interval_hours * 3600):
                return

            # Get cleanup hours from config
            config = await config_manager.load_config()
            cleanup_hours = config.get(
                'alert_cleanup_hours', ALERT_TIMINGS['CLEANUP_INTERVAL'])

            # Clear all alerts (simple approach - could be more sophisticated)
            old_count = len(self.alerted_events)
            self.alerted_events.clear()
            self.last_cleanup = now

            logger.info(f"Cleaned up {old_count} old alert IDs")

        except Exception as e:
            await error_handler.handle_error(e, "cleaning up alerts")

    def get_alert_count(self) -> int:
        """Get current number of tracked alerts"""
        return len(self.alerted_events)

    async def _should_check_frequently(self) -> bool:
        """Check if we should check alerts frequently (within 10 minutes of any event)"""
        try:
            # Get alert currencies
            database = await config_manager.load_database()
            alert_currencies = database.get('alert_currencies', [])
            if not alert_currencies:
                return False

            # Get today's high impact events
            current_timezone = await timezone_manager.get_current_timezone()
            events = await csv_manager.get_high_impact_events(
                timezone=current_timezone,
                currency_filter=alert_currencies
            )

            now = await timezone_manager.get_current_datetime()
            ten_minutes = 600  # 10 minutes in seconds

            for event in events:
                event_time_str = str(event.get('time', ''))
                if event_time_str in INVALID_TIME_STRINGS:
                    continue

                event_time = await self._parse_event_time(event, event_time_str)
                if not event_time:
                    continue

                time_diff = (event_time - now).total_seconds()

                # Check if event is within 10 minutes (past or future)
                if abs(time_diff) <= ten_minutes:
                    logger.debug(
                        f"Within 10 minutes of event: {event.get('event')} at {event.get('time')} (diff: {time_diff:.1f}s)")
                    return True

            return False

        except Exception as e:
            await error_handler.handle_error(e, "checking if should check frequently")
            return False


# Global alert manager instance
alert_manager = AlertManager()
