import discord
import asyncio
from logger import logger
from config_manager import config_manager
from command_handler import command_handler
from alert_manager import alert_manager


class EconomicBot(discord.Client):
    """Enhanced Discord bot for economic news alerts"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = None
        self.channel_ids = None

    async def setup_hook(self) -> None:
        """Initialize bot configuration and start background tasks"""
        try:
            # Load configuration
            self.config = await config_manager.load_config()
            self.channel_ids = await config_manager.get_channel_ids()

            logger.info("Bot configuration loaded successfully")

            # Start background alert monitoring
            self.alert_task = self.loop.create_task(alert_manager.start_alert_monitoring(self))
            logger.info("Background tasks started")

        except Exception as e:
            logger.critical(f"Failed to initialize bot: {e}", exc_info=True)
            raise

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Bot {self.user} is online and ready!")

        # Log configuration info
        if self.config:
            testing_mode = self.config.get('testing', False)
            logger.info(f"Running in {'testing' if testing_mode else 'production'} mode")
            logger.info(f"Monitoring {len(alert_manager.alerted_events)} alerts")

    async def on_message(self, message):
        """Handle incoming messages"""
        # Ignore bot's own messages
        if message.author == self.user:
            return

        try:
            # Use command handler to process message
            command_handled = await command_handler.handle_message(self, message)

            if command_handled:
                logger.debug(f"Command handled: {message.content} by {message.author.name}")

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            # Don't send error message to avoid spam

    async def close(self):
        """Clean shutdown of bot"""
        try:
            logger.info("Shutting down bot...")

            # Cancel background tasks
            if hasattr(self, 'alert_task'):
                self.alert_task.cancel()
                try:
                    await self.alert_task
                except asyncio.CancelledError:
                    pass

            # Clear caches
            config_manager.clear_cache()

            await super().close()
            logger.info("Bot shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)


async def main():
    """Main bot execution function"""
    try:
        # Create bot instance
        bot = EconomicBot(intents=discord.Intents.all())

        # Load config to get token
        config = await config_manager.load_config()
        token = config['token']

        logger.info("Starting Economic Discord Bot...")

        # Run the bot
        await bot.start(token)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Critical error starting bot: {e}", exc_info=True)
        raise
    finally:
        logger.info("Bot offline")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
