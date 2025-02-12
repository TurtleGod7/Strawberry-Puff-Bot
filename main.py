import os
import discord
from flask import Flask
import threading
from discord.ext import commands
from dotenv import load_dotenv
import random
import sqlite3
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Initialize Flask and the bot
app = Flask(__name__)

# Define a simple route for UptimeRobot
@app.route('/')
def index():
    return "Bot is running!"

# Start the Flask server in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=80)

# Start Flask in a separate thread to avoid blocking the bot
thread = threading.Thread(target=run_flask)
thread.start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

@bot.tree.command(name="puffroll", description="Roll a random puff")
async def Roll_a_puff(interaction: discord.Interaction):
    if os.name == "nt":
        conn = sqlite3.connect("assets\\database\\puffs.db")
    else:
        conn = sqlite3.connect("assets/database/puffs.db")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM puffs")
    rows = cursor.fetchall()
    # Checks if rows exist
    if rows:
        cursor.execute("SELECT id, weight FROM puffs")
        data =  cursor.fetchall()
        items, weights = zip(*data) # Randomly selects a weighted role (id)
        selected_id = random.choices(items, weights=weights, k=1)[0]

        cursor.execute("SELECT * FROM puffs WHERE id = ?", (selected_id,))
        choice = cursor.fetchone() # Gets the full info from the id
        
        cursor.execute("SELECT SUM(weight) FROM puffs")
        total_weight = cursor.fetchone()[0]
        cursor.close() # Gets info for the chance calculation
    else:
        await interaction.response.send_message("There's been an issue, please contact the developer for more assistance")
    
    item_id, name, description, image_path, weights = choice
    
    chance = round(weights/int(total_weight), 4)*100
    if os.name == "nt":
        image_path = f"assets\\puffs\\{image_path}"
    else:
        image_path = f"assets/puffs/{image_path}"
    img = discord.File(image_path, filename=image_path)
    
    await interaction.response.send_message(
        f"You got a {name}.\nIt is {description}\nIt was a {chance}% chance to roll this puff!\n",
        file=img
    )
bot.run(TOKEN)