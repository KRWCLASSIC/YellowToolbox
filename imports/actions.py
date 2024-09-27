# External Imports
import configparser
import discord
import re

# Internal Imports
from imports.functions import *
from imports.bot_instance import bot

# Load the config file
config = configparser.ConfigParser()
config.read('config.ini')

# Some variables and arrays
enable_nick_change = str(config['nicktrack']['enable_nick_change'])
nicktrack_enabled = str(config['nicktrack']['nicktrack_enabled'])
ADMIN_USER_ID = int(config['settings']['ADMIN_USER_ID'])
target_id = int(config['nicktrack']['target_id'])
no_gif = config['settings']['no_gif']
camera_clicks = {}

async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    for guild in bot.guilds:
        print(f'- {guild.name}')

async def on_member_join(member):
    return

async def on_reaction_add(reaction, user):
    if reaction.message.author == bot.user:
        return

    if str(reaction.emoji) == '📷':
        if reaction.message.id not in camera_clicks:
            camera_clicks[reaction.message.id] = user

        message = await reaction.message.channel.fetch_message(reaction.message.id)
        camera_reactions = count_camera_reactions(message)

        if camera_reactions >= 2:
            async for user in reaction.users():
                await message.remove_reaction('📷', user)

            await handle_gif_creation(message, camera_clicks[reaction.message.id])

async def on_member_update(before: discord.Member, after: discord.Member):
    # Check if the nickname has changed
    if nicktrack_enabled == 'True' and before.nick != after.nick and after.id == target_id:
        # Send a message to the channel when the user changes their nickname
        channel = after.guild.get_channel(1287007606870904914)
        if channel:
            await channel.send(f"<@{ADMIN_USER_ID}>, User {after.name} got their nickname changed from '{before.nick}' to '{after.nick}'")

    # Forced nickname change mechanism (only if enabled)
    if enable_nick_change == 'True' and after.id == target_id and after.nick != "frajer":
        await after.edit(nick="frajer")

async def on_message(message):
    BLOCKED_USER_IDS = get_blocked_user_ids()

    if message.author == bot.user:
        return

    if message.author.id in BLOCKED_USER_IDS:
        if bot.user in message.mentions:
            await message.reply("kys", file=discord.File(no_gif))
        return

    if bot.user in message.mentions and message.author != bot.user:
        content = message.content.lower()
        if re.search(r'\bgif\b', content):
            await handle_gif_command(message)
        elif re.search(r'\beveryone\b', content):
            await handle_everyone_command(message)
        elif re.search(r'\bwrong\b', content):
            await handle_wrong_command(message)
        elif re.search(r'\bunban\(\d+\)', content):
            await handle_unban_command(message)
        elif re.search(r'\bban\(\d+\)', content):
            await handle_ban_command(message)
        elif re.search(r'\brr\b', content):
            await handle_russian_roulette_command(message)
        elif re.search(r'\binvite\b', content):
            await handle_invite_command(message)
        elif re.search(r'\bhelp\b', content) or len(content.split()) == 1:
            await send_help(message)
        return  # Exit early if the bot is mentioned with its own command
        
    if message.attachments:
        await message.add_reaction('📷')