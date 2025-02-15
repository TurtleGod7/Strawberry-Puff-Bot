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
    user_id = interaction.user.id

    conn = sqlite3.connect("assets\\database\\users.db") if os.name == "nt" else sqlite3.connect("assets/database/users.db")

    cursor = conn.cursor()
    
    cursor.execute("SELECT pity FROM pity WHERE username = ?", (user_id,))
    pityinfo = cursor.fetchone()

    if pityinfo is None:  # If user is not in the database
        pity = 0
        cursor.execute("INSERT INTO pity (username, pity) VALUES (?, ?)", (user_id, 0))
        conn.commit()
    else:
        pity = pityinfo[0]  # Extract pity value
    
    cursor.close()
    conn.close()
    
    conn = sqlite3.connect("assets\\database\\puffs.db") if os.name == "nt" else sqlite3.connect("assets/database/puffs.db")

    cursor = conn.cursor()
    
    if int(pity) < 100:
        cursor.execute("SELECT * FROM puffs")
        rows = cursor.fetchall()
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
        item_id, name, description, image_path, weights, isRare = choice

    else:
        cursor.execute("SELECT * FROM puffs WHERE isRare = 2")
        rows = cursor.fetchall()
        choice = random.choice(rows)
        total_weight = len(rows)
        weights = 1
        cursor.close()
        conn.close()
        item_id, name, description, image_path, notneededweight, isRare = choice
    
    chance = round(round(weights/int(total_weight), 4)*100,2)
    
    conn = sqlite3.connect("assets\\database\\users.db") if os.name == "nt" else sqlite3.connect("assets/database/users.db")
    
    cursor = conn.cursor()
    
    
    cursor.execute("SELECT EXISTS(SELECT 1 FROM stats WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 0: 
        cursor.execute("INSERT INTO stats (username, rolls, gold, purple) VALUES (?,?,?,?)", (user_id, 0, 0, 0))
    
    cursor.execute("UPDATE stats SET rolls = rolls + 1 WHERE username = ?", (user_id,))
    
    if int(isRare) == 2:
        cursor.execute("UPDATE stats SET gold = gold + 1 WHERE username = ?", (user_id,))
    if int(isRare) == 1:
        cursor.execute("UPDATE stats SET purple = purple + 1 WHERE username = ?", (user_id,))
    
    cursor.execute("UPDATE pity SET pity = pity + 1 WHERE username = ?", (user_id,))

    if isRare == 2:
        cursor.execute("UPDATE pity SET pity = 0 WHERE username = ?", (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    rareColors = {
        0 : discord.Color.blue(),
        1 : discord.Color.purple(),
        2 : discord.Color.gold()
    }
    
    image_path = f"https://raw.githubusercontent.com/TurtleGod7/Strawberry-Puff-Bot/refs/heads/main/assets/puffs/{image_path}?=raw"
    
    embed = discord.Embed(title="Your Roll Results", color=rareColors.get(isRare))
    if isRare == 2:
        embed.add_field(name=":strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry:",
                    value=f"You got a **{name}**.\nIt is {description}\nIt was a **{chance}%** chance to roll this puff!\nYou rolled this puff at **{pity}** pity.\n"
        )
    else:
        embed.add_field(name=":strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry:",
                    value=f"You got a **{name}**.\nIt is {description}\nIt was a **{chance}%** chance to roll this puff!\n"
        )
    embed.set_image(url=image_path)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="statistics", description="Get some info on your rolls")
async def stats(interaction: discord.Interaction):
    conn = sqlite3.connect("assets\\database\\users.db") if os.name == "nt" else sqlite3.connect("assets/database/users.db")
    
    cursor = conn.cursor()
    
    user_id = interaction.user.id
    
    cursor.execute("SELECT * FROM stats WHERE username = ?", (user_id,))
    choice = cursor.fetchone()
    username, rolls, gold, purple = choice
    
    cursor.close()
    conn.close()
    
    embed = discord.Embed(title="Your Puff Gacha statistics", color=discord.Color.blurple())
    embed.add_field(name="Total Rolls", value=f"You've rolled **{rolls}** times!", inline=False)
    embed.add_field(name="Rare Rolls", value=f"You've also ~~pulled~~ rolled a gold rarity puff **{gold}** times and a purple rarity puff **{purple}** times!", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

class DropRatesView(discord.ui.View):
    def __init__(self, items, total_weight):
        super().__init__(timeout=60)  # Buttons expire after 60 seconds
        self.items = items
        self.total_weight = total_weight
        self.page = 0
        self.items_per_page = 5  # Adjust if needed

    def generate_embed(self):
        embed = discord.Embed(title="📊 Puff Drop Rates", color=discord.Color.gold())
        
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        page_items = self.items[start:end]

        for name, weight, isRare in page_items:
            chance = round(round((weight / self.total_weight), 4) * 100, 2)  # Convert to percentage
            if isRare == 2: embed.add_field(name=name+" :yellow_square:", value=f"{chance:.2f}%", inline=False)
            elif isRare == 1: embed.add_field(name=name+" :purple_square:", value=f"{chance:.2f}%", inline=False)
            else: embed.add_field(name=name+" :blue_square:", value=f"{chance:.2f}%", inline=False)
            

        embed.set_footer(text=f"Page {self.page + 1} / {len(self.items) // self.items_per_page + 1}")
        return embed

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="➡️ Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.page + 1) * self.items_per_page < len(self.items):
            self.page += 1
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

@bot.tree.command(name="chances", description="Displays the chances for each puff")
async def drop_rates(interaction: discord.Interaction):
    db_path = "assets\\database\\puffs.db" if os.name == "nt" else "assets/database/puffs.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(weight) FROM puffs")
    total_weight = cursor.fetchone()[0]

    if total_weight is None or total_weight == 0: await interaction.response.send_message("There's been an issue, please contact the developer for more assistance")

    cursor.execute("SELECT name, weight, isRare FROM puffs ORDER BY weight ASC")
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    view = DropRatesView(items, total_weight)
    await interaction.response.send_message(embed=view.generate_embed(), view=view)

@bot.tree.command(name="suggestions", description="Suggest new ideas for our bot!")
async def stats(interaction: discord.Interaction):
    embed = discord.Embed(title="Please direct your help here", color=discord.Color.fuchsia())
    embed.add_field(name="Please redirect your suggestions to this google form", value="*https://forms.gle/gce7woXR5i38fnXY7*")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Techsupport is on the way!", color=discord.Color.greyple())
    embed.add_field(name="/puffroll", value="This is the major mechanic of this bot and this is how you set up your local account.")
    embed.add_field(name="/statistics", value="This is the statistics function so you can understand more about your luck.")
    embed.add_field(name="/chances", value="This is the chances function that displays information for each puff.")
    embed.add_field(name="/suggestions", value="Use this function to give us any suggestions")
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)