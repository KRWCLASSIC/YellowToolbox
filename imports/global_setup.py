# External Imports
from discord.ext import commands
import discord
import toml

# Internal Imports
from imports.update import *

# Version Variable
ver = 'pre-2.1'

# Enable some permissions
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.members = True
intents.guilds = True

# Register the bot variable
bot = commands.Bot(command_prefix="", intents=intents, sync_commands=True)

# Load the config file
config = toml.load('files/installation/config.toml')

# Load autoupdate variable
update_input = str(config['settings']['autoupdate'])

# Prompt user for update
if update_input == '':
    update_input = input("Do you want to check for updates? [Y/n]: ").lower()
if update_input in ['y', 'yes']:
    update()
    updated = True