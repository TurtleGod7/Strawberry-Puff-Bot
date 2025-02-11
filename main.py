import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
import sqlite3
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

names = ()

@bot.event
async def on_ready():
    await bot.tree.sync()
    
    if os.name == "nt":
        conn = sqlite3.connect("assets\\database\\puffs.db")
    else:
        conn = sqlite3.connect("assets/database/puffs.db")
    
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS puffs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        imagepath TEXT NOT NULL
    )
    """)
    conn.close
    print(f'Logged in as {bot.user}')    

@bot.event
async def on_guild_join(guild):
    bot_member = guild.get_member(bot.user.id)
    bot_role = discord.utils.get(guild.roles, name="Bot")
    
    if not bot_role:
        bot_role = await guild.create_role(name="Bot")
    
    permissions = discord.Permissions(send_message=True, attach_files=True, read_message_history=True)
    
    await bot_member.add_roles(bot_role)
    
    await bot_role.edit(permissions=permissions)

@bot.tree.command(name="puffroll", description="Roll a random puff")
async def Roll_a_puff(interaction: discord.Interaction):
    if os.name == "nt":
        conn = sqlite3.connect("assets\\database\\puffs.db")
    else:
        conn = sqlite3.connect("assets/database/puffs.db")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM puffs")
    rows = cursor.fetchall()
    
    cursor.close()
    
    if rows:
        choice = random.choice(rows)
    else:
        await interaction.response.send_message("There's been an issue, please contact the developer for more assitance")
    
    item_id, name, description, image_path = choice
    if os.name == "nt":
        image_path = f"assets/puffs/{image_path}"
    else:
        image_path = f"assets\\puffs\\{image_path}"
    img = discord.File(image_path, filename=image_path)
    
    await interaction.response.send_message(
        f"You got a {name}.\nIt is {description}\n",
        file=img
    )
bot.run(TOKEN)