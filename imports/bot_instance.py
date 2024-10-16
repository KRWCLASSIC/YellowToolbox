# External Imports
import discord
from discord.ext import commands

# Enable some permissions
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.members = True
intents.guilds = True

# Version Variable
ver = '1.7'

# Register the bot
bot = commands.Bot(command_prefix="", intents=intents)