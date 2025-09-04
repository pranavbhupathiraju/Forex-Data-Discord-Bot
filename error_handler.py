"""
Centralized error handling for the Economic Data Discord Bot
Provides consistent error handling and logging across all modules
Code clean up - Updated error handler
"""

import traceback
from typing import Optional, Callable, Any
from logger import logger


class ErrorHandler:
    """Centralized error handling with consistent logging and recovery"""

    @staticmethod
    async def handle_error(error: Exception, context: str, logger_instance=None,
                           recovery_func: Optional[Callable] = None,
                           recovery_args: Optional[tuple] = None) -> bool:
        """
        Handle an error with consistent logging and optional recovery

        Args:
            error: The exception that occurred
            context: Description of where the error occurred
            logger_instance: Optional logger instance (uses default if None)
            recovery_func: Optional function to call for recovery
            recovery_args: Arguments to pass to recovery function

        Returns:
            True if error was handled successfully, False otherwise
        """
        log = logger_instance or logger

        # Log the error with full context
        log.error(f"Error in {context}: {str(error)}", exc_info=True)

        # Try recovery if provided
        if recovery_func:
            try:
                if recovery_args:
                    await recovery_func(*recovery_args)
                else:
                    await recovery_func()
                log.info(f"Recovery successful for {context}")
                return True
            except Exception as recovery_error:
                log.error(
                    f"Recovery failed for {context}: {str(recovery_error)}", exc_info=True)
                return False

        return False

    @staticmethod
    def log_warning(message: str, context: str = "Unknown", logger_instance=None):
        """Log a warning with context"""
        log = logger_instance or logger
        log.warning(f"Warning in {context}: {message}")

    @staticmethod
    def log_info(message: str, context: str = "Unknown", logger_instance=None):
        """Log an info message with context"""
        log = logger_instance or logger
        log.info(f"Info in {context}: {message}")

    @staticmethod
    def format_error_message(error: Exception, context: str) -> str:
        """Format error message for user display"""
        error_type = type(error).__name__
        return f"An error occurred in {context}: {error_type} - {str(error)}"

    @staticmethod
    def is_network_error(error: Exception) -> bool:
        """Check if error is network-related"""
        network_errors = (
            ConnectionError,
            TimeoutError,
            OSError,
            Exception  # Add more specific network error types as needed
        )
        return isinstance(error, network_errors)

    @staticmethod
    def is_config_error(error: Exception) -> bool:
        """Check if error is configuration-related"""
        config_errors = (
            FileNotFoundError,
            ValueError,
            KeyError,
            TypeError
        )
        return isinstance(error, config_errors)

    @staticmethod
    def get_error_category(error: Exception) -> str:
        """Categorize error for appropriate handling"""
        if ErrorHandler.is_network_error(error):
            return "network"
        elif ErrorHandler.is_config_error(error):
            return "configuration"
        else:
            return "general"


# Global error handler instance
error_handler = ErrorHandler()
