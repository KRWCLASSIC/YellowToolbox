# External Imports
import discord
from discord.ext import commands

# Enable some permissions
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Register the bot
bot = commands.Bot(command_prefix="", intents=intents)