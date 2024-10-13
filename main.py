# External Imports
import configparser

# Internal Imports
from imports.bot_instance import bot
from imports.actions import *
from imports.update import *

# Load the config file
config = configparser.ConfigParser()
config.read('config.ini')

# Check if all importnant files exist
check_files()

# Load autoupdate variable
update_input = str(config['settings']['autoupdate'])

# Prompt user for update
if update_input == '':
    update_input = input("Do you want to check for updates? [Y/n]: ").lower()
if update_input in ['y', 'yes']:
    update()

# Load token from file
with open(config['token']['token'], 'r') as file:
    TOKEN = file.read().strip()

# Actions imported from file
bot.event(on_member_update)
bot.event(on_reaction_add)
bot.event(on_member_join)
bot.event(on_message)
bot.event(on_ready)

# Run the bot
bot.run(TOKEN)