import asyncio
from typing import Dict, Callable, Any, Optional
from discord import Message
from logger import logger
from config_manager import config_manager
import responses
from error_handler import error_handler


class CommandHandler:
    """Centralized command handling system with improved error handling"""

    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self.prefix_commands: Dict[str, Callable] = {}
        self._register_commands()

    def _register_commands(self):
        """Register all bot commands"""
        # Exact match commands
        self.commands = {
            '!ping': self._ping_command,
            '!state': self._state_command,
            '!quote': self._quote_command,
            '!today': self._today_command,
            '!timezone': self._timezone_command,
            '!datetime': self._datetime_command,
            '!news': self._news_command,
            '!refresh': self._refresh_command,
            '!debug': self._debug_command,
        }

        # Prefix commands (commands that start with a pattern)
        self.prefix_commands = {
            '!currencies:': self._currencies_command,
            '!impacts:': self._impacts_command,
            '!daily:': self._daily_command,
            '!alerts': self._alerts_command,
            '!alertrole:': self._alertrole_command,
        }

    async def handle_message(self, client, message: Message) -> bool:
        """
        Handle incoming message and execute command if found
        Returns True if command was handled, False otherwise
        """
        try:
            # Check authorization
            if not await self._is_authorized(message):
                return False

            content = message.content.strip()

            # Check exact match commands
            if content.lower() in self.commands:
                command_func = self.commands[content.lower()]
                await self._execute_command(command_func, client, message)
                return True

            # Check prefix commands
            for prefix, command_func in self.prefix_commands.items():
                if content.lower().startswith(prefix.lower()):
                    await self._execute_command(command_func, client, message)
                    return True

            return False

        except Exception as e:
            await error_handler.handle_error(e, "handling message")
            await message.channel.send("An error occurred while processing your command.")
            return True  # Command was attempted, so return True

    async def _is_authorized(self, message: Message) -> bool:
        """Check if user is authorized to use commands"""
        try:
            # Get channel IDs and authorized users
            channel_ids = await config_manager.get_channel_ids()
            authorized_users = await config_manager.get_authorized_users()

            # Check if message is in operations channel and user is authorized
            is_in_ops_channel = message.channel.id == channel_ids['operations_channel']
            is_authorized_user = message.author.name in authorized_users

            return is_in_ops_channel and is_authorized_user

        except Exception as e:
            await error_handler.handle_error(e, "checking authorization")
            return False

    async def _execute_command(self, command_func: Callable, client, message: Message):
        """Execute a command function with error handling"""
        try:
            logger.info(
                f"Executing command: {message.content} by {message.author.name}")

            # Check if command needs client parameter
            if command_func.__name__ in ['_timezone_command']:
                await command_func(client, message)
            else:
                await command_func(message)

        except Exception as e:
            await error_handler.handle_error(e, f"executing command {command_func.__name__}")
            await message.channel.send("An error occurred while executing the command.")

    async def _ping_command(self, message: Message):
        """Handle ping command"""
        await message.channel.send("Pong! 🏓")

    async def _state_command(self, message: Message):
        """Handle state command"""
        await responses.state(message)

    async def _quote_command(self, message: Message):
        """Handle quote command"""
        await responses.send_qoute(message)

    async def _today_command(self, message: Message):
        """Handle today command"""
        await responses.today_news(message)

    async def _timezone_command(self, client, message: Message):
        """Handle timezone command"""
        await responses.handle_timezone_message(client, message)

    async def _datetime_command(self, message: Message):
        """Handle datetime command"""
        await responses.handle_datetime_command(message)

    async def _news_command(self, message: Message):
        """Handle news command"""
        await responses.today_news(message)

    async def _refresh_command(self, message: Message):
        """Handle refresh command"""
        await responses.refresh_data(message)

    async def _debug_command(self, message: Message):
        """Handle debug command"""
        await responses.debug_time(message)

    async def _currencies_command(self, message: Message):
        """Handle currencies command"""
        await responses.set_allowed_currencies(message)

    async def _impacts_command(self, message: Message):
        """Handle impacts command"""
        await responses.set_allowed_impacts(message)

    async def _daily_command(self, message: Message):
        """Handle daily command"""
        await responses.set_daily_update_time(message)

    async def _alerts_command(self, message: Message):
        """Handle alerts command"""
        await responses.set_alert_currencies(message)

    async def _alertrole_command(self, message: Message):
        """Handle alert role command"""
        try:
            content = message.content.replace('!alertrole:', '').strip()
            if not content:
                await message.channel.send("Please provide a role ID. Use `!alertrole:ROLE_ID`")
                return

            try:
                role_id = int(content)
            except ValueError:
                await message.channel.send("Invalid role ID. Please provide a valid number.")
                return

            await config_manager.update_alert_role(role_id)
            await message.channel.send(f"Alert role updated to {role_id}")

        except Exception as e:
            await error_handler.handle_error(e, "setting alert role")
            await message.channel.send("Error setting alert role.")


# Global command handler instance
command_handler = CommandHandler()
