# External Imports
# -

# Internal Imports
from imports.global_setup import *
from imports.actions import *
from imports.update import *

# Remove pycache folders
remove_pycache()

# Check if all important files exist
check_files(config)

# Check if updated is defined and true
if 'updated' in locals() and updated:
    restart()

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