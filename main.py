import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select
import aiosqlite
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# === KEEP ALIVE ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is alive!"

def keep_alive():
    Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080}).start()

keep_alive()

# === LOAD ENV ===
load_dotenv()

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")

if not TOKEN:
    print("❌ ERROR: DISCORD TOKEN not found in .env")
    exit()

if not LOG_CHANNEL_ID or not LOG_CHANNEL_ID.isdigit():
    print("❌ ERROR: LOG_CHANNEL_ID is missing or invalid in .env")
    exit()

LOG_CHANNEL_ID = int(LOG_CHANNEL_ID)

# === BOT SETUP ===
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

DB_FILE = "vouches.db"

products = [
    ("1337-ch3at5", "1337-ch3at5"),
    ("grandrp-m0n3y", "grandrp-m0n3y"),
    ("grandrp-acc0unt5", "grandrp-acc0unt5"),
    ("grandrp-m0n3y-m3th0d", "grandrp-m0n3y-m3th0d"),
    ("tr1gg3r-b0t", "tr1gg3r-b0t"),
    ("shax-cl3an3r", "shax-cl3an3r"),
    ("custom-discord-bot", "custom-discord-bot"),
    ("custom-ch3at3r", "custom-ch3at3r"),
    ("l3ad3r-scr1pts", "l3ad3r-scr1pts"),
    ("adm1n-scr1pts", "adm1n-scr1pts"),
    ("l3ad3r-or-adm1n-appl1cat1on", "l3ad3r-or-adm1n-appl1cat1on"),
    ("pc-cl3an3r", "pc-cl3an3r"),
    ("custom-ch3at3r-redux", "custom-ch3at3r-redux"),
    ("h0w-to-b4n-evad3", "h0w-to-b4n-evad3"),
    ("premium-b4n-evad3", "premium-b4n-evad3"),
    ("pc-ch3ck-pr0c3dur3", "pc-ch3ck-pr0c3dur3"),
    ("V4LOR4NT-SHOP", "V4LOR4NT-SHOP"),
    ("FreeFire-P4N3LS", "FreeFire-P4N3LS"),
    ("FreeFire-D14MONDS", "FreeFire-D14MONDS"),
    ("FreeFire-ACC0UN7S", "FreeFire-ACC0UN7S"),
    ("FreeFire-TOURN4M3NT", "FreeFire-TOURN4M3NT"),
    ("BGMI-ACC0UN7S", "BGMI-ACC0UN7S"),
    ("BGMI-UC", "BGMI-UC"),
    ("BGMI-TOURN4M3NT", "BGMI-TOURN4M3NT"),
    ("4M4ZON-SHOP", "4M4ZON-SHOP"),
    ("OTHER PRODUCT", "OTHER PRODUCT")
]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await tree.sync()
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name="Vouches Of GrandX Store")
    )

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS vouches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vouched_user_id INTEGER,
                vouched_by_id INTEGER,
                product TEXT,
                feedback TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()
        print("📦 Database initialized!")

class ProductSelect(Select):
    def __init__(self, view):
        self.parent_view = view
        options = [discord.SelectOption(label=label, value=value) for value, label in products]
        super().__init__(placeholder="🏩 Select your Product", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected = self.values[0]
        await interaction.response.defer()
        self.parent_view.stop()

class ProductView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.selected = None
        self.select = ProductSelect(self)
        self.add_item(self.select)

@tree.command(name="vouch", description="Vouch for a user")
@app_commands.describe(user="User to vouch for", feedback="Your feedback message")
async def vouch(interaction: discord.Interaction, user: discord.Member, feedback: str):
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't vouch for yourself!\nMade by Kai", ephemeral=True)
        return

    view = ProductView()
    await interaction.response.send_message("🏩 Please select a product to vouch for:", view=view, ephemeral=True)
    timeout = await view.wait()

    if timeout or not view.selected:
        await interaction.followup.send("⚠️ You didn't select a product in time. Please try again.", ephemeral=True)
        return

    product = view.selected

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO vouches (vouched_user_id, vouched_by_id, product, feedback) VALUES (?, ?, ?, ?)",
            (user.id, interaction.user.id, product, feedback)
        )
        await db.commit()
        cursor = await db.execute("SELECT last_insert_rowid()")
        (vouch_id,) = await cursor.fetchone()

    embed = discord.Embed(
        title=f"📬 Vouch #{vouch_id}",
        color=discord.Color.purple()
    )
    embed.add_field(name="🎯 Product", value=f"**{product}**", inline=False)
    embed.add_field(name="💬 Feedback", value=f"*{feedback}*", inline=False)
    embed.add_field(name="🙋 Vouched by", value=f"<@{interaction.user.id}>", inline=False)
    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png")
    embed.set_footer(text="❤ Made By Kai | discord.gg/e2U2FNszUU")

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
    else:
        print("⚠️ LOG_CHANNEL_ID is invalid or bot can't access that channel.")

    await interaction.followup.send("✅ Your vouch has been submitted successfully!", ephemeral=True)

@tree.command(name="vouches", description="See how many vouches a user has")
@app_commands.describe(user="User to check")
async def vouches(interaction: discord.Interaction, user: discord.Member):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT id, vouched_by_id, product, feedback, timestamp FROM vouches WHERE vouched_user_id = ?", (user.id,))
        rows = await cursor.fetchall()

    if not rows:
        await interaction.response.send_message(f"{user.mention} has no vouches yet.\nMade by Kai")
        return

    embed = discord.Embed(title=f"📋 Vouches for {user.display_name}", color=discord.Color.blue())
    for vouch_id, vouched_by_id, product, feedback, timestamp in rows[:10]:
        embed.add_field(name=f"📬 Vouch #{vouch_id}", value=f"🎯 **{product}**\n💬 *{feedback}*\n🙋 By: <@{vouched_by_id}>\n📅 {timestamp[:10]}", inline=False)
    embed.set_footer(text="❤ Made By Kai | discord.gg/e2U2FNszUU")

    await interaction.response.send_message(embed=embed)

@tree.command(name="unvouch", description="Remove a user's vouch (admin only)")
@app_commands.describe(user="User to unvouch")
async def unvouch(interaction: discord.Interaction, user: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only admins can use this command.\nMade by Kai", ephemeral=True)
        return

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM vouches WHERE vouched_user_id = ?", (user.id,))
        await db.commit()

    await interaction.response.send_message(f"🗑️ All vouches for {user.mention} have been removed.\nMade by Kai")

@tree.command(name="topvouched", description="See the most vouched users")
async def topvouched(interaction: discord.Interaction):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('''
            SELECT vouched_user_id, COUNT(*) as count FROM vouches
            GROUP BY vouched_user_id ORDER BY count DESC LIMIT 5
        ''')
        top = await cursor.fetchall()

    embed = discord.Embed(title="🏆 Top Vouched Users", color=discord.Color.gold())
    for user_id, count in top:
        try:
            user = await bot.fetch_user(user_id)
            embed.add_field(name=user.display_name, value=f"{count} vouches", inline=False)
        except:
            embed.add_field(name=f"Unknown User ({user_id})", value=f"{count} vouches", inline=False)
    embed.set_footer(text="@GrandX Vouches | discord.gg/e2U2FNszUU")

    await interaction.response.send_message(embed=embed)

# === START THE BOT ===
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ ERROR while starting bot: {e}")
