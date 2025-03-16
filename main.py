from dis import disco
from os import getenv, path; from os import name as os_name
from random import choices
from sqlite3 import connect # If you want to change the format to JSON, go for it but I prefer SQLite3 due to how out of the box it is
from statistics import mean
from math import ceil, floor
from time import time, mktime
from datetime import datetime
from turtle import title
import pvp_module
import discord
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("DISCORD_TOKEN")
ADMIN_USERS = set(map(int,getenv("ADMIN_USERS", "").split(",")))

### Control variables
CHANGE_PROFILE = False
STOP_PING_ON_STARTUP = False
DEBUG = False
TABLE_CREATION = False
PITY_LIMIT = 200
GIT_USERNAME = "TurtleGod7"
GIT_REPO = "Strawberry-Puff-Bot"
BUTTON_PAGE_EXPIRY = 60
ITEMS_PER_PAGE = 5
SETTINGS_EXPIRY = 60
ASCENSION_MAX = 10
AVATAR_PATH = "assets\\puffs\\strawberry.png" if os_name == "nt" else "assets/puffs/strawberry.png" # This and banner to be used when setting it as a gif
BANNER_FILE = "banner_angel.gif"
BANNER_START = "3/2/2025"
BANNER_END = "4/1/2025"
RARITY_WEIGHTS = [.887, .083, .03]
LIMITED_WEIGHTS = [.8, .2]
STATUSES = [
    discord.Activity(type=discord.ActivityType.playing, name="with puffs", state="The puff is one of the cutest animals in the animal kingdom. They are known for how fluffy they are and make as great pillows"),
    discord.Activity(type=discord.ActivityType.watching, name="over the puff kingdom", state="There's lots of land that the king puff has to manage, if only he paid me to do it."),
    discord.Activity(type=discord.ActivityType.watching, name="for the next fairy puff", state="I heard that they're really rare, but I'm sure you'll get it soon"),
    discord.Activity(type=discord.ActivityType.watching, name="the puff kingdom grow", state="I'm sure that the puff kingdom will be the best kingdom in the world"),
    discord.Activity(type=discord.ActivityType.watching, name="you use `/help` when you need help", state="It's always there to help you whenever you're lost. Try going to a server with me in it to see what I can do"),
    discord.Activity(type=discord.ActivityType.competing, name="for max ascension puffs", state="I heard that the max ascension puff is rare to have. If only spamming this bot wasn't allowed, it would be even rarer"),
]
COOLDOWN_TIME = 30  # Cooldown in seconds

###

### Global Variables that DON'T need to be changed
weightsMultipier = {
    0 : RARITY_WEIGHTS[0],
    1 : RARITY_WEIGHTS[1],
    2 : RARITY_WEIGHTS[2]*LIMITED_WEIGHTS[0],
    3 : RARITY_WEIGHTS[2]*LIMITED_WEIGHTS[1],
    4 : LIMITED_WEIGHTS[0], # When pity hits 100
    5 : LIMITED_WEIGHTS[1], 
}
weightedColor = {
    -1: discord.Color.brand_red(),
    0: discord.Color.yellow(),
    1: discord.Color.brand_green(),
}
rareColors = {
        0 : discord.Color.blue(),
        1 : discord.Color.purple(),
        2 : discord.Color.gold(),
        3 : discord.Color.greyple()
    }
activity_task_running = False
puff_list = []
###
# Note: Discord will print information in embeds differently if it was a multi-line string compared to a normal string. Sorry about the readability issues :(

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# The `ToLowerConverter` class is a custom converter in Python that converts a string argument to
# lowercase.
class ToLowerConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if not isinstance(argument, str):
            raise commands.BadArgument("Argument must be a string")
        return argument.lower()

async def dm_ping(user_id: int, message: str):
    """
    The function `dm_ping` sends a direct message to a user with a specified message, handling
    exceptions for user not found or permission issues.
    
    :param user_id: The `user_id` parameter is an integer representing the unique identifier of the user
    to whom you want to send a direct message (DM)
    :type user_id: int
    :param message: The `message` parameter is a string that contains the message you want to send to
    the user via direct message
    :type message: str
    :return: If an error occurs while fetching the user or sending the direct message, the function will
    return without performing the DM action. If the user is not found (user is None), the function will 
    also return without sending the message.
    """
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

def unpack_rolled_info(rollInfo: str, returndictempty: bool=False):
    """
    The function `unpack_rolled_info` takes a string input containing key-value pairs separated by
    semicolons, extracts the keys and values, and returns a dictionary sorted by keys.
    
    :param rollInfo: The `rollInfo` parameter is a string that contains information about rolled items
    and their frequencies. Each item and its frequency are separated by an underscore, and each item is
    separated by a semicolon
    :type rollInfo: str
    :param returndictempty: The `returndictempty` parameter in the `unpack_rolled_info` function is a
    boolean parameter with a default value of `False`. If this parameter is set to `True`, the function
    will return an empty dictionary `{}` if the `rollInfo` input is `None`. This, defaults to False
    :type returndictempty: bool (optional)
    :return: The function `unpack_rolled_info` is returning a dictionary containing the frequency of
    each item in the input `rollInfo` string. The items in the dictionary are sorted alphabetically by
    key. If the `returndictempty` parameter is set to `True` and `rollInfo` is `None`, an empty
    dictionary is returned. If `rollInfo` is `None` without
    """
    if returndictempty and rollInfo is None:
        return {}
    if rollInfo is None:
        return
    
    frequency = {}
    split_by_puffs = rollInfo.split(";")
    for split in split_by_puffs:
        frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    return dict(sorted(frequency.items()))

def pack_rolled_info(frequency_dict: dict):
    """
    The function `pack_rolled_info` takes a dictionary `frequency_dict` as input and returns a string
    representation of the key-value pairs in the dictionary separated by semicolons.
    
    :param frequency_dict: The `frequency_dict` parameter is a dictionary that contains the frequency of
    rolled items. Each key in the dictionary represents an item, and the corresponding value represents
    the frequency of that item being rolled
    :type frequency_dict: dict
    :return: The function `pack_rolled_info` returns a string that contains key-value pairs from the
    input `frequency_dict` dictionary, separated by semicolons. Each key-value pair is formatted as
    `key_value`. If the input `frequency_dict` is `None`, the function returns `None`. If the resulting
    string is empty, the function also returns `None`.
    """
    if frequency_dict is None: 
        return None
    return ";".join([f"{k}_{v}" for k, v in frequency_dict.items()]) or None

@tasks.loop(seconds=1800)
async def update_status():
    """
    This Python function updates the bot's status every 30 minutes with a list of predefined statuses.
    """
    global activity_task_running
    activity_task_running = True
    
    current_status = STATUSES.pop(0)
    STATUSES.append(current_status)
    await bot.change_presence(activity=current_status)
    
    activity_task_running = False

def is_authorised_user():
    """
    The function `is_authorised_user` checks if the author of a context is in the list of admin users.
    :return: A check function is being returned that checks if the author of a command is in the list of
    ADMIN_USERS.
    """
    async def predicate(ctx):
        if ctx.author.id in ADMIN_USERS:
            return True
        return False
    return commands.check(predicate)

def flatten_list(nested_list):
    """
    The `flatten_list` function recursively flattens a nested list into a single flat list.
    
    :param nested_list: The `flatten_list` function takes a nested list as input and recursively
    flattens it into a single list. If the input list contains nested lists or tuples, it will flatten those as
    well
    :return: The function `flatten_list` returns a flattened version of the input nested list by
    recursively flattening any nested lists within it.
    """
    flat_list = []
    for item in nested_list:
        if isinstance(item, (list, tuple)):
            flat_list.extend(flatten_list(item))  # Recursively flatten nested lists
        else:
            flat_list.append(item)
    return flat_list

@bot.event
async def on_ready():
    """
    The function sets up database tables, checks for debug mode, updates bot status, and sends direct
    messages to users based on settings.
    """
    await bot.tree.sync()
    if update_status.is_running() is False:
        update_status.start()
    
    if DEBUG:
        print(f"Discord version: {discord.__version__}")
        print("Registered commands:")
        for command in bot.tree.get_commands():
            print(f" - {command.name}")
        print(f"DEBUG: Admin Users: {ADMIN_USERS}")
    
    conn = connect("assets\\database\\puffs.db") if os_name == "nt" else connect("assets/database/puffs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM puffs")
    global puff_list
    puff_list = flatten_list(cursor.fetchall())
    if DEBUG:
        print(f"List of puffs: {puff_list}")
    
    if TABLE_CREATION:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS puffs (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
            "name" TEXT NOT NULL UNIQUE,
            "description" TEXT NOT NULL,
            "imagepath"	TEXT NOT NULL UNIQUE,
            "weight" REAL,
            "isRare" NUMERIC NOT NULL DEFAULT 0,
            "stats"	TEXT DEFAULT NULL,
        )
        """)
        
        cursor.execute("PRAGMA journal_mode=WAL")
        
        conn.commit()
    cursor.close()
    conn.close()
    
    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()
    
    if TABLE_CREATION:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            "username"	INTEGER PRIMARY KEY NOT NULL UNIQUE,
            "rolls"	INTEGER DEFAULT 0,
            "limited"	INTEGER DEFAULT 0,
            "gold"	rolls INTEGER DEFAULT 0,
            "purple"	INTEGER DEFAULT 0,
            "rolledGolds"	TEXT DEFAULT NULL,
            "rolledNormals"	TEXT DEFAULT NULL,
            "avgPity"	REAL DEFAULT 0,
            "win"	INTEGER DEFAULT 0,
	        "loss"	INTEGER DEFAULT 0,
            "totalBattles"	INTEGER DEFAULT 0,
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pvp_lineup (
            "username"	INTEGER PRIMARY KEY NOT NULL UNIQUE,
            "lineup"	TEXT DEFAULT NULL,
        )
        """)
        
        cursor.execute("""
        CREATE TABLE "cooldowns" (
	        "username" INTEGER PRIMARY KEY NOT NULL UNIQUE,
	        "battle" INTEGER DEFAULT 0,
        )
        """)
        
        cursor.execute("PRAGMA journal_mode=WAL")
        
        conn.commit()
    
    PeopletoDM = []
    if not STOP_PING_ON_STARTUP:
        cursor.execute("SELECT username FROM settings WHERE DMonStartup = 1")
        PeopletoDM = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    for k in PeopletoDM:
        await dm_ping(k[0],"you have set your settings to ping you when I go online\n-# If you would like to change this setting please do `/settings` here or in any server with me in it.")
    
    if CHANGE_PROFILE:
        if not path.exists(AVATAR_PATH):
            print("avatar .gif isn't found")
        else:
            with open(AVATAR_PATH, "rb") as f:
                avatar_img = f.read()
                try:
                    await bot.user.edit(avatar=avatar_img) # type: ignore
                except Exception as e:
                    print(f'{e}')
    
        if not path.exists(f"assets\\profile\\{BANNER_FILE}" if os_name == "nt" else f"assets/profile/{BANNER_FILE}"):
            print("banner .gif isn't found")
        else:
            with open(f"assets\\profile\\{BANNER_FILE}" if os_name == "nt" else f"assets/profile/{BANNER_FILE}", "rb") as f:
                banner_img = f.read()
                try:
                    await bot.user.edit(banner=banner_img) # type: ignore
                except Exception as e:
                    print(f'{e}')
    
    print(f'Logged in as {bot.user}')    

@bot.tree.command(name="puffroll", description="Roll a random puff")
async def roll_a_puff(interaction: discord.Interaction):
    """
    This function rolls a random puff for a user in a Discord bot, handling rarity, statistics tracking,
    and generating an embed with the roll results.
    
    :param interaction: The `interaction` parameter in the code snippet represents the interaction
    object that contains information about the user's interaction with the bot. It includes details such
    as the user who triggered the interaction, the type of interaction (e.g., command invocation), and
    any options or data provided by the user
    :type interaction: discord.Interaction
    """
    await interaction.response.defer()
    # So Discord doesn't time out the interaction
    
    user_id = interaction.user.id
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT pity FROM pity WHERE username = ?", (user_id,))
    pityInfo = cursor.fetchone()

    if pityInfo is None:
        pity = 0
        cursor.execute("INSERT INTO pity (username) VALUES (?)", (user_id,))
        conn.commit()
    else:
        pity = pityInfo[0]
    
    cursor.close()
    conn.close()
    
    conn = connect("assets\\database\\puffs.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/puffs.db", check_same_thread=False)
    cursor = conn.cursor()
    
    if int(pity) < PITY_LIMIT:
        isRareval = choices([0,1,2], weights=RARITY_WEIGHTS, k=1)[0]
        if isRareval < 2:
            cursor.execute("SELECT id, weight FROM puffs WHERE isRare = ?", (isRareval,))
            data =  cursor.fetchall()
            items, weights = zip(*data) # Randomly selects a weighted role (id)
            selected_id = choices(items, weights=weights, k=1)[0]
            cursor.execute("SELECT name, description, imagepath, weight, isRare FROM puffs WHERE id = ?", (selected_id,))
            choice = cursor.fetchone() # Gets the full info from the id 
            
            cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = ?", (isRareval,))
            total_weight = cursor.fetchone()[0]
        else:
            isLimitedval = choices([2,3], weights=LIMITED_WEIGHTS, k=1)[0]
            cursor.execute("SELECT id, weight FROM puffs WHERE isRare = ?", (isLimitedval,))
            data =  cursor.fetchall()
            items, weights = zip(*data) # Randomly selects a weighted role (id)
            selected_id = choices(items, weights=weights, k=1)[0]
            cursor.execute("SELECT name, description, imagepath, weight, isRare FROM puffs WHERE id = ?", (selected_id,))
            choice = cursor.fetchone() # Gets the full info from the id 
            
            cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = ?", (isLimitedval,))
            total_weight = cursor.fetchone()[0]
            
            isRareval = isLimitedval
        cursor.close() # Gets info for the chance calculation
        conn.close()
    else:
        isLimitedval = choices([2,3], weights=LIMITED_WEIGHTS, k=1)[0]
        cursor.execute("SELECT id, weight FROM puffs WHERE isRare = ?", (isLimitedval,))
        data =  cursor.fetchall()
        items, weights = zip(*data) # Randomly selects a weighted role (id)
        selected_id = choices(items, weights=weights, k=1)[0]
        cursor.execute("SELECT name, description, imagepath, weight, isRare FROM puffs WHERE id = ?", (selected_id,))
        choice = cursor.fetchone() # Gets the full info from the id 
        
        cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = ?", (isLimitedval,))
        total_weight = cursor.fetchone()[0]
        
        isRareval = isLimitedval+2
        
        cursor.close()
        conn.close()
        
    name, description, image_path, weights, isRare = choice
    
    chance = round(round((weights/total_weight)*weightsMultipier.get(isRareval), 4)*100,2)
    
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT EXISTS(SELECT 1 FROM stats WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 0: 
        cursor.execute("INSERT INTO stats (username) VALUES (?)", (user_id,))
    
    cursor.execute("SELECT rolledGolds,rolledNormals FROM stats WHERE username = ?", (user_id,))
    rolledGolds, rolledNormals = cursor.fetchone()
    frequencyGold = unpack_rolled_info(rolledGolds)
    frequencyNormal = unpack_rolled_info(rolledNormals)

    
    if isRare >= 2:
        if frequencyGold is None: frequencyGold = {}
        ascension = frequencyGold.get(name, -1)
        if ascension < ASCENSION_MAX:
            frequencyGold[name] = ascension+1
        frequencyGold = dict(sorted(frequencyGold.items()))
    else:
        if frequencyNormal is None: frequencyNormal = {}
        ascension = frequencyNormal.get(name, -1)
        if ascension < ASCENSION_MAX:
            frequencyNormal[name] = ascension+1
        frequencyNormal = dict(sorted(frequencyNormal.items()))
    
    
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
        if avgPity == 0:
            cursor.execute("UPDATE stats SET avgPity = ? WHERE username = ?", (pity, user_id))
        else:
            cursor.execute("UPDATE stats SET avgPity = ? WHERE username = ?", (mean([avgPity,pity]), user_id))
    elif int(isRare) == 1:
        cursor.execute("UPDATE stats SET purple = purple + 1 WHERE username = ?", (user_id,))
        
    cursor.execute("UPDATE stats SET rolledGolds = ?, rolledNormals = ? WHERE username = ?", (pack_rolled_info(frequencyGold), pack_rolled_info(frequencyNormal), user_id))    
    cursor.execute("SELECT EXISTS (SELECT 1 FROM settings WHERE username = ?)", (user_id,))
    cursor.execute("INSERT OR IGNORE INTO settings (username) VALUES (?)", (user_id,)) 
    cursor.execute("SELECT PingonGold FROM settings WHERE username = ?", (user_id,))
    PingonGold = cursor.fetchone()[0]
    
    conn.commit()
    cursor.close()
    conn.close()
    
    numsuffix = {
        1 : "st",
        2 : "nd"
    }
    image_path = f"https://raw.githubusercontent.com/{GIT_USERNAME}/{GIT_REPO}/refs/heads/main/assets/puffs/{image_path}?=raw"
    
    embed = discord.Embed(title="Your Roll Results", color=rareColors.get(isRare))
    if isRare >= 2:
        ascension_text = "is your first time getting this puff!" if frequencyGold[name] == 0 else f"is your **{frequencyGold[name]}**{numsuffix.get(frequencyGold[name], 'th')} ascension"
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

@bot.tree.command(name="pity", description="What's my pity")
async def get_pity(interaction: discord.Interaction):
    """
    This Python function retrieves a user's pity value from a database and sends it as an embedded
    message in response to a Discord interaction.
    
    :param interaction: The `interaction` parameter in the code snippet represents the interaction
    between the user and the bot. It contains information about the user who triggered the command, the
    context of the interaction, and any data associated with the interaction. In this specific context,
    it is used to retrieve the user's ID to fetch
    :type interaction: discord.Interaction
    """
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT pity FROM pity WHERE username = ?", (interaction.user.id,))
    pity = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    embed = discord.Embed(title="Your pity", color=discord.Color.orange())
    embed.add_field(name=f"Your pity is {pity}", value="")
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="statistics", description="Get some info on your rolls")
async def statistics(interaction: discord.Interaction):
    """
    This Python function retrieves and displays statistics related to a user's rolls in a gacha game
    using Discord interactions.
    
    :param interaction: The `interaction` parameter in the `statistics` command function represents the
    interaction between the user and the bot. It contains information about the user who triggered the
    command, the context in which the command was triggered, and allows the bot to respond to the user
    :type interaction: discord.Interaction
    """
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    user_id = interaction.user.id
    
    cursor.execute("SELECT EXISTS (SELECT 1 FROM stats WHERE username = ?)", (user_id,))    
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stats (username) VALUES (?)", (user_id,))
        conn.commit()
    
    cursor.execute("SELECT rolls, limited, gold, purple, rolledGolds, avgPity, win, loss, totalBattles FROM stats WHERE username = ?", (user_id,))
    choice = cursor.fetchone()
    
    rolls,limited, gold, purple, rolledGolds, avgPity, wins, losses, battles = choice
    
    cursor.close()
    conn.close()
    
    if losses == 0: losses+=1 # In case of division by 0
    frequency = {}
    if None is not rolledGolds:
        split_by_puffs = rolledGolds.split(";")
        for split in split_by_puffs:
            frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    ascensions_description_string = ""
    for k, v in frequency.items():
        ascensions_description_string += f"* *{k}*  **{v}** {'time' if v == 1 else 'times'}\n"
    if ascensions_description_string == "":
        ascensions_description_string += "You're seeing this because you didn't roll any gold/limited rarity puffs :sob:"
    
    embed = discord.Embed(title="Your Puff Gacha statistics", color=discord.Color.blurple())
    embed.add_field(name="**Gacha Statistics**", value="")
    embed.add_field(name="Total Rolls", value=f"You've rolled **{rolls}** times!", inline=False)
    embed.add_field(name="Rare Rolls", value=f"You've also ~~pulled~~ rolled a limited rarity puff **{limited}** {'time' if limited == 1 else 'times'}, a gold rarity puff **{gold}** {'time' if gold == 1 else 'times'}, and a purple rarity puff **{purple}** {'time' if purple == 1 else 'times'}!", inline=False)
    embed.add_field(name="Average Pity", value=f"Your average pity to roll a gold/limited rarity puff is **{round(avgPity,2)}**", inline=False)
    embed.add_field(name="Ascensions", value=ascensions_description_string, inline=False)
    embed.add_field(name="**Battle Statistics**",value="")
    embed.add_field(name="Wins/Losses", value=f"You have battled {battles} times and have won {wins} and have lost {losses}", inline=False)
    embed.add_field(name="WLR (Win Loss Ratio)", value=f"Your WLR is {round(wins/losses, 2)}", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

# This class `DropRatesView` in Python implements a view for displaying drop rates of items with
# pagination controls in a Discord bot.
class DropRatesView(discord.ui.View):
    def __init__(self, items, total_weight0, total_weight1, total_weight2, total_weight3):
        super().__init__(timeout=BUTTON_PAGE_EXPIRY)  # Buttons expire after 60 seconds
        self.items = items
        self.total_weight0 = total_weight0
        self.total_weight1 = total_weight1
        self.total_weight2 = total_weight2
        self.total_weight3 = total_weight3
        self.page = 0
        self.items_per_page = ITEMS_PER_PAGE  # Adjust if needed

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
    """
    This Python function retrieves data from a SQLite database and calculates the chances for each
    category of puffs, then sends the information in an embed message.
    
    :param interaction: The `interaction` parameter in the code snippet represents the interaction with
    the user in a Discord context. In this case, it is used to handle the interaction triggered by the
    user invoking the `/chances` command. The interaction object contains information about the user,
    the command invoked, and other relevant details
    :type interaction: discord.Interaction
    """
    db_path = "assets\\database\\puffs.db" if os_name == "nt" else "assets/database/puffs.db"
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
    """
    The `suggestions` function in the Python code provides a command for users to suggest new ideas for
    the bot by directing them to a Google Form through an embedded message.
    
    :param interaction: The `interaction` parameter in the `suggestions` command represents the
    interaction that triggered the command. In this case, it is a Discord interaction, which allows the
    bot to respond to user input or commands in a Discord server
    :type interaction: discord.Interaction
    """
    embed = discord.Embed(title="Please direct your help here", color=discord.Color.fuchsia())
    embed.add_field(name="Please redirect your suggestions to this google form", value="*https://forms.gle/gce7woXR5i38fnXY7*")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="AHHHHH, I NEED HELP!!!!")
async def help(interaction: discord.Interaction):
    """
    The `help` function in this Python code provides a list of commands and their descriptions for
    assisting users with the bot's functionalities.
    
    :param interaction: The `interaction` parameter in the `help` command function represents the
    interaction between the user and the bot. It contains information about the user who triggered the
    command, the context of the interaction, and allows the bot to respond back to the user with
    messages or embeds
    :type interaction: discord.Interaction
    """
    embed = discord.Embed(title="Techsupport is on the way!", color=discord.Color.greyple())
    embed.add_field(
        name="/puffroll", 
        value="This is the major mechanic of this bot and this is how you set up your local account."
    )
    embed.add_field(
        name="/pity",
        value="See your pity, refer to /info if you don't know what pity is"
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
        value="Use this function to change any settings you want with the bot"
    )
    embed.add_field(
        name="/banner",
        value="Use this function to view the current limited banner that's running"
    )
    embed.add_field(
        name="/github",
        value="Use this function to view the github repository for this bot"
    )
    embed.add_field(
        name="/compare",
        value="Use this function to compare your statistics with another user"
    )
    embed.add_field(
        name="/lineup",
        value="Use this function to see your lineup and your owned puffs that's used for battle"
    )
    embed.add_field(
        name="/setup_lineup",
        value="Use this function to modify the order or change puffs in your lineup"
    )
    embed.add_field(
        name="/battle",
        value="Use this function to challenge other players"
    )
    embed.add_field(
        name="/preview",
        value="View any puff in the game and its stats"
    )
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="Just some good to know information")
async def information(interaction: discord.Interaction):
    """
    The `information` function provides helpful information about rarities, saving data, the gacha
    system, etc. in a Discord embed format.
    
    :param interaction: The `interaction` parameter in the `information` function represents the
    interaction between the user and the bot. It contains information about the user who triggered the
    command, the channel where the interaction occurred, and other relevant details needed to respond to
    the user's command effectively. In this case, it is specifically
    :type interaction: discord.Interaction
    """
    embed = discord.Embed(title="Good to know information", color=discord.Color.dark_orange())
    embed.add_field(
        name="Rarities", 
        value="1. <:gray_square:1342727158673707018> is a limited puff (highest rarity)\n2. :yellow_square: is a gold rarity puff which is the next highest\u200b\n3. :purple_square: is a purple rarity puff that is the third rarest puff to get\u200b\n4. Finally a :blue_square: is a blue rarity puff that is the most common type to get\nPlease check the `/chances` function to see what they correlate to.", 
        inline=False
    )
    embed.add_field(
        name="How is information saved?",
        value="Information like\n* amount of rolls\n* pity\n* types of rolls\nare **NOT** server specific (AKA Discord-wide)\n\nThis means that lets say you roll a puff in another server, this will affect your experience in this server.", 
        inline=False
    )
    embed.add_field(
        name="Gacha system",
        value=f"This system works by initially rolling for the rarity at weights of **{RARITY_WEIGHTS[2]*100}**%, **{RARITY_WEIGHTS[1]*100}**%, and **{RARITY_WEIGHTS[0]*100}**% from least common to common rarities. Then if you roll in the {RARITY_WEIGHTS[2]*100}%, there is another roll to decide if you will get a limited which is at **{LIMITED_WEIGHTS[1]*100}**%. After getting selected to your rarity rank, then each puffs individual weights will apply.",
        inline=False
    )
    embed.add_field(
        name="Pity system",
        value=f"When you reach **{PITY_LIMIT}** pity, you will roll only a gold/limited rarity puff (check `/chances` for what they are). Although, this is a weighted roll, so that means that the more common puffs have a higher chance of being selected compared to the less common ones.\n-# By the way, your pity is only showed when you roll a gold/limited rarity puff, it is not public in the `/statistics` function.",
        inline=False
    )
    embed.add_field(
        name="Ascensions",
        value=f"These work exactly like eidolons/constellations (if you play Honkai: Star Rail or Genshin Impact), but as you get more gold rarity, you can increase the ascension of the puff up to the max of **{ASCENSION_MAX}** ascension. These affect the stats of your puffs in battle against others. Please check `/statistics` for what you've ascended.",
        inline=False
    )
    embed.add_field(
        name="Comparison calculations",
        value="This works by comparing your rolls to another user, so you can see how lucky you are compared to them. This is done by comparing the amount of rolls, limited rarity puffs, gold rarity puffs, purple rarity puffs, the average pity, and ascensions.\nAlso, the embed color signifies if on average if you have better stats. It's calculated by having each value better as 1 and worse as -1. First it starts with the mean of each ascension together. that value is rounded to 1 or -1, whichever is closest to be averaged by mean with the other stats. (**less** is better for pity/rolls, everything else, **more**) is better\n-# Please check `/statistics` for what you've rolled.",
        inline=False
    )
    embed.add_field(
        name="Battle calculations",
        value="The battling continues for every puff until someone's lineup ends (This **doesn't** give the other side the win). It works by each removing the other puff's health and checking for a draw, then if the challenger won, then if the opponent won. The average number of wins is used to calculate the wins and losses. The color logic from the comparison function is also implemented here.",
        inline=False
    )
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

# The `SettingsView` class in Python represents a view for selecting and updating user settings with
# options to notify about bot startup and Gold/Limited Rarity puff rolls.
class SettingsView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=SETTINGS_EXPIRY)  # View expires after 60 seconds
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
        
        db_path = "assets\\database\\users.db" if os_name == "nt" else "assets/database/users.db"
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
    """
    The function sets up user settings in a database and sends a message with options to the user.
    
    :param interaction: The `interaction` parameter in your `settings` command function represents the
    interaction that triggered the command. It contains information about the user who interacted with
    the bot, the channel where the interaction occurred, and other relevant details. In this case, you
    are using it to retrieve the user's ID to
    :type interaction: discord.Interaction
    """
    user_id = interaction.user.id
    
    db_path = "assets\\database\\users.db" if os_name == "nt" else "assets/database/users.db"
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
    """
    This Python function displays the current limited puff banner with its start and end dates, time
    remaining, and the user who requested it.
    
    :param interaction: The `interaction` parameter in the `showBanner` function represents the
    interaction between the user and the bot. It contains information about the user who triggered the
    command, the context of the interaction, and allows the bot to respond back to the user with
    messages or embeds
    :type interaction: discord.Interaction
    """
    now  = int(time())
    start_time = int(mktime(datetime.strptime(BANNER_START, "%m/%d/%Y").timetuple()))
    end_time = int(mktime(datetime.strptime(BANNER_END, "%m/%d/%Y").timetuple()))
    delta_time = end_time - now
    delta_time = f"<t:{end_time}:R>" if delta_time > 0 else "Ended"
    
    embed = discord.Embed(title="Latest Banner", color=discord.Color.dark_theme())
    embed.set_image(url=f"https://raw.githubusercontent.com/{GIT_USERNAME}/{GIT_REPO}/refs/heads/main/assets/profile/{BANNER_FILE}?=raw")
    embed.add_field(name="Banner Dates", value=f"Start: <t:{start_time}:F>\nEnd: <t:{end_time}:F>\nTime till end: {delta_time}", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

@bot.command()
async def pring(ctx, *, arg):
    """
    The above Python function defines a command for a bot that sends a message with the input argument
    provided by the user.
    
    :param ctx: The `ctx` parameter in the code snippet represents the context in which the command is
    being invoked. It contains information about the message, the channel, the author, and other
    relevant details related to the command execution
    :param arg: The `arg` parameter in the `pring` command is a variable that represents the input
    provided by the user when the command is called. It is a string that can contain any text or
    characters that the user wants to send as a message
    """
    await ctx.send(arg)

@bot.tree.command(name="compare", description="Compare your rolls to other people!")
async def comparision(interaction: discord.Interaction, user: discord.Member):
    """
    This function compares the puff rolls and statistics of the user invoking the command with another
    specified user and displays the differences in a formatted embed message.
    
    :param interaction: The `interaction` parameter in the `compare` command function represents the
    interaction that triggered the command. It contains information about the user who triggered the
    command, the channel where the interaction occurred, and other relevant details related to the
    interaction. In this context, it is used to retrieve the user ID of
    :type interaction: discord.Interaction
    :param user: The `compare` command in your code is designed to compare the stats of the user who
    triggers the command with the stats of another user specified as the `user` parameter. The command
    retrieves the stats of both users from a database, calculates the differences in various stats such
    as rolls, average pity,
    :type user: discord.Member
    :return: The `compare` command is returning an embedded message that displays a comparison between
    the user who triggered the command and the target user specified in the command. The comparison
    includes information such as the difference in rolls, average pity, limited puffs, gold puffs, and
    purple puffs between the two users. Additionally, it provides a breakdown of specific puff types
    where one user has more or less than the
    """
    client_user_id = interaction.user.id
    target_user_id = user.id
    
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT rolls, limited, gold, purple, rolledGolds, avgPity FROM stats WHERE username = ?", (client_user_id,))
    clientChoice = cursor.fetchone()
    
    cursor.execute("SELECT rolls, limited, gold, purple, rolledGolds, avgPity FROM stats WHERE username = ?", (target_user_id,))
    targetChoice = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    try: clientRolls, clientLimited, clientGold, clientPurple, clientRolled, clientavgPity = clientChoice
    except:
        await interaction.response.send_message("Please use another function as your data account hasn't been created", ephemeral=True)
        return
    try: targetRolls, targetLimited, targetGold, targetPurple, targetRolled, targetavgPity = targetChoice
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
    avgListmean = mean(averageList)
    if avgListmean > 0:
        color = weightedColor.get(ceil(avgListmean))
    elif avgListmean < 0:
        color = weightedColor.get(floor(avgListmean))
    else:
        color = weightedColor.get(0)
    
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
    """
    This Python function sends the GitHub link for the bot to the user in a Discord interaction.
    
    :param interaction: The `interaction` parameter in the code snippet represents the interaction
    object that contains information about the user's interaction with the bot, such as the user who
    triggered the command, the channel where the interaction occurred, and any options or data provided
    by the user. In this specific context, it is used to
    :type interaction: discord.Interaction
    """
    embed = discord.Embed(title="Github", color=discord.Color.random())
    embed.add_field(name="Repository link for this instance of the bot",value=f"https://github.com/{GIT_USERNAME}/{GIT_REPO}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def skater(ctx, *, arg):
    """
    The function sends a message with the input argument followed by a skater emoji.
    
    :param ctx: ctx represents the context in which the command is being invoked. It contains
    information about the message, the channel, the author, and other relevant details that can be used
    to interact with the user or perform actions within the Discord server
    :param arg: The `arg` parameter in the `skater` command represents the input provided by the user
    when invoking the command. It can be any text or phrase that the user wants to send along with the
    command
    """
    await ctx.send(arg + " <:skater:1345246453911781437>")

# This class defines buttons for rearranging a lineup and selecting new puffs in a Discord UI.
class LineupSetupButtons(discord.ui.View):
    def __init__(self, timeout=SETTINGS_EXPIRY):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="🛠️ Rearrange Lineup", style=discord.ButtonStyle.primary)
    async def rearrange_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_lineups = pvp_module.get_lineup(interaction.user.id)
        await interaction.response.edit_message(view=RearrangeDropdown(user_lineups))
        # Trigger rearrange function

    @discord.ui.button(label="✨ Pick New Puffs", style=discord.ButtonStyle.success)
    async def select_puffs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_puffs = pvp_module.get_owned(interaction.user.id)
        await interaction.response.edit_message(view=PuffDropdown(user_puffs))
        # Trigger dropdown function

# The `PuffDropdown` class creates a dropdown menu for selecting puffs, with options based on a
# provided list, and handles the callback to save the selected puffs to a database.
class PuffDropdown(discord.ui.View):
    def __init__(self, puff_list: dict, timeout=SETTINGS_EXPIRY):
        super().__init__(timeout=timeout)
        self.puff_list = puff_list

        # Create dropdown directly in the View
        if not puff_list:
            options = [discord.SelectOption(label="No puffs available", value="none")]
            self.select = discord.ui.Select(
                placeholder="No puffs available",
                options=options,
                disabled=True
            )
        else:
            options = [
                discord.SelectOption(label=f"{puff} (Lvl {level})", value=puff) for puff, level in puff_list.items()
            ]
            self.select = discord.ui.Select(
                placeholder="Choose your puffs!",
                options=options,
                min_values=1,
                max_values=min(len(puff_list), 5)
            )

        self.select.callback = self.select_puffs_callback
        self.add_item(self.select)

    async def select_puffs_callback(self, interaction: discord.Interaction):
        if self.select.values[0] == "none":
            await interaction.response.send_message("You don't have any puffs to select.", ephemeral=True)
            return

        selected_puffs = self.select.values
        await interaction.response.send_message(f"✅ Selected Puffs: {', '.join(selected_puffs)}", ephemeral=True)
        pvp_module.save_lineup(selected_puffs, interaction.user.id)
        # Save the new lineup to the database

# The `RearrangeDropdown` class in Python creates a Discord UI dropdown for rearranging items in a
# lineup with interactive callbacks for selecting and moving items.
class RearrangeDropdown(discord.ui.View):
    def __init__(self, lineup: list, timeout=SETTINGS_EXPIRY):
        super().__init__(timeout=timeout)
        self.lineup = lineup

        # Ensure lineup has at least 1 puff, otherwise disable the dropdown
        disabled_item = discord.ui.Select(
            placeholder="No puffs available to rearrange",
            options=[discord.SelectOption(label="No puffs available", value="none")],
            disabled=True
        )
        if not lineup: self.add_item(item=disabled_item)
        else:
            # Dropdown for selecting the puff to move
            self.select = discord.ui.Select(
                placeholder="Select a puff to move",
                options=[discord.SelectOption(label=puff, value=str(i)) for i, puff in enumerate(lineup)]
            )
            self.select.callback = self.select_puff_callback
            self.add_item(self.select)

    async def select_puff_callback(self, interaction: discord.Interaction):
        if self.select.values[0] == "none":
            await interaction.response.send_message("You don't have any puffs to rearrange.", ephemeral=True)
            return

        selected_index = int(self.select.values[0])
        selected_puff = self.lineup[selected_index]

        # Ask where to move the puff
        positions = [discord.SelectOption(label=f"Position {i+1}", value=str(i)) for i in range(len(self.lineup))]
        position_select = discord.ui.Select(
            placeholder="Choose a new position",
            options=positions
        )

        # Create a new view for position selection
        position_view = discord.ui.View()
        position_view.add_item(position_select)

        # Edit the original message with the new dropdown
        await interaction.response.edit_message(content=f"🔄 Move **{selected_puff}** to a new position:", view=position_view)

        # Position selection callback
        async def position_callback(interaction: discord.Interaction):
            new_position = int(position_select.values[0])
            self.lineup.remove(selected_puff)
            self.lineup.insert(new_position, selected_puff)

            # Show updated lineup with rearrange button
            lineup_display = "\n".join([f"{i+1}. {puff}" for i, puff in enumerate(self.lineup)])
            rearrange_again_button = discord.ui.Button(label="🔁 Rearrange Again", style=discord.ButtonStyle.primary)

            async def rearrange_again_callback(interaction: discord.Interaction):
                await interaction.response.edit_message(content="🔁 Let’s rearrange again!", view=RearrangeDropdown(self.lineup))

            rearrange_again_button.callback = rearrange_again_callback

            button_view = discord.ui.View()
            button_view.add_item(rearrange_again_button)

            await interaction.response.edit_message(
                content=f"✅ **{selected_puff}** moved to position **{new_position+1}**!\n\n📌 Updated Lineup:\n{lineup_display}",
                view=button_view
            )

        position_select.callback = position_callback

@bot.tree.command(name="setup_lineup", description="Set or rearrange your lineup!")
async def setup_lineup(interaction: discord.Interaction):
    """
    This Python function sets up or rearranges a user's lineup by fetching their puffs from the database
    and displaying interactive dropdowns for lineup setup.
    
    :param interaction: The `interaction` parameter in your `setup_lineup` command represents the
    interaction that triggered the command. It contains information about the user who interacted with
    the command, the channel where the interaction occurred, and other relevant details. You can use
    this parameter to send responses back to the user, access
    :type interaction: discord.Interaction
    """
    view = LineupSetupButtons(timeout=SETTINGS_EXPIRY)
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="⏳ Lineup setup timed out!", view=self)
    await interaction.response.send_message("⚔️ Setup your lineup!", view=view, ephemeral=True)
    # Handle dropdown for selecting new puffs

@bot.tree.command(name="battle", description="Battle another user!")
async def battle_command(interaction: discord.Interaction, opponent: discord.Member):
    """
    The `battle_command` function in a Python Discord bot allows users to battle against each other
    using their saved lineups of Puff objects.
    
    :param interaction: The `interaction` parameter in the `battle_command` function represents the
    interaction between the user and the bot. It contains information about the user who triggered the
    command, the channel where the interaction occurred, and other relevant details needed to respond to
    the user's command effectively
    :type interaction: discord.Interaction
    :param opponent: The `opponent` parameter in the `battle_command` function refers to the Discord
    member (user) whom the user initiating the command wants to battle against. This parameter is used
    to retrieve the opponent's lineup of Puffs for the battle
    :type opponent: discord.Member
    :return: The `battle_command` function is returning the results of a battle between two users'
    lineups of Puff objects. The battle results are displayed in an embedded message that includes the
    competitors, their lineups, and the outcome of each battle between corresponding Puff objects in the
    lineups.
    """
    user_id = interaction.user.id
    opponent_id = opponent.id
    global COOLDOWN_TIME # Do not set any values = to this
    
    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()
    cursor.executemany("INSERT OR IGNORE INTO cooldowns (username) VALUES (?)", [(user_id,),(opponent_id,)]) 
    current_time = time()

    # Check if the user is on cooldown by querying the database
    cursor.execute("SELECT battle FROM cooldowns WHERE username = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        last_used = result[0]
        if current_time - last_used < COOLDOWN_TIME:
            remaining_time = COOLDOWN_TIME - (current_time - last_used)
            await interaction.response.send_message(f"You're on cooldown! Try again in {round(remaining_time, 1)} seconds.", ephemeral=True)
            conn.close()
            return

    # If user is not on cooldown, update their cooldown time
    cursor.execute("REPLACE INTO cooldowns (username, battle) VALUES (?, ?)", (user_id, current_time))
    
    conn.commit()
    cursor.close()
    conn.close()

    user_lineup = pvp_module.get_lineup(user_id)
    opponent_lineup = pvp_module.get_lineup(opponent_id)

    if not user_lineup or not opponent_lineup:
        await interaction.response.send_message("⚔️ Both users need a saved lineup!", ephemeral=True)
        return

    # Convert names to Puff objects
    user_puffs = pvp_module.get_puffs_for_battle(user_lineup, user_id)
    opponent_puffs = pvp_module.get_puffs_for_battle(opponent_lineup, opponent_id)

    results = []
    scores = []
    for u_puff, o_puff in zip(user_puffs, opponent_puffs):
        result_battle, score = pvp_module.battle(u_puff, o_puff)
        results.append(result_battle)
        scores.append(score)
    overall_score = int(round(mean(scores),0))
    color = weightedColor.get(overall_score)
    winner = interaction.user.display_name
    if overall_score < 0: 
        winner = opponent.display_name
    elif overall_score == 0:
        winner = ""
    
    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()
    
    cursor.execute("UPDATE stats SET totalBattles = totalBattles + 1 WHERE username = ?", (user_id,))
    cursor.execute("UPDATE stats SET totalBattles = totalBattles + 1 WHERE username = ?", (opponent_id,))
    if overall_score > 0:
        cursor.execute("UPDATE stats SET win = win + 1 WHERE username = ?", (user_id,))
        cursor.execute("UPDATE stats SET loss = loss + 1 WHERE username = ?", (opponent_id,))
    elif overall_score < 0:
        cursor.execute("UPDATE stats SET win = win + 1 WHERE username = ?", (opponent_id,))
        cursor.execute("UPDATE stats SET loss = loss + 1 WHERE username = ?", (opponent_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    result_message = "\n".join(results)
    embed = discord.Embed(title=f"Puff Battle Results - {winner if winner != "" else "**⚔️ DRAW**"}", description=result_message, color=color)
    embed.add_field(name="Competitors", value=f"<@{interaction.user.id}> vs <@{opponent.id}>", inline=False)
    embed.add_field(name="Your Lineup", value=", ".join(user_lineup), inline=True)
    embed.add_field(name="Opponent's Lineup", value=", ".join(opponent_lineup), inline=True)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="lineup", description="Show your lineup")
async def get_lineup(interaction: discord.Interaction, visible: bool=False):
    """
    This Python function retrieves a user's owned puffs and lineup from a database, formats the data
    into an embed message, and sends it as a response to a Discord interaction.
    
    :param interaction: The `interaction` parameter in the `get_lineup` function represents the
    interaction that triggered the command. It contains information about the user who triggered the
    command, the channel where the interaction occurred, and other relevant details needed to respond to
    the interaction
    :type interaction: discord.Interaction
    :param visible: The `visible` parameter in the `get_lineup` function is a boolean parameter that
    determines whether the lineup information should be visible to all users or only visible to the user
    who requested it. If `visible` is set to `True`, the lineup information will be visible to all
    users, and, defaults to False
    :type visible: bool (optional)
    """
    user_id = interaction.user.id
    owned_puffs = pvp_module.get_owned(user_id)
    puff_stats = []
    lineup_puffs = pvp_module.get_lineup(user_id)
    conn = connect("assets\\database\\puffs.db") if os_name == "nt" else connect("assets/database/puffs.db")
    cursor = conn.cursor()
    for puff in owned_puffs.keys():
        cursor.execute("SELECT stats FROM puffs WHERE name = ?", (puff,))
        puff_stats.append(cursor.fetchone()[0].split(";"))
    cursor.close()
    conn.close()
    puff_names = list(owned_puffs.keys())
    ownedPuffsmessage = "\n".join(f"* {puff} (Lvl {level})\n    * Attack: {puff_stats[puff_names.index(puff)][0]} Health: {puff_stats[puff_names.index(puff)][1]}" for puff, level in owned_puffs.items())
    embed = discord.Embed(title="Your lineup", color=discord.Color.blue())
    embed.add_field(name="Owned Puffs", value=ownedPuffsmessage)
    embed.add_field(name="Puffs in your lineup", value="\n".join(f"{i+1}. **{puff}**" for i,puff in enumerate(lineup_puffs)))
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=not visible)

async def item_autocomplete(interaction: discord.Interaction, current: str):
    """
    The function `item_autocomplete` suggests items that match what the user types based on a list of
    items called `puff_list`.
    
    :param interaction: The `interaction` parameter in the `item_autocomplete` function represents the
    interaction that triggered the autocomplete request. This interaction contains information about the
    user, the command that was invoked, and any data associated with the interaction. It allows you to
    interact with the user and respond accordingly based on their input
    :type interaction: discord.Interaction
    :param current: The `current` parameter in the `item_autocomplete` function represents the current
    input or text that the user has typed so far. This input is used to filter and suggest items that
    match what the user is typing
    :type current: str
    :return: The function `item_autocomplete` returns a list of `discord.app_commands.Choice` objects
    that match the user input `current`. These choices are generated based on the items in the
    `puff_list` that contain the user input (case-insensitive match). The choices are created by
    splitting the items in `puff_list` by spaces and joining them with underscores.
    """
    if DEBUG:
        print(f"info being entered for autocomplete {current}")
        print(f"First few puffs in puff_list {puff_list[:5]}")
    choices= [
        discord.app_commands.Choice(name=puff, value="_".join(puff.split(" ")))
        for puff in puff_list
        if current.lower() in puff.lower()]
    if DEBUG:
        for choice in choices:
            print(f"Choice: name='{choice.name}', value='{choice.value}'")
    return choices

@bot.tree.command(name="preview", description="Preview a puff")
@discord.app_commands.describe(puff="A puff to preview")
@discord.app_commands.autocomplete(puff=item_autocomplete)
async def preview(interaction: discord.Interaction, puff: str):
    """
    This Python function previews a puff by fetching its data from a database and creating an embed with
    relevant information and an image.
    
    :param interaction: The `interaction` parameter in the code snippet represents the interaction
    between the user and the bot. It contains information about the user's input, the command invoked,
    and other relevant details needed to process and respond to the user's request effectively
    :type interaction: discord.Interaction
    :param puff: The `puff` parameter in the code snippet represents the name of a puff that the user
    wants to preview. The code fetches information about the specified puff from a database and
    generates an embed with details such as description, rarity, and stats of the puff. The embed also
    includes an image of
    :type puff: str
    """
    puff = " ".join(puff.split("_"))
    conn = connect("assets\\database\\puffs.db") if os_name == "nt" else connect("assets/database/puffs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT description, imagepath, isRare, stats FROM puffs WHERE name = ?", (puff,))
    puff_data = cursor.fetchone()
    cursor.close()
    conn.close()
    description, imagepath, isRare, stats = puff_data
    embed = discord.Embed(title=f"Previewing {puff}", color=rareColors.get(isRare))
    embed.add_field(name="Info", value=f"{puff}\nIt is {description}")
    embed.add_field(name="Rarity", value=f"{'Limited' if isRare >= 2 else 'Gold' if isRare == 2 else 'Purple' if isRare == 1 else 'Blue'}", inline=False)
    embed.add_field(name="Stats", value=f"Health: {stats.split(";")[1]}\nAttack: {stats.split(";")[0]}")
    embed.set_image(url=f"https://raw.githubusercontent.com/{GIT_USERNAME}/{GIT_REPO}/refs/heads/main/assets/puffs/{imagepath}?=raw")
    await interaction.response.send_message(embed=embed)

### All the functions below this comment are for the developer/bot admin users only ###

@bot.command()
@is_authorised_user()
async def get(ctx, *, arg: ToLowerConverter):
    """
    This function retrieves information about a specific item or character and displays it in an
    embedded message, including details like name, description, rarity, and image.
    
    :param ctx: The `ctx` parameter in the code snippet represents the context in which a command is
    being invoked. It contains information about the message, the channel, the author of the message,
    and other relevant details needed to process the command effectively
    :param arg: The `arg` parameter in the code snippet represents the input argument provided by the
    user when invoking the `get` command. This argument is passed as a string and is converted to
    lowercase using the `ToLowerConverter`
    :type arg: ToLowerConverter
    :return: The code snippet provided is a Discord bot command function that retrieves information
    about a specific item or banner based on the input argument.
    """
    if len(str(arg).split("_")) > 1:
        embed = discord.Embed(title="Latest Banner", color=discord.Color.dark_theme())
        embed.set_image(url=f"https://raw.githubusercontent.com/{GIT_USERNAME}/{GIT_REPO}/refs/heads/main/assets/profile/{str(arg)+'.gif'}?=raw")
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)
        return

    file = str(arg) + ".png"
    conn = connect("assets\\database\\puffs.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/puffs.db", check_same_thread=False)
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
    image_path = f"https://raw.githubusercontent.com/{GIT_USERNAME}/{GIT_REPO}/refs/heads/main/assets/puffs/{file}?=raw"
    
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
    embed.set_footer(text=f"Requested by Developer: {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@bot.command()
@is_authorised_user()
async def activity_change(ctx):
    """
    This Python function checks if an activity task is already running, restarts it if not, and sends a
    message indicating the status change.
    
    :param ctx: ctx stands for Context, which represents the context in which a command is being
    invoked. It contains information about the message, the channel, the author of the message, and
    more. In Discord.py, it is used to interact with the Discord API and send responses back to the user
    :return: If the `activity_task_running` flag is `True`, the bot will send a message saying "Activity
    task is running right now, please try again" and then return without restarting the activity task.
    """
    global activity_task_running
    
    if activity_task_running:
        await ctx.send("Activity task is running right now, please try again", ephemeral=True)
        return
    
    update_status.restart()
    await ctx.send("Activity task has been changed", ephemeral=True)

@bot.command()
@is_authorised_user()
async def statsof(ctx, arg: discord.User):
    """
    This function retrieves and displays statistics related to a user's activity in a puff gacha game.
    
    :param ctx: ctx represents the context in which a command is being invoked. It provides information
    about the message, the channel, the author, and more. In this case, it is used to send a response
    back to the user who triggered the command
    :param arg: The `arg` parameter in the code snippet represents a Discord user object that is passed
    as an argument when the command is invoked. This parameter is used to fetch the statistics of the
    specified user from the database and display them in an embedded message
    :type arg: discord.User
    """
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    
    cursor = conn.cursor()
    
    user_id = arg.id
    
    cursor.execute("SELECT EXISTS (SELECT 1 FROM stats WHERE username = ?)", (user_id,))    
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stats (username) VALUES (?)", (user_id,))
        conn.commit()
    
    cursor.execute("SELECT rolls, limited, gold, purple, rolledGolds, avgPity FROM stats WHERE username = ?", (user_id,))
    choice = cursor.fetchone()
    
    rolls,limited, gold, purple, rolledGolds, avgPity = choice
    
    cursor.close()
    conn.close()
    
    frequency = {}
    if None is not rolledGolds:
        split_by_puffs = rolledGolds.split(";")
        for split in split_by_puffs:
            frequency[split.split("_")[0]] = int(split.split("_")[1])
    
    ascensions_description_string = ""
    for k, v in frequency.items():
        ascensions_description_string += f"* *{k}*  **{v}** {'time' if v == 1 else 'times'}\n"
    if ascensions_description_string == "":
        ascensions_description_string += "You're seeing this because they didn't roll any gold/limited rarity puffs :sob:"
    
    embed = discord.Embed(title=f"{arg.display_name.capitalize()} Puff Gacha statistics", color=discord.Color.blurple())
    embed.add_field(name="Total Rolls", value=f"They've rolled **{rolls}** times!", inline=False)
    embed.add_field(name="Rare Rolls", value=f"They've also ~~pulled~~ rolled a limited rarity puff **{limited}** {'time' if limited == 1 else 'times'}, a gold rarity puff **{gold}** {'time' if gold == 1 else 'times'}, and a purple rarity puff **{purple}** {'time' if purple == 1 else 'times'}!", inline=False)
    embed.add_field(name="Average Pity", value=f"Their average pity to roll a gold/limited rarity puff is **{round(avgPity,2)}**", inline=False)
    embed.add_field(name="Ascensions", value=ascensions_description_string, inline=False)
    embed.set_footer(text=f"Requested by Developer: {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@bot.command()
@is_authorised_user()
async def createacct(ctx, table, arg: discord.User):
    """
    This Python function creates an account for a specified user in a specified table within a database,
    checking if the account already exists before insertion.
    
    :param ctx: The `ctx` parameter in the `createacct` command function represents the context in which
    the command was invoked. It contains information about the message, the channel, the author of the
    message, and other relevant details needed to process and respond to the command effectively
    :param table: The `table` parameter in the `createacct` command represents the name of the table in
    the database where the user account information will be stored. When the command is executed, a new
    entry will be added to this table with the user's ID as the username
    :param arg: The `arg` parameter in the `createacct` command is expecting a Discord user object as
    input. This user object will be used to create an account for the specified user in the specified
    table in the database
    :type arg: discord.User
    """
    user_id = arg.id
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"SELECT EXISTS(SELECT 1 FROM {table} WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 0:
        cursor.execute(f"INSERT INTO {table} (username) VALUES (?)", (user_id,))
        conn.commit()
        await ctx.send(f"Account created for {arg.display_name} in {table}")
    cursor.close()
    conn.close()

@bot.command()
@is_authorised_user()
async def deleteacct(ctx, table, arg: discord.User):
    """
    This Python function deletes a user account from a specified table in a database based on the user's
    ID.
    
    :param ctx: The `ctx` parameter in the `deleteacct` command function represents the context in which
    the command was invoked. It contains information about the message, the channel, the author of the
    message, and more. This context is essential for interacting with the Discord API and sending
    responses back to the user who
    :param table: The `table` parameter in the `deleteacct` command represents the name of the table
    from which you want to delete the account. It is a required parameter that specifies the table in
    the database where the user account information is stored. When calling this command, you need to
    provide the name of the
    :param arg: The `arg` parameter in the `deleteacct` command is expecting a Discord user object as
    input. This user object will be used to identify the account to be deleted from the specified table
    in the database
    :type arg: discord.User
    """
    user_id = arg.id
    conn = connect("assets\\database\\users.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"SELECT EXISTS(SELECT 1 FROM {table} WHERE username = ?)", (user_id,))
    if cursor.fetchone()[0] == 1:
        cursor.execute(f"DELETE FROM {table} (username) VALUES (?)", (user_id,))
        conn.commit()
        await ctx.send(f"Account deleted for {arg.display_name} in {table}")
    cursor.close()
    conn.close()

@bot.command()
@is_authorised_user()
async def getdata(ctx, *, arg:ToLowerConverter):
    """
    This Python function retrieves data from a SQLite database based on a given argument, constructs an
    embed with the retrieved information, and sends it as a message in a Discord channel.
    
    :param ctx: The `ctx` parameter in the code snippet represents the context in which a command is
    being invoked. It contains information about the message, the channel, the author, and other
    relevant details needed to process the command within a Discord bot
    :param arg: The `arg` parameter in the `getdata` command is used to specify the name of the image
    file (without the extension) that corresponds to the data you want to retrieve. This parameter is
    passed as an argument to the command and is converted to lowercase using the `ToLowerConverter`
    :type arg: ToLowerConverter
    """
    file = str(arg) + ".png"
    conn = connect("assets\\database\\puffs.db", check_same_thread=False) if os_name == "nt" else connect("assets/database/puffs.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, isRare, stats FROM puffs WHERE imagepath = ?", (file,))
    name, description, isRare, stats = cursor.fetchone()
    cursor.execute("SELECT SUM(weight) FROM puffs WHERE isRare = ?", (isRare,))
    rarityWeight = cursor.fetchone()[0]
    cursor.close()
    conn.close()  
    
    image_path = f"https://raw.githubusercontent.com/{GIT_USERNAME}/{GIT_REPO}/refs/heads/main/assets/puffs/{file}?=raw"
    weightString = f"{rarityWeight*weightsMultipier.get(isRare)}%"
    if isRare >= 2:
        weightString += f" and {weightsMultipier.get(isRare+2)}%"
    
    embed = discord.Embed(title="Puff Info", color=discord.Color.darker_grey())
    embed.add_field(name="Name", value=name, inline=False)
    embed.add_field(name="Description", value=description, inline=False)
    embed.add_field(name="Rarity", value=f"{'Limited' if isRare >= 2 else 'Gold' if isRare == 2 else 'Purple' if isRare == 1 else 'Blue'}", inline=False)
    embed.add_field(name="Chance", value=weightString, inline=False)
    embed.add_field(name="Stats", value=f"Attacks: {stats.split(";")[0]} Health: {stats.split(';')[1]}", inline=False)
    embed.set_footer(text=f"Requested by Developer: {ctx.author.display_name}")
    embed.set_image(url=image_path)
    await ctx.send(embed=embed)

@bot.command()
@is_authorised_user()
async def devdocs(ctx):
    """
    This function sends a Discord embed message containing information about developer documentation and
    commands to authorized users.
    
    :param ctx: The `ctx` parameter in the code snippet represents the context in which the command is
    being invoked. It contains information about the message, the channel, the author of the message,
    and other relevant details needed to process the command within the Discord environment
    """
    embed = discord.Embed(title="Developer Docs", color=discord.Color.random())
    embed.add_field(name="How does this work?",value="Your Discord User ID just needs to be added to the enviornment and then you can use all of these commands! Also, these are NOT added to the bot tree", inline=False)
    embed.add_field(name="Commands", value="* `!get` gets any puff or banner by specifying its file name without the extension\n* `!createacct` creates an account for the user in the specified table\n* `!deleteacct` deletes an account for the user in the specified table\n* `!getdata` gets the data in the database of a puff by specifying its file name without the extension\n* `!activity_change` changes the activity of the bot to cycle in the statuses list\n* `!statsof` gets the statistics of a user", inline=False)
    embed.add_field(name="What if non-admins find this??", value="Don't worry as the command won't work for them. Also the bot prints their user ID and name to the console in case they spam it", inline=False)
    embed.set_footer(text=f"Requested by Developer: {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """
    This Python function prints a message when a user without the necessary permissions tries to use an
    admin command.
    
    :param ctx: The `ctx` parameter in the `on_command_error` event represents the context in which the
    command error occurred. It contains information about the message, the channel, the author of the
    command, and more
    :param error: The `error` parameter in the `on_command_error` event handler represents the error
    that occurred when a command raised an exception. In the provided code snippet, the event handler
    specifically checks if the error is an instance of `commands.CheckFailure`, which typically occurs
    when a command check fails (e.g
    """
    if isinstance(error, commands.CheckFailure):# Would only be for admin commands right now
        print(f"{ctx.author.display_name}({ctx.author.id}) tried to use an admin command")

# add pvp fucntion
bot.run(TOKEN) # type: ignore