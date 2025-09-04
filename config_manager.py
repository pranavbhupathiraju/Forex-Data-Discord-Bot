# Code clean up - Updated config manager
import json
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional, List
from logger import logger
from cache_manager import cache_manager
from constants import DEFAULT_CONFIG_FILE, DEFAULT_DATABASE_FILE, DEFAULT_DATABASE
from error_handler import error_handler


class ConfigManager:
    """Centralized configuration management with caching"""

    def __init__(self, config_file: str = DEFAULT_CONFIG_FILE, database_file: str = DEFAULT_DATABASE_FILE):
        self.config_file = Path(config_file)
        self.database_file = Path(database_file)

    async def load_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """Load configuration from config.json with caching"""
        cache_key = f"config_{self.config_file}"

        if use_cache:
            cached_config = cache_manager.get(cache_key)
            if cached_config:
                return cached_config

        try:
            if not self.config_file.exists():
                logger.error(f"Config file not found: {self.config_file}")
                raise FileNotFoundError(
                    f"Config file not found: {self.config_file}")

            async with aiofiles.open(self.config_file, 'r') as f:
                content = await f.read()
                config = json.loads(content)

            # Validate required fields
            required_fields = [
                'token', 'news_channel_id', 'operations_channel_id']
            missing_fields = [
                field for field in required_fields if field not in config]

            if missing_fields:
                logger.error(
                    f"Missing required config fields: {missing_fields}")
                raise ValueError(
                    f"Missing required config fields: {missing_fields}")

            # Cache the config
            if use_cache:
                cache_manager.set(cache_key, config)

            logger.debug("Configuration loaded successfully")
            return config

        except Exception as e:
            await error_handler.handle_error(e, "loading configuration")
            raise

    async def save_config(self, config: Dict[str, Any]):
        """Save configuration to config.json"""
        try:
            async with aiofiles.open(self.config_file, 'w') as f:
                await f.write(json.dumps(config, indent=4))

            # Update cache
            cache_key = f"config_{self.config_file}"
            cache_manager.set(cache_key, config)

            logger.info("Configuration saved successfully")

        except Exception as e:
            await error_handler.handle_error(e, "saving configuration")
            raise

    async def load_database(self, use_cache: bool = True) -> Dict[str, Any]:
        """Load database from database.json with caching"""
        cache_key = f"database_{self.database_file}"

        if use_cache:
            cached_database = cache_manager.get(cache_key)
            if cached_database:
                return cached_database

        try:
            if not self.database_file.exists():
                logger.warning(
                    f"Database file not found: {self.database_file}, creating default")
                return await self._create_default_database()

            async with aiofiles.open(self.database_file, 'r') as f:
                content = await f.read()
                database = json.loads(content)

            # Cache the database
            if use_cache:
                cache_manager.set(cache_key, database)

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

            # Update cache
            cache_key = f"database_{self.database_file}"
            cache_manager.set(cache_key, database)

            logger.debug("Database saved successfully")

        except Exception as e:
            await error_handler.handle_error(e, "saving database")
            raise

    async def _create_default_database(self) -> Dict[str, Any]:
        """Create default database structure"""
        await self.save_database(DEFAULT_DATABASE)
        logger.info("Created default database")
        return DEFAULT_DATABASE

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
        cache_manager.clear()
        logger.info("Configuration cache cleared")


# Global config manager instance
config_manager = ConfigManager()
