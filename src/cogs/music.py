"""
Music cog with gaming-inspired features
Zero-lag streaming, multi-platform support, and advanced audio effects
"""

import discord
from discord.ext import commands
import wavelink
import asyncio
from typing import Optional, List
import re
from datetime import datetime, timedelta
import random

from bot.config import BotColors, BotEmojis, PLATFORM_CONFIG, EFFECT_PRESETS
from core.queue_manager import QueueManager
from core.search_engine import SearchEngine
from utils.helpers import format_duration, create_progress_bar


class MusicPlayer(wavelink.Player):
    """Enhanced player with gaming features"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = QueueManager()
        self.loop_mode = "off"  # off, track, queue
        self.effects = {
            "bass_boost": 0,
            "nightcore": False,
            "karaoke": False,
            "echo": False,
            "3d": False
        }
        self.dj_enabled = False
        self.last_activity = datetime.utcnow()
        self.skip_votes = set()
        self.session_stats = {
            "songs_played": 0,
            "total_duration": 0,
            "most_played": {}
        }


class Music(commands.Cog):
    """Music commands with gaming-inspired design"""

    def __init__(self, bot):
        self.bot = bot
        self.search_engine = SearchEngine(bot)
        self.emoji = BotEmojis()
        self.colors = BotColors()

    async def cog_load(self):
        """Initialize wavelink nodes"""
        nodes = [
            wavelink.Node(
                uri="http://localhost:2333",
                password="youshallnotpass",
                retries=3
            )
        ]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot)

    async def cog_check(self, ctx):
        """Check if command can be run"""
        if not ctx.guild:
            raise commands.NoPrivateMessage("Music commands can't be used in DMs")
        return True

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Node ready event"""
        self.bot.logger.info(f"Wavelink node {payload.node.identifier} ready")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Track start event"""
        player = payload.player
        track = payload.track

        if not player.guild:
            return

        player.session_stats["songs_played"] += 1
        player.session_stats["total_duration"] += track.length // 1000

        # Update most played
        track_name = track.title
        if track_name in player.session_stats["most_played"]:
            player.session_stats["most_played"][track_name] += 1
        else:
            player.session_stats["most_played"][track_name] = 1

        # Create now playing embed
        embed = self.create_now_playing_embed(player, track)

        # Get the text channel
        channel = player.ctx.channel if hasattr(player, 'ctx') else None
        if channel:
            message = await channel.send(embed=embed)

            # Add control reactions
            controls = ["⏮️", "⏸️", "⏭️", "🔁", "🔀", "⏹️"]
            for emoji in controls:
                await message.add_reaction(emoji)

            # Store message for updates
            player.now_playing_message = message

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Track end event"""
        player = payload.player

        if not player.guild:
            return

        # Handle loop modes
        if player.loop_mode == "track":
            await player.play(payload.track)
            return
        elif player.loop_mode == "queue" and player.queue.is_empty:
            # Re-add all tracks to queue
            player.queue.reset_loop()

        # Auto-play next track
        if not player.queue.is_empty:
            next_track = await player.queue.get()
            await player.play(next_track)
        elif player.dj_enabled:
            # Auto-DJ: Play recommended track
            await self.auto_dj_next(player)
        else:
            # Disconnect after timeout
            await asyncio.sleep(player.bot.config.AUTO_DISCONNECT_TIMEOUT)
            if not player.playing and player.queue.is_empty:
                await player.disconnect()

    def create_now_playing_embed(self, player, track) -> discord.Embed:
        """Create gaming-styled now playing embed"""
        # Determine platform
        platform = self.detect_platform(track.uri)
        platform_config = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG["youtube"])

        # Create embed
        embed = discord.Embed(
            title=f"{self.emoji.GAMING} Now Playing",
            color=platform_config["color"]
        )

        # Track info
        embed.add_field(
            name=f"{self.emoji.MUSIC} Track",
            value=f"**{track.title}**",
            inline=False
        )

        embed.add_field(
            name=f"{self.emoji.FIRE} Artist",
            value=track.author or "Unknown",
            inline=True
        )

        embed.add_field(
            name="⏱️ Duration",
            value=format_duration(track.length // 1000),
            inline=True
        )

        embed.add_field(
            name=f"{platform_config['emoji']} Platform",
            value=platform_config["name"],
            inline=True
        )

        # Volume and effects
        effects_active = [name for name, value in player.effects.items() if value]
        effects_str = ", ".join(effects_active) if effects_active else "None"

        embed.add_field(
            name=f"{self.emoji.VOLUME_HIGH} Volume",
            value=f"{player.volume}%",
            inline=True
        )

        embed.add_field(
            name=f"{self.emoji.LIGHTNING} Effects",
            value=effects_str,
            inline=True
        )

        embed.add_field(
            name=f"{self.emoji.LOOP} Loop",
            value=player.loop_mode.capitalize(),
            inline=True
        )

        # Progress bar (will be updated dynamically)
        progress = create_progress_bar(0, track.length // 1000)
        embed.add_field(
            name="Progress",
            value=progress,
            inline=False
        )

        # Queue info
        if not player.queue.is_empty:
            embed.add_field(
                name=f"{self.emoji.QUEUE} Queue",
                value=f"{len(player.queue)} tracks remaining",
                inline=False
            )

        # Thumbnail
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        # Footer
        embed.set_footer(
            text=f"🎮 Gaming Mode Active | Session: {player.session_stats['songs_played']} songs played",
            icon_url=self.bot.user.display_avatar.url
        )

        embed.timestamp = datetime.utcnow()

        return embed

    def detect_platform(self, uri: str) -> str:
        """Detect platform from URI"""
        if "youtube" in uri or "youtu.be" in uri:
            return "youtube"
        elif "spotify" in uri:
            return "spotify"
        elif "soundcloud" in uri:
            return "soundcloud"
        return "youtube"

    async def auto_dj_next(self, player):
        """Auto-DJ feature to play recommended tracks"""
        # This would integrate with recommendation algorithms
        # For now, play a random popular track
        pass

    @commands.hybrid_command(name="play", aliases=["p"], description="Play a song or playlist")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def play(self, ctx, *, query: str):
        """Play a song with zero-lag streaming"""
        # Check voice channel
        if not ctx.author.voice:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Not Connected",
                description="You need to be in a voice channel to play music!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Get or create player
        player = ctx.voice_client
        if not player:
            player = await ctx.author.voice.channel.connect(cls=MusicPlayer)
            player.ctx = ctx

        # Show loading embed
        loading_embed = discord.Embed(
            title=f"{self.emoji.LOADING} Searching...",
            description=f"Looking for: **{query}**",
            color=self.colors.LOADING
        )
        loading_msg = await ctx.send(embed=loading_embed)

        # Search for tracks
        tracks = await self.search_engine.search(query)

        if not tracks:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} No Results",
                description=f"No tracks found for: **{query}**",
                color=self.colors.ERROR_RED
            )
            await loading_msg.edit(embed=embed)
            return await loading_msg.delete(delay=10)

        # Handle playlist
        if isinstance(tracks, wavelink.Playlist):
            added = len(tracks.tracks)
            for track in tracks.tracks:
                track.requester = ctx.author
                await player.queue.put(track)

            embed = discord.Embed(
                title=f"{self.emoji.SUCCESS} Playlist Added",
                description=f"Added **{added}** tracks from **{tracks.name}**",
                color=self.colors.SUCCESS
            )
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await loading_msg.edit(embed=embed)
        else:
            # Single track
            track = tracks[0] if isinstance(tracks, list) else tracks
            track.requester = ctx.author

            # Add to queue or play immediately
            if player.playing:
                await player.queue.put(track)
                position = len(player.queue)

                embed = discord.Embed(
                    title=f"{self.emoji.SUCCESS} Added to Queue",
                    color=self.colors.SUCCESS
                )
                embed.add_field(
                    name="Track",
                    value=f"**{track.title}**",
                    inline=False
                )
                embed.add_field(
                    name="Position",
                    value=f"#{position}",
                    inline=True
                )
                embed.add_field(
                    name="Duration",
                    value=format_duration(track.length // 1000),
                    inline=True
                )
                embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

                if track.artwork:
                    embed.set_thumbnail(url=track.artwork)

                await loading_msg.edit(embed=embed)
            else:
                await player.play(track)
                await loading_msg.delete()

        # Update bot stats
        self.bot.songs_played += 1

    @commands.hybrid_command(name="pause", description="Pause the current track")
    async def pause(self, ctx):
        """Pause playback"""
        player = ctx.voice_client

        if not player or not player.playing:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="There's no music playing to pause!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        await player.pause(True)

        embed = discord.Embed(
            title=f"{self.emoji.PAUSE} Paused",
            description=f"Playback paused by {ctx.author.mention}",
            color=self.colors.PAUSED
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="resume", aliases=["unpause"], description="Resume playback")
    async def resume(self, ctx):
        """Resume playback"""
        player = ctx.voice_client

        if not player or not player.paused:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Not Paused",
                description="The music isn't paused!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        await player.pause(False)

        embed = discord.Embed(
            title=f"{self.emoji.PLAY} Resumed",
            description=f"Playback resumed by {ctx.author.mention}",
            color=self.colors.PLAYING
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="skip", aliases=["s", "next"], description="Skip the current track")
    async def skip(self, ctx):
        """Skip current track with vote system"""
        player = ctx.voice_client

        if not player or not player.playing:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="There's no music to skip!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Check if requester or admin
        current_track = player.current
        if ctx.author == current_track.requester or ctx.author.guild_permissions.manage_guild:
            await player.skip()
            embed = discord.Embed(
                title=f"{self.emoji.SKIP} Skipped",
                description=f"Skipped **{current_track.title}**",
                color=self.colors.SUCCESS
            )
            await ctx.send(embed=embed)
        else:
            # Vote skip system
            voice_members = len([m for m in ctx.author.voice.channel.members if not m.bot])
            required_votes = max(2, voice_members // 2)

            player.skip_votes.add(ctx.author.id)
            current_votes = len(player.skip_votes)

            if current_votes >= required_votes:
                await player.skip()
                embed = discord.Embed(
                    title=f"{self.emoji.SKIP} Vote Skip Successful",
                    description=f"Skipped **{current_track.title}**",
                    color=self.colors.SUCCESS
                )
                player.skip_votes.clear()
            else:
                embed = discord.Embed(
                    title=f"{self.emoji.INFO} Vote Skip",
                    description=f"Vote skip: **{current_votes}/{required_votes}**",
                    color=self.colors.INFO_BLUE
                )

            await ctx.send(embed=embed)

    @commands.hybrid_command(name="queue", aliases=["q"], description="Show the music queue")
    async def queue(self, ctx):
        """Display queue with gaming style"""
        player = ctx.voice_client

        if not player or player.queue.is_empty:
            embed = discord.Embed(
                title=f"{self.emoji.QUEUE} Queue Empty",
                description="No tracks in queue. Add some with `/play`!",
                color=self.colors.INFO_BLUE
            )
            return await ctx.send(embed=embed)

        # Create paginated queue
        queue_list = list(player.queue)[:10]  # Show first 10

        embed = discord.Embed(
            title=f"{self.emoji.QUEUE} Music Queue",
            color=self.colors.NEON_PURPLE
        )

        # Current track
        if player.current:
            embed.add_field(
                name=f"{self.emoji.PLAY} Now Playing",
                value=f"**{player.current.title}**\n"
                      f"By {player.current.author} • {format_duration(player.current.length // 1000)}",
                inline=False
            )

        # Queue tracks
        queue_text = ""
        total_duration = 0

        for i, track in enumerate(queue_list, 1):
            duration = format_duration(track.length // 1000)
            total_duration += track.length // 1000

            # Gaming-style numbering
            number_emoji = f"`#{i:02d}`"
            queue_text += f"{number_emoji} **{track.title[:40]}**\n"
            queue_text += f"　　 {track.author[:30]} • {duration}\n\n"

        embed.add_field(
            name=f"{self.emoji.FIRE} Up Next",
            value=queue_text or "Empty",
            inline=False
        )

        # Queue stats
        embed.add_field(
            name=f"{self.emoji.INFO} Queue Stats",
            value=f"**Tracks:** {len(player.queue)}\n"
                  f"**Duration:** {format_duration(total_duration)}\n"
                  f"**Loop:** {player.loop_mode.capitalize()}",
            inline=True
        )

        # Effects active
        effects_active = [name for name, value in player.effects.items() if value]
        effects_str = ", ".join(effects_active) if effects_active else "None"
        embed.add_field(
            name=f"{self.emoji.LIGHTNING} Effects",
            value=effects_str,
            inline=True
        )

        embed.set_footer(
            text=f"🎮 Gaming Mode • Page 1/{max(1, len(player.queue) // 10)}",
            icon_url=self.bot.user.display_avatar.url
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="Show current track")
    async def nowplaying(self, ctx):
        """Show now playing with progress"""
        player = ctx.voice_client

        if not player or not player.current:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="No track is currently playing!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        track = player.current

        # Calculate progress
        position = player.position // 1000
        duration = track.length // 1000
        progress_bar = create_progress_bar(position, duration)

        embed = discord.Embed(
            title=f"{self.emoji.GAMING} Now Playing",
            color=self.colors.PLAYING
        )

        embed.add_field(
            name=f"{self.emoji.MUSIC} Track",
            value=f"**{track.title}**",
            inline=False
        )

        embed.add_field(
            name=f"{self.emoji.FIRE} Artist",
            value=track.author or "Unknown",
            inline=True
        )

        embed.add_field(
            name="⏱️ Progress",
            value=f"{format_duration(position)} / {format_duration(duration)}",
            inline=True
        )

        embed.add_field(
            name="Progress Bar",
            value=progress_bar,
            inline=False
        )

        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        embed.set_footer(
            text=f"Requested by {track.requester}",
            icon_url=track.requester.display_avatar.url
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="volume", aliases=["vol"], description="Adjust volume")
    async def volume(self, ctx, volume: int = None):
        """Set volume with visual feedback"""
        player = ctx.voice_client

        if not player:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Not Connected",
                description="I'm not connected to a voice channel!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        if volume is None:
            # Show current volume
            volume_bar = self.create_volume_bar(player.volume)
            embed = discord.Embed(
                title=f"{self.emoji.VOLUME_HIGH} Current Volume",
                description=f"Volume: **{player.volume}%**\n{volume_bar}",
                color=self.colors.INFO_BLUE
            )
            return await ctx.send(embed=embed)

        # Set volume
        if not 0 <= volume <= self.bot.config.MAX_VOLUME:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Invalid Volume",
                description=f"Volume must be between 0 and {self.bot.config.MAX_VOLUME}!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        await player.set_volume(volume)

        # Volume emoji based on level
        if volume == 0:
            vol_emoji = self.emoji.VOLUME_MUTE
        elif volume < 33:
            vol_emoji = self.emoji.VOLUME_LOW
        elif volume < 66:
            vol_emoji = self.emoji.VOLUME_MEDIUM
        else:
            vol_emoji = self.emoji.VOLUME_HIGH

        volume_bar = self.create_volume_bar(volume)

        embed = discord.Embed(
            title=f"{vol_emoji} Volume Set",
            description=f"Volume: **{volume}%**\n{volume_bar}",
            color=self.colors.SUCCESS
        )
        await ctx.send(embed=embed)

    def create_volume_bar(self, volume: int) -> str:
        """Create visual volume bar"""
        max_vol = self.bot.config.MAX_VOLUME
        filled = int((volume / max_vol) * 10)
        bar = "🟦" * filled + "⬜" * (10 - filled)
        return f"{bar} {volume}%"

    @commands.hybrid_command(name="disconnect", aliases=["dc", "leave"], description="Disconnect the bot")
    async def disconnect(self, ctx):
        """Disconnect with session stats"""
        player = ctx.voice_client

        if not player:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Not Connected",
                description="I'm not in a voice channel!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Show session stats
        stats = player.session_stats
        embed = discord.Embed(
            title=f"{self.emoji.STOP} Session Ended",
            description="Thanks for listening! Here are your session stats:",
            color=self.colors.NEON_PURPLE
        )

        embed.add_field(
            name=f"{self.emoji.MUSIC} Songs Played",
            value=stats["songs_played"],
            inline=True
        )

        embed.add_field(
            name="⏱️ Total Duration",
            value=format_duration(stats["total_duration"]),
            inline=True
        )

        if stats["most_played"]:
            most_played = max(stats["most_played"], key=stats["most_played"].get)
            embed.add_field(
                name=f"{self.emoji.CROWN} Most Played",
                value=most_played,
                inline=False
            )

        embed.set_footer(
            text="🎮 See you next time!",
            icon_url=self.bot.user.display_avatar.url
        )

        await ctx.send(embed=embed)
        await player.disconnect()


async def setup(bot):
    await bot.add_cog(Music(bot))
