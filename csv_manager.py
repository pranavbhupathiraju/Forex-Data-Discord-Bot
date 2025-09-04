# Code clean up - Updated CSV manager
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from logger import logger
from cache_manager import cache_manager
from timezone_manager import timezone_manager
from constants import DEFAULT_NEWS_DIR, REQUIRED_CSV_COLUMNS, CSV_CACHE_TTL
from error_handler import error_handler


class CSVManager:
    """Centralized CSV file management for news data with improved caching"""

    def __init__(self, news_dir: str = DEFAULT_NEWS_DIR):
        self.news_dir = Path(news_dir)
        self.news_dir.mkdir(exist_ok=True)

    def get_latest_csv_file(self) -> Optional[Path]:
        """Get the CSV file for the current month"""
        try:
            csv_files = list(self.news_dir.glob("*.csv"))
            if not csv_files:
                logger.warning("No CSV files found in news directory")
                return None

            # Get current month name
            current_month = datetime.now().strftime('%B')
            logger.debug(
                f"Looking for CSV file for current month: {current_month}")

            # Look for file with current month name
            for file in csv_files:
                if current_month.lower() in file.name.lower():
                    logger.debug(f"Found CSV file for current month: {file}")
                    return file

            # If no current month file found, get the most recent file
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            logger.debug(f"Using most recent CSV file: {latest_file}")
            return latest_file

        except Exception as e:
            logger.error(f"Error finding CSV file: {e}", exc_info=True)
            return None

    def load_latest_csv(self, use_cache: bool = True, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """Load the latest CSV file with improved caching"""
        try:
            latest_file = self.get_latest_csv_file()
            if not latest_file:
                return None

            cache_key = f"csv_{latest_file}"

            # Check if we need to refresh cache
            if not force_refresh and use_cache:
                cached_data = cache_manager.get(cache_key)
                if cached_data is not None:
                    # Check if file has been modified since last cache
                    file_mtime = latest_file.stat().st_mtime
                    cache_mtime = cache_manager._timestamps.get(cache_key, 0)

                    if file_mtime <= cache_mtime:
                        logger.debug(f"Using cached data for {latest_file}")
                        return cached_data
                    else:
                        logger.info(
                            f"CSV file modified, refreshing cache for {latest_file}")
                        cache_manager.delete(cache_key)

            # Load fresh data
            logger.info(f"Loading CSV file: {latest_file}")
            df = pd.read_csv(latest_file)

            # Validate CSV structure
            if not self.validate_csv_structure(df):
                logger.error(f"Invalid CSV structure in {latest_file}")
                return None

            # Cache the data
            if use_cache:
                cache_manager.set(cache_key, df.copy(), CSV_CACHE_TTL)

            return df

        except Exception as e:
            logger.error(f"Error loading CSV file: {e}", exc_info=True)
            return None

    async def get_today_events(self,
                               timezone: str = None,
                               impact_filter: Optional[List[str]] = None,
                               currency_filter: Optional[List[str]] = None,
                               force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get today's events with optional filtering"""
        try:
            df = self.load_latest_csv(force_refresh=force_refresh)
            if df is None:
                return []

            # Get timezone if not provided
            if timezone is None:
                timezone = await timezone_manager.get_current_timezone()

            # Get today's date in the specified timezone
            tz = timezone_manager.get_timezone_object(timezone)
            today = datetime.now(tz)
            today_str = today.strftime('%d/%m/%Y')

            # Filter by today's date
            today_events = df[df['date'].astype(str).str.strip() == today_str]

            # Apply impact filter
            if impact_filter:
                impact_filter_lower = [i.lower() for i in impact_filter]
                today_events = today_events[
                    today_events['impact'].astype(str).str.lower(
                    ).str.strip().isin(impact_filter_lower)
                ]

            # Apply currency filter
            if currency_filter:
                currency_filter_upper = [c.upper() for c in currency_filter]
                today_events = today_events[
                    today_events['currency'].astype(str).str.upper(
                    ).str.strip().isin(currency_filter_upper)
                ]

            # Convert to list of dictionaries
            events = today_events.to_dict('records')
            logger.debug(f"Found {len(events)} events for today ({today_str})")
            return events

        except Exception as e:
            logger.error(f"Error getting today's events: {e}", exc_info=True)
            return []

    async def get_high_impact_events(self,
                                     timezone: str = None,
                                     currency_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get today's high impact (red/orange) events"""
        return await self.get_today_events(
            timezone=timezone,
            impact_filter=['red', 'orange'],
            currency_filter=currency_filter
        )

    def clear_cache(self):
        """Clear the CSV cache"""
        cache_manager.clear()
        logger.info("CSV cache cleared")

    def force_refresh_cache(self):
        """Force refresh the CSV cache"""
        cache_manager.clear()
        logger.info("CSV cache force refreshed")

    def validate_csv_structure(self, df: pd.DataFrame) -> bool:
        """Validate that CSV has required columns"""
        missing_columns = [
            col for col in REQUIRED_CSV_COLUMNS if col not in df.columns]

        if missing_columns:
            logger.error(f"CSV missing required columns: {missing_columns}")
            return False

        return True


# Global CSV manager instance
csv_manager = CSVManager()
