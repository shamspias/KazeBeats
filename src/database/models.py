"""
Database models using SQLAlchemy
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, BigInteger, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Guild(Base):
    """Guild (Discord server) model"""
    __tablename__ = 'guilds'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False)
    prefix = Column(String(10), default='!')
    volume = Column(Float, default=0.5)
    max_queue_size = Column(Integer, default=100)
    dj_role_id = Column(BigInteger, nullable=True)
    announcement_channel_id = Column(BigInteger, nullable=True)
    premium = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default=dict)

    # Relationships
    play_history = relationship("PlayHistory", back_populates="guild", cascade="all, delete-orphan")
    playlists = relationship("Playlist", back_populates="guild", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_guild_premium', 'premium'),
    )


class User(Base):
    """User model"""
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String(100), nullable=False)
    discriminator = Column(String(10))
    play_count = Column(Integer, default=0)
    favorite_genre = Column(String(50))
    total_listening_time = Column(Integer, default=0)  # in seconds
    last_played = Column(DateTime)
    premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    preferences = Column(JSON, default=dict)

    # Relationships
    play_history = relationship("PlayHistory", back_populates="user")
    playlists = relationship("Playlist", back_populates="owner")

    # Indexes
    __table_args__ = (
        Index('idx_user_premium', 'premium'),
        Index('idx_user_play_count', 'play_count'),
    )


class PlayHistory(Base):
    """Play history model"""
    __tablename__ = 'play_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    track_title = Column(String(200), nullable=False)
    track_url = Column(Text)
    track_duration = Column(Integer)  # in seconds
    source = Column(String(50))  # YouTube, Spotify, etc.
    played_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    guild = relationship("Guild", back_populates="play_history")
    user = relationship("User", back_populates="play_history")

    # Indexes
    __table_args__ = (
        Index('idx_history_guild', 'guild_id'),
        Index('idx_history_user', 'user_id'),
        Index('idx_history_played_at', 'played_at'),
        Index('idx_history_track', 'track_title'),
    )


class Playlist(Base):
    """Playlist model"""
    __tablename__ = 'playlists'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    play_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guild = relationship("Guild", back_populates="playlists")
    owner = relationship("User", back_populates="playlists")
    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_playlist_guild', 'guild_id'),
        Index('idx_playlist_user', 'user_id'),
        Index('idx_playlist_public', 'is_public'),
    )


class PlaylistTrack(Base):
    """Playlist track model"""
    __tablename__ = 'playlist_tracks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey('playlists.id'), nullable=False)
    track_url = Column(Text, nullable=False)
    track_title = Column(String(200), nullable=False)
    track_duration = Column(Integer)
    track_artist = Column(String(100))
    track_thumbnail = Column(Text)
    position = Column(Integer, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(BigInteger)  # User ID

    # Relationships
    playlist = relationship("Playlist", back_populates="tracks")

    # Indexes
    __table_args__ = (
        Index('idx_playlist_track_playlist', 'playlist_id'),
        Index('idx_playlist_track_position', 'position'),
    )


class Analytics(Base):
    """Analytics data model"""
    __tablename__ = 'analytics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False)
    date = Column(DateTime, nullable=False)
    total_plays = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    total_duration = Column(Integer, default=0)  # in seconds
    popular_tracks = Column(JSON, default=list)
    popular_sources = Column(JSON, default=dict)
    peak_listeners = Column(Integer, default=0)

    # Indexes
    __table_args__ = (
        Index('idx_analytics_guild_date', 'guild_id', 'date'),
    )


# src/database/manager.py
"""
Database manager for all database operations
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from database.models import Base, Guild, User, PlayHistory, Playlist, PlaylistTrack, Analytics

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Async database manager"""

    def __init__(self, config):
        self.config = config
        self.engine: Optional[AsyncEngine] = None
        self.async_session: Optional[sessionmaker] = None

    async def initialize(self):
        """Initialize database connection"""
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.config.connection_string.replace('postgresql://', 'postgresql+asyncpg://'),
                echo=False,
                pool_size=self.config.connection_pool_size if hasattr(self.config, 'connection_pool_size') else 10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )

            # Create session factory
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    @asynccontextmanager
    async def get_session(self):
        """Get database session context manager"""
        if not self.async_session:
            raise RuntimeError("Database not initialized")

        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                await session.close()

    # Guild operations
    async def add_guild(self, guild_id: int, name: str) -> Guild:
        """Add or update guild"""
        async with self.get_session() as session:
            guild = await session.get(Guild, guild_id)

            if not guild:
                guild = Guild(id=guild_id, name=name)
                session.add(guild)
            else:
                guild.name = name

            await session.commit()
            return guild

    async def get_guild(self, guild_id: int) -> Optional[Guild]:
        """Get guild by ID"""
        async with self.get_session() as session:
            return await session.get(Guild, guild_id)

    async def remove_guild(self, guild_id: int):
        """Remove guild and all related data"""
        async with self.get_session() as session:
            guild = await session.get(Guild, guild_id)
            if guild:
                await session.delete(guild)
                await session.commit()

    async def get_guild_prefix(self, guild_id: int) -> Optional[str]:
        """Get guild custom prefix"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Guild.prefix).where(Guild.id == guild_id)
            )
            row = result.first()
            return row[0] if row else None

    async def set_guild_prefix(self, guild_id: int, prefix: str):
        """Set guild custom prefix"""
        async with self.get_session() as session:
            await session.execute(
                update(Guild).where(Guild.id == guild_id).values(prefix=prefix)
            )
            await session.commit()

    # User operations
    async def get_or_create_user(self, user_id: int, username: str) -> User:
        """Get or create user"""
        async with self.get_session() as session:
            user = await session.get(User, user_id)

            if not user:
                user = User(id=user_id, username=username)
                session.add(user)
                await session.commit()

            return user

    async def update_user_stats(self, user_id: int, duration: int):
        """Update user statistics"""
        async with self.get_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    play_count=User.play_count + 1,
                    total_listening_time=User.total_listening_time + duration,
                    last_played=datetime.utcnow()
                )
            )
            await session.commit()

    # Play history operations
    async def log_play(self, guild_id: int, user_id: int, track_title: str,
                       track_url: str, source: str, duration: int = 0):
        """Log track play to history"""
        async with self.get_session() as session:
            # Ensure guild exists
            guild = await session.get(Guild, guild_id)
            if not guild:
                guild = Guild(id=guild_id, name="Unknown")
                session.add(guild)

            # Ensure user exists
            user = await session.get(User, user_id)
            if not user:
                user = User(id=user_id, username="Unknown")
                session.add(user)

            # Add play history
            history = PlayHistory(
                guild_id=guild_id,
                user_id=user_id,
                track_title=track_title,
                track_url=track_url,
                track_duration=duration,
                source=source
            )
            session.add(history)

            # Update user stats
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    play_count=User.play_count + 1,
                    total_listening_time=User.total_listening_time + duration,
                    last_played=datetime.utcnow()
                )
            )

            await session.commit()

    async def get_top_tracks(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Get most played tracks in a guild"""
        async with self.get_session() as session:
            result = await session.execute(
                select(
                    PlayHistory.track_title,
                    func.count(PlayHistory.id).label('play_count'),
                    PlayHistory.source
                )
                .where(PlayHistory.guild_id == guild_id)
                .group_by(PlayHistory.track_title, PlayHistory.source)
                .order_by(func.count(PlayHistory.id).desc())
                .limit(limit)
            )

            return [
                {
                    'title': row.track_title,
                    'plays': row.play_count,
                    'source': row.source
                }
                for row in result
            ]

    async def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user statistics"""
        async with self.get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return None

            # Get recent tracks
            recent_tracks = await session.execute(
                select(PlayHistory)
                .where(PlayHistory.user_id == user_id)
                .order_by(PlayHistory.played_at.desc())
                .limit(10)
            )

            return {
                'username': user.username,
                'play_count': user.play_count,
                'total_listening_time': user.total_listening_time,
                'last_played': user.last_played,
                'recent_tracks': [
                    {
                        'title': track.track_title,
                        'source': track.source,
                        'played_at': track.played_at
                    }
                    for track in recent_tracks.scalars()
                ]
            }

    # Playlist operations
    async def create_playlist(self, user_id: int, name: str,
                              description: str = "", guild_id: Optional[int] = None) -> Playlist:
        """Create a new playlist"""
        async with self.get_session() as session:
            playlist = Playlist(
                user_id=user_id,
                guild_id=guild_id,
                name=name,
                description=description
            )
            session.add(playlist)
            await session.commit()
            return playlist

    async def get_playlist(self, playlist_id: int) -> Optional[Playlist]:
        """Get playlist by ID"""
        async with self.get_session() as session:
            return await session.get(Playlist, playlist_id)

    async def get_user_playlists(self, user_id: int) -> List[Playlist]:
        """Get all playlists for a user"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Playlist)
                .where(Playlist.user_id == user_id)
                .order_by(Playlist.created_at.desc())
            )
            return list(result.scalars())

    async def add_track_to_playlist(self, playlist_id: int, track_data: Dict):
        """Add track to playlist"""
        async with self.get_session() as session:
            # Get current max position
            result = await session.execute(
                select(func.max(PlaylistTrack.position))
                .where(PlaylistTrack.playlist_id == playlist_id)
            )
            max_position = result.scalar() or 0

            # Add track
            track = PlaylistTrack(
                playlist_id=playlist_id,
                track_url=track_data['url'],
                track_title=track_data['title'],
                track_duration=track_data.get('duration', 0),
                track_artist=track_data.get('artist'),
                track_thumbnail=track_data.get('thumbnail'),
                position=max_position + 1,
                added_by=track_data.get('added_by')
            )
            session.add(track)

            # Update playlist updated_at
            await session.execute(
                update(Playlist)
                .where(Playlist.id == playlist_id)
                .values(updated_at=datetime.utcnow())
            )

            await session.commit()

    async def get_playlist_tracks(self, playlist_id: int) -> List[PlaylistTrack]:
        """Get all tracks in a playlist"""
        async with self.get_session() as session:
            result = await session.execute(
                select(PlaylistTrack)
                .where(PlaylistTrack.playlist_id == playlist_id)
                .order_by(PlaylistTrack.position)
            )
            return list(result.scalars())

    async def delete_playlist(self, playlist_id: int):
        """Delete a playlist"""
        async with self.get_session() as session:
            playlist = await session.get(Playlist, playlist_id)
            if playlist:
                await session.delete(playlist)
                await session.commit()

    # Analytics operations
    async def update_analytics(self, guild_id: int):
        """Update analytics for a guild"""
        async with self.get_session() as session:
            today = datetime.utcnow().date()

            # Get or create today's analytics
            result = await session.execute(
                select(Analytics)
                .where(
                    and_(
                        Analytics.guild_id == guild_id,
                        func.date(Analytics.date) == today
                    )
                )
            )
            analytics = result.scalar()

            if not analytics:
                analytics = Analytics(
                    guild_id=guild_id,
                    date=datetime.combine(today, datetime.min.time())
                )
                session.add(analytics)

            # Update statistics
            # Get today's plays
            plays_result = await session.execute(
                select(func.count(PlayHistory.id))
                .where(
                    and_(
                        PlayHistory.guild_id == guild_id,
                        func.date(PlayHistory.played_at) == today
                    )
                )
            )
            analytics.total_plays = plays_result.scalar() or 0

            # Get unique users
            users_result = await session.execute(
                select(func.count(func.distinct(PlayHistory.user_id)))
                .where(
                    and_(
                        PlayHistory.guild_id == guild_id,
                        func.date(PlayHistory.played_at) == today
                    )
                )
            )
            analytics.unique_users = users_result.scalar() or 0

            await session.commit()

    async def get_guild_analytics(self, guild_id: int, days: int = 7) -> List[Analytics]:
        """Get analytics for a guild"""
        async with self.get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)

            result = await session.execute(
                select(Analytics)
                .where(
                    and_(
                        Analytics.guild_id == guild_id,
                        Analytics.date >= start_date
                    )
                )
                .order_by(Analytics.date)
            )

            return list(result.scalars())

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
