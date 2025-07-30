"""
Constants for the Economic Data Discord Bot
Centralized configuration for all magic numbers and default values
"""

# Alert timing constants (in seconds)
ALERT_TIMINGS = {
    'FIVE_MIN_WARNING': 300,  # 5 minutes before event
    'RELEASE_WINDOW': 60,     # 1 minute after event
    'CLEANUP_INTERVAL': 24    # hours
}

# Timezone constants
DEFAULT_TIMEZONE = 'US/Eastern'
DEFAULT_TIMEZONE_OFFSET = 'UTC-5'

# Cache constants (in seconds)
DEFAULT_CACHE_TTL = 300  # 5 minutes
CSV_CACHE_TTL = 600      # 10 minutes

# Discord constants
DEFAULT_TIMEOUT = 60.0   # seconds for user input
MAX_MESSAGE_LENGTH = 2000

# File constants
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_DATABASE_FILE = "database.json"
DEFAULT_NEWS_DIR = "news"

# Time format constants
TIME_FORMATS = [
    "%d/%m/%Y %I:%M%p",  # 12-hour format with DD/MM/YYYY date
    "%d/%m/%Y %H:%M"     # 24-hour format with DD/MM/YYYY date
]

# Impact level constants
IMPACT_LEVELS = {
    'red': 0xE74C3C,      # Red color for high impact
    'orange': 0xF39C12,   # Orange color for medium impact
    'yellow': 0xF1C40F,   # Yellow color for low impact
    'gray': 0x95A5A6,     # Gray color for no impact
    'grey': 0x95A5A6      # Alternative spelling
}

# Currency to flag emoji mapping
CURRENCY_FLAGS = {
    "USD": ":flag_us:",
    "AUD": ":flag_au:",
    "CAD": ":flag_ca:",
    "CHF": ":flag_ch:",
    "CNY": ":flag_cn:",
    "EUR": ":flag_eu:",
    "GBP": ":flag_gb:",
    "JPY": ":flag_jp:",
    "NZD": ":flag_nz:",
}

# Invalid time strings that should be skipped
INVALID_TIME_STRINGS = ["", "All Day", "Day 1", "Day 2", "Tentative", "nan"]

# Required CSV columns
REQUIRED_CSV_COLUMNS = ['date', 'time', 'currency', 'impact', 'event']

# Default database structure
DEFAULT_DATABASE = {
    "timezone": {
        "name": DEFAULT_TIMEZONE,
        "offset": DEFAULT_TIMEZONE_OFFSET
    },
    "timezone_scraped": {
        "name": DEFAULT_TIMEZONE,
        "offset": DEFAULT_TIMEZONE_OFFSET
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
