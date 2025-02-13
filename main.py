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
    # Hope that this code doesn't run since I've changed the columns already
    
    conn = sqlite3.connect("assets\\database\\puffs.db") if os.name == "nt" else sqlite3.connect("assets/database/puffs.db")
    
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
    
    conn = sqlite3.connect("assets\\database\\users.db") if os.name == "nt" else sqlite3.connect("assets/database/users.db")
    
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        rolls INTEGER,
        rare rolls INTEGER
    )               
    """)
    
    cursor.close()
    conn.close()
    print(f'Logged in as {bot.user}')    

@bot.tree.command(name="puffroll", description="Roll a random puff")
async def Roll_a_puff(interaction: discord.Interaction):
    
    conn = sqlite3.connect("assets\\database\\puffs.db") if os.name == "nt" else sqlite3.connect("assets/database/puffs.db")

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
        conn.close()
    else:
        await interaction.response.send_message("There's been an issue, please contact the developer for more assistance")
    
    item_id, name, description, image_path, weights, isRare = choice
    
    chance = round(round(weights/int(total_weight), 4)*100,2)
    
    conn = sqlite3.connect("assets\\database\\users.db") if os.name == "nt" else sqlite3.connect("assets/database/users.db")
    
    cursor = conn.cursor()
    
    user_id = interaction.user.id
    
    cursor.execute("SELECT EXISTS(SELECT 1 FROM stats WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 0: 
        cursor.execute("INSERT INTO stats (username, rolls, rare) VALUES (?,?,?)", (user_id, 0, 0))
    
    cursor.execute("UPDATE stats SET rolls = rolls + 1 WHERE username = ?", (user_id,))
    
    if int(isRare) == 1:
        cursor.execute("UPDATE stats SET rare = rare + 1 WHERE username = ?", (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if os.name == "nt":
        image_path = f"assets\\puffs\\{image_path}"
    else:
        image_path = f"assets/puffs/{image_path}"
    img = discord.File(image_path, filename=image_path)
    
    await interaction.response.send_message(
        f"You got a {name}.\nIt is {description}\nIt was a {chance}% chance to roll this puff!\n",
        file=img
    )

@bot.tree.command(name="statistics", description="Get some info on your rolls")
async def stats(interaction: discord.Interaction):
    conn = sqlite3.connect("assets\\database\\users.db") if os.name == "nt" else sqlite3.connect("assets/database/users.db")
    
    cursor = conn.cursor()
    
    user_id = interaction.user.id
    
    cursor.execute("SELECT * FROM stats WHERE username = ?", (user_id,))
    choice = cursor.fetchone()
    username, rolls, rare = choice
    
    cursor.close()
    conn.close()
    
    embed = discord.Embed(title="Your Puff Gacha statistics", color=discord.Color.blurple())
    embed.add_field(name="Total Rolls", value=f"You've rolled **{rolls}** times!", inline=False)
    embed.add_field(name="Rare Rolls", value=f"You've also ~~pulled~~ rolled a 5 star **{rare}** times!", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="chances", description="Displays the chances for each puff")
async def chances(interaction: discord.Interaction):
    conn = sqlite3.connect("assets\\database\\puffs.db") if os.name == "nt" else sqlite3.connect("assets/database/puffs.db")
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(weight) FROM puffs")
    total_weight = cursor.fetchone()[0]
    
    if total_weight is None or total_weight == 0: await interaction.response.send_message("There's been an issue, please contact the developer for more assistance")
    
    cursor.execute("SELECT name, weight, isRare FROM puffs ORDER by weight ASC")
    items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    embed = discord.Embed(title="Puff Weights", color=discord.Color.blurple())
    
    for name, weight, isRare in items:
        chance = round((weight/total_weight)*100, 2)
        if isRare == 1:
            embed.add_field(name=name+":star:", value=f"{chance:.2f}%", inline=False)
        else:
            embed.add_field(name=name, value=f"{chance:.2f}%", inline=False)
    
    embed.set_footer(text=f"Star indicates a 5 star\nRequested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Techsupport is on the way!", color=discord.Color.blurple())
    embed.add_field(name="\\puffroll", value="This is the major mechanic of this bot and this is how you set up your local account.", inline=False)
    embed.add_field(name="\\statistics", value="This is the statistics function so you can understand more about your luck.")
    embed.add_field(name="\\chances", value="This is the chances function that displays information for each puff.")
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)