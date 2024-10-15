# External Imports
from urllib.parse import urlparse, urlunparse
from moviepy.editor import VideoFileClip
from datetime import datetime
import configparser
import subprocess
import discord
import asyncio
import random
import shutil
import json
import os
import re

# Internal Imports
from imports.functions import *
from imports.bot_instance import bot

# Load the config file
config = configparser.ConfigParser()
config.read('config.ini')

# Some variables
admin_ids = [int(id.strip()) for id in config['settings']['admin_ids'].split(',')]
max_file_size = int(config['settings']['max_file_size']) * 1024 * 1024
telemetry_enabled = str(config['telemetry']['enabled'])
telemetry_file_path = config['telemetry']['file_path']
quote_channel_id = int(config['quotes']['channel_id'])
embed_color = int(config['quotes']['embed_color'], 16)
quotes_enabled = str(config['quotes']['enabled'])
ban_list = config['settings']['ban_list']
wrong_mp3 = config['media']['wrong_mp3']

# Async Functions
async def handle_gif_creation(message, credited_users):
    if message.attachments:
        for attachment in message.attachments:
            file_path = f"./{attachment.filename}"
            gif_path = file_path.rsplit('.', 1)[0] + ".gif"
            
            try:
                if attachment.size > max_file_size:
                    await message.reply(f"File is too large. Please attach a file smaller than {max_file_size}MB.")
                    continue

                # Save the attached file locally
                await attachment.save(file_path)

                # Handle image and video files separately
                if attachment.filename.lower().endswith(('png', 'jpg', 'jpeg')):
                    create_gif_from_image(file_path, gif_path)
                elif attachment.filename.lower().endswith(('mp4', 'mov', 'avi')):
                    # Check video duration
                    if not is_video_duration_valid(file_path, max_duration=10):
                        await message.reply("Video is too long. Please attach a video shorter than 10 seconds.")
                        os.remove(file_path)
                        continue
                    create_gif_from_video(file_path, gif_path)
                else:
                    await message.reply("Unsupported file type. Please attach an image or video.")
                    continue

                # Check if the GIF exceeds the size limit, and compress if necessary
                if os.path.exists(gif_path) and os.path.getsize(gif_path) > max_file_size:
                    gif_path = compress_gif(gif_path)

                # Send the created GIF in the channel
                message_sent = await message.channel.send(file=discord.File(gif_path))
                gif_link = message_sent.attachments[0].url
                clean_link = remove_query_params(gif_link)

                guild_name = message.guild.name
                channel_name = message.channel.name
                usernames = ", ".join(user.name for user in credited_users if user != bot.user)

                log_gif_creation(attachment.filename, clean_link, guild_name, channel_name, usernames)

            except Exception as e:
                await message.reply("There was an error processing the file.")
                print(f"Error processing file: {e}")
            finally:
                # Ensure both the input and output files are deleted
                if os.path.exists(file_path):
                    os.remove(file_path)
                if os.path.exists(gif_path):
                    os.remove(gif_path)

async def handle_gif_command(message):
    if message.attachments:
        for attachment in message.attachments:
            file_path = f"./{attachment.filename}"
            gif_path = file_path.rsplit('.', 1)[0] + ".gif"

            try:
                if attachment.size > max_file_size:
                    await message.reply(f"File is too large. Please attach a file smaller than {max_file_size}MB.")
                    continue

                # Save the attached file locally
                await attachment.save(file_path)

                # Handle image and video files separately
                if attachment.filename.lower().endswith(('png', 'jpg', 'jpeg')):
                    create_gif_from_image(file_path, gif_path)
                elif attachment.filename.lower().endswith(('mp4', 'mov', 'avi')):
                    # Check video duration
                    if not is_video_duration_valid(file_path, max_duration=10):
                        await message.reply("Video is too long. Please attach a video shorter than 10 seconds.")
                        os.remove(file_path)
                        continue
                    create_gif_from_video(file_path, gif_path)
                else:
                    await message.reply("Unsupported file type. Please attach an image or video.")
                    continue
                
                # Check if the GIF exceeds the size limit, and compress if necessary
                if os.path.exists(gif_path) and os.path.getsize(gif_path) > max_file_size:
                    gif_path = compress_gif(gif_path)

                # Send the created GIF in the channel
                message_sent = await message.channel.send(file=discord.File(gif_path))
                gif_link = message_sent.attachments[0].url
                clean_link = remove_query_params(gif_link)
                
                guild_name = message.guild.name if message.guild and message.guild.name else "None"
                channel_name = "Direct Message" if isinstance(message.channel, discord.DMChannel) else (message.channel.name if message.channel and message.channel.name else "None")
                username = message.author.name if message.author and message.author.name else "None"

                print_and_log(f"GIF Created: {attachment.filename} | Link: {clean_link} | Server: {guild_name} | Channel: {channel_name} | User: {username}")

            except Exception as e:
                await message.reply("There was an error processing the file.")
                print(f"Error processing file: {e}")
            finally:
                # Ensure both the input and output files are deleted
                if os.path.exists(file_path):
                    os.remove(file_path)
                if os.path.exists(gif_path):
                    os.remove(gif_path)

    # Optionally delete the original message after processing
    try:
        await message.delete()
    except:
        return
async def handle_everyone_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return
    
    guild_name = message.guild.name if message.guild and message.guild.name else "None"
    channel_name = "Direct Message" if isinstance(message.channel, discord.DMChannel) else (message.channel.name if message.channel and message.channel.name else "None")
    username = message.author.name if message.author and message.author.name else "None"
    
    print_and_log(f"Everyone got pinged | Server: {guild_name} | Channel: {channel_name} | User: {username}")

    await message.delete()
    await message.channel.send("@everyone")

async def handle_wrong_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return
    
    guild_name = message.guild.name if message.guild and message.guild.name else "None"
    channel_name = "Direct Message" if isinstance(message.channel, discord.DMChannel) else (message.channel.name if message.channel and message.channel.name else "None")
    username = message.author.name if message.author and message.author.name else "None"
    
    print_and_log(f"Someone was told wrong | Server: {guild_name} | Channel: {channel_name} | User: {username}")
    
    await message.delete()
    await message.channel.send(file=discord.File(wrong_mp3), reference=message.reference)

async def handle_ban_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return
    
    if message.author.id not in admin_ids:
        await message.reply("You do not have permission to use this command.")
        print_and_log(f'Banned {message.author.id} due to attempted use of admin command!')
        BLOCKED_USER_IDS = get_blocked_user_ids()
        if message.author.id not in BLOCKED_USER_IDS:
            BLOCKED_USER_IDS.append(message.author.id)
            with open(ban_list, 'w') as file:
                file.write(','.join(map(str, BLOCKED_USER_IDS)))
        return

    try:
        user_id = int(re.search(r'ban\((\d+)\)', message.content).group(1))
        blocked_user_ids = get_blocked_user_ids()
        if user_id not in blocked_user_ids:
            blocked_user_ids.append(user_id)
            with open(ban_list, 'w') as file:
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
    
    if message.author.id not in admin_ids:
        await message.reply("You do not have permission to use this command.")
        print_and_log(f'Banned {message.author.id} due to attempted use of admin command!')
        BLOCKED_USER_IDS = get_blocked_user_ids()
        if message.author.id not in BLOCKED_USER_IDS:
            BLOCKED_USER_IDS.append(message.author.id)
            with open(ban_list, 'w') as file:
                file.write(','.join(map(str, BLOCKED_USER_IDS)))
        return

    try:
        user_id = int(re.search(r'unban\((\d+)\)', message.content).group(1))
        blocked_user_ids = get_blocked_user_ids()
        if user_id in blocked_user_ids:
            blocked_user_ids.remove(user_id)
            with open(ban_list, 'w') as file:
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
 
    if message.author.id not in admin_ids:
        await message.reply("You do not have permission to use this command.")
        print_and_log(f'Banned {message.author.id} due to attempted use of admin command!')
        BLOCKED_USER_IDS = get_blocked_user_ids()
        if message.author.id not in BLOCKED_USER_IDS:
            BLOCKED_USER_IDS.append(message.author.id)
            with open(ban_list, 'w') as file:
                file.write(','.join(map(str, BLOCKED_USER_IDS)))
        return
    
    guild_name = message.guild.name if message.guild and message.guild.name else "None"
    channel_name = "Direct Message" if isinstance(message.channel, discord.DMChannel) else (message.channel.name if message.channel and message.channel.name else "None")
    username = message.author.name if message.author and message.author.name else "None"
    
    print_and_log(f"Invite was created | Server: {guild_name} | Channel: {channel_name} | User: {username}")

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
    embed.add_field(name="@Bot rr", value="Plays russian roulette.", inline=False)
    embed.add_field(name="@Bot quote", value="Quotes replied message in the channel.", inline=False)
    embed.add_field(name="@Bot invite", value="Creates for you temporary server invite. [ADMIN ONLY]", inline=False)
    embed.add_field(name="@Bot readlog(number)", value="Shows you last (number) lines of log. [ADMIN ONLY]", inline=False)
    embed.add_field(name="@Bot chatlog(userid/all)", value="Sends you entire DM history with provided user. [ADMIN ONLY]", inline=False)
    embed.add_field(name="@Bot ban/unban(userid)", value="Bans user from using most of the bot features. [ADMIN ONLY]", inline=False)
    await message.channel.send(embed=embed)

async def handle_russian_roulette_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return

    random_number = random.randint(1, 8)

    # Announce Russian Roulette action
    await message.reply(f"🔫 Russian Roulette: Rolling the chamber...")

    # Add a delay before revealing the result
    await asyncio.sleep(2)  # Wait for 2 seconds

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
            await dm_channel.send(f"You're about to be kicked! Here's an invite to rejoin: {invite.url}")

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

    guild_name = message.guild.name if message.guild and message.guild.name else "None"
    channel_name = "Direct Message" if isinstance(message.channel, discord.DMChannel) else (message.channel.name if message.channel and message.channel.name else "None")
    username = message.author.name if message.author and message.author.name else "None"
    
    print_and_log(f"Someone played russian roulette | Server: {guild_name} | Channel: {channel_name} | User: {username}")

async def handle_readlog_command(message, number: int):
    if message.author.id not in admin_ids:
        await message.reply("You do not have permission to use this command.")
        print_and_log(f'Banned {message.author.id} due to attempted use of admin command!')
        BLOCKED_USER_IDS = get_blocked_user_ids()
        if message.author.id not in BLOCKED_USER_IDS:
            BLOCKED_USER_IDS.append(message.author.id)
            with open(ban_list, 'w') as file:
                file.write(','.join(map(str, BLOCKED_USER_IDS)))
        return
    
    try:
        # Load the telemetry data from the JSON file
        with open(telemetry_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Get the telemetry logs
        telemetry_logs = data.get("telemetry", {})
        
        # Sort logs by timestamp (key) to get them in chronological order
        sorted_logs = sorted(telemetry_logs.items(), key=lambda item: item[0])
        
        # Get the last 'number' entries, but adjust if there are less logs than requested
        last_logs = sorted_logs[-number:] if len(sorted_logs) >= number else sorted_logs
        
        # Prepare the log message
        log_message = "\n".join([f"{timestamp}: {log}" for timestamp, log in last_logs])
        
        # Save the log message to a text file
        with open("last_logs.txt", 'w', encoding='utf-8') as file:
            file.write(log_message)
        
        # Send the log message back to the Discord channel as a file
        if log_message:
            file = discord.File("last_logs.txt")
            # Adjust the message to reflect the actual number of logs sent
            actual_number = len(last_logs)
            await message.channel.send(f"Last {actual_number} lines of log:", file=file)
            os.remove("last_logs.txt")  # Remove the file after sending
        else:
            await message.channel.send("No logs found.")
    except FileNotFoundError:
        await message.channel.send("Telemetry file not found.")
    except Exception as e:
        await message.channel.send(f"An error occurred: {str(e)}")

async def handle_chatlog_command(message, user_id_or_all: str):
    if message.author.id not in admin_ids:
        await message.reply("You do not have permission to use this command.")
        print_and_log(f'Banned {message.author.id} due to attempted use of admin command!')
        BLOCKED_USER_IDS = get_blocked_user_ids()
        if message.author.id not in BLOCKED_USER_IDS:
            BLOCKED_USER_IDS.append(message.author.id)
            with open(ban_list, 'w') as file:
                file.write(','.join(map(str, BLOCKED_USER_IDS)))
        return

    try:
        if user_id_or_all == "all":
            # Go through all users the bot can see
            all_users = bot.users
            print(f"Found {len(all_users)} users the bot can access.")
        else:
            # Fetch DM for a single user
            user = bot.get_user(int(user_id_or_all))
            all_users = [user] if user else []
            print(f"Found user with ID {user_id_or_all}: {bool(user)}")

        if not all_users:
            await message.reply(f"No chat logs found.")
            return

        for user in all_users:
            if user.bot:  # Skip bots
                continue

            # Create a DM channel with the user
            dm_channel = await user.create_dm()
            messages = [msg async for msg in dm_channel.history(limit=100)]
            
            if not messages:
                continue  # Skip if no messages found

            chat_logs = []
            for msg in messages:
                # Include messages with content, attachments, or embeds
                if msg.content.strip() or msg.attachments or msg.embeds:
                    attachments = [attachment.url for attachment in msg.attachments]
                    logEntry = {
                        "author": msg.author.name,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat(),
                        "attachments": attachments
                    }
                    if msg.embeds:  # Check if there are any embeds
                        embedContent = [{"title": embed.title, "description": embed.description} for embed in msg.embeds]
                        logEntry["embed_content"] = embedContent
                    chat_logs.append(logEntry)

            # Only save and send if there are logs (i.e., chat_logs is not empty)
            if chat_logs:  
                log_file_path = f"chatlog_{user.id}.json"
                with open(log_file_path, 'w') as file:
                    json.dump(chat_logs, file, indent=4)

                # Send the chat log to the admin user, including a mention of the user
                admin_user = bot.get_user(admin_ids[0])
                if admin_user:
                    admin_dm_channel = await admin_user.create_dm()
                    await admin_dm_channel.send(
                        f"Chat logs for <@{user.id}>:",  # Mention the user here
                        file=discord.File(log_file_path)
                    )
                    os.remove(log_file_path)

    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")
        print(f"Error occurred: {str(e)}")

async def handle_quote_command(message):
    # Check if quoting is enabled
    if quotes_enabled.lower() != 'True':
        await message.reply("Quoting is currently disabled.")
        return

    # Check if the message is a reply
    if not message.reference or not message.reference.resolved:
        await message.reply("Please reply to a message you want to quote.")
        return

    # Get the original message being replied to
    original_message = message.reference.resolved
    
    quote_channel = message.guild.get_channel(quote_channel_id)

    if not quote_channel:
        await message.reply("Quote channel not found.")
        return

    # Create an embed for the quoted message
    embed = discord.Embed(
        description=f"{original_message.content}\n\n[Quoted message](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})",
        color=discord.Color(embed_color)  # Use the custom hex color
    )
    embed.set_author(name=original_message.author.display_name, icon_url=original_message.author.avatar.url)
    embed.set_footer(text=f"Quoted by {message.author.display_name}")

    # Send the embed to the specified channel
    await quote_channel.send(embed=embed)

    # Optionally, delete the command message
    await message.delete()

# Functions
def count_camera_reactions(message):
    for reaction in message.reactions:
        if str(reaction.emoji) == '📷':
            return reaction.count
    return 0

def remove_pycache():
    for root, dirs, files in os.walk('.'):
        for dir in dirs:
            if dir == '__pycache__':
                shutil.rmtree(os.path.join(root, dir))

def check_files():
    # Collect all file paths from the config
    missing_files = []

    # Iterate over all sections and keys in the config
    for section in config.sections():
        for key, value in config.items(section):
            # Check if the value is a file path
            if os.path.splitext(value)[1]:  # Check if there's a file extension
                if not os.path.exists(value):
                    missing_files.append(value)

    # Check if token.txt is missing and print a warning message
    if 'files/token.txt' not in missing_files and not os.path.exists('files/token.txt'):
        print("Warning: token.txt file is missing. Please paste your bot token there.")

    if missing_files:
        print("The following files are missing:")
        for file in missing_files:
            print(f"- {file}")
            # Attempt to create the missing file
            with open(file, 'w') as f:
                f.write("")  # Create an empty file
            print(f"Created {file} as an empty file.")
        exit(1)

def get_blocked_user_ids():
    try:
        with open(ban_list, 'r') as file:
            ids = file.read().strip().split(',')
            return [int(id.strip()) for id in ids if id.strip().isdigit()]
    except Exception as e:
        print_and_log(f"Error reading ban.txt: {e}")
        return []

def is_video_duration_valid(file_path, max_duration=10):
    try:
        with VideoFileClip(file_path) as video:
            duration = video.duration
            return duration <= max_duration
    except Exception as e:
        print(f"Error checking video duration: {e}")
        return False
    
def create_gif_from_image(input_path, output_path):
    try:
        # Convert image to GIF without heavy compression
        subprocess.run([
            'ffmpeg',
            '-i', input_path,
            '-loop', '1',
            '-t', '10',
            '-vf', 'scale=640:-1',
            output_path,
            '-y'  # Overwrite output file if it exists
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error while processing image: {e}")
        raise

def create_gif_from_video(input_path, output_path):
    try:
        # Convert video to GIF without heavy compression
        subprocess.run([
            'ffmpeg',
            '-i', input_path,
            '-vf', 'fps=10,scale=640:-1',
            output_path,
            '-y'  # Overwrite output file if it exists
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error while processing video: {e}")
        raise

def compress_gif(gif_path):
    try:
        # Generate a palette for the GIF
        palette_path = gif_path.rsplit('.', 1)[0] + "_palette.png"
        subprocess.run([
            'ffmpeg',
            '-i', gif_path,
            '-vf', 'fps=10,palettegen=dither=bayer',
            palette_path,
            '-y'  # Overwrite output file if it exists
        ], check=True)

        # Create the compressed GIF using the generated palette
        compressed_path = gif_path.rsplit('.', 1)[0] + "_compressed.gif"
        subprocess.run([
            'ffmpeg',
            '-i', gif_path,
            '-i', palette_path,
            '-vf', 'fps=10,paletteuse=dither=floyd_steinberg',
            compressed_path,
            '-y'  # Overwrite output file if it exists
        ], check=True)
        
        return compressed_path
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error during compression: {e}")
        raise
def remove_query_params(url):
    parsed_url = urlparse(url)
    clean_url = urlunparse(parsed_url._replace(query=""))
    return clean_url

def log_telemetry(message):
    if telemetry_enabled:
        timestamp = datetime.now().isoformat()
        log_entry = {timestamp: message}
        
        if os.path.exists(telemetry_file_path):
            with open(telemetry_file_path, 'r') as file:
                telemetry_data = json.load(file)
        else:
            telemetry_data = {"telemetry": {}}
        
        telemetry_data["telemetry"].update(log_entry)
        
        with open(telemetry_file_path, 'w') as file:
            json.dump(telemetry_data, file, indent=4)

def print_and_log(message):
    print(message)
    log_telemetry(message)

def log_gif_creation(filename, link, guild_name, channel_name, usernames):
    message = f"GIF Created: {filename} | Link: {link} | Server: {guild_name} | Channel: {channel_name} | Users: {usernames}"
    print_and_log(message)