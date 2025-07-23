import os
import pandas as pd
import pytz
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from logger import logger


class CSVManager:
    """Centralized CSV file management for news data"""
    
    def __init__(self, news_dir: str = "news"):
        self.news_dir = Path(news_dir)
        self.news_dir.mkdir(exist_ok=True)
        self._cached_data = {}
        self._cache_timestamp = {}
    
    def get_latest_csv_file(self) -> Optional[Path]:
        """Get the most recent CSV file in the news directory"""
        try:
            csv_files = list(self.news_dir.glob("*.csv"))
            if not csv_files:
                logger.warning("No CSV files found in news directory")
                return None
            
            # Get the most recently modified file
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            logger.debug(f"Latest CSV file: {latest_file}")
            return latest_file
            
        except Exception as e:
            logger.error(f"Error finding latest CSV file: {e}", exc_info=True)
            return None
    
    def load_latest_csv(self, use_cache: bool = True) -> Optional[pd.DataFrame]:
        """Load the latest CSV file with optional caching"""
        try:
            latest_file = self.get_latest_csv_file()
            if not latest_file:
                return None
            
            # Check cache
            if use_cache and latest_file in self._cached_data:
                file_mtime = latest_file.stat().st_mtime
                cache_time = self._cache_timestamp.get(latest_file, 0)
                
                if file_mtime <= cache_time:
                    logger.debug(f"Using cached data for {latest_file}")
                    return self._cached_data[latest_file].copy()
            
            # Load fresh data
            logger.info(f"Loading CSV file: {latest_file}")
            df = pd.read_csv(latest_file)
            
            # Cache the data
            if use_cache:
                self._cached_data[latest_file] = df.copy()
                self._cache_timestamp[latest_file] = datetime.now().timestamp()
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}", exc_info=True)
            return None
    
    def get_today_events(self, 
                        timezone: str = 'US/Eastern',
                        impact_filter: Optional[List[str]] = None,
                        currency_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get today's events with optional filtering"""
        try:
            df = self.load_latest_csv()
            if df is None:
                return []
            
            # Get today's date in the specified timezone
            tz = pytz.timezone(timezone)
            today = datetime.now(tz).strftime('%d/%m/%Y')
            
            # Filter by today's date
            today_events = df[df['date'].astype(str).str.strip() == today]
            
            # Apply impact filter
            if impact_filter:
                impact_filter_lower = [i.lower() for i in impact_filter]
                today_events = today_events[
                    today_events['impact'].astype(str).str.lower().str.strip().isin(impact_filter_lower)
                ]
            
            # Apply currency filter
            if currency_filter:
                currency_filter_upper = [c.upper() for c in currency_filter]
                today_events = today_events[
                    today_events['currency'].astype(str).str.upper().str.strip().isin(currency_filter_upper)
                ]
            
            # Convert to list of dictionaries
            events = today_events.to_dict('records')
            logger.debug(f"Found {len(events)} events for today with filters")
            return events
            
        except Exception as e:
            logger.error(f"Error getting today's events: {e}", exc_info=True)
            return []
    
    def get_high_impact_events(self, 
                              timezone: str = 'US/Eastern',
                              currency_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get today's high impact (red/orange) events"""
        return self.get_today_events(
            timezone=timezone,
            impact_filter=['red', 'orange'],
            currency_filter=currency_filter
        )
    
    def clear_cache(self):
        """Clear the CSV cache"""
        self._cached_data.clear()
        self._cache_timestamp.clear()
        logger.info("CSV cache cleared")
    
    def validate_csv_structure(self, df: pd.DataFrame) -> bool:
        """Validate that CSV has required columns"""
        required_columns = ['date', 'time', 'currency', 'impact', 'event']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"CSV missing required columns: {missing_columns}")
            return False
        
        return True


# Global CSV manager instance
csv_manager = CSVManager()
