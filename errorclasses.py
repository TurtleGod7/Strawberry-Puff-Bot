from discord import app_commands
from discord.ext import commands

class NotAdminError(commands.CheckFailure):
    """Raised when a user isn't an admin."""
    pass

class BannedPlayerError(app_commands.CheckFailure):
    """Raised when a user is banned. For the app_commands context"""
    pass

class BannedPlayerErrorCtx(commands.CheckFailure):
    """Raised when a user is banned. For the commands context"""
    pass
