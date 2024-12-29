# External Imports
import discord
import re

# Internal Imports
from imports.functions import *
from imports.global_setup import bot, ver, config

# Some variables and arrays
reaction_gif_enabled = config['gifs']['reaction_enabled']
nicktrack_channel_id = config['nicktrack']['channel_id']
triple_attachment = config['media']['triple_attachment']
triple_message = config['triple_message']['message']
triple_enabled = config['triple_message']['enabled']
forcenick_enabled = config['forcenick']['enabled']
nicktrack_enabled = config['nicktrack']['enabled']
kys_attachment = config['media']['kys_attachment']
tracked_user_ids = config['pingdm']['target_ids']
cmg_enabled = config['gifs']['cmg_enabled']
target_ids = config['nicktrack']['target_ids']
forcenick = str(config['forcenick']['nick'])
enable_pingdm = config['pingdm']['enabled']
admin_ids = config['settings']['admin_ids']
consecutive_messages = {}
camera_clicks = {}

async def on_ready():
    await bot.tree.sync()

    print('')
    print('   ^^^:  .^^^          :55Y .555.                         ^^^^^^^^^^                      ?55! 7557                               ')
    print('   P@@@: #@@P          ?@@@ ~@@@:                        .@@@@@@@@@&                      &@@G B@@#                               ')
    print('    5@@&P@@Y   7G###P: ?@@@ ^@@@: :YB&&#G7 .B##: G##Y J##:   &@@B    .?B&&&B?.  ^5#&&#P~  &@@P B@@&5&&#J  .JB&&&G?  ?##B. G##!    ')
    print('     Y@@@@?   #@@B?@@@:7@@@ ^@@@.^@@@J~#@@# P@@Y~@@@@:&@#    &@@G   .@@@P^P@@@.J@@@7!&@@P &@@P B@@&!7@@@Y.@@@5^G@@&. ?@@&&@@~     ')
    print('      &@@B   .@@@&PPGB.7@@@ ^@@@.!@@@^ 5@@@  @@&&@7@@#@@.    &@@G   :@@@7 7@@@:P@@&. #@@B &@@P B@@& .@@@Y^@@@! ?@@@. :@@@@@&.     ')
    print('      B@@G    ^B@@&#&7 7@@& ^@@@. ?&@@@@@G:  7@@@G P@@@J     #@@P    ~#@@@@@#~  5&@@@@&5  #@@5 G@@&&@@@P  !#@@@@@B^ ?@@&:?@@@~    ')
    print('                 ....                ...        .                       ...       ....              ..       ...    ..      ..    ')
    print('')

    print(f'Bot is online! Logged in as {bot.user}')
    print(f'Yellow Toolbox ver. {ver}')
    for guild in bot.guilds:
        print(f'- {guild.name}')

async def on_member_join(member):
    return

async def on_reaction_add(reaction, user):
    if reaction.message.author == bot.user:
        return

    if reaction_gif_enabled and str(reaction.emoji) == '📷':

        BLOCKED_USER_IDS = get_blocked_user_ids()
        if reaction.message.author.id in BLOCKED_USER_IDS:
            await reaction.message.channel.send(f"kys {reaction.message.author.mention} ", file=discord.File(kys_attachment))
            return
        
        if reaction.message.id not in camera_clicks:
            camera_clicks[reaction.message.id] = []

        camera_clicks[reaction.message.id].append(user)

        message = await reaction.message.channel.fetch_message(reaction.message.id)
        camera_reactions = count_camera_reactions(message)

        if camera_reactions >= 1:
            async for user in reaction.users():
                await message.remove_reaction('📷', user)

            await handle_gifs(message, camera_clicks[reaction.message.id])

async def on_member_update(before: discord.Member, after: discord.Member):
    if not nicktrack_enabled:
        return

    # Check if the nickname has changed
    if before.nick != after.nick and after.id in target_ids:
        # Send a message to the channel when the user changes their nickname
        channel = after.guild.get_channel(nicktrack_channel_id)
        if channel:
            await channel.send(f"{', '.join(f'<@{admin_id}>' for admin_id in admin_ids)}, User {after.name} got their nickname changed from '{before.nick}' to '{after.nick}'")

    # Forced nickname change mechanism (only if enabled)
    if forcenick_enabled:
        if after.id in target_ids and after.nick != f"{forcenick}":
            await after.edit(nick=f"{forcenick}")

async def on_message(message):
    BLOCKED_USER_IDS = get_blocked_user_ids()

    if message.author == bot.user:
        return

    if message.author.id in BLOCKED_USER_IDS:
        if bot.user in message.mentions:
            await message.reply(f"kys", file=discord.File(kys_attachment))
        return

    if isinstance(message.channel, discord.DMChannel) and message.author.id not in admin_ids:
        for admin_id in admin_ids:
            admin_user = bot.get_user(admin_id)
            if admin_user:
                try:
                    dm_channel = await admin_user.create_dm()
                    await dm_channel.send(f"Message from {message.author.name}: {message.content}")
                except discord.Forbidden:
                    print(f"I can't send a DM to admin with ID {admin_id}.")

    if enable_pingdm:
        for user in message.mentions:
            if user.id in tracked_user_ids:
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

                    # Prepare attachments
                    files = [await attachment.to_file() for attachment in message.attachments]

                    # Send the embed and attachments as a DM
                    await user.send(embed=embed, files=files)

                except discord.Forbidden:
                    print("I can't send a DM to targeted user.")

    # Check for camera emoji message
    if cmg_enabled:
        if message.content.strip() == '📷' and message.reference and message.reference.resolved:
            original_message = message.reference.resolved
            if original_message.attachments:
                await handle_gifs(original_message, [message.author])

    if triple_enabled:
        global consecutive_messages
        normalized_content = message.content.lower()
        normalized_triple_string = triple_message.lower()

        # Check for consecutive messages
        user_id = message.author.id
        if user_id not in consecutive_messages:
            consecutive_messages[user_id] = {'content': normalized_content, 'count': 1}
        else:
            if consecutive_messages[user_id]['content'] == normalized_content:
                consecutive_messages[user_id]['count'] += 1
            else:
                consecutive_messages[user_id] = {'content': normalized_content, 'count': 1}

        # Check if the message has been sent 3 times in a row
        if consecutive_messages[user_id]['count'] == 3 and normalized_content == normalized_triple_string:
            await message.channel.send(file=discord.File(triple_attachment))
            
            guild_name = message.guild.name if message.guild and message.guild.name else "None"
            channel_name = "Direct Message" if isinstance(message.channel, discord.DMChannel) else (message.channel.name if message.channel and message.channel.name else "None")
            username = message.author.name if message.author and message.author.name else "None"
            
            print_and_log(f"Tripple message got activated! | Server: {guild_name} | Channel: {channel_name} | User: {username}")
            consecutive_messages[user_id]['count'] = 0  # Reset the count after sending the attachment

    if message.author != bot.user and message.content.startswith(f"<@{bot.user.id}>"):
        content = message.content.lower()
        if re.search(r'\bgif\b', content):
            await handle_gifs(message)
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
        elif re.search(r'\brestart\b', content):
            await handle_restart_command(message)
        elif match := re.search(r'readlog\((\d+)\)', content):
            await handle_readlog_command(message, int(match.group(1)))
        elif match := re.search(r'chatlog\((\w+)\)', content):
            await handle_chatlog_command(message, match.group(1))
        elif re.search(r'\bhelp\b', content) or len(content.split()) == 1:
            await send_help(message)
        elif re.search(r'\bquote\b', content):
            await handle_quote_command(message)
        return