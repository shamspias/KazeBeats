"""
Configuration management for KazeBeats
Gaming-inspired design constants and settings
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class BotColors:
    """Gaming-inspired neon color scheme"""
    # Primary colors
    NEON_BLUE = 0x00D4FF
    NEON_PURPLE = 0x9D00FF
    NEON_PINK = 0xFF00DC
    NEON_GREEN = 0x00FF88
    NEON_YELLOW = 0xFFD700
    NEON_ORANGE = 0xFF6B00
    NEON_RED = 0xFF0040

    # Status colors
    SUCCESS = 0x00FF88
    ERROR_RED = 0xFF0040
    WARNING_YELLOW = 0xFFD700
    INFO_BLUE = 0x00D4FF

    # Music states
    PLAYING = 0x00FF88
    PAUSED = 0xFFD700
    STOPPED = 0xFF0040
    LOADING = 0x00D4FF

    # Effect colors
    BASS_BOOST = 0x9D00FF
    NIGHTCORE = 0xFF00DC
    KARAOKE = 0x00D4FF
    ECHO = 0xFF6B00
    THREE_D = 0x00FF88


@dataclass
class BotEmojis:
    """Gaming and music emojis"""
    # Music controls
    PLAY = "▶️"
    PAUSE = "⏸️"
    STOP = "⏹️"
    SKIP = "⏭️"
    PREVIOUS = "⏮️"
    LOOP = "🔁"
    SHUFFLE = "🔀"
    QUEUE = "📋"

    # Volume
    VOLUME_HIGH = "🔊"
    VOLUME_MEDIUM = "🔉"
    VOLUME_LOW = "🔈"
    VOLUME_MUTE = "🔇"

    # Status
    LOADING = "⏳"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    GAMING = "🎮"
    MUSIC = "🎵"
    STAR = "⭐"
    FIRE = "🔥"
    LIGHTNING = "⚡"
    ROCKET = "🚀"
    CROWN = "👑"

    # Platforms
    YOUTUBE = "🎬"
    SPOTIFY = "🎧"
    SOUNDCLOUD = "☁️"

    # Effects
    BASS_BOOST = "🔊"
    NIGHTCORE = "🌙"
    KARAOKE = "🎤"
    ECHO = "🔄"
    THREE_D = "🎭"

    # Progress bar
    PROGRESS_START_FULL = "🟦"
    PROGRESS_MID_FULL = "🟦"
    PROGRESS_END_FULL = "🟦"
    PROGRESS_START_EMPTY = "⬜"
    PROGRESS_MID_EMPTY = "⬜"
    PROGRESS_END_EMPTY = "⬜"
    PROGRESS_SLIDER = "🔘"


class Config:
    """Bot configuration from environment variables"""

    def __init__(self):
        # Discord
        self.DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
        self.DEFAULT_PREFIX = os.getenv('DEFAULT_PREFIX', '!')
        self.OWNER_ID = int(os.getenv('OWNER_ID', '0'))

        # Bot info
        self.BOT_NAME = os.getenv('BOT_NAME', 'KazeBeats')
        self.BOT_VERSION = os.getenv('BOT_VERSION', '1.0.0')
        self.BOT_DESCRIPTION = os.getenv('BOT_DESCRIPTION',
                                         'High-performance Discord music bot with gaming-inspired design')

        # Audio settings
        self.AUDIO_BITRATE = int(os.getenv('AUDIO_BITRATE', '320'))
        self.AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '48000'))
        self.MAX_VOLUME = int(os.getenv('MAX_VOLUME', '200'))
        self.DEFAULT_VOLUME = int(os.getenv('DEFAULT_VOLUME', '100'))

        # Database
        self.DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
        self.DB_PATH = os.getenv('DB_PATH', 'kazebeats.db')
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = int(os.getenv('DB_PORT', '5432'))
        self.DB_NAME = os.getenv('DB_NAME', 'kazebeats')
        self.DB_USER = os.getenv('DB_USER', 'kazebeats_user')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', '')

        # Redis cache
        self.REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

        # API Keys
        self.YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
        self.SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
        self.SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')
        self.SOUNDCLOUD_CLIENT_ID = os.getenv('SOUNDCLOUD_CLIENT_ID', '')
        self.GENIUS_API_TOKEN = os.getenv('GENIUS_API_TOKEN', '')

        # Web Dashboard
        self.WEB_ENABLED = os.getenv('WEB_ENABLED', 'true').lower() == 'true'
        self.WEB_PORT = int(os.getenv('WEB_PORT', '8080'))
        self.WEB_SECRET_KEY = os.getenv('WEB_SECRET_KEY', 'your_secret_key_here')
        self.WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')

        # Performance
        self.MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', '1000'))
        self.CACHE_SIZE_MB = int(os.getenv('CACHE_SIZE_MB', '500'))
        self.PRELOAD_NEXT_TRACK = os.getenv('PRELOAD_NEXT_TRACK', 'true').lower() == 'true'
        self.AUTO_DISCONNECT_TIMEOUT = int(os.getenv('AUTO_DISCONNECT_TIMEOUT', '300'))

        # Features
        self.ENABLE_EFFECTS = os.getenv('ENABLE_EFFECTS', 'true').lower() == 'true'
        self.ENABLE_LYRICS = os.getenv('ENABLE_LYRICS', 'true').lower() == 'true'
        self.ENABLE_PLAYLISTS = os.getenv('ENABLE_PLAYLISTS', 'true').lower() == 'true'
        self.ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'
        self.ENABLE_AUTO_DJ = os.getenv('ENABLE_AUTO_DJ', 'true').lower() == 'true'

        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/kazebeats.log')
        self.LOG_MAX_SIZE_MB = int(os.getenv('LOG_MAX_SIZE_MB', '10'))
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))

        # Limits
        self.MAX_PLAYLIST_SIZE = 100
        self.MAX_SEARCH_RESULTS = 10
        self.MAX_LYRICS_LENGTH = 4000
        self.COMMAND_COOLDOWN = 3  # seconds

        # Effect limits
        self.MAX_BASS_BOOST = 20
        self.MAX_ECHO_DELAY = 1.0
        self.MAX_SPEED = 2.0
        self.MIN_SPEED = 0.5

    def get_db_url(self) -> str:
        """Get database connection URL"""
        if self.DB_TYPE == 'sqlite':
            return f"sqlite:///{self.DB_PATH}"
        elif self.DB_TYPE == 'postgresql':
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            raise ValueError(f"Unsupported database type: {self.DB_TYPE}")

    def get_redis_url(self) -> Optional[str]:
        """Get Redis connection URL"""
        if not self.REDIS_ENABLED:
            return None
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required")

        if self.OWNER_ID == 0:
            raise ValueError("OWNER_ID is required")

        return True


# Audio effect presets
EFFECT_PRESETS = {
    "bass_low": {"bass": 5, "description": "Subtle bass enhancement"},
    "bass_medium": {"bass": 10, "description": "Moderate bass boost"},
    "bass_high": {"bass": 15, "description": "Heavy bass boost"},
    "bass_extreme": {"bass": 20, "description": "Maximum bass boost"},
    "nightcore": {"speed": 1.3, "pitch": 1.3, "description": "Nightcore effect"},
    "daycore": {"speed": 0.7, "pitch": 0.7, "description": "Daycore/Anti-nightcore"},
    "karaoke": {"karaoke": True, "description": "Vocal removal"},
    "echo": {"echo": 0.5, "description": "Echo effect"},
    "3d": {"rotation": True, "description": "3D audio effect"},
    "gaming": {"bass": 8, "clarity": True, "description": "Gaming optimized"}
}

# Platform configurations
PLATFORM_CONFIG = {
    "youtube": {
        "name": "YouTube",
        "emoji": BotEmojis.YOUTUBE,
        "color": BotColors.ERROR_RED,
        "max_duration": 10800  # 3 hours
    },
    "spotify": {
        "name": "Spotify",
        "emoji": BotEmojis.SPOTIFY,
        "color": BotColors.NEON_GREEN,
        "max_duration": 7200  # 2 hours
    },
    "soundcloud": {
        "name": "SoundCloud",
        "emoji": BotEmojis.SOUNDCLOUD,
        "color": BotColors.NEON_ORANGE,
        "max_duration": 7200  # 2 hours
    }
}
