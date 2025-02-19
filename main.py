import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from random import choices
import sqlite3
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

### Control variables
pity_limit = 100
git_username = "TurtleGod7"
git_repo = "Strawberry-Puff-Bot"
button_page_expiry = 60
items_per_page = 5
eidolon_max = 10
###

'''
Gold Rarity puffs: <1%
Purple rarity puffs: 1%<=x<=10%
Blue rarity puffs: everything else
'''

'''
from flask import Flask
import threading

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
'''

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
        imagepath TEXT NOT NULL UNIQUE,
        weight INTEGER,
        isRare NUMERIC NOT NULL DEFAULT 0
    )
    """)
    
    cursor.execute("PRAGMA journal_mode=WAL")
    
    conn.commit
    cursor.close
    conn.close
    
    conn = sqlite3.connect("assets\\database\\users.db") if os.name == "nt" else sqlite3.connect("assets/database/users.db")
    
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        "username" INTEGER PRIMARY KEY NOT NULL UNIQUE,
        "rolls" INTEGER DEFAULT 0,
        "gold" rolls INTEGER DEFAULT 0,
        "purple" INTEGER DEFAULT 0,
        "rolledGolds" TEXT
    )               
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pity (
        "username" INTEGER PRIMARY KEY NOT NULL UNIQUE,
        "pity" INTEGER NOT NULL DEFAULT 0
    )               
    """)
    
    cursor.execute("PRAGMA journal_mode=WAL")
    
    conn.commit
    cursor.close()
    conn.close()
    
    print(f'Logged in as {bot.user}')    

@bot.tree.command(name="puffroll", description="Roll a random puff")
async def Roll_a_puff(interaction: discord.Interaction):
    user_id = interaction.user.id

    conn = sqlite3.connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else sqlite3.connect("assets/database/users.db", check_same_thread=False)

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
    
    conn = sqlite3.connect("assets\\database\\puffs.db", check_same_thread=False) if os.name == "nt" else sqlite3.connect("assets/database/puffs.db", check_same_thread=False)

    cursor = conn.cursor()
    
    if int(pity) < pity_limit:
        cursor.execute("SELECT id, weight FROM puffs")
        data =  cursor.fetchall()
        items, weights = zip(*data) # Randomly selects a weighted role (id)
        selected_id = choices(items, weights=weights, k=1)[0]
        cursor.execute("SELECT * FROM puffs WHERE id = ?", (selected_id,))
        choice = cursor.fetchone() # Gets the full info from the id 
        
        cursor.execute("SELECT SUM(weight) FROM puffs")
        total_weight = cursor.fetchone()[0]
        
        cursor.close() # Gets info for the chance calculation
        conn.close()
    else:
        cursor.execute("SELECT id, weight FROM puffs WHERE isRare = 2")
        data =  cursor.fetchall()
        items, weights = zip(*data) # Randomly selects a weighted role (id)
        selected_id = choices(items, weights=weights, k=1)[0]
        cursor.execute("SELECT * FROM puffs WHERE id = ?", (selected_id,))
        choice = cursor.fetchone() # Gets the full info from the id 
        
        cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 2")
        total_weight = cursor.fetchone()[0]
        cursor.close()
        
        conn.close()
        
    item_id, name, description, image_path, weights, isRare = choice
    
    chance = round(round(weights/int(total_weight), 4)*100,2)
    
    conn = sqlite3.connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else sqlite3.connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT EXISTS(SELECT 1 FROM stats WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 0: 
        cursor.execute("INSERT INTO stats (username, rolls, gold, purple, rolledGolds) VALUES (?,?,?,?,?)", (user_id, 0, 0, 0,""))
    
    cursor.execute("SELECT rolledGolds FROM stats WHERE username = ?", (user_id,))
    rolledGolds = cursor.fetchone()[0]
    frequency = {}
    if None != rolledGolds:
        split_by_puffs = rolledGolds.split(";")
        for split in split_by_puffs:
            frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    if isRare == 2:
        eidolon = frequency.get(name, -1)
        if eidolon < eidolon_max:
            frequency[name] = eidolon+1
    
    frequency = dict(sorted(frequency.items()))
    
    cursor.execute("UPDATE stats SET rolls = rolls + 1 WHERE username = ?", (user_id,))
    
    if int(isRare) == 2:
        cursor.execute("UPDATE stats SET gold = gold + 1 WHERE username = ?", (user_id,))
    if int(isRare) == 1:
        cursor.execute("UPDATE stats SET purple = purple + 1 WHERE username = ?", (user_id,))
    
    cursor.execute("UPDATE pity SET pity = pity + 1 WHERE username = ?", (user_id,))

    if isRare == 2:
        cursor.execute("UPDATE pity SET pity = 0 WHERE username = ?", (user_id,))
    
    cursor.execute("UPDATE stats SET rolledGolds = ? WHERE username = ?", (";".join([f"{k}_{v}" for k, v in frequency.items()]) or None, user_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    rareColors = {
        0 : discord.Color.blue(),
        1 : discord.Color.purple(),
        2 : discord.Color.gold()
    }
    
    image_path = f"https://raw.githubusercontent.com/{git_username}/{git_repo}/refs/heads/main/assets/puffs/{image_path}?=raw"
    
    embed = discord.Embed(title="Your Roll Results", color=rareColors.get(isRare))
    if isRare == 2:
        embed.add_field(
            name=":strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry:",
            value=f"You got a **{name}**.\nIt is {description}\nIt was a **{chance}%** chance to roll this puff!\nYou rolled this puff at **{pity}** pity.\n"
        )
    else:
        embed.add_field(
            name=":strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry:",
            value=f"You got a **{name}**.\nIt is {description}\nIt was a **{chance}%** chance to roll this puff!\n"
        )
    embed.set_image(url=image_path)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="statistics", description="Get some info on your rolls")
async def statistics(interaction: discord.Interaction):
    conn = sqlite3.connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else sqlite3.connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    user_id = interaction.user.id
    
    cursor.execute("SELECT * FROM stats WHERE username = ?", (user_id,))
    choice = cursor.fetchone()
    
    if choice is None:
        cursor.execute("INSERT INTO stats (username, rolls, gold, purple, rolledGolds) VALUES (?, ?, ?, ?)", (user_id, 0, 0, 0,""))
        conn.commit()
    
    username, rolls, gold, purple, rolledGolds = choice
    
    cursor.close()
    conn.close()
    
    frequency = {}
    if None != rolledGolds:
        split_by_puffs = rolledGolds.split(";")
        for split in split_by_puffs:
            frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    ascenscions_description_string = ""
    for k, v in frequency.items():
        ascenscions_description_string += f"* *{k}*  **{v}** time(s)\n"
    if ascenscions_description_string == "":
        ascenscions_description_string += "You're seeing this because you didn't roll any gold rarity puffs :sob:"
    
    embed = discord.Embed(title="Your Puff Gacha statistics", color=discord.Color.blurple())
    embed.add_field(name="Total Rolls", value=f"You've rolled **{rolls}** times!", inline=False)
    embed.add_field(name="Rare Rolls", value=f"You've also ~~pulled~~ rolled a gold rarity puff **{gold}** time(s) and a purple rarity puff **{purple}** time(s)!", inline=False)
    embed.add_field(name="Ascensions", value=ascenscions_description_string, inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

class DropRatesView(discord.ui.View):
    def __init__(self, items, total_weight):
        super().__init__(timeout=button_page_expiry)  # Buttons expire after 60 seconds
        self.items = items
        self.total_weight = total_weight
        self.page = 0
        self.items_per_page = items_per_page  # Adjust if needed

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
    conn = sqlite3.connect(db_path, check_same_thread=False)
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

@bot.tree.command(name="help", description="AHHHHH, I NEED HELP!!!!")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Techsupport is on the way!", color=discord.Color.greyple())
    embed.add_field(name="/puffroll", value="This is the major mechanic of this bot and this is how you set up your local account.")
    embed.add_field(name="/statistics", value="This is the statistics function so you can understand more about your luck.")
    embed.add_field(name="/chances", value="This is the chances function that displays information for each puff.")
    embed.add_field(name="/suggestions", value="Use this function to give us any suggestions")
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="Just some good to know information")
async def information(interaction: discord.Interaction):
    embed = discord.Embed(title="Good to know information", color=discord.Color.dark_orange())
    embed.add_field(
        name="Rarities", 
        value="1. :yellow_square: is a gold rarity puff (the highest rarity available)\u200b\n2. :purple_square: is a purple rarity puff that is the second rarest puff to get\u200b\n3. Finally a :blue_square: is a blue rarity puff that is the most common type to get\nPlease check the /chances function to see what they corrolate to", 
        inline=False
    )
    embed.add_field(
        name="How is information saved?",
        value="Information like\n* amount of rolls\n* pity\n* types of rolls\nare **NOT** server specifc (AKA Discord-wide)\n\nThis means that lets say you roll a puff in another server, this will affect your experience in this server", 
        inline=False
    )
    embed.add_field(
        name="Pity system",
        value="When you reach **100** pity, you will roll only a gold rarity puff (check /chances for what they are). Although, this is a weighted roll, so that means that the more common gold rarity puffs have a higher chance of being selected compared to the less common ones.\n-# By the way, your pity is only showed when you roll a gold rarity puff, it is not public in the /statistics function",
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN) # type: ignore

