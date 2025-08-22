"""
Multi-platform search engine for music
Supports YouTube, Spotify, SoundCloud, and more
"""

import wavelink
import re
from typing import Optional, List, Union
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import aiohttp


class SearchEngine:
    """Multi-platform music search engine"""

    def __init__(self, bot):
        self.bot = bot
        self.spotify = None

        # Initialize Spotify if credentials available
        if bot.config.SPOTIFY_CLIENT_ID and bot.config.SPOTIFY_CLIENT_SECRET:
            self.spotify = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=bot.config.SPOTIFY_CLIENT_ID,
                    client_secret=bot.config.SPOTIFY_CLIENT_SECRET
                )
            )

    async def search(self, query: str) -> Optional[
        Union[wavelink.Playable, wavelink.Playlist, List[wavelink.Playable]]]:
        """
        Search for tracks across multiple platforms
        Automatically detects URLs and searches appropriate platform
        """
        # Check if it's a URL
        if self.is_url(query):
            return await self.search_url(query)

        # Check for platform-specific searches
        if query.startswith("spotify:"):
            return await self.search_spotify(query[8:])
        elif query.startswith("soundcloud:"):
            return await self.search_soundcloud(query[11:])
        elif query.startswith("ytsearch:"):
            return await self.search_youtube(query[9:])

        # Default to YouTube search
        return await self.search_youtube(query)

    def is_url(self, query: str) -> bool:
        """Check if query is a URL"""
        url_pattern = re.compile(
            r'^https?://'
            r'(?:www\.)?'
            r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
            r'[a-zA-Z0-9()]{1,6}\b'
            r'(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)$'
        )
        return bool(url_pattern.match(query))

    async def search_url(self, url: str) -> Optional[Union[wavelink.Playable, wavelink.Playlist]]:
        """Handle direct URL searches"""
        # Spotify URL
        if "spotify.com" in url:
            return await self.handle_spotify_url(url)

        # SoundCloud URL
        elif "soundcloud.com" in url:
            return await self.search_soundcloud_url(url)

        # YouTube URL (default)
        else:
            return await self.search_youtube_url(url)

    async def search_youtube(self, query: str) -> Optional[
        Union[wavelink.Playable, wavelink.Playlist, List[wavelink.Playable]]]:
        """Search YouTube for tracks"""
        try:
            # Check if it's a playlist URL
            if "playlist?list=" in query or "/playlist/" in query:
                tracks = await wavelink.Playable.search(query)
                return tracks

            # Regular search
            tracks = await wavelink.Playable.search(query)

            if not tracks:
                return None

            # Return playlist if found
            if isinstance(tracks, wavelink.Playlist):
                return tracks

            # Return first result for single track
            return tracks

        except Exception as e:
            self.bot.logger.error(f"YouTube search error: {e}")
            return None

    async def search_youtube_url(self, url: str) -> Optional[Union[wavelink.Playable, wavelink.Playlist]]:
        """Handle YouTube URLs directly"""
        try:
            tracks = await wavelink.Playable.search(url)
            return tracks
        except Exception as e:
            self.bot.logger.error(f"YouTube URL search error: {e}")
            return None

    async def search_spotify(self, query: str) -> Optional[List[wavelink.Playable]]:
        """Search Spotify and convert to YouTube tracks"""
        if not self.spotify:
            self.bot.logger.warning("Spotify credentials not configured")
            return None

        try:
            # Search Spotify
            results = self.spotify.search(q=query, type='track', limit=1)

            if not results['tracks']['items']:
                return None

            track = results['tracks']['items'][0]

            # Build YouTube search query
            artists = ', '.join([artist['name'] for artist in track['artists']])
            search_query = f"{artists} - {track['name']}"

            # Search on YouTube
            return await self.search_youtube(search_query)

        except Exception as e:
            self.bot.logger.error(f"Spotify search error: {e}")
            return None

    async def handle_spotify_url(self, url: str) -> Optional[Union[wavelink.Playable, List[wavelink.Playable]]]:
        """Handle Spotify URLs (track/playlist/album)"""
        if not self.spotify:
            self.bot.logger.warning("Spotify credentials not configured")
            return None

        try:
            # Extract Spotify ID from URL
            if "/track/" in url:
                track_id = url.split("/track/")[1].split("?")[0]
                return await self.handle_spotify_track(track_id)

            elif "/playlist/" in url:
                playlist_id = url.split("/playlist/")[1].split("?")[0]
                return await self.handle_spotify_playlist(playlist_id)

            elif "/album/" in url:
                album_id = url.split("/album/")[1].split("?")[0]
                return await self.handle_spotify_album(album_id)

            return None

        except Exception as e:
            self.bot.logger.error(f"Spotify URL error: {e}")
            return None

    async def handle_spotify_track(self, track_id: str) -> Optional[wavelink.Playable]:
        """Convert Spotify track to YouTube"""
        try:
            track = self.spotify.track(track_id)

            # Build search query
            artists = ', '.join([artist['name'] for artist in track['artists']])
            search_query = f"{artists} - {track['name']}"

            # Search on YouTube
            result = await self.search_youtube(search_query)
            return result[0] if isinstance(result, list) else result

        except Exception as e:
            self.bot.logger.error(f"Spotify track error: {e}")
            return None

    async def handle_spotify_playlist(self, playlist_id: str) -> Optional[List[wavelink.Playable]]:
        """Convert Spotify playlist to YouTube tracks"""
        try:
            # Get playlist tracks
            results = self.spotify.playlist_tracks(playlist_id, limit=50)
            tracks = []

            for item in results['items'][:25]:  # Limit to 25 tracks
                if item['track']:
                    track = item['track']
                    artists = ', '.join([artist['name'] for artist in track['artists']])
                    search_query = f"{artists} - {track['name']}"

                    # Search on YouTube
                    yt_result = await self.search_youtube(search_query)
                    if yt_result:
                        if isinstance(yt_result, list):
                            tracks.append(yt_result[0])
                        else:
                            tracks.append(yt_result)

            return tracks if tracks else None

        except Exception as e:
            self.bot.logger.error(f"Spotify playlist error: {e}")
            return None

    async def handle_spotify_album(self, album_id: str) -> Optional[List[wavelink.Playable]]:
        """Convert Spotify album to YouTube tracks"""
        try:
            # Get album tracks
            results = self.spotify.album_tracks(album_id, limit=50)
            album = self.spotify.album(album_id)
            tracks = []

            for item in results['items']:
                artists = ', '.join([artist['name'] for artist in item['artists']])
                search_query = f"{artists} - {item['name']}"

                # Search on YouTube
                yt_result = await self.search_youtube(search_query)
                if yt_result:
                    if isinstance(yt_result, list):
                        tracks.append(yt_result[0])
                    else:
                        tracks.append(yt_result)

            return tracks if tracks else None

        except Exception as e:
            self.bot.logger.error(f"Spotify album error: {e}")
            return None

    async def search_soundcloud(self, query: str) -> Optional[wavelink.Playable]:
        """Search SoundCloud for tracks"""
        try:
            # Use wavelink's SoundCloud search
            search_query = f"scsearch:{query}"
            tracks = await wavelink.Playable.search(search_query)

            if not tracks:
                return None

            return tracks[0] if isinstance(tracks, list) else tracks

        except Exception as e:
            self.bot.logger.error(f"SoundCloud search error: {e}")
            return None

    async def search_soundcloud_url(self, url: str) -> Optional[wavelink.Playable]:
        """Handle SoundCloud URLs"""
        try:
            tracks = await wavelink.Playable.search(url)
            return tracks
        except Exception as e:
            self.bot.logger.error(f"SoundCloud URL error: {e}")
            return None

    async def get_recommendations(self, track: wavelink.Playable, limit: int = 5) -> List[wavelink.Playable]:
        """Get track recommendations based on current track"""
        recommendations = []

        # If Spotify is available, use their recommendation engine
        if self.spotify and hasattr(track, 'title'):
            try:
                # Search for the track on Spotify
                results = self.spotify.search(
                    q=f"{track.author} {track.title}" if track.author else track.title,
                    type='track',
                    limit=1
                )

                if results['tracks']['items']:
                    spotify_track = results['tracks']['items'][0]
                    track_id = spotify_track['id']

                    # Get recommendations
                    recs = self.spotify.recommendations(
                        seed_tracks=[track_id],
                        limit=limit
                    )

                    for rec_track in recs['tracks']:
                        artists = ', '.join([artist['name'] for artist in rec_track['artists']])
                        search_query = f"{artists} - {rec_track['name']}"

                        yt_result = await self.search_youtube(search_query)
                        if yt_result:
                            if isinstance(yt_result, list):
                                recommendations.append(yt_result[0])
                            else:
                                recommendations.append(yt_result)

            except Exception as e:
                self.bot.logger.error(f"Recommendation error: {e}")

        # Fallback: Search for similar artist tracks
        if not recommendations and track.author:
            try:
                search_query = f"{track.author} top tracks"
                results = await self.search_youtube(search_query)

                if results:
                    if isinstance(results, list):
                        recommendations = results[:limit]
                    elif isinstance(results, wavelink.Playlist):
                        recommendations = results.tracks[:limit]

            except Exception as e:
                self.bot.logger.error(f"Fallback recommendation error: {e}")

        return recommendations

    async def search_lyrics(self, track: wavelink.Playable) -> Optional[str]:
        """Search for track lyrics using Genius API"""
        if not self.bot.config.GENIUS_API_TOKEN:
            return None

        try:
            import lyricsgenius
            genius = lyricsgenius.Genius(self.bot.config.GENIUS_API_TOKEN)

            # Search for song
            song = genius.search_song(
                title=track.title,
                artist=track.author if track.author else ""
            )

            if song:
                # Clean up lyrics
                lyrics = song.lyrics
                # Remove [Verse], [Chorus] etc tags
                lyrics = re.sub(r'\[.*?\]', '', lyrics)
                # Limit length
                if len(lyrics) > self.bot.config.MAX_LYRICS_LENGTH:
                    lyrics = lyrics[:self.bot.config.MAX_LYRICS_LENGTH] + "..."

                return lyrics

            return None

        except Exception as e:
            self.bot.logger.error(f"Lyrics search error: {e}")
            return None

    async def get_track_info(self, track: wavelink.Playable) -> dict:
        """Get detailed track information"""
        info = {
            'title': track.title,
            'author': track.author,
            'duration': track.length // 1000,
            'url': track.uri,
            'thumbnail': track.artwork,
            'platform': 'Unknown'
        }

        # Detect platform
        if 'youtube' in track.uri.lower():
            info['platform'] = 'YouTube'
        elif 'soundcloud' in track.uri.lower():
            info['platform'] = 'SoundCloud'
        elif 'spotify' in track.uri.lower():
            info['platform'] = 'Spotify'

        return info
