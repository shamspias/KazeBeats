"""
Settings cog for server configuration
Allows admins to customize bot settings including prefix
"""

import discord
from discord.ext import commands
from typing import Optional

from bot.config import BotColors, BotEmojis


class Settings(commands.Cog):
    """Server settings and configuration"""

    def __init__(self, bot):
        self.bot = bot
        self.emoji = BotEmojis()
        self.colors = BotColors()

    @commands.hybrid_command(name="setprefix", description="Change the bot's prefix for this server")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def setprefix(self, ctx, *, new_prefix: str):
        """
        Change the bot's prefix for this server
        Only server administrators can use this command
        """
        # Validate prefix
        if len(new_prefix) > 5:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Invalid Prefix",
                description="Prefix must be 5 characters or less!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        if not new_prefix.strip():
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Invalid Prefix",
                description="Prefix cannot be empty!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Save to database
        await self.bot.db.set_guild_prefix(ctx.guild.id, new_prefix)

        # Create confirmation embed
        embed = discord.Embed(
            title=f"{self.emoji.SUCCESS} Prefix Updated",
            description=f"Bot prefix for **{ctx.guild.name}** has been changed!",
            color=self.colors.SUCCESS
        )

        embed.add_field(
            name="New Prefix",
            value=f"`{new_prefix}`",
            inline=True
        )

        embed.add_field(
            name="Example Usage",
            value=f"`{new_prefix}play <song>`",
            inline=True
        )

        embed.add_field(
            name="💡 Tips",
            value=(
                f"• All members can now use `{new_prefix}` to run commands\n"
                f"• Use `{new_prefix}help` to see all commands\n"
                f"• Slash commands `/` always work regardless of prefix"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Changed by {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)

        # Update bot's activity
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{new_prefix}help | 🎮 Gaming Mode"
            )
        )

    @commands.hybrid_command(name="resetprefix", description="Reset the prefix to default")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def resetprefix(self, ctx):
        """Reset the server's prefix to default"""
        await self.bot.db.delete_guild_prefix(ctx.guild.id)

        embed = discord.Embed(
            title=f"{self.emoji.SUCCESS} Prefix Reset",
            description=f"Prefix has been reset to default: `{self.bot.config.DEFAULT_PREFIX}`",
            color=self.colors.SUCCESS
        )

        embed.set_footer(
            text=f"Reset by {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="prefix", description="Show the current prefix")
    @commands.guild_only()
    async def prefix(self, ctx):
        """Display the current prefix for this server"""
        current_prefix = await self.bot.get_prefix(ctx.message)

        embed = discord.Embed(
            title=f"{self.emoji.INFO} Current Prefix",
            description=f"The prefix for **{ctx.guild.name}** is: `{current_prefix}`",
            color=self.colors.INFO_BLUE
        )

        embed.add_field(
            name="Usage Examples",
            value=(
                f"`{current_prefix}play <song>` - Play music\n"
                f"`{current_prefix}help` - Show commands\n"
                f"`{current_prefix}queue` - View queue"
            ),
            inline=False
        )

        if ctx.author.guild_permissions.manage_guild:
            embed.add_field(
                name="🔧 Admin Options",
                value=(
                    f"`{current_prefix}setprefix <new>` - Change prefix\n"
                    f"`{current_prefix}resetprefix` - Reset to default"
                ),
                inline=False
            )

        embed.set_footer(text="💡 Slash commands always work with /")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="settings", aliases=["config"], description="Show server settings")
    @commands.guild_only()
    async def settings(self, ctx):
        """Display all server settings"""
        guild_id = ctx.guild.id

        # Get settings from database
        settings = await self.bot.db.get_guild_settings(guild_id)
        current_prefix = await self.bot.get_prefix(ctx.message)

        embed = discord.Embed(
            title=f"⚙️ Server Settings",
            description=f"Configuration for **{ctx.guild.name}**",
            color=self.colors.NEON_PURPLE
        )

        # Basic settings
        embed.add_field(
            name="🔧 Basic Configuration",
            value=(
                f"**Prefix:** `{current_prefix}`\n"
                f"**DJ Role:** {settings.get('dj_role', 'Not Set')}\n"
                f"**Auto-DJ:** {'Enabled' if settings.get('auto_dj', False) else 'Disabled'}\n"
                f"**Max Queue:** {settings.get('max_queue', self.bot.config.MAX_QUEUE_SIZE)} tracks"
            ),
            inline=False
        )

        # Music settings
        embed.add_field(
            name="🎵 Music Settings",
            value=(
                f"**Default Volume:** {settings.get('default_volume', self.bot.config.DEFAULT_VOLUME)}%\n"
                f"**Vote Skip Required:** {settings.get('vote_skip_ratio', 50)}%\n"
                f"**Auto Disconnect:** {settings.get('auto_disconnect', self.bot.config.AUTO_DISCONNECT_TIMEOUT)}s"
            ),
            inline=False
        )

        # Feature toggles
        embed.add_field(
            name="✨ Features",
            value=(
                f"**Effects:** {'✅' if settings.get('effects_enabled', True) else '❌'}\n"
                f"**Playlists:** {'✅' if settings.get('playlists_enabled', True) else '❌'}\n"
                f"**Lyrics:** {'✅' if settings.get('lyrics_enabled', True) else '❌'}\n"
                f"**Analytics:** {'✅' if settings.get('analytics_enabled', True) else '❌'}"
            ),
            inline=False
        )

        if ctx.author.guild_permissions.manage_guild:
            embed.add_field(
                name="💡 Admin Commands",
                value=(
                    f"`{current_prefix}setprefix` - Change prefix\n"
                    f"`{current_prefix}setdj @role` - Set DJ role\n"
                    f"`{current_prefix}toggle <feature>` - Enable/disable features"
                ),
                inline=False
            )

        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_footer(
            text="🎮 Gaming Mode Active",
            icon_url=self.bot.user.display_avatar.url
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="setdj", description="Set the DJ role")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def setdj(self, ctx, role: discord.Role):
        """Set the DJ role for music commands"""
        await self.bot.db.set_guild_dj_role(ctx.guild.id, role.id)

        embed = discord.Embed(
            title=f"{self.emoji.SUCCESS} DJ Role Set",
            description=f"DJ role has been set to {role.mention}",
            color=self.colors.SUCCESS
        )

        embed.add_field(
            name="DJ Permissions",
            value=(
                "• Skip any track without voting\n"
                "• Clear the entire queue\n"
                "• Set any volume level\n"
                "• Use all audio effects"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Set by {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="toggle", description="Toggle bot features")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def toggle(self, ctx, feature: str):
        """Toggle bot features on/off"""
        valid_features = ["effects", "playlists", "lyrics", "analytics", "autodj"]

        feature = feature.lower()
        if feature not in valid_features:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Invalid Feature",
                description=f"Valid features: {', '.join(valid_features)}",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Toggle in database
        current = await self.bot.db.get_guild_feature(ctx.guild.id, feature)
        new_state = not current
        await self.bot.db.set_guild_feature(ctx.guild.id, feature, new_state)

        embed = discord.Embed(
            title=f"{self.emoji.SUCCESS} Feature Toggled",
            description=f"**{feature.capitalize()}** has been **{'enabled' if new_state else 'disabled'}**",
            color=self.colors.SUCCESS if new_state else self.colors.WARNING_YELLOW
        )

        # Feature description
        descriptions = {
            "effects": "Audio effects like bass boost and nightcore",
            "playlists": "Custom playlist creation and management",
            "lyrics": "Display lyrics for current track",
            "analytics": "Track music statistics and analytics",
            "autodj": "Automatic song recommendations when queue ends"
        }

        embed.add_field(
            name="Description",
            value=descriptions.get(feature, ""),
            inline=False
        )

        embed.set_footer(
            text=f"Toggled by {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)

    @setprefix.error
    @resetprefix.error
    @setdj.error
    @toggle.error
    async def settings_error(self, ctx, error):
        """Handle settings command errors"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Permission Denied",
                description="You need **Manage Server** permission to use this command!",
                color=self.colors.ERROR_RED
            )
            await ctx.send(embed=embed, delete_after=10)


async def setup(bot):
    await bot.add_cog(Settings(bot))
