"""
Helper utilities for KazeBeats
Formatting, conversion, and utility functions
"""

import discord
from datetime import timedelta
import re
from typing import Optional, Union, List
import humanize
import asyncio


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable format
    Examples: 3:45, 1:02:30, 2:45:30
    """
    if seconds < 0:
        return "0:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse duration string to seconds
    Accepts: 1h30m, 90m, 5m30s, 330, 5:30
    """
    # Direct number (seconds)
    if duration_str.isdigit():
        return int(duration_str)

    # Time format (1:30, 1:30:00)
    time_pattern = re.match(r'^(?:(\d+):)?(\d+):(\d+)$', duration_str)
    if time_pattern:
        parts = time_pattern.groups()
        hours = int(parts[0]) if parts[0] else 0
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    # Human format (1h30m, 90m, 5m30s)
    total_seconds = 0

    # Hours
    hours = re.search(r'(\d+)h', duration_str)
    if hours:
        total_seconds += int(hours.group(1)) * 3600

    # Minutes
    minutes = re.search(r'(\d+)m', duration_str)
    if minutes:
        total_seconds += int(minutes.group(1)) * 60

    # Seconds
    seconds = re.search(r'(\d+)s', duration_str)
    if seconds:
        total_seconds += int(seconds.group(1))

    return total_seconds if total_seconds > 0 else None


def create_progress_bar(current: int, total: int, length: int = 12) -> str:
    """
    Create a visual progress bar with gaming style
    """
    if total <= 0:
        return "⬜" * length

    progress = min(current / total, 1.0)
    filled = int(progress * length)

    # Create bar with slider
    bar = ""
    for i in range(length):
        if i < filled:
            bar += "🟦"
        elif i == filled:
            bar += "🔘"
        else:
            bar += "⬜"

    # Add percentage and time
    percentage = int(progress * 100)
    time_str = f"{format_duration(current)} / {format_duration(total)}"

    return f"{bar} {percentage}% | {time_str}"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to specified length
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def escape_markdown(text: str) -> str:
    """
    Escape Discord markdown characters
    """
    markdown_chars = ['*', '_', '`', '~', '|', '>', '#', '-', '=', '[', ']', '(', ')']
    for char in markdown_chars:
        text = text.replace(char, f'\\{char}')
    return text


def create_embed_pages(items: List[any], per_page: int = 10,
                       title: str = "List", color: int = 0x00D4FF,
                       format_item=None) -> List[discord.Embed]:
    """
    Create paginated embeds for long lists
    """
    pages = []
    total_pages = (len(items) + per_page - 1) // per_page

    for page_num in range(total_pages):
        start_idx = page_num * per_page
        end_idx = min(start_idx + per_page, len(items))
        page_items = items[start_idx:end_idx]

        embed = discord.Embed(
            title=f"{title} (Page {page_num + 1}/{total_pages})",
            color=color
        )

        description = ""
        for i, item in enumerate(page_items, start=start_idx + 1):
            if format_item:
                description += format_item(i, item) + "\n"
            else:
                description += f"{i}. {item}\n"

        embed.description = description
        embed.set_footer(text=f"Total: {len(items)} items")
        pages.append(embed)

    return pages


def format_number(number: int) -> str:
    """
    Format large numbers with K, M, B suffixes
    """
    if number < 1000:
        return str(number)
    elif number < 1_000_000:
        return f"{number / 1000:.1f}K"
    elif number < 1_000_000_000:
        return f"{number / 1_000_000:.1f}M"
    else:
        return f"{number / 1_000_000_000:.1f}B"


def get_user_avatar(user: discord.User) -> str:
    """
    Get user avatar URL with fallback
    """
    if user.avatar:
        return user.avatar.url
    else:
        return user.default_avatar.url


def create_error_embed(title: str, description: str,
                       footer: Optional[str] = None) -> discord.Embed:
    """
    Create a standardized error embed
    """
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=0xFF0040  # Error red
    )

    if footer:
        embed.set_footer(text=footer)

    return embed


def create_success_embed(title: str, description: str,
                         footer: Optional[str] = None) -> discord.Embed:
    """
    Create a standardized success embed
    """
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=0x00FF88  # Success green
    )

    if footer:
        embed.set_footer(text=footer)

    return embed


def create_loading_embed(title: str = "Loading...",
                         description: str = "Please wait...") -> discord.Embed:
    """
    Create a loading embed
    """
    embed = discord.Embed(
        title=f"⏳ {title}",
        description=description,
        color=0x00D4FF  # Loading blue
    )

    return embed


async def create_selection_menu(ctx, options: List[str],
                                title: str = "Select an option",
                                timeout: int = 30) -> Optional[int]:
    """
    Create an interactive selection menu
    Returns the selected index or None if timeout
    """
    if len(options) > 10:
        options = options[:10]

    # Create embed
    embed = discord.Embed(
        title=f"🎮 {title}",
        color=0x00D4FF
    )

    description = ""
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, option in enumerate(options):
        description += f"{emojis[i]} {option}\n"

    embed.description = description
    embed.set_footer(text=f"React to select • Expires in {timeout} seconds")

    message = await ctx.send(embed=embed)

    # Add reactions
    for i in range(len(options)):
        await message.add_reaction(emojis[i])

    # Wait for reaction
    def check(reaction, user):
        return (user == ctx.author and
                str(reaction.emoji) in emojis[:len(options)] and
                reaction.message.id == message.id)

    try:
        reaction, user = await ctx.bot.wait_for('reaction_add',
                                                timeout=timeout,
                                                check=check)

        # Get selected index
        selected = emojis.index(str(reaction.emoji))

        # Update embed to show selection
        embed.color = 0x00FF88  # Success green
        embed.set_footer(text=f"Selected: {options[selected]}")
        await message.edit(embed=embed)
        await message.clear_reactions()

        return selected

    except asyncio.TimeoutError:
        embed.color = 0xFF0040  # Error red
        embed.set_footer(text="Selection timed out")
        await message.edit(embed=embed)
        await message.clear_reactions()
        return None


def format_timestamp(seconds: int) -> str:
    """
    Format timestamp for display
    """
    return humanize.naturaldelta(timedelta(seconds=seconds))


def is_url(text: str) -> bool:
    """
    Check if text is a valid URL
    """
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(url_pattern.match(text))


def extract_urls(text: str) -> List[str]:
    """
    Extract all URLs from text
    """
    url_pattern = re.compile(
        r'https?://(?:[-\w.])+(?::\d+)?(?:/[^\s]*)?',
        re.IGNORECASE
    )
    return url_pattern.findall(text)


def clean_channel_name(name: str) -> str:
    """
    Clean channel name for display
    """
    # Remove special characters
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces with hyphens
    name = re.sub(r'\s+', '-', name)
    # Convert to lowercase
    return name.lower()


def format_permissions(permissions: discord.Permissions) -> str:
    """
    Format permissions for display
    """
    perm_list = []
    for perm, value in permissions:
        if value:
            # Convert snake_case to Title Case
            perm_name = perm.replace('_', ' ').title()
            perm_list.append(perm_name)

    return ', '.join(perm_list) if perm_list else 'None'


def calculate_level(experience: int) -> tuple[int, int, int]:
    """
    Calculate level from experience points
    Returns (level, current_exp, exp_for_next_level)
    """
    level = 0
    total_exp = 0

    while total_exp <= experience:
        level += 1
        total_exp += level * 100

    level -= 1
    exp_for_current = sum(i * 100 for i in range(1, level + 1))
    current_exp = experience - exp_for_current
    exp_for_next = (level + 1) * 100

    return level, current_exp, exp_for_next


def create_level_bar(current_exp: int, required_exp: int, length: int = 10) -> str:
    """
    Create a visual level progress bar
    """
    if required_exp <= 0:
        return "⬜" * length

    progress = min(current_exp / required_exp, 1.0)
    filled = int(progress * length)

    bar = "🟩" * filled + "⬜" * (length - filled)
    percentage = int(progress * 100)

    return f"{bar} {percentage}% ({current_exp}/{required_exp} XP)"


class Paginator:
    """
    Interactive paginator for embeds
    """

    def __init__(self, ctx, pages: List[discord.Embed], timeout: int = 60):
        self.ctx = ctx
        self.pages = pages
        self.timeout = timeout
        self.current_page = 0
        self.message = None

        # Add page numbers to footers
        for i, page in enumerate(self.pages):
            if not page.footer.text:
                page.set_footer(text=f"Page {i + 1}/{len(pages)}")
            else:
                page.set_footer(
                    text=f"{page.footer.text} • Page {i + 1}/{len(pages)}",
                    icon_url=page.footer.icon_url
                )

    async def start(self):
        """Start the paginator"""
        if len(self.pages) == 1:
            await self.ctx.send(embed=self.pages[0])
            return

        self.message = await self.ctx.send(embed=self.pages[0])

        # Add navigation reactions
        await self.message.add_reaction("⏮️")  # First
        await self.message.add_reaction("◀️")  # Previous
        await self.message.add_reaction("▶️")  # Next
        await self.message.add_reaction("⏭️")  # Last
        await self.message.add_reaction("⏹️")  # Stop

        # Start listening for reactions
        await self.paginate()

    async def paginate(self):
        """Handle pagination"""

        def check(reaction, user):
            return (user == self.ctx.author and
                    reaction.message.id == self.message.id and
                    str(reaction.emoji) in ["⏮️", "◀️", "▶️", "⏭️", "⏹️"])

        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for(
                    'reaction_add',
                    timeout=self.timeout,
                    check=check
                )

                # Remove user's reaction
                await self.message.remove_reaction(reaction, user)

                # Handle navigation
                if str(reaction.emoji) == "⏮️":  # First page
                    self.current_page = 0
                elif str(reaction.emoji) == "◀️":  # Previous
                    self.current_page = max(0, self.current_page - 1)
                elif str(reaction.emoji) == "▶️":  # Next
                    self.current_page = min(len(self.pages) - 1, self.current_page + 1)
                elif str(reaction.emoji) == "⏭️":  # Last page
                    self.current_page = len(self.pages) - 1
                elif str(reaction.emoji) == "⏹️":  # Stop
                    await self.message.clear_reactions()
                    return

                # Update embed
                await self.message.edit(embed=self.pages[self.current_page])

            except asyncio.TimeoutError:
                await self.message.clear_reactions()
                return
