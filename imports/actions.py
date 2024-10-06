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
forcenick_enabled = str(config['forcenick']['forcenick_enabled'])
nicktrack_enabled = str(config['nicktrack']['nicktrack_enabled'])
tracked_user_id = int(config['pingdm']['target_id'])
target_id = int(config['nicktrack']['target_id'])
enable_pingdm = str(config['pingdm']['enabled'])
admin_id = int(config['settings']['admin_id'])
forcenick = str(config['forcenick']['nick'])
no_gif = config['settings']['no_gif']
camera_clicks = {}
ver = 'pre-1.2'

async def on_ready():
    print(f'Bot is online! Logged in as {bot.user}')
    print(f'Yellow Toolbox ver. {ver}')
    for guild in bot.guilds:
        print(f'- {guild.name}')

async def on_member_join(member):
    return

async def on_reaction_add(reaction, user):
    if reaction.message.author == bot.user:
        return

    if str(reaction.emoji) == '📷':

        BLOCKED_USER_IDS = get_blocked_user_ids()
        if reaction.message.author.id in BLOCKED_USER_IDS:
            await reaction.message.channel.send(f"kys {reaction.message.author.mention}", file=discord.File(no_gif))
            return
        
        if reaction.message.id not in camera_clicks:
            camera_clicks[reaction.message.id] = []

        camera_clicks[reaction.message.id].append(user)

        message = await reaction.message.channel.fetch_message(reaction.message.id)
        camera_reactions = count_camera_reactions(message)

        if camera_reactions >= 1:
            async for user in reaction.users():
                await message.remove_reaction('📷', user)

            await handle_gif_creation(message, camera_clicks[reaction.message.id])

async def on_member_update(before: discord.Member, after: discord.Member):
    # Check if the nickname has changed
    if nicktrack_enabled == 'True' and before.nick != after.nick and after.id == target_id:
        # Send a message to the channel when the user changes their nickname
        channel = after.guild.get_channel(1287007606870904914)
        if channel:
            await channel.send(f"<@{admin_id}>, User {after.name} got their nickname changed from '{before.nick}' to '{after.nick}'")

    # Forced nickname change mechanism (only if enabled)
    if forcenick_enabled == 'True' and after.id == target_id and after.nick != f"{forcenick}":
        await after.edit(nick=f"{forcenick}")

async def on_message(message):
    BLOCKED_USER_IDS = get_blocked_user_ids()

    if message.author == bot.user:
        return

    if message.author.id in BLOCKED_USER_IDS:
        if bot.user in message.mentions:
            await message.reply("kys", file=discord.File(no_gif))
        return

    if isinstance(message.channel, discord.DMChannel) and message.author.id != admin_id:
        admin_user = bot.get_user(admin_id)
        if admin_user:
            try:
                dm_channel = await admin_user.create_dm()
                await dm_channel.send(f"Message from {message.author.name}: {message.content}")
            except discord.Forbidden:
                print("I can't send a DM to the admin.")

    if enable_pingdm == 'True':
        if any(user.id == tracked_user_id for user in message.mentions):
            user = bot.get_user(tracked_user_id)
            if user is not None:
                try:
                    message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

                    # Create an embed with the message content and link
                    embed = discord.Embed(
                        title="You've been mentioned in a message!",
                        description=f"[Jump to the message]({message_link})",  # Link to the message
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Message Content", value=message.content or "No content", inline=False)
                    embed.set_footer(text=f"From #{message.channel.name} in {message.guild.name}")
                    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)

                    # Send the embed as a DM
                    await user.send(embed=embed)

                except discord.Forbidden:
                    print("I can't send a DM to targeted user.")

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
        elif match := re.search(r'readlog\((\d+)\)', content):
            await handle_readlog_command(message, int(match.group(1)))
        elif match := re.search(r'chatlog\((\w+)\)', content):
            await handle_chatlog_command(message, match.group(1))
        elif re.search(r'\bhelp\b', content) or len(content.split()) == 1:
            await send_help(message)
        return  # Exit early if the bot is mentioned with its own commands