"""
Database manager for KazeBeats
Handles guild settings, playlists, and analytics
"""

import aiosqlite
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import os


class DatabaseManager:
    """Async database manager"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def setup(self):
        """Initialize database and create tables"""
        self.conn = await aiosqlite.connect(self.db_path)

        # Create tables
        await self.create_tables()

    async def create_tables(self):
        """Create all required tables"""

        # Guild settings table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT,
                dj_role_id INTEGER,
                default_volume INTEGER DEFAULT 100,
                max_queue_size INTEGER DEFAULT 1000,
                vote_skip_ratio INTEGER DEFAULT 50,
                auto_disconnect INTEGER DEFAULT 300,
                auto_dj BOOLEAN DEFAULT FALSE,
                effects_enabled BOOLEAN DEFAULT TRUE,
                playlists_enabled BOOLEAN DEFAULT TRUE,
                lyrics_enabled BOOLEAN DEFAULT TRUE,
                analytics_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User playlists table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                tracks TEXT NOT NULL,
                is_public BOOLEAN DEFAULT FALSE,
                plays INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Music analytics table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS music_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                track_name TEXT NOT NULL,
                track_author TEXT,
                track_url TEXT,
                platform TEXT,
                duration INTEGER,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User stats table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                songs_played INTEGER DEFAULT 0,
                total_listening_time INTEGER DEFAULT 0,
                favorite_genre TEXT,
                commands_used INTEGER DEFAULT 0,
                playlists_created INTEGER DEFAULT 0,
                effects_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Guild stats table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_stats (
                guild_id INTEGER PRIMARY KEY,
                total_songs_played INTEGER DEFAULT 0,
                total_listening_hours INTEGER DEFAULT 0,
                most_played_track TEXT,
                most_active_user INTEGER,
                peak_listeners INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # DJ presets table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS dj_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                effects TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                uses INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.conn.commit()

    # Guild settings methods
    async def get_guild_prefix(self, guild_id: int) -> Optional[str]:
        """Get custom prefix for a guild"""
        async with self.conn.execute(
                "SELECT prefix FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def set_guild_prefix(self, guild_id: int, prefix: str):
        """Set custom prefix for a guild"""
        await self.conn.execute("""
            INSERT INTO guild_settings (guild_id, prefix, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET
                prefix = excluded.prefix,
                updated_at = CURRENT_TIMESTAMP
        """, (guild_id, prefix))
        await self.conn.commit()

    async def delete_guild_prefix(self, guild_id: int):
        """Delete custom prefix (reset to default)"""
        await self.conn.execute("""
            UPDATE guild_settings 
            SET prefix = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
        """, (guild_id,))
        await self.conn.commit()

    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get all settings for a guild"""
        async with self.conn.execute(
                "SELECT * FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if not row:
                return {}

            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

    async def set_guild_dj_role(self, guild_id: int, role_id: int):
        """Set DJ role for a guild"""
        await self.conn.execute("""
            INSERT INTO guild_settings (guild_id, dj_role_id, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET
                dj_role_id = excluded.dj_role_id,
                updated_at = CURRENT_TIMESTAMP
        """, (guild_id, role_id))
        await self.conn.commit()

    async def get_guild_feature(self, guild_id: int, feature: str) -> bool:
        """Get feature toggle state"""
        feature_column = f"{feature}_enabled"
        async with self.conn.execute(
                f"SELECT {feature_column} FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else True  # Default to enabled

    async def set_guild_feature(self, guild_id: int, feature: str, enabled: bool):
        """Set feature toggle state"""
        feature_column = f"{feature}_enabled"
        await self.conn.execute(f"""
            INSERT INTO guild_settings (guild_id, {feature_column}, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET
                {feature_column} = excluded.{feature_column},
                updated_at = CURRENT_TIMESTAMP
        """, (guild_id, enabled))
        await self.conn.commit()

    # Playlist methods
    async def create_playlist(self, user_id: int, guild_id: Optional[int],
                              name: str, description: str = None) -> int:
        """Create a new playlist"""
        async with self.conn.execute("""
            INSERT INTO playlists (user_id, guild_id, name, description, tracks)
            VALUES (?, ?, ?, ?, '[]')
        """, (user_id, guild_id, name, description)) as cursor:
            playlist_id = cursor.lastrowid

        await self.conn.commit()
        return playlist_id

    async def get_user_playlists(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all playlists for a user"""
        async with self.conn.execute("""
            SELECT * FROM playlists 
            WHERE user_id = ? 
            ORDER BY updated_at DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def add_to_playlist(self, playlist_id: int, track_data: Dict[str, Any]):
        """Add track to playlist"""
        async with self.conn.execute(
                "SELECT tracks FROM playlists WHERE id = ?",
                (playlist_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False

            tracks = json.loads(row[0])
            tracks.append(track_data)

            await self.conn.execute("""
                UPDATE playlists 
                SET tracks = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(tracks), playlist_id))
            await self.conn.commit()
            return True

    # Analytics methods
    async def log_track_play(self, guild_id: int, user_id: int,
                             track_name: str, track_author: str = None,
                             track_url: str = None, platform: str = None,
                             duration: int = None):
        """Log a track play for analytics"""
        await self.conn.execute("""
            INSERT INTO music_analytics 
            (guild_id, user_id, track_name, track_author, track_url, platform, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, user_id, track_name, track_author, track_url, platform, duration))

        # Update user stats
        await self.conn.execute("""
            INSERT INTO user_stats (user_id, songs_played, total_listening_time)
            VALUES (?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                songs_played = songs_played + 1,
                total_listening_time = total_listening_time + ?,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, duration or 0, duration or 0))

        # Update guild stats
        await self.conn.execute("""
            INSERT INTO guild_stats (guild_id, total_songs_played, total_listening_hours)
            VALUES (?, 1, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                total_songs_played = total_songs_played + 1,
                total_listening_hours = total_listening_hours + ?,
                updated_at = CURRENT_TIMESTAMP
        """, (guild_id, (duration or 0) / 3600, (duration or 0) / 3600))

        await self.conn.commit()

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics for a user"""
        async with self.conn.execute(
                "SELECT * FROM user_stats WHERE user_id = ?",
                (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {
                    "songs_played": 0,
                    "total_listening_time": 0,
                    "commands_used": 0,
                    "playlists_created": 0
                }

            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

    async def get_guild_stats(self, guild_id: int) -> Dict[str, Any]:
        """Get statistics for a guild"""
        async with self.conn.execute(
                "SELECT * FROM guild_stats WHERE guild_id = ?",
                (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {
                    "total_songs_played": 0,
                    "total_listening_hours": 0,
                    "peak_listeners": 0
                }

            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

    async def get_top_tracks(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most played tracks in a guild"""
        async with self.conn.execute("""
            SELECT track_name, track_author, COUNT(*) as plays
            FROM music_analytics
            WHERE guild_id = ?
            GROUP BY track_name, track_author
            ORDER BY plays DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [
                {"name": row[0], "author": row[1], "plays": row[2]}
                for row in rows
            ]

    async def get_top_users(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most active users in a guild"""
        async with self.conn.execute("""
            SELECT user_id, COUNT(*) as songs_played
            FROM music_analytics
            WHERE guild_id = ?
            GROUP BY user_id
            ORDER BY songs_played DESC
            LIMIT ?
        """, (guild_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [
                {"user_id": row[0], "songs_played": row[1]}
                for row in rows
            ]

    # DJ Presets methods
    async def save_dj_preset(self, guild_id: int, name: str,
                             effects: Dict[str, Any], created_by: int) -> int:
        """Save a DJ effects preset"""
        async with self.conn.execute("""
            INSERT INTO dj_presets (guild_id, name, effects, created_by)
            VALUES (?, ?, ?, ?)
        """, (guild_id, name, json.dumps(effects), created_by)) as cursor:
            preset_id = cursor.lastrowid

        await self.conn.commit()
        return preset_id

    async def get_dj_presets(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all DJ presets for a guild"""
        async with self.conn.execute("""
            SELECT * FROM dj_presets
            WHERE guild_id = ?
            ORDER BY uses DESC, created_at DESC
        """, (guild_id,)) as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            presets = []
            for row in rows:
                preset = dict(zip(columns, row))
                preset['effects'] = json.loads(preset['effects'])
                presets.append(preset)
            return presets

    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
