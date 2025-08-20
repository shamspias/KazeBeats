"""
Admin commands for bot management
"""

import logging
import sys
import os
import psutil
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from utils.helpers import format_time, humanize_number, confirm_action
from utils.decorators import log_command

logger = logging.getLogger(__name__)


class AdminCog(commands.Cog, name="Admin"):
    """Administrative commands for bot owners"""

    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()

    async def cog_check(self, ctx):
        """Check if user is bot owner"""
        return await self.bot.is_owner(ctx.author)

    @commands.command(name='shutdown', aliases=['kill'])
    @log_command()
    async def shutdown(self, ctx):
        """Shutdown the bot"""
        if await confirm_action(ctx, "Are you sure you want to shutdown the bot?"):
            embed = discord.Embed(
                title="🔌 Shutting Down",
                description="Bot is shutting down...",
                color=0xFF0000
            )
            await ctx.send(embed=embed)

            logger.info(f"Shutdown initiated by {ctx.author}")
            await self.bot.close()

    @commands.command(name='restart')
    @log_command()
    async def restart(self, ctx):
        """Restart the bot"""
        if await confirm_action(ctx, "Are you sure you want to restart the bot?"):
            embed = discord.Embed(
                title="🔄 Restarting",
                description="Bot is restarting...",
                color=0xFFAA00
            )
            await ctx.send(embed=embed)

            logger.info(f"Restart initiated by {ctx.author}")

            # Restart using execv
            os.execv(sys.executable, ['python'] + sys.argv)

    @commands.command(name='status')
    async def status(self, ctx):
        """Show bot status and statistics"""
        # Calculate uptime
        uptime = datetime.utcnow() - self.bot.startup_time if self.bot.startup_time else None

        # Get memory usage
        memory_info = self.process.memory_info()
        memory_usage = memory_info.rss / 1024 / 1024  # MB

        # Get CPU usage
        cpu_percent = self.process.cpu_percent(interval=1)

        # Count voice connections
        voice_connections = len(self.bot.voice_clients)

        # Build embed
        embed = discord.Embed(
            title="📊 Bot Status",
            color=0x00FF88,
            timestamp=datetime.utcnow()
        )

        # Basic info
        embed.add_field(
            name="📈 Statistics",
            value=f"**Guilds:** {len(self.bot.guilds)}\n"
                  f"**Users:** {sum(g.member_count for g in self.bot.guilds)}\n"
                  f"**Voice:** {voice_connections} connections",
            inline=True
        )

        # System info
        embed.add_field(
            name="💻 System",
            value=f"**CPU:** {cpu_percent:.1f}%\n"
                  f"**Memory:** {memory_usage:.1f} MB\n"
                  f"**Latency:** {self.bot.latency * 1000:.1f}ms",
            inline=True
        )

        # Uptime
        if uptime:
            embed.add_field(
                name="⏱️ Uptime",
                value=format_time(int(uptime.total_seconds())),
                inline=True
            )

        # Version info
        embed.add_field(
            name="📦 Version",
            value=f"**Bot:** v{self.bot.config.bot_version}\n"
                  f"**Python:** {sys.version.split()[0]}\n"
                  f"**Discord.py:** {discord.__version__}",
            inline=True
        )

        # Environment
        embed.add_field(
            name="🌍 Environment",
            value=f"**Mode:** {self.bot.config.environment}\n"
                  f"**Debug:** {'Yes' if self.bot.config.debug else 'No'}",
            inline=True
        )

        embed.set_footer(text=f"{self.bot.config.bot_name}")

        await ctx.send(embed=embed)

    @commands.command(name='reload')
    @log_command()
    async def reload(self, ctx, cog: str = None):
        """Reload a cog or all cogs"""
        if cog:
            # Reload specific cog
            try:
                await self.bot.reload_extension(f"cogs.{cog}")
                embed = discord.Embed(
                    title="✅ Reloaded",
                    description=f"Successfully reloaded `{cog}`",
                    color=0x00FF88
                )
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to reload `{cog}`: {e}",
                    color=0xFF0000
                )
        else:
            # Reload all cogs
            success = []
            failed = []

            for extension in list(self.bot.extensions):
                try:
                    await self.bot.reload_extension(extension)
                    success.append(extension)
                except Exception as e:
                    failed.append((extension, str(e)))

            embed = discord.Embed(
                title="🔄 Reload Complete",
                color=0x00FF88 if not failed else 0xFFAA00
            )

            if success:
                embed.add_field(
                    name="✅ Success",
                    value="\n".join(success),
                    inline=False
                )

            if failed:
                embed.add_field(
                    name="❌ Failed",
                    value="\n".join(f"{ext}: {err}" for ext, err in failed),
                    inline=False
                )

        await ctx.send(embed=embed)

    @commands.command(name='guilds')
    async def guilds(self, ctx):
        """List all guilds the bot is in"""
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)

        embed = discord.Embed(
            title=f"📋 Guilds ({len(guilds)})",
            color=0x00FF88
        )

        # Show top 10 guilds
        for i, guild in enumerate(guilds[:10], 1):
            embed.add_field(
                name=f"{i}. {guild.name}",
                value=f"ID: {guild.id}\nMembers: {guild.member_count}",
                inline=True
            )

        if len(guilds) > 10:
            embed.set_footer(text=f"...and {len(guilds) - 10} more")

        await ctx.send(embed=embed)

    @commands.command(name='leave')
    @log_command()
    async def leave_guild(self, ctx, guild_id: int):
        """Make the bot leave a guild"""
        guild = self.bot.get_guild(guild_id)

        if not guild:
            embed = discord.Embed(
                title="❌ Guild Not Found",
                description=f"Could not find guild with ID {guild_id}",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        if await confirm_action(ctx, f"Leave guild **{guild.name}**?"):
            await guild.leave()
            embed = discord.Embed(
                title="✅ Left Guild",
                description=f"Successfully left **{guild.name}**",
                color=0x00FF88
            )
            await ctx.send(embed=embed)

    @commands.command(name='blacklist')
    async def blacklist(self, ctx, action: str, target_id: int):
        """Manage blacklist (add/remove user/guild)"""
        # This would interact with database
        # Simplified version
        embed = discord.Embed(
            title="🚫 Blacklist",
            description=f"Action: {action}\nTarget: {target_id}",
            color=0xFFAA00
        )
        await ctx.send(embed=embed)


# src/cogs/playlist.py
"""
Playlist management commands
"""

import logging
from typing import Optional, List

import discord
from discord.ext import commands

from utils.helpers import truncate_string, paginate_list, confirm_action
from utils.decorators import log_command, typing

logger = logging.getLogger(__name__)


class PlaylistCog(commands.Cog, name="Playlist"):
    """Playlist management commands"""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.group(name='playlist', aliases=['pl'], invoke_without_command=True)
    async def playlist(self, ctx):
        """Playlist management commands"""
        embed = discord.Embed(
            title="📋 Playlist Commands",
            description="Manage your playlists",
            color=0x00FF88
        )

        embed.add_field(
            name="Commands",
            value="`create <name>` - Create a playlist\n"
                  "`delete <name>` - Delete a playlist\n"
                  "`list` - List your playlists\n"
                  "`add <name>` - Add current track to playlist\n"
                  "`play <name>` - Play a playlist\n"
                  "`show <name>` - Show playlist tracks\n"
                  "`share <name>` - Make playlist public",
            inline=False
        )

        await ctx.send(embed=embed)

    @playlist.command(name='create')
    @typing()
    @log_command()
    async def create_playlist(self, ctx, *, name: str):
        """Create a new playlist"""
        if not self.db:
            embed = discord.Embed(
                title="❌ Database Not Available",
                description="Playlist feature requires database",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        # Check name length
        if len(name) > 100:
            embed = discord.Embed(
                title="❌ Name Too Long",
                description="Playlist name must be under 100 characters",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        try:
            # Create playlist
            playlist = await self.db.create_playlist(
                user_id=ctx.author.id,
                name=name,
                description=f"Created by {ctx.author.name}",
                guild_id=ctx.guild.id
            )

            embed = discord.Embed(
                title="✅ Playlist Created",
                description=f"Created playlist **{name}**",
                color=0x00FF88
            )
            embed.set_footer(text=f"ID: {playlist.id}")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error creating playlist: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to create playlist",
                color=0xFF0000
            )
            await ctx.send(embed=embed)

    @playlist.command(name='delete')
    @log_command()
    async def delete_playlist(self, ctx, *, name: str):
        """Delete a playlist"""
        if not self.db:
            return await ctx.send("❌ Database not available")

        # Get user playlists
        playlists = await self.db.get_user_playlists(ctx.author.id)
        playlist = next((p for p in playlists if p.name.lower() == name.lower()), None)

        if not playlist:
            embed = discord.Embed(
                title="❌ Playlist Not Found",
                description=f"You don't have a playlist named **{name}**",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        # Confirm deletion
        if await confirm_action(ctx, f"Delete playlist **{playlist.name}**?"):
            await self.db.delete_playlist(playlist.id)

            embed = discord.Embed(
                title="✅ Playlist Deleted",
                description=f"Deleted playlist **{playlist.name}**",
                color=0x00FF88
            )
            await ctx.send(embed=embed)

    @playlist.command(name='list')
    async def list_playlists(self, ctx):
        """List your playlists"""
        if not self.db:
            return await ctx.send("❌ Database not available")

        playlists = await self.db.get_user_playlists(ctx.author.id)

        if not playlists:
            embed = discord.Embed(
                title="📭 No Playlists",
                description="You don't have any playlists yet!\n"
                            f"Create one with `{ctx.prefix}playlist create <name>`",
                color=0x00AAFF
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"📋 Your Playlists ({len(playlists)})",
            color=0x00FF88
        )

        for playlist in playlists[:10]:
            tracks = await self.db.get_playlist_tracks(playlist.id)
            embed.add_field(
                name=playlist.name,
                value=f"Tracks: {len(tracks)}\n"
                      f"Created: {playlist.created_at.strftime('%Y-%m-%d')}\n"
                      f"{'🌍 Public' if playlist.is_public else '🔒 Private'}",
                inline=True
            )

        if len(playlists) > 10:
            embed.set_footer(text=f"...and {len(playlists) - 10} more")

        await ctx.send(embed=embed)

    @playlist.command(name='add')
    @log_command()
    async def add_to_playlist(self, ctx, *, name: str):
        """Add current track to playlist"""
        if not self.db:
            return await ctx.send("❌ Database not available")

        # Get current track
        player = self.bot.get_cog('Music').get_player(ctx.guild)

        if not player or not player.current:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="No track currently playing to add",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        # Get playlist
        playlists = await self.db.get_user_playlists(ctx.author.id)
        playlist = next((p for p in playlists if p.name.lower() == name.lower()), None)

        if not playlist:
            embed = discord.Embed(
                title="❌ Playlist Not Found",
                description=f"You don't have a playlist named **{name}**",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        # Add track
        track_data = {
            'url': player.current.url,
            'title': player.current.title,
            'duration': player.current.duration,
            'artist': player.current.artist,
            'thumbnail': player.current.thumbnail,
            'added_by': ctx.author.id
        }

        await self.db.add_track_to_playlist(playlist.id, track_data)

        embed = discord.Embed(
            title="✅ Track Added",
            description=f"Added **{player.current.title}** to **{playlist.name}**",
            color=0x00FF88
        )
        await ctx.send(embed=embed)

    @playlist.command(name='play')
    @log_command()
    async def play_playlist(self, ctx, *, name: str):
        """Play a playlist"""
        if not self.db:
            return await ctx.send("❌ Database not available")

        # Get playlist
        playlists = await self.db.get_user_playlists(ctx.author.id)
        playlist = next((p for p in playlists if p.name.lower() == name.lower()), None)

        if not playlist:
            embed = discord.Embed(
                title="❌ Playlist Not Found",
                description=f"You don't have a playlist named **{name}**",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        # Get tracks
        tracks = await self.db.get_playlist_tracks(playlist.id)

        if not tracks:
            embed = discord.Embed(
                title="📭 Empty Playlist",
                description=f"Playlist **{playlist.name}** has no tracks",
                color=0xFFAA00
            )
            await ctx.send(embed=embed)
            return

        # Get music cog and player
        music_cog = self.bot.get_cog('Music')
        if not music_cog:
            return await ctx.send("❌ Music system not available")

        player = music_cog.get_player(ctx.guild)

        # Queue all tracks
        for track_data in tracks:
            from cogs.music import Track
            track = Track(
                url=track_data.track_url,
                title=track_data.track_title,
                duration=track_data.track_duration or 0,
                thumbnail=track_data.track_thumbnail,
                requester=ctx.author,
                source='Playlist',
                artist=track_data.track_artist
            )
            player.queue.append(track)

        embed = discord.Embed(
            title="📋 Playlist Loaded",
            description=f"Added **{len(tracks)}** tracks from **{playlist.name}**",
            color=0x00FF88
        )
        await ctx.send(embed=embed)

        # Start playing if not already
        if not player.is_playing:
            await ctx.invoke(music_cog.join)


# src/cogs/effects.py
"""
Audio effects commands
"""

import logging
from typing import Optional

import discord
from discord.ext import commands

from core.audio_processor import AudioProcessor
from utils.decorators import bot_in_voice, same_voice_channel, log_command

logger = logging.getLogger(__name__)


class EffectsCog(commands.Cog, name="Effects"):
    """Audio effects commands"""

    def __init__(self, bot):
        self.bot = bot
        self.processor = AudioProcessor(bot.config)

    def get_player(self, guild):
        """Get player from music cog"""
        music_cog = self.bot.get_cog('Music')
        if music_cog:
            return music_cog.get_player(guild)
        return None

    @commands.command(name='bassboost', aliases=['bb', 'bass'])
    @bot_in_voice()
    @same_voice_channel()
    @log_command()
    async def bass_boost(self, ctx, level: int = 5):
        """Apply bass boost effect (0-20)"""
        player = self.get_player(ctx.guild)
        if not player:
            return await ctx.send("❌ Music player not available")

        # Validate level
        level = max(0, min(20, level))

        # Apply effect
        effect_filter = self.processor.add_effect('bass_boost', level=level)
        if effect_filter:
            if 'bass_boost' in player.effects:
                player.effects.remove(player.effects[player.effects.index('bass_boost')])
            player.effects.append(effect_filter)

        # Create visualization
        bar_length = 20
        filled = int(bar_length * (level / 20))
        bar = '█' * filled + '░' * (bar_length - filled)

        embed = discord.Embed(
            title="🔊 Bass Boost",
            description=f"Level: **{level}/20**\n`{bar}`",
            color=0xFF00FF
        )

        await ctx.send(embed=embed)

    @commands.command(name='karaoke')
    @bot_in_voice()
    @same_voice_channel()
    @log_command()
    async def karaoke(self, ctx):
        """Toggle karaoke mode (removes vocals)"""
        player = self.get_player(ctx.guild)
        if not player:
            return await ctx.send("❌ Music player not available")

        # Toggle effect
        effect_name = 'karaoke'
        if any(effect_name in e for e in player.effects):
            player.effects = [e for e in player.effects if effect_name not in e]
            status = "disabled"
            emoji = "🎤❌"
        else:
            effect_filter = self.processor.add_effect(effect_name)
            if effect_filter:
                player.effects.append(effect_filter)
            status = "enabled"
            emoji = "🎤✅"

        embed = discord.Embed(
            title=f"{emoji} Karaoke Mode",
            description=f"Karaoke mode **{status}**!\nVocals will be {'removed' if status == 'enabled' else 'restored'}.",
            color=0xFF00FF
        )

        await ctx.send(embed=embed)

    @commands.command(name='nightcore')
    @bot_in_voice()
    @same_voice_channel()
    @log_command()
    async def nightcore(self, ctx):
        """Toggle nightcore effect (speed up + pitch up)"""
        player = self.get_player(ctx.guild)
        if not player:
            return await ctx.send("❌ Music player not available")

        # Toggle effect
        effect_name = 'nightcore'
        if any(effect_name in e for e in player.effects):
            player.effects = [e for e in player.effects if effect_name not in e]
            status = "disabled"
            emoji = "⚡❌"
        else:
            effect_filter = self.processor.add_effect(effect_name)
            if effect_filter:
                player.effects.append(effect_filter)
            status = "enabled"
            emoji = "⚡✅"

        embed = discord.Embed(
            title=f"{emoji} Nightcore",
            description=f"Nightcore effect **{status}**!",
            color=0xFF00FF
        )

        await ctx.send(embed=embed)

    @commands.command(name='vaporwave')
    @bot_in_voice()
    @same_voice_channel()
    @log_command()
    async def vaporwave(self, ctx):
        """Toggle vaporwave effect (slow + pitch down)"""
        player = self.get_player(ctx.guild)
        if not player:
            return await ctx.send("❌ Music player not available")

        # Toggle effect
        effect_name = 'vaporwave'
        if any(effect_name in e for e in player.effects):
            player.effects = [e for e in player.effects if effect_name not in e]
            status = "disabled"
            emoji = "🌊❌"
        else:
            effect_filter = self.processor.add_effect(effect_name)
            if effect_filter:
                player.effects.append(effect_filter)
            status = "enabled"
            emoji = "🌊✅"

        embed = discord.Embed(
            title=f"{emoji} Vaporwave",
            description=f"Vaporwave effect **{status}**!",
            color=0xFF00FF
        )

        await ctx.send(embed=embed)

    @commands.command(name='3d', aliases=['surround'])
    @bot_in_voice()
    @same_voice_channel()
    @log_command()
    async def audio_3d(self, ctx):
        """Toggle 3D audio effect"""
        player = self.get_player(ctx.guild)
        if not player:
            return await ctx.send("❌ Music player not available")

        # Toggle effect
        effect_name = '3d'
        if any(effect_name in e for e in player.effects):
            player.effects = [e for e in player.effects if effect_name not in e]
            status = "disabled"
            emoji = "🎧❌"
        else:
            effect_filter = self.processor.add_effect(effect_name)
            if effect_filter:
                player.effects.append(effect_filter)
            status = "enabled"
            emoji = "🎧✅"

        embed = discord.Embed(
            title=f"{emoji} 3D Audio",
            description=f"3D audio effect **{status}**!",
            color=0xFF00FF
        )

        await ctx.send(embed=embed)

    @commands.command(name='echo')
    @bot_in_voice()
    @same_voice_channel()
    @log_command()
    async def echo(self, ctx):
        """Toggle echo effect"""
        player = self.get_player(ctx.guild)
        if not player:
            return await ctx.send("❌ Music player not available")

        # Toggle effect
        effect_name = 'echo'
        if any(effect_name in e for e in player.effects):
            player.effects = [e for e in player.effects if effect_name not in e]
            status = "disabled"
        else:
            effect_filter = self.processor.add_effect(effect_name)
            if effect_filter:
                player.effects.append(effect_filter)
            status = "enabled"

        embed = discord.Embed(
            title="🔊 Echo Effect",
            description=f"Echo effect **{status}**!",
            color=0xFF00FF
        )

        await ctx.send(embed=embed)

    @commands.command(name='clearfx', aliases=['clear', 'reset'])
    @bot_in_voice()
    @same_voice_channel()
    @log_command()
    async def clear_effects(self, ctx):
        """Clear all audio effects"""
        player = self.get_player(ctx.guild)
        if not player:
            return await ctx.send("❌ Music player not available")

        # Clear effects
        effect_count = len(player.effects)
        player.effects.clear()
        self.processor.clear_effects()

        embed = discord.Embed(
            title="🔧 Effects Cleared",
            description=f"Removed **{effect_count}** audio effects",
            color=0x00FF88
        )

        await ctx.send(embed=embed)

    @commands.command(name='effects', aliases=['fx'])
    async def list_effects(self, ctx):
        """List all available effects"""
        player = self.get_player(ctx.guild)

        embed = discord.Embed(
            title="🎛️ Audio Effects",
            description="Available audio effects and their status",
            color=0xFF00FF
        )

        # Available effects
        effects_list = [
            ("🔊 Bass Boost", "bassboost <0-20>", "Enhance bass frequencies"),
            ("🎤 Karaoke", "karaoke", "Remove vocals from track"),
            ("⚡ Nightcore", "nightcore", "Speed up and pitch up"),
            ("🌊 Vaporwave", "vaporwave", "Slow down and pitch down"),
            ("🎧 3D Audio", "3d", "Surround sound effect"),
            ("🔊 Echo", "echo", "Add echo/reverb"),
            ("🎚️ Tremolo", "tremolo", "Volume oscillation"),
            ("🎵 Vibrato", "vibrato", "Pitch oscillation"),
        ]

        for name, command, description in effects_list:
            # Check if active
            active = False
            if player:
                for effect in player.effects:
                    if command.split()[0] in effect.lower():
                        active = True
                        break

            status = "✅ Active" if active else "⭕ Available"
            embed.add_field(
                name=f"{name} {status}",
                value=f"`{ctx.prefix}{command}`\n{description}",
                inline=True
            )

        # Current effects
        if player and player.effects:
            embed.add_field(
                name="🎛️ Active Effects",
                value=f"**{len(player.effects)}** effects active\n"
                      f"Use `{ctx.prefix}clearfx` to reset",
                inline=False
            )

        embed.set_footer(text="Effects apply to the next track played")

        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function for cog"""
    await bot.add_cog(EffectsCog(bot))
