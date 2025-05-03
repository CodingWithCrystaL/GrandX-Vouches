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
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

# === BOT SETUP ===
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
DB_FILE = "vouches.db"

PRODUCTS = [
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

GRANDX_LOGO_URL = "https://cdn.discordapp.com/attachments/1226891662254286911/1235928196612139090/7E21D39E-ECDF-4C6C-B393-347F979B16CE.jpeg"

# === DB INIT ===
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS vouches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vouched_user_id INTEGER,
                vouched_by_id INTEGER,
                product TEXT,
                feedback TEXT,
                rating INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# === DROPDOWNS ===
class ProductSelect(Select):
    def __init__(self, view):
        self.parent_view = view
        options = [discord.SelectOption(label=label, value=value) for value, label in PRODUCTS]
        super().__init__(placeholder="Select your Product", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.product = self.values[0]
        await interaction.response.send_message("✅ Product selected. Now rate the service:", view=self.parent_view.rating_view, ephemeral=True)

class RatingSelect(Select):
    def __init__(self, view):
        self.parent_view = view
        options = [
            discord.SelectOption(label="Fast Delivery ⚡", value="5"),
            discord.SelectOption(label="Legit ✅", value="5"),
            discord.SelectOption(label="Good 👍", value="4"),
            discord.SelectOption(label="5/5 ⭐⭐⭐⭐⭐", value="5"),
            discord.SelectOption(label="4/5 ⭐⭐⭐⭐", value="4"),
            discord.SelectOption(label="3/5 ⭐⭐⭐", value="3"),
            discord.SelectOption(label="2/5 ⭐⭐", value="2"),
            discord.SelectOption(label="1/5 ⭐", value="1"),
        ]
        super().__init__(placeholder="Select your Feedback for the Service", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.rating = int(self.values[0])
        self.parent_view.stop()
        await interaction.response.send_message("✅ Rating recorded!", ephemeral=True)

class ProductRatingView(View):
    def __init__(self):
        super().__init__(timeout=120)
        self.product = None
        self.rating = None
        self.rating_view = RatingView(self)
        self.add_item(ProductSelect(self))

class RatingView(View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view
        self.add_item(RatingSelect(parent_view))

# === READY EVENT (sync commands) ===
@bot.event
async def on_ready():
    await init_db()
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} commands to GUILD_ID: {GUILD_ID}")
    except Exception as e:
        print(f"❌ Command sync failed: {e}")
    await bot.change_presence(activity=discord.Game(name="Vouching Service"))
    print(f"✅ Bot is online as {bot.user}")

# === VOUCH COMMAND ===
@tree.command(name="vouch", description="Give a vouch to someone", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User to vouch for", feedback="Your feedback message")
async def vouch(interaction: discord.Interaction, user: discord.Member, feedback: str):
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't vouch for yourself.", ephemeral=True)
        return

    view = ProductRatingView()
    if interaction.response.is_done():
        await interaction.followup.send("Please select a product to vouch for:", view=view, ephemeral=True)
    else:
        await interaction.response.send_message("Please select a product to vouch for:", view=view, ephemeral=True)

    await view.wait()

    if not view.product or not view.rating:
        await interaction.followup.send("⏰ You didn't complete the selection in time.", ephemeral=True)
        return

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO vouches (vouched_user_id, vouched_by_id, product, feedback, rating) VALUES (?, ?, ?, ?, ?)",
            (user.id, interaction.user.id, view.product, feedback, view.rating)
        )
        await db.commit()

    embed = discord.Embed(title="Feedback Received", description="We received feedback for your transaction!", color=discord.Color.green())
    embed.add_field(name="Customer", value=user.mention, inline=False)
    embed.add_field(name="Rating", value=f"{view.rating} ⭐", inline=False)
    embed.add_field(name="Feedback", value=feedback, inline=False)
    embed.set_thumbnail(url=GRANDX_LOGO_URL)
    embed.set_footer(text="Thanks for your support! | Made by Kai", icon_url=GRANDX_LOGO_URL)

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

    await interaction.followup.send("✅ Your vouch has been submitted!", ephemeral=True)

# === RUN BOT ===
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ Error while running the bot: {e}")
