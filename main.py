import os
import discord
from discord import app_commands
from discord.ext import commands
import wavelink

TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_URL = os.getenv("LAVALINK_URL")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD") or "youshallnotpass"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

queues = {}

# 🔥 UI BUTTON
class MusicButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⏸", style=discord.ButtonStyle.primary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client
        if player:
            await player.pause(True)
            await interaction.response.send_message("⏸ Paused", ephemeral=True)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.success)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client
        if player:
            await player.pause(False)
            await interaction.response.send_message("▶️ Resumed", ephemeral=True)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client
        if player:
            await player.stop()
            await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    @discord.ui.button(label="🛑", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client
        queues[interaction.guild.id] = []
        if player:
            await player.disconnect()
            await interaction.response.send_message("🛑 Stopped", ephemeral=True)

# 🔥 NEXT SONG
async def play_next(guild, channel):
    player: wavelink.Player = guild.voice_client
    q = queues.get(guild.id, [])

    if not player or not q:
        await channel.send("✅ Queue sesh.")
        return

    track = q.pop(0)
    await player.play(track)

    embed = discord.Embed(
        title="🎶 Now Playing",
        description=f"**{track.title}**",
        color=0x8A2BE2
    )
    await channel.send(embed=embed, view=MusicButtons())

# 🔥 FIXED CONNECT
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    try:
        node = wavelink.Node(
            uri=LAVALINK_URL,
            password=LAVALINK_PASSWORD
        )
        await wavelink.Pool.connect(client=bot, nodes=[node])
        print("✅ Lavalink Connected")
    except Exception as e:
        print(f"❌ Lavalink Error: {e}")

    await bot.tree.sync()
    print("✅ Slash commands synced")

# 🔥 PLAY
@bot.tree.command(name="play", description="Play music")
@app_commands.describe(query="Song or YouTube link")
async def play(interaction: discord.Interaction, query: str):

    if not interaction.user.voice:
        return await interaction.response.send_message("❌ Join VC first", ephemeral=True)

    await interaction.response.defer()

    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect(cls=wavelink.Player)

    player: wavelink.Player = interaction.guild.voice_client
    queues.setdefault(interaction.guild.id, [])

    tracks = await wavelink.Playable.search(query)

    if not tracks:
        return await interaction.followup.send("❌ No result")

    if isinstance(tracks, wavelink.Playlist):
        for t in tracks.tracks:
            queues[interaction.guild.id].append(t)

        await interaction.followup.send(f"✅ Playlist add: {len(tracks.tracks)} songs")
    else:
        track = tracks[0]
        queues[interaction.guild.id].append(track)
        await interaction.followup.send(f"✅ Added: {track.title}")

    if not player.playing:
        await play_next(interaction.guild, interaction.channel)

# 🔥 SKIP
@bot.tree.command(name="skip")
async def skip(interaction: discord.Interaction):
    player = interaction.guild.voice_client
    if player:
        await player.stop()
        await interaction.response.send_message("⏭ Skipped")

# 🔥 STOP
@bot.tree.command(name="stop")
async def stop(interaction: discord.Interaction):
    queues[interaction.guild.id] = []
    player = interaction.guild.voice_client
    if player:
        await player.disconnect()
    await interaction.response.send_message("🛑 Stopped")

bot.run(TOKEN)
