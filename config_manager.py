import json
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional, List
from logger import logger


class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_file: str = "config.json", database_file: str = "database.json"):
        self.config_file = Path(config_file)
        self.database_file = Path(database_file)
        self._config_cache = None
        self._database_cache = None
    
    async def load_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """Load configuration from config.json"""
        if use_cache and self._config_cache is not None:
            return self._config_cache
        
        try:
            if not self.config_file.exists():
                logger.error(f"Config file not found: {self.config_file}")
                raise FileNotFoundError(f"Config file not found: {self.config_file}")
            
            async with aiofiles.open(self.config_file, 'r') as f:
                content = await f.read()
                config = json.loads(content)
            
            # Validate required fields
            required_fields = ['token', 'news_channel_id', 'operations_channel_id']
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                logger.error(f"Missing required config fields: {missing_fields}")
                raise ValueError(f"Missing required config fields: {missing_fields}")
            
            self._config_cache = config
            logger.debug("Configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            raise
    
    async def save_config(self, config: Dict[str, Any]):
        """Save configuration to config.json"""
        try:
            async with aiofiles.open(self.config_file, 'w') as f:
                await f.write(json.dumps(config, indent=4))
            
            self._config_cache = config
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)
            raise
    
    async def load_database(self, use_cache: bool = True) -> Dict[str, Any]:
        """Load database from database.json"""
        if use_cache and self._database_cache is not None:
            return self._database_cache
        
        try:
            if not self.database_file.exists():
                logger.warning(f"Database file not found: {self.database_file}, creating default")
                return await self._create_default_database()
            
            async with aiofiles.open(self.database_file, 'r') as f:
                content = await f.read()
                database = json.loads(content)
            
            self._database_cache = database
            logger.debug("Database loaded successfully")
            return database
            
        except Exception as e:
            logger.error(f"Error loading database: {e}", exc_info=True)
            return await self._create_default_database()
    
    async def save_database(self, database: Dict[str, Any]):
        """Save database to database.json"""
        try:
            async with aiofiles.open(self.database_file, 'w') as f:
                await f.write(json.dumps(database, indent=4))
            
            self._database_cache = database
            logger.debug("Database saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving database: {e}", exc_info=True)
            raise
    
    async def _create_default_database(self) -> Dict[str, Any]:
        """Create default database structure"""
        default_db = {
            "timezone": {
                "name": "America/New_York",
                "offset": "UTC-5"
            },
            "timezone_scraped": {
                "name": "America/New_York", 
                "offset": "UTC-5"
            },
            "daily_update": {
                "hour": "7",
                "minute": "0"
            },
            "time_threshold": 5,
            "updated": False,
            "currencies": ["USD"],
            "impacts": ["red", "orange"],
            "all_currencies": ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "NZD", "CNY"],
            "all_impacts": ["red", "orange", "yellow", "gray"],
            "updated_rows": [],
            "alert_currencies": []
        }
        
        await self.save_database(default_db)
        logger.info("Created default database")
        return default_db
    
    async def get_authorized_users(self) -> List[str]:
        """Get list of authorized users"""
        config = await self.load_config()
        return config.get('authorized_users', ['pnavtradez'])
    
    async def get_channel_ids(self) -> Dict[str, int]:
        """Get channel IDs based on testing mode"""
        config = await self.load_config()
        testing = config.get('testing', False)
        
        if testing:
            return {
                'news_channel': config.get('test_news_channel_id', config['news_channel_id']),
                'operations_channel': config.get('test_operations_channel_id', config['operations_channel_id'])
            }
        else:
            return {
                'news_channel': config['news_channel_id'],
                'operations_channel': config['operations_channel_id']
            }
    
    async def update_alert_role(self, role_id: int):
        """Update alert role ID in config"""
        config = await self.load_config(use_cache=False)
        config['alert_role_id'] = role_id
        await self.save_config(config)
        logger.info(f"Alert role updated to {role_id}")
    
    def clear_cache(self):
        """Clear configuration cache"""
        self._config_cache = None
        self._database_cache = None
        logger.info("Configuration cache cleared")


# Global config manager instance
config_manager = ConfigManager()
