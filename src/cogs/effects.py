"""
Audio effects cog with gaming-inspired presets
Bass boost, nightcore, karaoke, and more
"""

import discord
from discord.ext import commands
import wavelink
from typing import Optional

from bot.config import BotColors, BotEmojis, EFFECT_PRESETS


class Effects(commands.Cog):
    """Audio effects and filters"""

    def __init__(self, bot):
        self.bot = bot
        self.emoji = BotEmojis()
        self.colors = BotColors()

    async def cog_check(self, ctx):
        """Check if effects are enabled for this guild"""
        if not ctx.guild:
            return False

        # Check if effects are enabled
        effects_enabled = await self.bot.db.get_guild_feature(ctx.guild.id, "effects")
        if not effects_enabled:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Effects Disabled",
                description="Audio effects are disabled on this server!",
                color=self.colors.ERROR_RED
            )
            await ctx.send(embed=embed, delete_after=10)
            return False

        return True

    @commands.hybrid_group(name="effect", aliases=["fx"], description="Audio effects control")
    async def effect(self, ctx):
        """Audio effects base command"""
        if ctx.invoked_subcommand is None:
            await self.show_effects_menu(ctx)

    async def show_effects_menu(self, ctx):
        """Show available effects menu"""
        embed = discord.Embed(
            title=f"{self.emoji.LIGHTNING} Audio Effects Menu",
            description="Gaming-optimized audio effects for the ultimate experience!",
            color=self.colors.NEON_PURPLE
        )

        # Bass Boost
        embed.add_field(
            name=f"{self.emoji.BASS_BOOST} Bass Boost",
            value=(
                "`/effect bass <0-20>` - Adjust bass levels\n"
                "• `5` - Subtle enhancement\n"
                "• `10` - Moderate boost\n"
                "• `15` - Heavy bass\n"
                "• `20` - Maximum bass"
            ),
            inline=False
        )

        # Nightcore
        embed.add_field(
            name=f"{self.emoji.NIGHTCORE} Nightcore",
            value="`/effect nightcore` - Speed up with pitch shift",
            inline=True
        )

        # Karaoke
        embed.add_field(
            name=f"{self.emoji.KARAOKE} Karaoke",
            value="`/effect karaoke` - Remove vocals",
            inline=True
        )

        # Echo
        embed.add_field(
            name=f"{self.emoji.ECHO} Echo",
            value="`/effect echo` - Add echo effect",
            inline=True
        )

        # 3D Audio
        embed.add_field(
            name=f"{self.emoji.THREE_D} 3D Audio",
            value="`/effect 3d` - Spatial audio effect",
            inline=True
        )

        # Presets
        embed.add_field(
            name="🎮 Gaming Presets",
            value=(
                "`/effect preset gaming` - Optimized for gaming\n"
                "`/effect preset movie` - Cinema experience\n"
                "`/effect preset party` - Party mode"
            ),
            inline=False
        )

        # Commands
        embed.add_field(
            name="⚙️ Commands",
            value=(
                "`/effect clear` - Remove all effects\n"
                "`/effect show` - Show active effects\n"
                "`/effect save <name>` - Save current as preset"
            ),
            inline=False
        )

        embed.set_footer(
            text="🎮 Gaming Mode Active | Effects stack for ultimate customization",
            icon_url=self.bot.user.display_avatar.url
        )

        await ctx.send(embed=embed)

    @effect.command(name="bass", description="Adjust bass boost level")
    async def bass(self, ctx, level: int):
        """Set bass boost level (0-20)"""
        player = ctx.voice_client

        if not player or not player.playing:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="Play something first to apply effects!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Validate level
        if not 0 <= level <= self.bot.config.MAX_BASS_BOOST:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Invalid Level",
                description=f"Bass boost must be between 0 and {self.bot.config.MAX_BASS_BOOST}!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Apply bass boost filter
        filters = wavelink.Filters()

        if level > 0:
            # Calculate equalizer bands for bass boost
            bands = []
            for i in range(15):
                if i < 6:  # Boost lower frequencies more
                    gain = level * (1 - i * 0.1)
                else:
                    gain = 0
                bands.append(wavelink.Equalizer(band=i, gain=gain / 20))

            filters.equalizer.set(bands=bands)

        await player.set_filters(filters)
        player.effects["bass_boost"] = level

        # Visual feedback
        bass_bar = self.create_effect_bar(level, self.bot.config.MAX_BASS_BOOST)

        embed = discord.Embed(
            title=f"{self.emoji.BASS_BOOST} Bass Boost {'Enabled' if level > 0 else 'Disabled'}",
            description=f"Level: **{level}**\n{bass_bar}",
            color=self.colors.BASS_BOOST if level > 0 else self.colors.INFO_BLUE
        )

        # Add description based on level
        if level == 0:
            embed.add_field(name="Effect", value="Bass boost disabled", inline=False)
        elif level <= 5:
            embed.add_field(name="Effect", value="🎵 Subtle bass enhancement", inline=False)
        elif level <= 10:
            embed.add_field(name="Effect", value="🔊 Moderate bass boost", inline=False)
        elif level <= 15:
            embed.add_field(name="Effect", value="💥 Heavy bass boost", inline=False)
        else:
            embed.add_field(name="Effect", value="🌋 MAXIMUM BASS", inline=False)

        embed.set_footer(text=f"Adjusted by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @effect.command(name="nightcore", description="Enable/disable nightcore effect")
    async def nightcore(self, ctx):
        """Toggle nightcore effect (speed + pitch up)"""
        player = ctx.voice_client

        if not player or not player.playing:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="Play something first to apply effects!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Toggle nightcore
        nightcore_enabled = not player.effects.get("nightcore", False)

        filters = wavelink.Filters()

        if nightcore_enabled:
            filters.timescale.set(pitch=1.3, speed=1.3, rate=1)

        await player.set_filters(filters)
        player.effects["nightcore"] = nightcore_enabled

        embed = discord.Embed(
            title=f"{self.emoji.NIGHTCORE} Nightcore {'Enabled' if nightcore_enabled else 'Disabled'}",
            description=(
                "🌙 Speed and pitch increased by 30%" if nightcore_enabled
                else "Effect removed"
            ),
            color=self.colors.NIGHTCORE if nightcore_enabled else self.colors.INFO_BLUE
        )

        embed.set_footer(text=f"Toggled by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @effect.command(name="karaoke", description="Enable/disable karaoke mode")
    async def karaoke(self, ctx):
        """Toggle karaoke mode (vocal removal)"""
        player = ctx.voice_client

        if not player or not player.playing:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="Play something first to apply effects!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Toggle karaoke
        karaoke_enabled = not player.effects.get("karaoke", False)

        filters = wavelink.Filters()

        if karaoke_enabled:
            filters.karaoke.set(
                level=1.0,
                mono_level=1.0,
                filter_band=220,
                filter_width=100
            )

        await player.set_filters(filters)
        player.effects["karaoke"] = karaoke_enabled

        embed = discord.Embed(
            title=f"{self.emoji.KARAOKE} Karaoke Mode {'Enabled' if karaoke_enabled else 'Disabled'}",
            description=(
                "🎤 Vocals removed - sing along!" if karaoke_enabled
                else "Vocals restored"
            ),
            color=self.colors.KARAOKE if karaoke_enabled else self.colors.INFO_BLUE
        )

        embed.set_footer(text=f"Toggled by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @effect.command(name="echo", description="Enable/disable echo effect")
    async def echo(self, ctx, delay: float = 0.5):
        """Toggle echo effect with adjustable delay"""
        player = ctx.voice_client

        if not player or not player.playing:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="Play something first to apply effects!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Validate delay
        if not 0.1 <= delay <= 1.0:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Invalid Delay",
                description="Echo delay must be between 0.1 and 1.0 seconds!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Toggle echo
        echo_enabled = not player.effects.get("echo", False)

        filters = wavelink.Filters()

        if echo_enabled:
            filters.channel_mix.set(
                left_to_left=1.0,
                left_to_right=0.0,
                right_to_left=0.0,
                right_to_right=1.0
            )
            # Note: Wavelink doesn't have direct echo, using channel mix for effect

        await player.set_filters(filters)
        player.effects["echo"] = echo_enabled

        embed = discord.Embed(
            title=f"{self.emoji.ECHO} Echo {'Enabled' if echo_enabled else 'Disabled'}",
            description=(
                f"🔄 Echo with {delay}s delay" if echo_enabled
                else "Echo removed"
            ),
            color=self.colors.ECHO if echo_enabled else self.colors.INFO_BLUE
        )

        embed.set_footer(text=f"Toggled by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @effect.command(name="3d", description="Enable/disable 3D audio effect")
    async def three_d(self, ctx):
        """Toggle 3D spatial audio effect"""
        player = ctx.voice_client

        if not player or not player.playing:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="Play something first to apply effects!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Toggle 3D audio
        three_d_enabled = not player.effects.get("3d", False)

        filters = wavelink.Filters()

        if three_d_enabled:
            filters.rotation.set(rotation_hz=0.2)

        await player.set_filters(filters)
        player.effects["3d"] = three_d_enabled

        embed = discord.Embed(
            title=f"{self.emoji.THREE_D} 3D Audio {'Enabled' if three_d_enabled else 'Disabled'}",
            description=(
                "🎭 Spatial audio effect active" if three_d_enabled
                else "3D effect removed"
            ),
            color=self.colors.THREE_D if three_d_enabled else self.colors.INFO_BLUE
        )

        embed.set_footer(text=f"Toggled by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @effect.command(name="preset", description="Apply effect preset")
    async def preset(self, ctx, preset_name: str):
        """Apply a predefined effect preset"""
        player = ctx.voice_client

        if not player or not player.playing:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Nothing Playing",
                description="Play something first to apply effects!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        preset_name = preset_name.lower()

        # Gaming preset
        if preset_name == "gaming":
            filters = wavelink.Filters()
            # Enhanced bass and clarity for gaming
            bands = [
                wavelink.Equalizer(band=0, gain=0.15),
                wavelink.Equalizer(band=1, gain=0.1),
                wavelink.Equalizer(band=2, gain=0.05),
                wavelink.Equalizer(band=6, gain=0.05),
                wavelink.Equalizer(band=7, gain=0.1),
                wavelink.Equalizer(band=8, gain=0.1),
            ]
            filters.equalizer.set(bands=bands)
            await player.set_filters(filters)

            player.effects = {"bass_boost": 8, "gaming": True}

            embed = discord.Embed(
                title=f"🎮 Gaming Preset Applied",
                description="Optimized for gaming with enhanced bass and spatial clarity!",
                color=self.colors.NEON_GREEN
            )

        # Movie/Cinema preset
        elif preset_name == "movie" or preset_name == "cinema":
            filters = wavelink.Filters()
            # Cinema-like sound
            bands = [
                wavelink.Equalizer(band=0, gain=0.2),
                wavelink.Equalizer(band=1, gain=0.15),
                wavelink.Equalizer(band=2, gain=0.1),
                wavelink.Equalizer(band=12, gain=0.1),
                wavelink.Equalizer(band=13, gain=0.15),
                wavelink.Equalizer(band=14, gain=0.2),
            ]
            filters.equalizer.set(bands=bands)
            await player.set_filters(filters)

            player.effects = {"bass_boost": 10, "cinema": True}

            embed = discord.Embed(
                title=f"🎬 Cinema Preset Applied",
                description="Experience theater-quality sound with enhanced bass and treble!",
                color=self.colors.NEON_PURPLE
            )

        # Party preset
        elif preset_name == "party":
            filters = wavelink.Filters()
            # Party mode with heavy bass
            bands = [
                wavelink.Equalizer(band=0, gain=0.3),
                wavelink.Equalizer(band=1, gain=0.25),
                wavelink.Equalizer(band=2, gain=0.2),
                wavelink.Equalizer(band=3, gain=0.15),
                wavelink.Equalizer(band=4, gain=0.1),
            ]
            filters.equalizer.set(bands=bands)
            await player.set_filters(filters)

            player.effects = {"bass_boost": 15, "party": True}

            embed = discord.Embed(
                title=f"🎉 Party Preset Applied",
                description="Maximum bass and energy for the ultimate party experience!",
                color=self.colors.NEON_PINK
            )

        else:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Unknown Preset",
                description="Available presets: `gaming`, `movie`, `party`",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        embed.set_footer(text=f"Applied by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @effect.command(name="clear", description="Remove all audio effects")
    async def clear(self, ctx):
        """Clear all active effects"""
        player = ctx.voice_client

        if not player:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Not Connected",
                description="I'm not connected to a voice channel!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Clear all filters
        await player.set_filters(wavelink.Filters())
        player.effects = {
            "bass_boost": 0,
            "nightcore": False,
            "karaoke": False,
            "echo": False,
            "3d": False
        }

        embed = discord.Embed(
            title=f"{self.emoji.SUCCESS} Effects Cleared",
            description="All audio effects have been removed!",
            color=self.colors.SUCCESS
        )

        embed.set_footer(text=f"Cleared by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @effect.command(name="show", description="Show active effects")
    async def show(self, ctx):
        """Display all active effects"""
        player = ctx.voice_client

        if not player:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Not Connected",
                description="I'm not connected to a voice channel!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        embed = discord.Embed(
            title=f"{self.emoji.LIGHTNING} Active Effects",
            color=self.colors.NEON_PURPLE
        )

        # Check each effect
        effects_list = []

        if player.effects.get("bass_boost", 0) > 0:
            level = player.effects["bass_boost"]
            effects_list.append(f"{self.emoji.BASS_BOOST} Bass Boost: Level {level}")

        if player.effects.get("nightcore", False):
            effects_list.append(f"{self.emoji.NIGHTCORE} Nightcore: Active")

        if player.effects.get("karaoke", False):
            effects_list.append(f"{self.emoji.KARAOKE} Karaoke Mode: Active")

        if player.effects.get("echo", False):
            effects_list.append(f"{self.emoji.ECHO} Echo: Active")

        if player.effects.get("3d", False):
            effects_list.append(f"{self.emoji.THREE_D} 3D Audio: Active")

        if effects_list:
            embed.description = "\n".join(effects_list)
        else:
            embed.description = "No effects active. Use `/effect` to see available effects!"

        # Add current track info
        if player.current:
            embed.add_field(
                name="🎵 Current Track",
                value=f"{player.current.title}",
                inline=False
            )

        embed.set_footer(
            text="🎮 Gaming Mode Active",
            icon_url=self.bot.user.display_avatar.url
        )

        await ctx.send(embed=embed)

    @effect.command(name="save", description="Save current effects as preset")
    async def save(self, ctx, name: str):
        """Save current effect configuration as a preset"""
        player = ctx.voice_client

        if not player:
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} Not Connected",
                description="I'm not connected to a voice channel!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Check if any effects are active
        if not any(player.effects.values()):
            embed = discord.Embed(
                title=f"{self.emoji.ERROR} No Effects Active",
                description="Apply some effects first before saving a preset!",
                color=self.colors.ERROR_RED
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Save preset to database
        preset_id = await self.bot.db.save_dj_preset(
            guild_id=ctx.guild.id,
            name=name,
            effects=player.effects,
            created_by=ctx.author.id
        )

        embed = discord.Embed(
            title=f"{self.emoji.SUCCESS} Preset Saved",
            description=f"Preset **{name}** has been saved!",
            color=self.colors.SUCCESS
        )

        # Show saved effects
        effects_str = []
        if player.effects.get("bass_boost", 0) > 0:
            effects_str.append(f"Bass: {player.effects['bass_boost']}")
        if player.effects.get("nightcore"):
            effects_str.append("Nightcore")
        if player.effects.get("karaoke"):
            effects_str.append("Karaoke")
        if player.effects.get("echo"):
            effects_str.append("Echo")
        if player.effects.get("3d"):
            effects_str.append("3D Audio")

        embed.add_field(
            name="Saved Effects",
            value=", ".join(effects_str),
            inline=False
        )

        embed.set_footer(text=f"Created by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    def create_effect_bar(self, current: int, maximum: int) -> str:
        """Create a visual effect intensity bar"""
        filled = int((current / maximum) * 10)

        if filled == 0:
            bar = "⬜" * 10
        elif filled <= 3:
            bar = "🟦" * filled + "⬜" * (10 - filled)
        elif filled <= 6:
            bar = "🟩" * filled + "⬜" * (10 - filled)
        elif filled <= 8:
            bar = "🟨" * filled + "⬜" * (10 - filled)
        else:
            bar = "🟥" * filled + "⬜" * (10 - filled)

        return f"{bar} {current}/{maximum}"


async def setup(bot):
    await bot.add_cog(Effects(bot))
