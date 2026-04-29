import os
import discord
from discord import app_commands
from discord.ext import commands
import wavelink

TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_URL = os.getenv("LAVALINK_URL")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

queues = {}


class MusicButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Pause", emoji="⏸", style=discord.ButtonStyle.primary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client
        if player:
            await player.pause(True)
        await interaction.response.send_message("⏸ Paused", ephemeral=True)

    @discord.ui.button(label="Resume", emoji="▶️", style=discord.ButtonStyle.success)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client
        if player:
            await player.pause(False)
        await interaction.response.send_message("▶️ Resumed", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client
        if player:
            await player.stop()
        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="🛑", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        queues[interaction.guild.id] = []
        player = interaction.guild.voice_client
        if player:
            await player.disconnect()
        await interaction.response.send_message("🛑 Stopped", ephemeral=True)


async def play_next(guild, channel):
    player = guild.voice_client
    q = queues.get(guild.id, [])

    if not player:
        return

    if not q:
        await channel.send("✅ Queue sesh.")
        return

    track = q.pop(0)
    await player.play(track)

    embed = discord.Embed(
        title="🎶 Now Playing",
        description=f"**{track.title}**",
        color=0x8A2BE2
    )
    embed.set_footer(text="MR-BRO-MUSIC • Lavalink")
    await channel.send(embed=embed, view=MusicButtons())


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    try:
        await bot.tree.sync()
        print("✅ Slash commands synced")
    except Exception as e:
        print(f"❌ Slash sync error: {e}")

    if not LAVALINK_URL:
        print("❌ LAVALINK_URL missing")
        return

    try:
        node = wavelink.Node(uri=LAVALINK_URL, password=LAVALINK_PASSWORD)
        await wavelink.Pool.connect(client=bot, nodes=[node])
        print(f"✅ Lavalink status: {node.status}")
    except Exception as e:
        print(f"❌ Lavalink connect failed: {e}")


@bot.tree.command(name="play", description="Play song / YouTube link / playlist")
@app_commands.describe(query="Song name, YouTube link, or playlist link")
async def play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("❌ Age voice channel e join koro.", ephemeral=True)

    await interaction.response.defer()

    try:
        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect(cls=wavelink.Player)

        player = interaction.guild.voice_client
        queues.setdefault(interaction.guild.id, [])

        tracks = await wavelink.Playable.search(query)

        if not tracks:
            return await interaction.followup.send("❌ Kono result pailam na.")

        if isinstance(tracks, wavelink.Playlist):
            for track in tracks.tracks:
                queues[interaction.guild.id].append(track)
            await interaction.followup.send(f"✅ Playlist add holo: **{len(tracks.tracks)}** songs")
        else:
            track = tracks[0]
            queues[interaction.guild.id].append(track)
            await interaction.followup.send(f"✅ Queue te add holo: **{track.title}**")

        if not player.playing:
            await play_next(interaction.guild, interaction.channel)

    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{e}`")


@bot.tree.command(name="skip", description="Skip current song")
async def skip(interaction: discord.Interaction):
    player = interaction.guild.voice_client
    if player:
        await player.stop()
        await interaction.response.send_message("⏭ Skipped")
    else:
        await interaction.response.send_message("❌ Bot voice channel e nai.", ephemeral=True)


@bot.tree.command(name="pause", description="Pause current song")
async def pause(interaction: discord.Interaction):
    player = interaction.guild.voice_client
    if player:
        await player.pause(True)
        await interaction.response.send_message("⏸ Paused")
    else:
        await interaction.response.send_message("❌ Bot voice channel e nai.", ephemeral=True)


@bot.tree.command(name="resume", description="Resume current song")
async def resume(interaction: discord.Interaction):
    player = interaction.guild.voice_client
    if player:
        await player.pause(False)
        await interaction.response.send_message("▶️ Resumed")
    else:
        await interaction.response.send_message("❌ Bot voice channel e nai.", ephemeral=True)


@bot.tree.command(name="queue", description="Show queue")
async def queue(interaction: discord.Interaction):
    q = queues.get(interaction.guild.id, [])
    if not q:
        return await interaction.response.send_message("📭 Queue empty.")

    text = "\n".join([f"**{i}.** {track.title}" for i, track in enumerate(q[:10], 1)])
    embed = discord.Embed(title="🎵 Music Queue", description=text, color=0x8A2BE2)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stop", description="Stop music and disconnect")
async def stop(interaction: discord.Interaction):
    queues[interaction.guild.id] = []
    player = interaction.guild.voice_client
    if player:
        await player.disconnect()
    await interaction.response.send_message("🛑 Stopped & disconnected")


bot.run(TOKEN)
