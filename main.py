# External Imports
import configparser

# Internal Imports
from imports.bot_instance import bot
from imports.actions import *

# Load the config file
config = configparser.ConfigParser()
config.read('config.ini')

# Load token from file
with open(config['settings']['token'], 'r') as file:
    TOKEN = file.read().strip()

# Actions imported from file
bot.event(on_member_update)
bot.event(on_reaction_add)
bot.event(on_member_join)
bot.event(on_message)
bot.event(on_ready)

# Run the bot
bot.run(TOKEN)