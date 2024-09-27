# External Imports
from urllib.parse import urlparse, urlunparse
from moviepy.editor import VideoFileClip
from collections import defaultdict
from discord.ext import commands
from PIL import Image
import configparser
import discord
import random
import os
import re

# Internal Imports
from imports.functions import *
from imports.bot_instance import bot

# Load the config file
config = configparser.ConfigParser()
config.read('config.ini')

# Some variables and arrays
kicked_users_roles = defaultdict(list)
ADMIN_USER_ID = int(config['settings']['ADMIN_USER_ID'])
ban_file = config['settings']['ban_file']
wrong_mp3 = config['settings']['wrong_mp3']

# Async Functions
async def handle_gif_creation(message, credited_user):
    if message.attachments:
        for attachment in message.attachments:
            try:
                file_path = f"./{attachment.filename}"
                await attachment.save(file_path)

                if attachment.filename.lower().endswith(('png', 'jpg', 'jpeg')):
                    gif_path = file_path.rsplit('.', 1)[0] + ".gif"
                    create_gif(file_path, gif_path)
                elif attachment.filename.lower().endswith(('mp4', 'mov', 'avi')):
                    gif_path = file_path.rsplit('.', 1)[0] + ".gif"
                    create_gif_from_video(file_path, gif_path)
                else:
                    await message.reply("Unsupported file type. Please attach an image or video.")
                    continue

                message_sent = await message.channel.send(file=discord.File(gif_path))
                gif_link = message_sent.attachments[0].url
                clean_link = remove_query_params(gif_link)
                guild_name = message.guild.name
                channel_name = message.channel.name
                username = credited_user.name

                print(f"GIF Created: {attachment.filename} | Link: {clean_link} | Server: {guild_name} | Channel: {channel_name} | User: {username}")

                os.remove(file_path)
                os.remove(gif_path)

            except Exception as e:
                await message.reply("There was an error processing the file.")
                print(f"Error processing file: {e}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                continue

async def handle_gif_command(message):
    if message.attachments:
        for attachment in message.attachments:
            try:
                file_path = f"./{attachment.filename}"
                await attachment.save(file_path)

                if attachment.filename.lower().endswith(('png', 'jpg', 'jpeg')):
                    gif_path = file_path.rsplit('.', 1)[0] + ".gif"
                    create_gif(file_path, gif_path)
                elif attachment.filename.lower().endswith(('mp4', 'mov', 'avi')):
                    gif_path = file_path.rsplit('.', 1)[0] + ".gif"
                    create_gif_from_video(file_path, gif_path)
                else:
                    await message.reply("Unsupported file type. Please attach an image or video.")
                    continue
                
                message_sent = await message.channel.send(file=discord.File(gif_path))
                gif_link = message_sent.attachments[0].url
                clean_link = remove_query_params(gif_link)
                guild_name = message.guild.name if message.guild and message.guild.name else "None"
                channel_name = "Direct Message" if isinstance(message.channel, discord.DMChannel) else (message.channel.name if message.channel and message.channel.name else "None")
                username = message.author.name if message.author and message.author.name else "None"

                print(f"GIF Created: {attachment.filename} | Link: {clean_link} | Server: {guild_name} | Channel: {channel_name} | User: {username}")

                os.remove(file_path)
                os.remove(gif_path)

            except Exception as e:
                await message.reply("There was an error processing the file.")
                print(f"Error processing file: {e}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                continue
    try:
        await message.delete()
    except:
        return

async def handle_everyone_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return

    await message.delete()
    await message.channel.send("@everyone")

async def handle_wrong_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return
    
    await message.delete()
    await message.channel.send(file=discord.File(wrong_mp3), reference=message.reference)

async def handle_ban_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return
    
    if message.author.id != ADMIN_USER_ID:
        await message.reply("You do not have permission to use this command.")
        BLOCKED_USER_IDS = get_blocked_user_ids()
        if message.author.id not in BLOCKED_USER_IDS:
            BLOCKED_USER_IDS.append(message.author.id)
            with open(ban_file, 'w') as file:
                file.write(','.join(map(str, BLOCKED_USER_IDS)))
        return

    try:
        user_id = int(re.search(r'ban\((\d+)\)', message.content).group(1))
        blocked_user_ids = get_blocked_user_ids()
        if user_id not in blocked_user_ids:
            blocked_user_ids.append(user_id)
            with open(ban_file, 'w') as file:
                file.write(','.join(map(str, blocked_user_ids)))
            await message.reply(f"User {user_id} has been banned.")
            await message.delete()
        else:
            await message.reply(f"User {user_id} is already banned.")
    except (ValueError, IndexError, AttributeError):
        await message.reply("Invalid ban command format. Use ban(user_id).")

async def handle_unban_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return
    
    if message.author.id != ADMIN_USER_ID:
        await message.reply("You do not have permission to use this command.")
        BLOCKED_USER_IDS = get_blocked_user_ids()
        if message.author.id not in BLOCKED_USER_IDS:
            BLOCKED_USER_IDS.append(message.author.id)
            with open(ban_file, 'w') as file:
                file.write(','.join(map(str, BLOCKED_USER_IDS)))
        return

    try:
        user_id = int(re.search(r'unban\((\d+)\)', message.content).group(1))
        blocked_user_ids = get_blocked_user_ids()
        if user_id in blocked_user_ids:
            blocked_user_ids.remove(user_id)
            with open(ban_file, 'w') as file:
                file.write(','.join(map(str, blocked_user_ids)))
            await message.reply(f"User {user_id} has been unbanned.")
            await message.delete()
        else:
            await message.reply(f"User {user_id} is not banned.")
    except (ValueError, IndexError, AttributeError):
        await message.reply("Invalid unban command format. Use unban(user_id).")

async def handle_invite_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return

    try:
        # Create a one-time 24-hour invite link
        invite = await message.channel.create_invite(max_uses=1, max_age=86400)
        
        # DM the invite to the user who sent the command
        dm_channel = await message.author.create_dm()
        await dm_channel.send(f"Here is your invite link: {invite.url}")

        await message.reply(f"Invite link has been sent to your DM!")
    except Exception as e:
        await message.reply(f"An error occurred while creating the invite: {e}")

async def send_help(message):
    embed = discord.Embed(title="Bot Help", description="Here are the commands you can use:", color=0x00ff00)
    embed.add_field(name="@Bot gif", value="Converts attached images or videos to GIFs.", inline=False)
    embed.add_field(name="@Bot everyone", value="Deletes the message and pings everyone.", inline=False)
    embed.add_field(name="@Bot wrong", value="Deletes the message and sends wrong.mp3.", inline=False)
    embed.add_field(name="@Bot help", value="Shows this help message.", inline=False)
    await message.channel.send(embed=embed)
    print("Sent help message.")

async def handle_russian_roulette_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return

    random_number = random.randint(1, 8)

    # Announce Russian Roulette action
    await message.reply(f"🔫 Russian Roulette: Rolling the chamber...")

    if random_number == 5:
        member = message.author

        # Check if the bot's role is higher than the user's role
        if message.guild.me.top_role <= member.top_role:
            await message.reply(f"Cannot kick {member.name} due to role hierarchy. My role must be higher than theirs.")
            return

        try:
            # Create a one-time 24-hour invite link before kicking the user
            invite = await message.channel.create_invite(max_uses=1, max_age=86400)
            
            # DM the invite to the user before kicking
            dm_channel = await member.create_dm()
            await dm_channel.send(f"You're about to be kicked! Here’s an invite to rejoin: {invite.url}")

        except discord.Forbidden:
            await message.reply("I don't have permission to DM this user or create invites.")
            return
        except Exception as e:
            await message.reply(f"An error occurred while sending the invite: {e}")
            return

        # Attempt to kick the user
        try:
            await message.guild.kick(member)

            # Check if the member is still in the guild after the kick attempt
            if member not in message.guild.members:
                # Successfully kicked
                await message.edit(content=f"Russian Roulette: 💀 {member.name} got unlucky and was kicked!")
            else:
                # Kick failed
                await message.reply(f"Failed to kick {member.name}. It seems I lack the proper permissions.")
        except discord.Forbidden:
            # Kick failed due to lack of permissions
            await message.reply(f"Failed to kick {member.name} due to insufficient permissions.")
        except Exception as e:
            # Any other error
            await message.reply(f"An error occurred during kicking: {e}")
    else:
        await message.reply(f"Russian Roulette: 😅 {message.author.name} survived!")

# Functions
def count_camera_reactions(message):
    for reaction in message.reactions:
        if str(reaction.emoji) == '📷':
            return reaction.count
    return 0

def get_blocked_user_ids():
    try:
        with open(ban_file, 'r') as file:
            ids = file.read().strip().split(',')
            return [int(id.strip()) for id in ids if id.strip().isdigit()]
    except Exception as e:
        print(f"Error reading ban.txt: {e}")
        return []

def create_gif(image_path, gif_path):
    try:
        image = Image.open(image_path)
        image.save(gif_path, save_all=True)
    except Exception as e:
        print(f"Error creating GIF: {e}")

def create_gif_from_video(video_path, gif_path):
    try:
        clip = VideoFileClip(video_path)
        clip.write_gif(gif_path)
    except Exception as e:
        print(f"Error creating GIF from video: {e}")

def remove_query_params(url):
    parsed_url = urlparse(url)
    clean_url = urlunparse(parsed_url._replace(query=""))
    return clean_url