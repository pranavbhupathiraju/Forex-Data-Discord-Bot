import asyncio
import discord
import pytz
from datetime import datetime, timedelta
from typing import Set, Dict, List, Optional, Any
from logger import logger
from config_manager import config_manager
from csv_manager import csv_manager


class AlertManager:
    """Manages real-time news alerts with memory cleanup"""
    
    def __init__(self):
        self.alerted_events: Set[str] = set()
        self.last_cleanup = datetime.now()
        self.cleanup_interval_hours = 24
    
    async def start_alert_monitoring(self, client):
        """Start the background alert monitoring task"""
        logger.info("Starting alert monitoring system")
        
        while not client.is_closed():
            try:
                await self._process_alerts(client)
                await self._cleanup_old_alerts()
                
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}", exc_info=True)
            
            # Wait 1 minute before next check
            await asyncio.sleep(60)
    
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
            news_channel = client.get_channel(channel_ids['news_channel'])
            if not news_channel:
                logger.error(f"News channel not found: {channel_ids['news_channel']}")
                return
            
            # Get today's high impact events
            events = csv_manager.get_high_impact_events(
                timezone='US/Eastern',
                currency_filter=alert_currencies
            )
            
            # Process each event for alerts
            est = pytz.timezone('US/Eastern')
            now = datetime.now(est)
            
            for event in events:
                await self._check_event_for_alerts(event, now, news_channel, config)
                
        except Exception as e:
            logger.error(f"Error processing alerts: {e}", exc_info=True)
    
    async def _check_event_for_alerts(self, event: Dict[str, Any], now: datetime, 
                                    news_channel, config: Dict[str, Any]):
        """Check if an event needs alerts and send them"""
        try:
            event_time_str = str(event.get('time', ''))
            
            # Skip events without valid times
            if event_time_str in ["", "All Day", "Day 1", "Day 2", "Tentative"]:
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
            logger.error(f"Error checking event for alerts: {e}", exc_info=True)
    
    async def _parse_event_time(self, event: Dict[str, Any], time_str: str) -> Optional[datetime]:
        """Parse event time string into datetime object"""
        try:
            est = pytz.timezone('US/Eastern')
            date_str = event.get('date', '')
            
            # Try different time formats
            for time_format in ["%d/%m/%Y %I:%M%p", "%d/%m/%Y %H:%M"]:
                try:
                    event_time = datetime.strptime(f"{date_str} {time_str}", time_format)
                    return est.localize(event_time)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse time: {date_str} {time_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing event time: {e}", exc_info=True)
            return None
    
    async def _check_5min_alert(self, event: Dict[str, Any], event_time: datetime, 
                              now: datetime, news_channel, config: Dict[str, Any]):
        """Check and send 5-minute warning alert"""
        time_diff = (event_time - now).total_seconds()
        
        # 5-minute alert (between 240-300 seconds before)
        if 240 <= time_diff <= 300:
            alert_id = self._generate_alert_id(event, "5min")
            
            if alert_id not in self.alerted_events:
                await self._send_alert(event, news_channel, config, "5 minutes before")
                self.alerted_events.add(alert_id)
                logger.info(f"Sent 5-minute alert for {event.get('currency')} {event.get('event')}")
    
    async def _check_release_alert(self, event: Dict[str, Any], event_time: datetime,
                                 now: datetime, news_channel, config: Dict[str, Any]):
        """Check and send release alert"""
        time_diff = (now - event_time).total_seconds()
        
        # Release alert (within 60 seconds after event time)
        if 0 <= time_diff < 60:
            alert_id = self._generate_alert_id(event, "release")
            
            if alert_id not in self.alerted_events:
                await self._send_alert(event, news_channel, config, "NOW!")
                self.alerted_events.add(alert_id)
                logger.info(f"Sent release alert for {event.get('currency')} {event.get('event')}")
    
    def _generate_alert_id(self, event: Dict[str, Any], alert_type: str) -> str:
        """Generate unique alert ID"""
        return f"{event.get('date')}_{event.get('time')}_{event.get('currency')}_{event.get('event')}_{alert_type}"
    
    async def _send_alert(self, event: Dict[str, Any], news_channel, 
                         config: Dict[str, Any], alert_text: str):
        """Send alert embed to news channel"""
        try:
            # Determine embed color based on impact
            impact = str(event.get('impact', '')).lower()
            color = 0xE74C3C if impact == 'red' else 0xF39C12
            
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
                name="Time (EST)", 
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
            logger.error(f"Error sending alert: {e}", exc_info=True)
    
    async def _cleanup_old_alerts(self):
        """Clean up old alert IDs to prevent memory leaks"""
        try:
            now = datetime.now()
            
            # Only cleanup once per cleanup interval
            if (now - self.last_cleanup).total_seconds() < (self.cleanup_interval_hours * 3600):
                return
            
            # Get cleanup hours from config
            config = await config_manager.load_config()
            cleanup_hours = config.get('alert_cleanup_hours', 24)
            
            # Clear all alerts (simple approach - could be more sophisticated)
            old_count = len(self.alerted_events)
            self.alerted_events.clear()
            self.last_cleanup = now
            
            logger.info(f"Cleaned up {old_count} old alert IDs")
            
        except Exception as e:
            logger.error(f"Error cleaning up alerts: {e}", exc_info=True)
    
    def get_alert_count(self) -> int:
        """Get current number of tracked alerts"""
        return len(self.alerted_events)


# Global alert manager instance
alert_manager = AlertManager()
