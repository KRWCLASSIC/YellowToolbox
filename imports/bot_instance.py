# External Imports
from discord.ext import commands
import discord
import toml

# Enable some permissions
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.members = True
intents.guilds = True

# Load the config file (global)
config = toml.load('files/installation/config.toml')

# Version Variable
ver = 'pre-1.8'

# Register the bot
bot = commands.Bot(command_prefix="", intents=intents)