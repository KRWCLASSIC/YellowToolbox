# External Imports
from pathlib import Path
from tqdm import tqdm
import configparser
import requests
import hashlib
import zipfile
import shutil
import os

# Internal Imports
from imports.bot_instance import bot
from imports.actions import *
from imports.update import *

# Prompt user for update
update_input = input("Do you want to check for updates? [Y/n]: ").lower()

if update_input in ['y', 'yes']:
    update()
    exit

# Load the config file
config = configparser.ConfigParser()
config.read('config.ini')

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