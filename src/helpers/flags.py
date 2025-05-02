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
PITY_LIMIT = 200
GIT_USERNAME = "TurtleGod7"
GIT_REPO = "Strawberry-Puff-Bot"
BUTTON_PAGE_EXPIRY = 60
ITEMS_PER_PAGE = 5
SETTINGS_EXPIRY = 60
ASCENSION_MAX = 10
AVATAR_PATH = str(Path("assets/puffs/sleepy.png")) # This and banner to be used when setting it as a gif
BANNER_FILE = "banner_tank.gif"
BANNER_NAME = BANNER_FILE.split('_')[1].split('.')[0].capitalize() + " Puff"  # Extract name from banner file
BANNER_START = "5/2/2025"
BANNER_END = "6/1/2025"
IMAGE_PATH = f"https://raw.githubusercontent.com/{GIT_USERNAME}/{GIT_REPO}/refs/heads/main/src/assets/"
RARITY_WEIGHTS = [.887, .083, .03]
LIMITED_WEIGHTS = [.8, .2]
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
COOLDOWN_TIME = 30  # Cooldown in seconds
MONEY_FROM_WIN = 5
###