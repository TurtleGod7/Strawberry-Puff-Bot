from cProfile import label
import os
from tkinter.tix import Select
import discord
from discord.ext import commands
from dotenv import load_dotenv
from random import choices
import sqlite3

from pyparsing import col
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

### Control variables
pity_limit = 200
git_username = "TurtleGod7"
git_repo = "Strawberry-Puff-Bot"
button_page_expiry = 60
items_per_page = 5
settings_expiry = 60
ascension_max = 10
avatar_path = "assets\\puffs\\strawberry.png" if os.name == "nt" else "assets/avatar.gif" # This and banner to be used when setting it as a gif
banner_path = "assets\\profile\\banner.gif" if os.name == "nt" else "assets/profile/banner.gif"
rarityWeights = [.887, .083, .003]
limitedWeights = [.9, .1]
weightsMultipier = {
        0 : rarityWeights[0],
        1 : rarityWeights[1],
        2 : rarityWeights[2]*limitedWeights[0],
        3 : rarityWeights[2]*limitedWeights[1],
        4 : limitedWeights[0], # When pity hits 100
        5 : limitedWeights[1], 
}
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

async def dm_ping(user_id: int, message: str) -> None:
    try:
        user = await bot.fetch_user(user_id)
    except Exception as e:
        print(e)
        return
    
    if user is None:
        return
    
    try:
        await user.send(f"<@{user_id}>, {message}", allowed_mentions=discord.AllowedMentions(users=True))
    except discord.Forbidden:
        print(f"Can't DM {user}; {user_id}")
    except discord.HTTPException as e:
        print(f'Error sending DM as {e}')

@bot.event
async def on_ready() -> None:
    await bot.tree.sync()
    
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
    
    conn.commit()
    cursor.close()
    conn.close()
    
    conn = sqlite3.connect("assets\\database\\users.db") if os.name == "nt" else sqlite3.connect("assets/database/users.db")
    
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        "username" INTEGER PRIMARY KEY NOT NULL UNIQUE,
        "rolls" INTEGER DEFAULT 0,
        "limited" INTEGER DEFAULT 0,
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
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        "username" INTEGER PRIMARY KEY NOT NULL UNIQUE,
        "DMonStartup" INTEGER NOT NULL DEFAULT 0
    )               
    """)
    
    cursor.execute("PRAGMA journal_mode=WAL")
    
    conn.commit()
    
    cursor.execute("SELECT username FROM settings WHERE DMonStartup = 1")
    PeopletoDM = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for k in PeopletoDM:
        await dm_ping(k[0],"you have set your settings to ping you when Strawberry Puff Bot goes online\n-# If you would like to change this setting please do `/settings` here or in any server with me in it.")
    
    if not os.path.exists(avatar_path):
        print("avatar .gif isn't found")
    else:
        with open(avatar_path, "rb") as f:
            avatar_img = f.read()
            await bot.user.edit(avatar=avatar_img) # type: ignore
    
    if not os.path.exists(banner_path):
        print("banner .gif isn't found")
    else:
        with open(banner_path, "rb") as f:
            banner_img = f.read()
            await bot.user.edit(banner=banner_img) # type: ignore
        
    
    print(f'Logged in as {bot.user}')    

@bot.tree.command(name="puffroll", description="Roll a random puff")
async def Roll_a_puff(interaction: discord.Interaction) -> None:
    user_id = interaction.user.id

    conn = sqlite3.connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else sqlite3.connect("assets/database/users.db", check_same_thread=False)

    cursor = conn.cursor()
    
    cursor.execute("SELECT pity FROM pity WHERE username = ?", (user_id,))
    pityInfo = cursor.fetchone()

    if pityInfo is None:  # If user is not in the database
        pity = 0
        cursor.execute("INSERT INTO pity (username, pity) VALUES (?, ?)", (user_id, 0))
        conn.commit()
    else:
        pity = pityInfo[0]  # Extract pity value
    
    cursor.close()
    conn.close()
    
    conn = sqlite3.connect("assets\\database\\puffs.db", check_same_thread=False) if os.name == "nt" else sqlite3.connect("assets/database/puffs.db", check_same_thread=False)

    cursor = conn.cursor()
    
    if int(pity) < pity_limit:
        isRareval = choices([0,1,2], weights=rarityWeights, k=1)[0]
        if isRareval < 2:
            cursor.execute("SELECT id, weight FROM puffs WHERE isRare = ?", (isRareval,))
            data =  cursor.fetchall()
            items, weights = zip(*data) # Randomly selects a weighted role (id)
            selected_id = choices(items, weights=weights, k=1)[0]
            cursor.execute("SELECT * FROM puffs WHERE id = ?", (selected_id,))
            choice = cursor.fetchone() # Gets the full info from the id 
            
            cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = ?", (isRareval,))
            total_weight = cursor.fetchone()[0]
        else:
            isLimitedval = choices([2,3], weights=limitedWeights, k=1)[0]
            cursor.execute("SELECT id, weight FROM puffs WHERE isRare = ?", (isLimitedval,))
            data =  cursor.fetchall()
            items, weights = zip(*data) # Randomly selects a weighted role (id)
            selected_id = choices(items, weights=weights, k=1)[0]
            cursor.execute("SELECT * FROM puffs WHERE id = ?", (selected_id,))
            choice = cursor.fetchone() # Gets the full info from the id 
            
            cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = ?", (isLimitedval,))
            total_weight = cursor.fetchone()[0]
            
            isRareval = isLimitedval
        cursor.close() # Gets info for the chance calculation
        conn.close()
    else:
        isLimitedval = choices([2,3], weights=limitedWeights, k=1)[0]
        cursor.execute("SELECT id, weight FROM puffs WHERE isRare = ?", (isLimitedval,))
        data =  cursor.fetchall()
        items, weights = zip(*data) # Randomly selects a weighted role (id)
        selected_id = choices(items, weights=weights, k=1)[0]
        cursor.execute("SELECT * FROM puffs WHERE id = ?", (selected_id,))
        choice = cursor.fetchone() # Gets the full info from the id 
        
        cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = ?", (isLimitedval,))
        total_weight = cursor.fetchone()[0]
        
        isRareval = isLimitedval+2
        
        cursor.close()
        
        conn.close()
        
    item_id, name, description, image_path, weights, isRare = choice
    
    chance = round(round((weights/int(total_weight))*weightsMultipier.get(isRareval), 4)*100,2)
    
    conn = sqlite3.connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else sqlite3.connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT EXISTS(SELECT 1 FROM stats WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 0: 
        cursor.execute("INSERT INTO stats (username, rolls, limited, gold, purple, rolledGolds) VALUES (?,?,?,?,?,?)", (user_id, 0, 0, 0, 0,""))
    
    cursor.execute("SELECT rolledGolds FROM stats WHERE username = ?", (user_id,))
    rolledGolds = cursor.fetchone()[0]
    frequency = {}
    if None != rolledGolds:
        split_by_puffs = rolledGolds.split(";")
        for split in split_by_puffs:
            frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    if isRare >= 2:
        ascension = frequency.get(name, -1)
        if ascension < ascension_max:
            frequency[name] = ascension+1
    
    frequency = dict(sorted(frequency.items()))
    
    cursor.execute("UPDATE stats SET rolls = rolls + 1 WHERE username = ?", (user_id,))
    
    if int(isRare) == 3:
        cursor.execute("UPDATE stats SET limited = limited + 1 WHERE username = ?", (user_id,))
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
        2 : discord.Color.gold(),
        3 : discord.Color.greyple()
    }
    
    image_path = f"https://raw.githubusercontent.com/{git_username}/{git_repo}/refs/heads/main/assets/puffs/{image_path}?=raw"
    
    embed = discord.Embed(title="Your Roll Results", color=rareColors.get(isRare))
    if isRare >= 2:
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
async def statistics(interaction: discord.Interaction) -> None:
    conn = sqlite3.connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else sqlite3.connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    user_id = interaction.user.id
    
    cursor.execute("SELECT * FROM stats WHERE username = ?", (user_id,))
    choice = cursor.fetchone()
    
    if choice is None:
        cursor.execute("INSERT INTO stats (username, rolls, limited, gold, purple, rolledGolds) VALUES (?, ?, ?, ?, ?)", (user_id, 0, 0, 0, 0,""))
        conn.commit()
    
    username, rolls,limited, gold, purple, rolledGolds = choice
    
    cursor.close()
    conn.close()
    
    frequency = {}
    if None != rolledGolds:
        split_by_puffs = rolledGolds.split(";")
        for split in split_by_puffs:
            frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    ascensions_description_string = ""
    for k, v in frequency.items():
        ascensions_description_string += f"* *{k}*  **{v}** {"time" if v == 1 else "times"}\n"
    if ascensions_description_string == "":
        ascensions_description_string += "You're seeing this because you didn't roll any gold/limited rarity puffs :sob:"
    
    embed = discord.Embed(title="Your Puff Gacha statistics", color=discord.Color.blurple())
    embed.add_field(name="Total Rolls", value=f"You've rolled **{rolls}** times!", inline=False)
    embed.add_field(name="Rare Rolls", value=f"You've also ~~pulled~~ rolled a limited rarity puff **{limited}** {"time" if limited == 1 else "times"}, a gold rarity puff **{gold}** {"time" if gold == 1 else "times"}, and a purple rarity puff **{purple}** {"time" if purple == 1 else "times"}!", inline=False)
    embed.add_field(name="Ascensions", value=ascensions_description_string, inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

class DropRatesView(discord.ui.View):
    def __init__(self, items, total_weight0, total_weight1, total_weight2, total_weight3):
        super().__init__(timeout=button_page_expiry)  # Buttons expire after 60 seconds
        self.items = items
        self.total_weight0 = total_weight0
        self.total_weight1 = total_weight1
        self.total_weight2 = total_weight2
        self.total_weight3 = total_weight3
        self.page = 0
        self.items_per_page = items_per_page  # Adjust if needed

    def generate_embed(self):
        isRaretoWeight = {0:self.total_weight0, 1:self.total_weight1, 2:self.total_weight2, 3:self.total_weight3,}
        
        embed = discord.Embed(title="📊 Puff Drop Rates", color=discord.Color.gold())
        
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        page_items = self.items[start:end]

        for name, weight, isRare in page_items:
            chance = round(round((weight / isRaretoWeight.get(isRare))*weightsMultipier.get(isRare), 4) * 100, 2)  # Convert to percentage
            if isRare == 3: embed.add_field(name=name+" <:gray_square:1342727158673707018>", value=f"{chance:.2f}%", inline=False)
            elif isRare == 2: embed.add_field(name=name+" :yellow_square:", value=f"{chance:.2f}%", inline=False)
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
async def drop_rates(interaction: discord.Interaction) -> None:
    db_path = "assets\\database\\puffs.db" if os.name == "nt" else "assets/database/puffs.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 0")
    total_weight0 = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 1")
    total_weight1 = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 2")
    total_weight2 = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 3")
    total_weight3 = cursor.fetchone()[0]

    cursor.execute("SELECT name, weight, isRare FROM puffs ORDER BY weight ASC")
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    view = DropRatesView(items, total_weight0, total_weight1, total_weight2, total_weight3)
    await interaction.response.send_message(embed=view.generate_embed(), view=view)

@bot.tree.command(name="suggestions", description="Suggest new ideas for our bot!")
async def stats(interaction: discord.Interaction) -> None:
    embed = discord.Embed(title="Please direct your help here", color=discord.Color.fuchsia())
    embed.add_field(name="Please redirect your suggestions to this google form", value="*https://forms.gle/gce7woXR5i38fnXY7*")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="AHHHHH, I NEED HELP!!!!")
async def help(interaction: discord.Interaction) -> None:
    embed = discord.Embed(title="Techsupport is on the way!", color=discord.Color.greyple())
    embed.add_field(name="/puffroll", value="This is the major mechanic of this bot and this is how you set up your local account.")
    embed.add_field(name="/statistics", value="This is the statistics function so you can understand more about your luck.")
    embed.add_field(name="/chances", value="This is the chances function that displays information for each puff.")
    embed.add_field(name="/suggestions", value="Use this function to give us any suggestions")
    embed.add_field(name="/info", value="Function that provides valuable details and information about how this bot works")
    embed.add_field(name="/settings", value="Use this function to change any settings you want with the bot", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="Just some good to know information")
async def information(interaction: discord.Interaction):
    embed = discord.Embed(title="Good to know information", color=discord.Color.dark_orange())
    embed.add_field(
        name="Rarities", 
        value="1. <:gray_square:1342727158673707018> is a limited puff (highest rarity)\n2. :yellow_square: is a gold rarity puff which is the next highest\u200b\n3. :purple_square: is a purple rarity puff that is the third rarest puff to get\u200b\n4. Finally a :blue_square: is a blue rarity puff that is the most common type to get\nPlease check the `/chances` function to see what they correlate to", 
        inline=False
    )
    embed.add_field(
        name="How is information saved?",
        value="Information like\n* amount of rolls\n* pity\n* types of rolls\nare **NOT** server specific (AKA Discord-wide)\n\nThis means that lets say you roll a puff in another server, this will affect your experience in this server", 
        inline=False
    )
    embed.add_field(
        name="Gacha system",
        value=f"This system works by initially rolling for the rarity at weights of 3%, 8.3%, and 88.7% from least common to common rarities. Then if you roll in the 3%, there is another roll to decide if you will get a limited which is at 10%. After getting selected to your rarity rank, then each puffs individual weights will apply.",
        inline=False
    )
    embed.add_field(
        name="Pity system",
        value=f"When you reach **{pity_limit}** pity, you will roll only a gold/limited rarity puff (check `/chances` for what they are). Although, this is a weighted roll, so that means that the more common puffs have a higher chance of being selected compared to the less common ones.\n-# By the way, your pity is only showed when you roll a gold/limited rarity puff, it is not public in the `/statistics` function",
        inline=False
    )
    embed.add_field(
        name="Ascensions",
        value=f"These work exactly like eidolons/constellations (if you play Honkai: Star Rail or Genshin Impact), but as you get more gold rarity, you can increase the ascension of the puff up to the max of **{ascension_max}** ascension. Please check `/statistics` for what you've ascended",
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

class SettingsView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=settings_expiry)  # View expires after 60 seconds
        self.user_id = user_id
    
    @discord.ui.select(
        placeholder="Choose a setting...",
        options=[
            discord.SelectOption(label="Notify you when the bot turns on", value="0", description="Enable or disable bot startup notifications.")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        value = int(select.values[0])
        
        db_path = "assets\\database\\users.db" if os.name == "nt" else "assets/database/users.db"
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()

        settingsDict = {
            0: "DMonStartup"
        }
        
        cursor.execute(f"SELECT {settingsDict.get(value)} FROM settings WHERE username = ?", (self.user_id,))
        current_value = cursor.fetchone()[0]

        new_value = current_value ^ 1

        cursor.execute(f"UPDATE settings SET {settingsDict.get(value)} = ? WHERE username = ?", (new_value, self.user_id))
        
        conn.commit()
        cursor.close()
        conn.close()

        await interaction.response.send_message(f"Your setting {settingsDict.get(value)} has been updated to {'Enabled' if new_value else 'Disabled'}.", ephemeral=True)

    async def on_timeout(self):
        self.stop()

@bot.tree.command(name="settings", description="Just set up your settings")
async def settings(interaction: discord.Interaction) -> None:
    user_id = interaction.user.id
    
    db_path = "assets\\database\\users.db" if os.name == "nt" else "assets/database/users.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT EXISTS (SELECT 1 FROM settings WHERE username = ?)", (user_id,))    
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (username, DMonStartup) VALUES (?,?)", (user_id, 0))
        conn.commit()
    
    cursor.close()
    conn.close()

    await interaction.response.send_message("Choose an option below:", view=SettingsView(user_id), ephemeral=True)

@bot.tree.command(name="banner", description="Show the current limited puff banner")
async def showBanner(interaction: discord.Interaction):
    embed = discord.Embed(title="Latest Banner", color=discord.Color.dark_theme())
    embed.set_image(url=f"https://raw.githubusercontent.com/{git_username}/{git_repo}/refs/heads/main/assets/profile/banner.gif?=raw")
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN) # type: ignore

