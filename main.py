import os
from random import choices
from sqlite3 import connect # If you want to change the format to JSON, go for it but I prefer SQLite3 due to how out of the box it is
from statistics import mean
from math import ceil, floor
from time import time, mktime
from datetime import datetime
import discord
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_USERS = set(map(int,os.getenv("ADMIN_USERS", "").split(",")))

### Control variables
STOP_PING_ON_STARTUP = False
DEBUG = False
pity_limit = 200
git_username = "TurtleGod7"
git_repo = "Strawberry-Puff-Bot"
button_page_expiry = 60
items_per_page = 5
settings_expiry = 60
ascension_max = 10
avatar_path = "assets\\puffs\\strawberry.png" if os.name == "nt" else "assets/puffs/strawberry.png" # This and banner to be used when setting it as a gif
banner_file = "banner_angel.gif"
banner_start = "3/2/2025"
banner_end = "4/1/2025"
rarityWeights = [.887, .083, .03]
limitedWeights = [.8, .2]
statuses = [
    discord.Activity(type=discord.ActivityType.playing, name="with puffs", state="The puff is one of the cutest animals in the animal kingdom. They are known for how fluffy they are and make as great pillows"),
    discord.Activity(type=discord.ActivityType.watching, name="over the puff kingdom", state="There's lots of land that the king puff has to manage, if only he paid me to do it."),
    discord.Activity(type=discord.ActivityType.watching, name="for the next fairy puff", state="I heard that they're really rare, but I'm sure you'll get it soon"),
    discord.Activity(type=discord.ActivityType.watching, name="the puff kingdom grow", state="I'm sure that the puff kingdom will be the best kingdom in the world"),
    discord.Activity(type=discord.ActivityType.watching, name="you use `/help` when you need help", state="It's always there to help you whenever you're lost. Try going to a server with me in it to see what I can do"),
    discord.Activity(type=discord.ActivityType.competing, name="for max ascension puffs", state="I heard that the max ascension puff is rare to have. If only spamming this bot wasn't allowed, it would be even rarer"),
]
###

### Global Variables that DON'T need to be changed
weightsMultipier = {
    0 : rarityWeights[0],
    1 : rarityWeights[1],
    2 : rarityWeights[2]*limitedWeights[0],
    3 : rarityWeights[2]*limitedWeights[1],
    4 : limitedWeights[0], # When pity hits 100
    5 : limitedWeights[1], 
}
activity_task_running = False
###
# Note: Discord will print information in embeds differently if it was a multi-line string compared to a normal string. Sorry about the readability issues :(
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

class ToLowerConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if not isinstance(argument, str):
            raise commands.BadArgument("Argument must be a string")
        return argument.lower()

async def dm_ping(user_id: int, message: str):
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

def unpack_rolled_info(rollInfo: str, returndictempty=False):
    if returndictempty and rollInfo == None:
        return {}
    if rollInfo == None:
        return
    
    frequency = {}
    split_by_puffs = rollInfo.split(";")
    for split in split_by_puffs:
        frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    return dict(sorted(frequency.items()))

def pack_rolled_info(frequencyDict: dict):
    if frequencyDict is None: return None
    return ";".join([f"{k}_{v}" for k, v in frequencyDict.items()]) or None

@tasks.loop(seconds=1800)
async def update_status():
    global activity_task_running
    activity_task_running = True
    
    current_status = statuses.pop(0)
    statuses.append(current_status)
    await bot.change_presence(activity=current_status)
    
    activity_task_running = False

def is_authorised_user():
    async def predicate(ctx):
        if ctx.author.id in ADMIN_USERS:
            return True
        return False
    return commands.check(predicate)

@bot.event
async def on_ready():
    await bot.tree.sync()
    update_status.start()
    
    if DEBUG:
        print("Registered commands:")
        for command in bot.tree.get_commands():
            print(f" - {command.name}")
        
        print(f"DEBUG: Admin Users: {ADMIN_USERS}")
    
    ''' Remove this when you want to run it (it makes the bot slower when I already have the data)
    conn = connect("assets\\database\\puffs.db") if os.name == "nt" else connect("assets/database/puffs.db")
    
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS puffs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        imagepath TEXT NOT NULL UNIQUE,
        weight REAL,
        isRare NUMERIC NOT NULL DEFAULT 0
    )
    """)
    
    cursor.execute("PRAGMA journal_mode=WAL")
    
    conn.commit()
    cursor.close()
    conn.close()
    '''
    conn = connect("assets\\database\\users.db") if os.name == "nt" else connect("assets/database/users.db")
    
    cursor = conn.cursor()
    ''' Same here
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        "username" INTEGER PRIMARY KEY NOT NULL UNIQUE,
        "rolls" INTEGER DEFAULT 0,
        "limited" INTEGER DEFAULT 0,
        "gold" rolls INTEGER DEFAULT 0,
        "purple" INTEGER DEFAULT 0,
        "rolledGolds" TEXT,
        "avgPity" REAL DEFAULT 0
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
    '''
    PeopletoDM = []
    if not STOP_PING_ON_STARTUP:
        cursor.execute("SELECT username FROM settings WHERE DMonStartup = 1")
        PeopletoDM = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for k in PeopletoDM:
        await dm_ping(k[0],"you have set your settings to ping you when I go online\n-# If you would like to change this setting please do `/settings` here or in any server with me in it.")
    
    if not os.path.exists(avatar_path):
        print("avatar .gif isn't found")
    else:
        with open(avatar_path, "rb") as f:
            avatar_img = f.read()
            try:
                await bot.user.edit(avatar=avatar_img) # type: ignore
            except Exception as e:
                print(f'{e}')
    
    if not os.path.exists(f"assets\\profile\\{banner_file}" if os.name == "nt" else f"assets/profile/{banner_file}"):
        print("banner .gif isn't found")
    else:
        with open(f"assets\\profile\\{banner_file}" if os.name == "nt" else f"assets/profile/{banner_file}", "rb") as f:
            banner_img = f.read()
            try:
                await bot.user.edit(banner=banner_img) # type: ignore
            except Exception as e:
                print(f'{e}')
    
    print(f'Logged in as {bot.user}')    

@bot.tree.command(name="puffroll", description="Roll a random puff")
async def Roll_a_puff(interaction: discord.Interaction):
    await interaction.response.defer()
    # So Discord doesn't time out the interaction
    
    user_id = interaction.user.id

    conn = connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else connect("assets/database/users.db", check_same_thread=False)

    cursor = conn.cursor()
    
    cursor.execute("SELECT pity FROM pity WHERE username = ?", (user_id,))
    pityInfo = cursor.fetchone()

    if pityInfo is None:
        pity = 0
        cursor.execute("INSERT INTO pity (username, pity) VALUES (?, ?)", (user_id, 0))
        conn.commit()
    else:
        pity = pityInfo[0]
    
    cursor.close()
    conn.close()
    
    conn = connect("assets\\database\\puffs.db", check_same_thread=False) if os.name == "nt" else connect("assets/database/puffs.db", check_same_thread=False)

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
        
        cursor.execute("SELECT SUM(CAST(weight AS REAL)) FROM puffs WHERE isRare = ?", (isLimitedval,))
        total_weight = cursor.fetchone()[0]
        
        isRareval = isLimitedval+2
        
        cursor.close()
        conn.close()
        
    item_id, name, description, image_path, weights, isRare = choice
    
    chance = round(round((weights/total_weight)*weightsMultipier.get(isRareval), 4)*100,2)
    
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT EXISTS(SELECT 1 FROM stats WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 0: 
        cursor.execute("INSERT INTO stats (username, rolls, limited, gold, purple, rolledGolds, avgPity) VALUES (?,?,?,?,?,?,?)", (user_id, 0, 0, 0, 0,None,0))
    
    cursor.execute("SELECT rolledGolds FROM stats WHERE username = ?", (user_id,))
    rolledGolds = cursor.fetchone()[0]
    frequency = unpack_rolled_info(rolledGolds)
    
    if isRare >= 2:
        if frequency == None: frequency = {}
        ascension = frequency.get(name, -1)
        if ascension < ascension_max:
            frequency[name] = ascension+1
        frequency = dict(sorted(frequency.items()))
    
    
    
    cursor.execute("UPDATE stats SET rolls = rolls + 1 WHERE username = ?", (user_id,))
    cursor.execute("UPDATE pity SET pity = pity + 1 WHERE username = ?", (user_id,))

    if int(isRare) >= 2:
        cursor.execute("UPDATE pity SET pity = 0 WHERE username = ?", (user_id,))

        if int(isRare) > 2:
            cursor.execute("UPDATE stats SET limited = limited + 1 WHERE username = ?", (user_id,))
        else:
            cursor.execute("UPDATE stats SET gold = gold + 1 WHERE username = ?", (user_id,))
        
        cursor.execute("SELECT avgPity FROM stats WHERE username = ?", (user_id,))
        avgPity = cursor.fetchone()[0]
        cursor.execute("UPDATE stats SET avgPity = ? WHERE username = ?", (mean([avgPity,pity]), user_id))
    
    if int(isRare) == 1:
        cursor.execute("UPDATE stats SET purple = purple + 1 WHERE username = ?", (user_id,))
        
    cursor.execute("UPDATE stats SET rolledGolds = ? WHERE username = ?", (pack_rolled_info(frequency), user_id))
    
    cursor.execute("SELECT EXISTS (SELECT 1 FROM settings WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (username, DMonStartup, PingonGold) VALUES (?, ?, ?)", (user_id, 0, 0)) 
    
    cursor.execute("SELECT PingonGold FROM settings WHERE username = ?", (user_id,))
    PingonGold = cursor.fetchone()[0]
    
    conn.commit()
    cursor.close()
    conn.close()
    
    rareColors = {
        0 : discord.Color.blue(),
        1 : discord.Color.purple(),
        2 : discord.Color.gold(),
        3 : discord.Color.greyple()
    }
    numsuffix = {
        1 : "st",
        2 : "nd"
    }
    image_path = f"https://raw.githubusercontent.com/{git_username}/{git_repo}/refs/heads/main/assets/puffs/{image_path}?=raw"
    
    embed = discord.Embed(title="Your Roll Results", color=rareColors.get(isRare))
    if isRare >= 2:
        ascension_text = "is your first time getting this puff!" if frequency[name] == 0 else f"is your **{frequency[name]}**{numsuffix.get(frequency[name], 'th')} ascension"
        embed.add_field(
            name=":strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry:",
            value=f"You got a **{name}**.\nIt is {description}\nIt was a **{chance}%** chance to roll this puff!\nYou rolled this puff at **{pity}** pity.\nThis {ascension_text}"
        )
        if PingonGold is not None and PingonGold == 1:
            await dm_ping(user_id,"you rolled a gold rarity puff! :yellow_square:\n-# If you would like to change this setting please do `/settings` here or in any server with me in it.\n" if isRare == 2 else "you rolled a limited rarity puff! <:gray_square:1342727158673707018>\n-# If you would like to change this setting please do `/settings` here or in any server with me in it.\n")
    else:
        embed.add_field(
            name=":strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry:",
            value=f"You got a **{name}**.\nIt is {description}\nIt was a **{chance}%** chance to roll this puff!\n"
        )
    embed.set_image(url=image_path)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="statistics", description="Get some info on your rolls")
async def statistics(interaction: discord.Interaction):
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    user_id = interaction.user.id
    
    cursor.execute("SELECT EXISTS (SELECT 1 FROM stats WHERE username = ?)", (user_id,))    
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stats (username, rolls, limited, gold, purple, rolledGolds, avgPity) VALUES (?, ?, ?, ?, ?, ?)", (user_id, 0, 0, 0, 0, None, 0))
        conn.commit()
    
    cursor.execute("SELECT * FROM stats WHERE username = ?", (user_id,))
    choice = cursor.fetchone()
    
    username, rolls,limited, gold, purple, rolledGolds, avgPity = choice
    
    cursor.close()
    conn.close()
    
    frequency = {}
    if None != rolledGolds:
        split_by_puffs = rolledGolds.split(";")
        for split in split_by_puffs:
            frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    ascensions_description_string = ""
    for k, v in frequency.items():
        ascensions_description_string += f"* *{k}*  **{v}** {'time' if v == 1 else 'times'}\n"
    if ascensions_description_string == "":
        ascensions_description_string += "You're seeing this because you didn't roll any gold/limited rarity puffs :sob:"
    
    embed = discord.Embed(title="Your Puff Gacha statistics", color=discord.Color.blurple())
    embed.add_field(name="Total Rolls", value=f"You've rolled **{rolls}** times!", inline=False)
    embed.add_field(name="Rare Rolls", value=f"You've also ~~pulled~~ rolled a limited rarity puff **{limited}** {'time' if limited == 1 else 'times'}, a gold rarity puff **{gold}** {'time' if gold == 1 else 'times'}, and a purple rarity puff **{purple}** {'time' if purple == 1 else 'times'}!", inline=False)
    embed.add_field(name="Average Pity", value=f"Your average pity to roll a gold/limited rarity puff is **{round(avgPity,2)}**", inline=False)
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
async def drop_rates(interaction: discord.Interaction):
    db_path = "assets\\database\\puffs.db" if os.name == "nt" else "assets/database/puffs.db"
    conn = connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 0")
    total_weight0 = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 1")
    total_weight1 = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 2")
    total_weight2 = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = 3")
    total_weight3 = cursor.fetchone()[0]

    cursor.execute("SELECT name, weight, isRare FROM puffs WHERE weight > 0 ORDER BY weight ASC")
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    view = DropRatesView(items, total_weight0, total_weight1, total_weight2, total_weight3)
    await interaction.response.send_message(embed=view.generate_embed(), view=view)

@bot.tree.command(name="suggestions", description="Suggest new ideas for our bot!")
async def suggestions(interaction: discord.Interaction):
    embed = discord.Embed(title="Please direct your help here", color=discord.Color.fuchsia())
    embed.add_field(name="Please redirect your suggestions to this google form", value="*https://forms.gle/gce7woXR5i38fnXY7*")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="AHHHHH, I NEED HELP!!!!")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Techsupport is on the way!", color=discord.Color.greyple())
    embed.add_field(
        name="/puffroll", 
        value="This is the major mechanic of this bot and this is how you set up your local account."
    )
    embed.add_field(
        name="/statistics", 
        value="This is the statistics function so you can understand more about your luck."
    )
    embed.add_field(
        name="/chances", 
        value="This is the chances function that displays information for each puff."
    )
    embed.add_field(
        name="/suggestions", 
        value="Use this function to give us any suggestions"
    )
    embed.add_field(
        name="/info", 
        value="Function that provides valuable details and information about how this bot works"
    )
    embed.add_field(
        name="/settings", 
        value="Use this function to change any settings you want with the bot", 
        inline=False
    )
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
        value=f"This system works by initially rolling for the rarity at weights of **{rarityWeights[2]*100}**%, **{rarityWeights[1]*100}**%, and **{rarityWeights[0]*100}**% from least common to common rarities. Then if you roll in the {rarityWeights[2]*100}%, there is another roll to decide if you will get a limited which is at **{limitedWeights[1]*100}**%. After getting selected to your rarity rank, then each puffs individual weights will apply.",
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
            discord.SelectOption(label="Notify you when the bot turns on", value="0", description="Enable or disable bot startup notifications."),
            discord.SelectOption(label="Notify you when you roll a Gold/Limited Rarity puff", value="1", description="Extremely useful when spamming")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        value = int(select.values[0])
        
        db_path = "assets\\database\\users.db" if os.name == "nt" else "assets/database/users.db"
        conn = connect(db_path, check_same_thread=False)
        cursor = conn.cursor()

        settingsDict = {
            0: "DMonStartup",
            1: "PingonGold",
        }
        
        cursor.execute(f"SELECT {settingsDict.get(value)} FROM settings WHERE username = ?", (self.user_id,))
        current_value = cursor.fetchone()[0]

        new_value = current_value ^ 1

        cursor.execute(f"UPDATE settings SET {settingsDict.get(value)} = ? WHERE username = ?", (new_value, self.user_id))
        
        conn.commit()
        cursor.close()
        conn.close()

        await interaction.response.send_message(f"Your setting has been updated to {'Enabled' if new_value else 'Disabled'}.", ephemeral=True)

    async def on_timeout(self):
        self.stop()

@bot.tree.command(name="settings", description="Just set up your settings")
async def settings(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    db_path = "assets\\database\\users.db" if os.name == "nt" else "assets/database/users.db"
    conn = connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT EXISTS (SELECT 1 FROM settings WHERE username = ?)", (user_id,))    
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (username, DMonStartup, PingonGold) VALUES (?,?)", (user_id, 0, 0))
        conn.commit()
    
    cursor.close()
    conn.close()

    await interaction.response.send_message("Choose an option below:", view=SettingsView(user_id), ephemeral=True)

@bot.tree.command(name="banner", description="Show the current limited puff banner")
async def showBanner(interaction: discord.Interaction):
    now  = int(time())
    start_time = int(mktime(datetime.strptime(banner_start, "%m/%d/%Y").timetuple()))
    end_time = int(mktime(datetime.strptime(banner_end, "%m/%d/%Y").timetuple()))
    delta_time = end_time - now
    delta_time = f"<t:{end_time}:R>" if delta_time > 0 else "Ended"
    
    embed = discord.Embed(title="Latest Banner", color=discord.Color.dark_theme())
    embed.set_image(url=f"https://raw.githubusercontent.com/{git_username}/{git_repo}/refs/heads/main/assets/profile/{banner_file}?=raw")
    embed.add_field(name="Banner Dates", value=f"Start: <t:{start_time}:F>\nEnd: <t:{end_time}:F>\nTime till end: {delta_time}", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

@bot.command()
async def pring(ctx, *, arg):
    await ctx.send(arg)

@bot.tree.command(name="compare", description="Compare your rolls to other people!")
async def comparision(interaction: discord.Interaction, user: discord.Member):
    client_user_id = interaction.user.id
    target_user_id = user.id
    
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os.name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM stats WHERE username = ?", (client_user_id,))
    clientChoice = cursor.fetchone()
    
    cursor.execute("SELECT * FROM stats WHERE username = ?", (target_user_id,))
    targetChoice = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    try: clientUsername, clientRolls, clientLimited, clientGold, clientPurple, clientRolled, clientavgPity = clientChoice
    except:
        await interaction.response.send_message("Please use another function as your data account hasn't been created", ephemeral=True)
        return
    try: targetUsername, targetRolls, targetLimited, targetGold, targetPurple, targetRolled, targetavgPity = targetChoice
    except:
        await interaction.response.send_message("Please ask the person you are comparing to to use another function as their data account hasn't been created", ephemeral=True)
        return
    
    # unpacking information
    clientFrequency = unpack_rolled_info(clientRolled, True)
    targetFrequency = unpack_rolled_info(targetRolled, True)
    
    diffRolls = targetRolls-clientRolls# Doing differences calculations
    diffPity = targetavgPity-clientavgPity
    diffLimited = clientLimited-targetLimited
    diffGold = clientGold-targetGold
    diffPurple = clientPurple-targetPurple
    diffPuffs = []# Same formatting as saving info to db
    common_keys = set(clientFrequency) & set(targetFrequency)
    client_dif_keys = set(clientFrequency) - common_keys
    target_dif_keys = set(targetFrequency) - common_keys

    diffPuffs.extend(f"{key}_{clientFrequency[key] - targetFrequency[key]}" for key in sorted(common_keys))
    diffPuffs.extend(f"{key}_{clientFrequency[key]+1}" for key in sorted(client_dif_keys))
    diffPuffs.extend(f"{key}_{targetFrequency[key]-1}" for key in sorted(target_dif_keys))
        
    averageList = []
    varList = [diffPity, diffRolls, diffLimited, diffGold, diffPurple]
    for i in range(len(varList)):
        if varList[i] >= 0:
            averageList.append(1)
        else:
            averageList.append(-1)
    try: averageList.append(1 if mean([1 if int(v.split("_")[1]) > 0 else -1 for v in diffPuffs]) > 0 else -1)
    except: averageList.append(0)
    #Gets average better or worse to get embed color
    averageListColor = {
        -1: discord.Color.brand_red(),#
        0: discord.Color.yellow(),#
        1: discord.Color.brand_green(),#
    }
    avgListmean = mean(averageList)
    if avgListmean > 0:
        color = averageListColor.get(ceil(avgListmean))
    elif avgListmean < 0:
        color = averageListColor.get(floor(avgListmean))
    else:
        color = averageListColor.get(0)
    
    diffPuffsdict = {}
    for val in diffPuffs:
        diffPuffsdict[val.split("_")[0]] = int(val.split("_")[1])
    
    embed = discord.Embed(title=f"Puff Comparison with {await bot.fetch_user(target_user_id)}", color=color)
    embed.add_field(name="Rolls", value=f"You have {abs(diffRolls)} {'more' if diffRolls < 0 else 'less'} rolls than them", inline=False)
    embed.add_field(name="Average Pity", value=f"Your average pity is {round(abs(diffPity),2)} {'more' if diffPity < 0 else 'less'} than them", inline=False)
    embed.add_field(name="Limiteds", value=f"You have {abs(diffLimited)} {'more' if diffLimited > 0 else 'less'} limited puffs than them", inline=False)
    embed.add_field(name="Golds", value=f"You have {abs(diffGold)} {'more' if diffGold > 0 else 'less'} gold puffs than them", inline=False)
    embed.add_field(name="Purples", value=f"You have {abs(diffPurple)} {'more' if diffPurple > 0 else 'less'} purple puffs than them", inline=False)
    embed.add_field(name="More Gold/Limited Info", value = "\n".join(f"* You have {v} more {k}s than them" if v >= 0 else f"* You have {abs(v)} less {k}s than them" for k, v in diffPuffsdict.items()), inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="github", description="Get the GitHub link for this bot")
async def github(interaction: discord.Interaction):
    embed = discord.Embed(title="Github", color=discord.Color.random())
    embed.add_field(name="Repository link for this instance of the bot",value=f"https://github.com/{git_username}/{git_repo}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def skater(ctx, *, arg):
    await ctx.send(arg + " <:skater:1345246453911781437>")

@bot.command()
@is_authorised_user()
async def get(ctx, *, arg: ToLowerConverter):
    if len(str(arg).split("_")) > 1:
        embed = discord.Embed(title="Latest Banner", color=discord.Color.dark_theme())
        embed.set_image(url=f"https://raw.githubusercontent.com/{git_username}/{git_repo}/refs/heads/main/assets/profile/{str(arg)+'.gif'}?=raw")
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)
        return

    file = str(arg) + ".png"
    conn = connect("assets\\database\\puffs.db", check_same_thread=False) if os.name == "nt" else connect("assets/database/puffs.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, isRare FROM puffs WHERE imagepath = ?", (file,))
    name, description, isRare = cursor.fetchone()
    cursor.close()
    conn.close()
    
    rareColors = {
        0 : discord.Color.blue(),
        1 : discord.Color.purple(),
        2 : discord.Color.gold(),
        3 : discord.Color.greyple()
    }
    chance = 100
    pity = None
    image_path = f"https://raw.githubusercontent.com/{git_username}/{git_repo}/refs/heads/main/assets/puffs/{file}?=raw"
    
    embed = discord.Embed(title="Your Roll Results", color=rareColors.get(isRare))
    if isRare >= 2:
        embed.add_field(
            name=":strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry:",
            value=f"You got a **{name}**.\nIt is {description}\nIt was a **{chance}%** chance to roll this puff!\nYou rolled this puff at **{pity}** pity.\nThis is your Noneth ascension"
        )
    else:
        embed.add_field(
            name=":strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry::turtle::strawberry:",
            value=f"You got a **{name}**.\nIt is {description}\nIt was a **{chance}%** chance to roll this puff!\n"
        )
    embed.set_image(url=image_path)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@bot.command()
@is_authorised_user()
async def activity_change(ctx):
    global activity_task_running
    
    if activity_task_running:
        await ctx.send("Activity task is running right now, please try again", ephemeral=True)
        return
    
    update_status.restart()
    await ctx.send("Activity task has been changed", ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):# Would only be for admin commands right now
        print(f"{ctx.author.display_name}({ctx.author.id}) tried to use an admin command")

# add pvp fucntion
bot.run(TOKEN) # type: ignore

