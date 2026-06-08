from pathlib import Path
from discord import Activity, ActivityType
import helpers.daemons as daemons


### Control variables
BANNED_HANDLER = daemons.BannedUsersHandler()
PRINT_EXTRA_ERROR_MESSAGES = False
CHANGE_PROFILE = False
STOP_PING_ON_STARTUP = True
DEBUG = False
TABLE_CREATION = False
SLEEP_PREVENTION = False
PITY_LIMIT = 200
GIT_USERNAME = "TurtleGod7"
GIT_REPO = "Strawberry-Puff-Bot"
BUTTON_PAGE_EXPIRY = 60
ITEMS_PER_PAGE = 5
SETTINGS_EXPIRY = 60
SHOP_EXPIRY = 15
ASCENSION_MAX = 10
AVATAR_PATH = str(Path("assets/puffs/sakura.png")) # This and banner to be used when setting it as a gif
BANNER_FILE = "banner_luna-khan.png"
BANNER_NAME = BANNER_FILE.split('_')[1].split('.')[0].replace('-', ' ').capitalize() + " Puff"  # Extract name from banner file
BANNER_START = "6/3/2026"
BANNER_END = "7/1/2026"
IMAGE_PATH = f"https://raw.githubusercontent.com/{GIT_USERNAME}/{GIT_REPO}/refs/heads/main/src/assets/"
RARITY_WEIGHTS = [.887, .083, .03]
LIMITED_WEIGHTS = [.9, .1]
STATUSES = [
    Activity(
        type=ActivityType.playing,
        name="with puffs",
        state="The puff is one of the cutest animals in the animal kingdom. They are known for how fluffy they are and make as great pillows"
    ),
    Activity(
        type=ActivityType.watching,
        name="over the puff kingdom",
        state="There's lots of land that the king puff has to manage, if only he paid me to do it."
    ),
    Activity(
        type=ActivityType.watching,
        name="for the next fairy puff",
        state="I heard that they're really rare, but I'm sure you'll get it soon"
    ),
    Activity(
        type=ActivityType.watching,
        name="the puff kingdom grow",
        state="I'm sure that the puff kingdom will be the best kingdom in the world"
    ),
    Activity(
        type=ActivityType.watching,
        name="you use `/help` when you need help",
        state="It's always there to help you whenever you're lost. Try going to a server with me in it to see what I can do"
    ),
    Activity(
        type=ActivityType.competing,
        name="for max ascension puffs",
        state="I heard that the max ascension puff is rare to have. If only spamming this bot wasn't allowed, it would be even rarer"
    ),
    Activity(
        type=ActivityType.custom,
        name=f"The new banner is for the {BANNER_NAME.lower()}",
        state="Make sure to check the new banner out before it ends!",
    )
]
PUFFROLL_COST = 3
PUFFROLL_COOLDOWN_TIME = 0  # Cooldown in seconds
BATTLE_COOLDOWN_TIME = 30  # Cooldown in seconds
MONEY_FROM_WIN = 5
RUBIES_FROM_WIN = 3
MAX_QUESTS = 3
QUEST_CHALLENGES = [
    {"index": 0, "description": "Win [placeholder] battle(s)", "reward": 4, "placeholder": 1},
    {"index": 1, "description": "Use the shop", "reward": 2},
    {"index": 2, "description": "Daily Check-In", "reward": 1},
    {"index": 3, "description": "Spend [placeholder] clouds", "reward": 2, "placeholder": 5}
]
QUEST_CHECK_FUNCTIONS = [
    lambda user, task: user.battle_won >= int(task[3]),
    lambda user, task: user.shop_open > 0,
    lambda user, task: __import__('datetime').datetime.fromtimestamp(user.checkinTime).date() == __import__('datetime').datetime.now().date(),
    lambda user, task: user.clouds_spent >= int(task[3]),
]
QUEST_PROGRESS_FUNCTIONS = [
    lambda user, task: f"{user.battle_won}/{int(task[3])} battles won",
    lambda user, task: f"{user.shop_open} times opened",
    lambda user, task: "Checked in today" if __import__('datetime').datetime.fromtimestamp(user.checkinTime).date() == __import__('datetime').datetime.now().date() else "Not checked in today",
    lambda user, task: f"{user.clouds_spent}/{int(task[3])} clouds spent"
]
DISABLE_PUFFROLL_COST_ADMIN = False
DISABLE_PUFFROLL_COST_EVERYONE = False
###