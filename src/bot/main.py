"""
KazeBeats - High-performance Discord Music Bot
Gaming-inspired design with professional architecture
"""

import os
import sys
import asyncio
import discord
from discord.ext import commands
from datetime import datetime
import aiohttp
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import Config, BotColors, BotEmojis
from database.manager import DatabaseManager
from utils.logger import setup_logger
from web.dashboard import create_app
from core.cache_manager import CacheManager

# Setup logging
logger = setup_logger('KazeBeats')


class KazeBeats(commands.Bot):
    """Main bot class with gaming-inspired features"""

    def __init__(self):
        # Load configuration
        self.config = Config()
        self.start_time = datetime.utcnow()

        # Initialize database
        self.db = DatabaseManager(self.config.DB_PATH)

        # Get custom prefixes from database
        intents = discord.Intents.all()
        intents.message_content = True

        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,  # Custom help command
            description=self.config.BOT_DESCRIPTION,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.config.DEFAULT_PREFIX}help | 🎮 Gaming Mode"
            ),
            status=discord.Status.online
        )

        # Initialize components
        self.session = None
        self.cache = CacheManager(max_size_mb=self.config.CACHE_SIZE_MB)
        self.web_app = None

        # Bot statistics
        self.commands_executed = 0
        self.songs_played = 0
        self.total_users = set()

    async def get_prefix(self, message):
        """Get custom prefix for each guild"""
        if not message.guild:
            return self.config.DEFAULT_PREFIX

        # Get custom prefix from database
        custom_prefix = await self.db.get_guild_prefix(message.guild.id)
        return custom_prefix or self.config.DEFAULT_PREFIX

    async def setup_hook(self):
        """Setup bot components"""
        logger.info("🚀 Initializing KazeBeats...")

        # Create aiohttp session
        self.session = aiohttp.ClientSession()

        # Load cogs
        await self.load_extensions()

        # Setup database tables
        await self.db.setup()

        # Start web dashboard if enabled
        if self.config.WEB_ENABLED:
            self.web_app = await self.start_web_dashboard()

        logger.info("✨ KazeBeats initialized successfully!")

    async def load_extensions(self):
        """Load all cogs"""
        cogs = [
            'cogs.music',
            'cogs.admin',
            'cogs.playlist',
            'cogs.effects',
            'cogs.settings'
        ]

        for cog in cogs:
            try:
                await self.load_extension(f"src.{cog}")
                logger.info(f"✅ Loaded {cog}")
            except Exception as e:
                logger.error(f"❌ Failed to load {cog}: {e}")

    async def start_web_dashboard(self):
        """Start web dashboard"""
        from aiohttp import web
        app = create_app(self)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            self.config.WEB_HOST,
            self.config.WEB_PORT
        )
        await site.start()
        logger.info(f"🌐 Web dashboard running on http://{self.config.WEB_HOST}:{self.config.WEB_PORT}")
        return runner

    async def on_ready(self):
        """Bot ready event"""
        logger.info(f"""
╔══════════════════════════════════════════╗
║         🎮 KAZEBEATS IS ONLINE 🎮        ║
╠══════════════════════════════════════════╣
║  Bot Name: {self.user.name:<29} ║
║  Bot ID: {self.user.id:<31} ║
║  Servers: {len(self.guilds):<31} ║
║  Users: {len(self.users):<33} ║
║  Version: {self.config.BOT_VERSION:<31} ║
║  Prefix: {self.config.DEFAULT_PREFIX:<32} ║
╚══════════════════════════════════════════╝
        """)

        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")

    async def on_guild_join(self, guild):
        """When bot joins a new guild"""
        logger.info(f"🎉 Joined guild: {guild.name} ({guild.id})")

        # Send welcome message
        embed = discord.Embed(
            title="🎮 KazeBeats Has Arrived!",
            description=(
                f"Thanks for inviting me to **{guild.name}**!\n\n"
                f"🎵 **Quick Start:**\n"
                f"`{self.config.DEFAULT_PREFIX}play <song>` - Play a song\n"
                f"`{self.config.DEFAULT_PREFIX}help` - Show all commands\n"
                f"`{self.config.DEFAULT_PREFIX}settings` - Configure bot\n\n"
                f"🎮 **Features:**\n"
                f"• Zero-lag streaming\n"
                f"• Multi-platform support\n"
                f"• Audio effects\n"
                f"• Web dashboard\n\n"
                f"💡 **Tip:** Server admins can change my prefix with "
                f"`{self.config.DEFAULT_PREFIX}setprefix <new_prefix>`"
            ),
            color=BotColors.NEON_BLUE,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=self.user.display_avatar.url)
        embed.set_footer(text="Gaming-inspired music experience")

        # Try to send to system channel
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            await guild.system_channel.send(embed=embed)

    async def on_command(self, ctx):
        """Track command usage"""
        self.commands_executed += 1
        self.total_users.add(ctx.author.id)

        logger.info(
            f"Command: {ctx.command.name} | "
            f"User: {ctx.author} | "
            f"Guild: {ctx.guild.name if ctx.guild else 'DM'}"
        )

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description=f"You need `{', '.join(error.missing_permissions)}` permission(s) to use this command.",
                color=BotColors.ERROR_RED
            )
            await ctx.send(embed=embed, delete_after=10)

        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description=f"I need `{', '.join(error.missing_permissions)}` permission(s) to execute this command.",
                color=BotColors.ERROR_RED
            )
            await ctx.send(embed=embed, delete_after=10)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"Please wait `{error.retry_after:.1f}` seconds before using this command again.",
                color=BotColors.WARNING_YELLOW
            )
            await ctx.send(embed=embed, delete_after=5)

        else:
            logger.error(f"Unhandled error in command {ctx.command}: {error}", exc_info=True)
            embed = discord.Embed(
                title="❌ An Error Occurred",
                description="An unexpected error occurred. Please try again later.",
                color=BotColors.ERROR_RED
            )
            await ctx.send(embed=embed, delete_after=10)

    async def close(self):
        """Cleanup on bot shutdown"""
        logger.info("🔄 Shutting down KazeBeats...")

        # Close web dashboard
        if self.web_app:
            await self.web_app.cleanup()

        # Close aiohttp session
        if self.session:
            await self.session.close()

        # Close database
        await self.db.close()

        # Clear cache
        self.cache.clear()

        await super().close()
        logger.info("👋 KazeBeats shutdown complete!")


def main():
    """Main entry point"""
    try:
        bot = KazeBeats()
        bot.run(bot.config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
