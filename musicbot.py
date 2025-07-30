# discord_music_bot.py

import os
import asyncio
import logging
import re
import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from yt_dlp import YoutubeDL, DownloadError
from discord import PCMVolumeTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('musicbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CURRENT_VERSION = "1.3.0"
GITHUB_CHANGELOG_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/CHANGELOG.md"

if not TOKEN:
    logger.error("DISCORD_TOKEN not found in environment variables.")
    logger.error("Please create a .env file with your Discord bot token:")
    logger.error("DISCORD_TOKEN=your_bot_token_here")
    exit(1)

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True,
}
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# Only enable the intents we actually need
intents = discord.Intents.default()
intents.message_content = True

ytdl = YoutubeDL(YTDL_OPTIONS)


# ─── Music Cog ──────────────────────────────────────────────────────────────────
class Music(commands.Cog):
    """Music playback commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: dict[int, list[dict[str, str]]] = {}
        self.loop_flags: dict[int, bool] = {}
        self.update_check_channels: set[int] = set()  # Channels to notify about updates
        self.version_check_task.start()  # Start version checking task

    async def update_status(self, activity_type, name):
        """Update bot status dynamically."""
        await self.bot.change_presence(
            activity=discord.Activity(type=activity_type, name=name)
        )

    @commands.Cog.listener()
    async def on_ready(self):
        if not discord.opus.is_loaded():
            try:
                discord.opus.load_opus("/opt/homebrew/lib/libopus.0.dylib")
                logger.info("Opus library loaded successfully.")
            except OSError:
                logger.warning("Opus library not found at macOS path; trying Linux path...")
        if not discord.opus.is_loaded():
            try:
                discord.opus.load_opus("/usr/lib/x86_64-linux-gnu/libopus.so.0")
                logger.info("Opus library loaded successfully.")
            except OSError:
                logger.warning("Opus library not found; voice will be disabled.")

        await self.update_status(discord.ActivityType.playing, ".help for commands")
        logger.info("Meep is ready!")
        
        # Check for updates on startup
        await self.check_for_updates()


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Unknown command. Try `.help`.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing argument: `{error.param.name}`.")
        else:
            await ctx.send(f"⚠️ Error: {error}")

    @commands.command(help="Search YouTube and play the top result")
    async def play(self, ctx, *, query: str):
        guild_id = ctx.guild.id
        if guild_id not in self.queues:
            self.queues[guild_id] = []

        if not ctx.author.voice:
            return await ctx.send("❌ You must join a voice channel first.")

        # Connect or move
        channel = ctx.author.voice.channel
        vc = ctx.voice_client or await channel.connect()
        if vc.channel != channel:
            await vc.move_to(channel)

        # Fetch info
        try:
            info = ytdl.extract_info(query, download=False)
        except DownloadError as e:
            return await ctx.send(f"❌ Could not fetch audio: {e}")

        if "entries" in info:
            info = info["entries"][0]

        # Pick best audio-only stream
        formats = [f for f in info.get("formats", [])
                   if f.get("acodec") != "none" and f.get("vcodec") == "none"]
        if not formats:
            return await ctx.send("❌ No playable audio format found.")

        best = max(formats, key=lambda f: f.get("abr") or 0)
        url, title = best["url"], info.get("title", "Unknown")

        # Enqueue or play
        self.queues[guild_id].append({"url": url, "title": title})
        source = PCMVolumeTransformer(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))

        def _after(err):
            queue = self.queues[guild_id]
            if self.loop_flags.get(guild_id, False) and queue:
                # replay same track
                item = queue[0]
                # Update status for looped song
                asyncio.run_coroutine_threadsafe(
                    self.update_status(discord.ActivityType.playing, f"🔁 {item['title']}"),
                    self.bot.loop
                )
                # Send now playing message for looped song
                asyncio.run_coroutine_threadsafe(
                    ctx.channel.send(f"🔁 Looping: **{item['title']}**"),
                    self.bot.loop
                )
            elif queue:
                # dequeue next
                item = queue.pop(0)
                # Update status for next song
                asyncio.run_coroutine_threadsafe(
                    self.update_status(discord.ActivityType.playing, f"{item['title']}"),
                    self.bot.loop
                )
                # Send now playing message for next song
                asyncio.run_coroutine_threadsafe(
                    ctx.channel.send(f"Now playing: **{item['title']}**"),
                    self.bot.loop
                )
            else:
                # Reset status when queue is empty
                asyncio.run_coroutine_threadsafe(
                    self.update_status(discord.ActivityType.playing, ".help for commands"),
                    self.bot.loop
                )
                # Disconnect when queue is empty
                asyncio.run_coroutine_threadsafe(
                    vc.disconnect(),
                    self.bot.loop
                )
                return
            new_src = PCMVolumeTransformer(discord.FFmpegPCMAudio(item["url"], **FFMPEG_OPTIONS))
            vc.play(new_src, after=lambda e: _after(e))

        if vc.is_playing():
            await ctx.send(f"Queued **{title}**")
        else:
            vc.play(source, after=lambda e: _after(e))
            # Update status for first song
            await self.update_status(discord.ActivityType.playing, f"{title}")
            await ctx.send(f"Now playing **{title}**")

    @commands.command(help="Skip the current track")
    async def skip(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_playing():
            return await ctx.send("❌ Nothing playing.")
        
        # Remove the current song from queue when skipping
        guild_id = ctx.guild.id
        if guild_id in self.queues and self.queues[guild_id]:
            self.queues[guild_id].pop(0)
        
        vc.stop()
        await ctx.send("⏭ Skipped.")

    @commands.command(help="Stop and leave")
    async def stop(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.disconnect()
            # Reset status to default
            await self.update_status(discord.ActivityType.playing, "Meep ready! .help for commands")
            await ctx.send("⏹ Stopped and disconnected.")
        else:
            await ctx.send("❌ Not in a voice channel.")

    @commands.command(help="Pause playback")
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            # Update status to show paused
            await self.update_status(discord.ActivityType.playing, "⏸ Paused")
            await ctx.send("⏸ Paused.")
        else:
            await ctx.send("❌ Nothing to pause.")

    @commands.command(help="Resume playback")
    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            # Get current song title for status
            current_title = "Unknown"
            if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
                current_title = self.queues[ctx.guild.id][0]['title']
            await self.update_status(discord.ActivityType.playing, f"{current_title}")
            await ctx.send("▶️ Resumed.")
        else:
            await ctx.send("❌ Nothing to resume.")

    @commands.command(help="Set volume (0–100)")
    async def volume(self, ctx, vol: int):
        vc = ctx.voice_client
        if not vc or not getattr(vc, "source", None):
            return await ctx.send("❌ Nothing playing.")
        if 0 <= vol <= 100:
            vc.source.volume = vol / 100
            await ctx.send(f"🔊 Volume set to {vol}%")
        else:
            await ctx.send("❌ Volume must be between 0 and 100.")

    @commands.command(help="Show queue")
    async def queue(self, ctx):
        q = self.queues.get(ctx.guild.id, [])
        if not q:
            return await ctx.send("❌ Queue is empty.")
        lines = [f"{i+1}. {item['title']}" for i, item in enumerate(q)]
        await ctx.send("📜 Queue:\n" + "\n".join(lines))

    @commands.command(help="Clear the queue")
    async def clear(self, ctx):
        self.queues[ctx.guild.id] = []
        await ctx.send("🧹 Queue cleared.")

    @commands.command(help="Enable loop")
    async def loop(self, ctx):
        self.loop_flags[ctx.guild.id] = True
        await ctx.send("🔁 Loop enabled.")

    @commands.command(help="Disable loop")
    async def unloop(self, ctx):
        self.loop_flags[ctx.guild.id] = False
        await ctx.send("🔁 Loop disabled.")

    @commands.command(help="Show current track")
    async def nowplaying(self, ctx):
        vc = ctx.voice_client
        q = self.queues.get(ctx.guild.id, [])
        if vc and vc.is_playing() and q:
            await ctx.send(f"Now playing: **{q[0]['title']}**")
        else:
            await ctx.send("❌ Nothing playing.")
    
    @tasks.loop(hours=6)  # Check for updates every 6 hours
    async def version_check_task(self):
        """Periodic version check task - only notifies if out of date"""
        await self.check_for_updates()
    
    @version_check_task.before_loop
    async def before_version_check(self):
        """Wait until bot is ready before starting version checks"""
        await self.bot.wait_until_ready()
    
    async def check_for_updates(self):
        """Check GitHub for newer version and notify only if out of date"""
        logger.info("Checking GitHub for version updates...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(GITHUB_CHANGELOG_URL) as response:
                    logger.info(f"GitHub version check response: HTTP {response.status}")
                    if response.status == 200:
                        changelog_content = await response.text()
                        latest_version = self.parse_latest_version(changelog_content)
                        
                        if latest_version:
                            logger.info(f"Parsed latest version from GitHub: {latest_version} (current: {CURRENT_VERSION})")
                            if self.is_newer_version(latest_version, CURRENT_VERSION):
                                logger.info(f"New version {latest_version} available - sending notifications")
                                await self.notify_update_available(latest_version)
                            else:
                                logger.info("Meep is up to date")
                        else:
                            logger.warning("Could not parse version from GitHub changelog")
                    else:
                        logger.warning(f"Could not check for updates: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
    
    def parse_latest_version(self, changelog_content: str) -> str:
        """Parse the latest version from changelog content"""
        # Look for first version pattern like ## [1.3.0]
        match = re.search(r'## \[([0-9]+\.[0-9]+\.[0-9]+)\]', changelog_content)
        return match.group(1) if match else None
    
    def is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings (semantic versioning)"""
        latest_parts = [int(x) for x in latest.split('.')]
        current_parts = [int(x) for x in current.split('.')]
        
        # Pad shorter version with zeros
        while len(latest_parts) < 3:
            latest_parts.append(0)
        while len(current_parts) < 3:
            current_parts.append(0)
        
        return latest_parts > current_parts
    
    async def notify_update_available(self, latest_version: str):
        """Notify registered channels about available update (only when out of date)"""
        if not self.update_check_channels:
            logger.info("No channels registered for update notifications")
            return
        
        logger.info(f"Sending update notifications to {len(self.update_check_channels)} channels")
        update_message = f"🔄 **Meep Update Available!**\\n\\n" \
                        f"Current version: **{CURRENT_VERSION}**\\n" \
                        f"Latest version: **{latest_version}**\\n\\n" \
                        f"Use `.update` to update Meep to the latest version."
        
        for channel_id in self.update_check_channels.copy():
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(update_message)
                    logger.info(f"Update notification sent to channel {channel_id} ({channel.name})")
                else:
                    logger.warning(f"Could not find channel {channel_id}, removing from notifications")
                    self.update_check_channels.discard(channel_id)
            except Exception as e:
                logger.error(f"Error sending update notification to channel {channel_id}: {e}")
                self.update_check_channels.discard(channel_id)
    
    @commands.command(help="Enable update notifications in this channel")
    async def updatenotify(self, ctx):
        """Enable update notifications for this channel"""
        self.update_check_channels.add(ctx.channel.id)
        await ctx.send("✅ Update notifications enabled for this channel.")
        logger.info(f"Update notifications enabled for channel {ctx.channel.id} ({ctx.channel.name})")
    
    @commands.command(help="Disable update notifications in this channel")
    async def noupdatenotify(self, ctx):
        """Disable update notifications for this channel"""
        self.update_check_channels.discard(ctx.channel.id)
        await ctx.send("❌ Update notifications disabled for this channel.")
        logger.info(f"Update notifications disabled for channel {ctx.channel.id} ({ctx.channel.name})")
    
    @commands.command(help="Manually check for updates")
    async def checkupdate(self, ctx):
        """Manually check for updates"""
        await ctx.send("🔍 Checking for updates...")
        logger.info(f"Manual update check requested by {ctx.author} in {ctx.channel}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(GITHUB_CHANGELOG_URL) as response:
                    logger.info(f"Manual GitHub version check response: HTTP {response.status}")
                    if response.status == 200:
                        changelog_content = await response.text()
                        latest_version = self.parse_latest_version(changelog_content)
                        
                        if latest_version:
                            logger.info(f"Manual check - parsed version: {latest_version} (current: {CURRENT_VERSION})")
                            if self.is_newer_version(latest_version, CURRENT_VERSION):
                                await ctx.send(f"🔄 **Update Available!**\\n\\n" \
                                             f"Current: **{CURRENT_VERSION}**\\n" \
                                             f"Latest: **{latest_version}**\\n\\n" \
                                             f"Use `.update` to update Meep.")
                            else:
                                await ctx.send(f"✅ **Meep is up to date!**\\n\\n" \
                                             f"Current version: **{CURRENT_VERSION}**")
                        else:
                            logger.warning("Manual check - could not parse version from changelog")
                            await ctx.send("❌ Could not parse version from changelog.")
                    else:
                        await ctx.send(f"❌ Could not check for updates: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error in manual update check: {e}")
            await ctx.send("❌ Error checking for updates. Please try again later.")
    @commands.command(help="Provides a list of commands")
    async def help(self, ctx):
        help_text = """**Meep Commands**

**Playback:**
• `.play <query>` - Search YouTube and play the top result
• `.skip` - Skip the current track
• `.stop` - Stop and leave voice channel
• `.pause` - Pause playback
• `.resume` - Resume playback

**Queue Management:**
• `.queue` - Show current queue
• `.clear` - Clear the queue
• `.nowplaying` - Show current track

**Settings:**
• `.volume <0-100>` - Set volume
• `.loop` - Enable loop (repeat current song)
• `.unloop` - Disable loop

**Utility:**
• `.ping` - Check bot responsiveness
• `.changelog` - Show bot version history
• `.version` - Show bot's version"""
        
        await ctx.send(help_text)



# ─── General Cog ────────────────────────────────────────────────────────────────
class General(commands.Cog):
    """Utility commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(help="Check bot responsiveness")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)  # Convert to milliseconds
        await ctx.send(f"🏓 Pong! Latency: **{latency}ms**")

    @commands.command(help="Show bot changelog")
    async def changelog(self, ctx):
        # GitHub raw URL for the CHANGELOG.md file
        github_url = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/CHANGELOG.md"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(github_url) as response:
                    if response.status == 200:
                        changelog_content = await response.text()
                        
                        # Format the markdown for Discord
                        # Remove the main title and format for Discord display
                        lines = changelog_content.split('\n')
                        formatted_lines = []
                        
                        for line in lines[2:]:  # Skip the main title
                            if line.startswith('## ['):
                                # Version headers
                                formatted_lines.append(f"**{line[3:].strip()}**")
                            elif line.startswith('### '):
                                # Section headers
                                formatted_lines.append(f"\n**{line[4:].strip()}**")
                            elif line.startswith('- **'):
                                # Feature items
                                formatted_lines.append(f"• {line[2:].strip()}")
                            elif line.strip() and not line.startswith('#'):
                                # Regular content
                                formatted_lines.append(line)
                        
                        # Limit to first 1900 characters for Discord message limit
                        changelog_text = '\n'.join(formatted_lines)[:1900]
                        if len('\n'.join(formatted_lines)) > 1900:
                            changelog_text += "\n\n*...view full changelog on GitHub*"
                        
                        await ctx.send(f"**Meep Changelog**\n\n{changelog_text}")
                    else:
                        raise aiohttp.ClientResponseError(None, None, status=response.status)
                        
        except Exception as e:
            logger.error(f"Error fetching changelog: {e}")
            await ctx.send("❌ Could not fetch changelog from GitHub. Please try again later.")
            
    @commands.command(help="Show bot version")
    async def version(self, ctx):
        version_text = """**Meep Version**

**Version 1.3.0 (Current)**"""
        
        await ctx.send(version_text)


# ─── Bot Subclass ──────────────────────────────────────────────────────────────
class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=".",
            intents=intents,
            help_command=None,
            status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.listening, name="Meep starting...")
        )

    async def setup_hook(self):
        await self.add_cog(Music(self))
        await self.add_cog(General(self))


# ─── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot = MusicBot()
    try:
        logger.info("Starting Meep...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord token. Please check your .env file.")
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error("Please check your configuration and try again.")