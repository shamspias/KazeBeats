"""
Logging configuration for KazeBeats
Gaming-themed colored console output and file logging
"""

import logging
import colorlog
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(name: str = "KazeBeats", log_file: str = None) -> logging.Logger:
    """
    Setup a logger with colored console output and file logging
    """
    logger = logging.getLogger(name)

    # Don't add handlers if they already exist
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console Handler with colors
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Gaming-themed color scheme
    console_format = colorlog.ColoredFormatter(
        "%(cyan)s[%(asctime)s]%(reset)s "
        "%(log_color)s%(levelname)-8s%(reset)s "
        "%(blue)s%(name)s%(reset)s "
        "%(white)s%(message)s%(reset)s",
        datefmt="%H:%M:%S",
        log_colors={
            'DEBUG': 'purple',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={
            'message': {
                'DEBUG': 'purple',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red'
            }
        }
    )

    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Log startup message
    logger.info("=" * 50)
    logger.info("🎮 KazeBeats Logger Initialized")
    logger.info(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    return logger


class BotLogger:
    """
    Custom logger wrapper with gaming-themed messages
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def startup(self, bot_name: str, version: str):
        """Log bot startup"""
        self.logger.info("🚀 Bot Starting Up...")
        self.logger.info(f"🎮 Name: {bot_name}")
        self.logger.info(f"📦 Version: {version}")

    def command(self, command: str, user: str, guild: str = None):
        """Log command execution"""
        location = guild if guild else "DM"
        self.logger.info(f"⚡ Command: {command} | User: {user} | Location: {location}")

    def music_play(self, track: str, user: str, guild: str):
        """Log music playback"""
        self.logger.info(f"🎵 Playing: {track} | Requested by: {user} | Guild: {guild}")

    def music_queue(self, track: str, position: int, user: str):
        """Log track added to queue"""
        self.logger.info(f"📋 Queued: {track} | Position: #{position} | By: {user}")

    def effect_applied(self, effect: str, user: str):
        """Log audio effect application"""
        self.logger.info(f"✨ Effect Applied: {effect} | By: {user}")

    def error(self, error: str, context: str = None):
        """Log error with context"""
        if context:
            self.logger.error(f"❌ Error in {context}: {error}")
        else:
            self.logger.error(f"❌ Error: {error}")

    def warning(self, message: str):
        """Log warning"""
        self.logger.warning(f"⚠️ Warning: {message}")

    def success(self, message: str):
        """Log success message"""
        self.logger.info(f"✅ Success: {message}")

    def database(self, operation: str, details: str = None):
        """Log database operations"""
        if details:
            self.logger.debug(f"💾 Database: {operation} | {details}")
        else:
            self.logger.debug(f"💾 Database: {operation}")

    def cache(self, operation: str, key: str = None):
        """Log cache operations"""
        if key:
            self.logger.debug(f"📦 Cache: {operation} | Key: {key}")
        else:
            self.logger.debug(f"📦 Cache: {operation}")

    def api_call(self, service: str, endpoint: str = None):
        """Log API calls"""
        if endpoint:
            self.logger.debug(f"🌐 API Call: {service} | Endpoint: {endpoint}")
        else:
            self.logger.debug(f"🌐 API Call: {service}")

    def performance(self, metric: str, value: any):
        """Log performance metrics"""
        self.logger.debug(f"📊 Performance: {metric} = {value}")

    def guild_join(self, guild_name: str, guild_id: int, member_count: int):
        """Log guild join"""
        self.logger.info(f"🎉 Joined Guild: {guild_name} (ID: {guild_id}) | Members: {member_count}")

    def guild_leave(self, guild_name: str, guild_id: int):
        """Log guild leave"""
        self.logger.info(f"👋 Left Guild: {guild_name} (ID: {guild_id})")

    def shutdown(self):
        """Log bot shutdown"""
        self.logger.info("🔄 Bot Shutting Down...")
        self.logger.info("=" * 50)


# Create a global logger instance
_logger = setup_logger()
bot_logger = BotLogger(_logger)
