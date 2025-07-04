import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp
import discord.opus
import asyncio

# In-memory song queues per guild
queues = {}

# Load bot token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# yt-dlp options: search YouTube, grab best audio, no playlists
ytdl_format_options = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True
}
ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(discord.opus.is_loaded())
    if not discord.opus.is_loaded():
        discord.opus.load_opus("/usr/lib/x86_64-linux-gnu/libopus.so.0")
        print(discord.opus.is_loaded())

@bot.command(name="play", help="Searches YouTube and plays the top result")
async def play(ctx, *, query: str):
    # Ensure a queue exists for this guild
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    # Ensure user is in a voice channel
    if not ctx.author.voice:
        await ctx.send("You need to join a voice channel first.")
        return

    channel = ctx.author.voice.channel
    # Connect or move the bot to that channel
    if ctx.voice_client is None:
        voice_client = await channel.connect()
    else:
        voice_client = ctx.voice_client
        if voice_client.channel != channel:
            await voice_client.move_to(channel)

    text_channel = ctx.channel

    # Use yt-dlp to search & extract info
    info = ytdl.extract_info(query, download=False)
    # If a playlist (search) result, grab the first entry
    if "entries" in info:
        info = info["entries"][0]

    # Select the best audio-only format by bitrate
    formats = info.get("formats", [])
    audio_formats = [
        f for f in formats
        if f.get("acodec") != "none" and f.get("vcodec") == "none"
    ]
    if not audio_formats:
        await ctx.send("❌ Could not find an audio stream for that query.")
        return
    # Sort descending by audio bitrate (abr) and pick the top one
    audio_formats.sort(key=lambda f: (f.get("abr") or 0), reverse=True)
    url = audio_formats[0]["url"]
    title = info.get("title", "Unknown title")
    # Create an audio source
    source = discord.FFmpegPCMAudio(url, **ffmpeg_options)

    # If already playing, enqueue and return
    if voice_client.is_playing():
        queues[guild_id].append({'url': url, 'title': title})
        await ctx.send(f"➕ Queued: **{title}**")
        return

    # Define a callback to play the next song in queue
    def after_play(error):
        queue = queues[guild_id]
        if queue:
            next_item = queue.pop(0)
            next_source = discord.FFmpegPCMAudio(next_item['url'], **ffmpeg_options)
            voice_client.play(next_source, after=lambda e: after_play(e))
            asyncio.run_coroutine_threadsafe(
                text_channel.send(f"⏵ Now playing: **{next_item['title']}**"),
                bot.loop
            )
        else:
            # Optionally leave when queue is empty
            asyncio.run_coroutine_threadsafe(
                voice_client.disconnect(),
                bot.loop
            )
            asyncio.run_coroutine_threadsafe(
                text_channel.send("👋 Queue empty, leaving voice channel."),
                bot.loop
            )

    # Play first track with callback
    voice_client.play(source, after=lambda e: after_play(e))

    await ctx.send(f"⏵ Now playing: **{title}**")

@bot.command(name="stop", help="Stops playback and leaves the channel")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹ Stopped and disconnected.")
    else:
        await ctx.send("I'm not connected to any voice channel.")

@bot.command(name="skip", help="Skips the current track")
async def skip(ctx):
    vc = ctx.voice_client
    if not vc or not vc.is_connected():
        await ctx.send("❌ I'm not in a voice channel.")
        return

    if vc.is_playing():
        vc.stop()
        await ctx.send("⏭ Skipped the current track.")
        # Leave if no more playing
        #await vc.disconnect()
        #await ctx.send("👋 Left the voice channel because there was nothing to play.")
    else:
        await ctx.send("❌ There's nothing playing right now.")

bot.run(TOKEN)
