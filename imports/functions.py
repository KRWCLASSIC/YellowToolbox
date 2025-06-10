# External Imports
from urllib.parse import urlparse, urlunparse
from moviepy.editor import VideoFileClip
from datetime import datetime
import subprocess
import discord
import asyncio
import random
import shutil
import json
import sys
import os
import re

# Internal Imports
from imports.functions import *
from imports.global_setup import bot, config

# Some variables
max_file_size = int(config['gifs']['max_file_size']) * 1024 * 1024
gifs_frame_limit = int(config['gifs']['gifs_frame_limit'])
telemetry_file_path = config['telemetry']['file_path']
wrong_attachment = config['media']['wrong_attachment']
quote_channel_id = int(config['quotes']['channel_id'])
embed_color = int(config['quotes']['embed_color'], 16)
max_vid_length = int(config['gifs']['max_vid_length'])
verbose_creation = config['gifs']['verbose_creation']
rr_waittime = int(config['r_roulette']['wait_time'])
telemetry_enabled = config['telemetry']['enabled']
gif_creation_enabled = config['gifs']['enabled']
quotes_enabled = config['quotes']['enabled']
admin_ids = config['settings']['admin_ids']
rr_odds = int(config['r_roulette']['odds'])
ban_list = config['files']['ban_list']

# --- Scissors Paper Stone Game Handler ---
sps_rigged = config.get('sps_game', {}).get('rigged', False)

# Async Functions
async def handle_gifs(message, credited_users=None):
    """Handles the GIF creation process triggered by a Discord command."""
    if credited_users is None:
        credited_users = []  # Initialize if not provided

    if gif_creation_enabled and message.attachments:
        for attachment in message.attachments:
            temp_file_path = os.path.join('temp', attachment.filename)
            gif_path = os.path.join('temp', attachment.filename.rsplit('.', 1)[0] + ".gif")

            try:
                # Check if the file size exceeds the limit
                if attachment.size > max_file_size:
                    await message.reply(f"File is too large. Please attach a file smaller than {max_file_size}MB.")
                    continue

                # Save the attachment in the temp folder
                os.makedirs('temp', exist_ok=True)
                await attachment.save(temp_file_path)

                # Process the file based on its type (image or video)
                if attachment.filename.lower().endswith(('png', 'jpg', 'jpeg')):
                    try:
                        create_gif_from_image(temp_file_path, gif_path)
                        # Try to send the processed GIF
                        try:
                            message_sent = await message.channel.send(file=discord.File(gif_path))
                            gif_link = message_sent.attachments[0].url
                            clean_link = remove_query_params(gif_link)
                        except discord.HTTPException as e:
                            if e.code == 40005:  # Payload Too Large
                                # Fallback: Just rename the original file to .gif
                                fallback_gif = os.path.join('temp', attachment.filename.rsplit('.', 1)[0] + "_fallback.gif")
                                shutil.copy2(temp_file_path, fallback_gif)
                                message_sent = await message.channel.send(file=discord.File(fallback_gif))
                                gif_link = message_sent.attachments[0].url
                                clean_link = remove_query_params(gif_link)
                            else:
                                raise
                    except Exception as e:
                        print(f"Error processing image: {e}")
                        continue

                elif attachment.filename.lower().endswith(('mp4', 'mov', 'avi')):
                    # Validate the video duration
                    if not is_video_duration_valid(temp_file_path, max_duration=max_vid_length):
                        await message.reply(f"Video is too long. Please attach a video shorter than {max_vid_length} seconds.")
                        continue
                    create_gif_from_video(temp_file_path, gif_path)
                    message_sent = await message.channel.send(file=discord.File(gif_path))
                    gif_link = message_sent.attachments[0].url
                    clean_link = remove_query_params(gif_link)
                else:
                    await message.reply("Unsupported file type. Please attach an image or video.")
                    continue

                # Log details about the created GIF
                guild_name = message.guild.name if message.guild else "None"
                channel_name = (
                    "Direct Message" if isinstance(message.channel, discord.DMChannel)
                    else (message.channel.name if message.channel else "None")
                )
                username = message.author.name if message.author else "None"
                credited_usernames = ", ".join(user.name for user in credited_users if user != bot.user)
                print_and_log(f"GIF Created: {attachment.filename} | Link: {clean_link} | Server: {guild_name} | Channel: {channel_name} | User: {username} | Credited Users: {credited_usernames}")

            except Exception as e:
                await message.reply("There was an error processing the file.")
                print(f"Error processing file: {e}")

            finally:
                # Clear the temp directory to ensure no leftover files
                clear_temp_directory()

    # Optionally delete the original message after processing
    if not credited_users:
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

async def handle_restart_command(message):
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
        await message.reply("Restarting the bot...")
        print_and_log("Bot is restarting...")

        # Restart the bot
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        await message.reply(f"An error occurred while restarting the bot: {e}")
        print(f"Error during bot restart: {e}")

async def handle_wrong_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return
    
    guild_name = message.guild.name if message.guild and message.guild.name else "None"
    channel_name = "Direct Message" if isinstance(message.channel, discord.DMChannel) else (message.channel.name if message.channel and message.channel.name else "None")
    username = message.author.name if message.author and message.author.name else "None"
    
    print_and_log(f"Someone was told wrong | Server: {guild_name} | Channel: {channel_name} | User: {username}")
    
    await message.delete()
    await message.channel.send(file=discord.File(wrong_attachment), reference=message.reference)

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
        user = bot.get_user(user_id)  # Fetch the user object
        blocked_user_ids = get_blocked_user_ids()
        if user_id not in blocked_user_ids:
            blocked_user_ids.append(user_id)
            with open(ban_list, 'w') as file:
                file.write(','.join(map(str, blocked_user_ids)))
            await message.reply(f"User {user.name} has been banned.")  # Use username here
            await message.delete()
        else:
            await message.reply(f"User {user.name} is already banned.")  # Use username here
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
        user = bot.get_user(user_id)  # Fetch the user object
        blocked_user_ids = get_blocked_user_ids()
        if user_id in blocked_user_ids:
            blocked_user_ids.remove(user_id)
            with open(ban_list, 'w') as file:
                file.write(','.join(map(str, blocked_user_ids)))
            await message.reply(f"User {user.name} has been unbanned.")  # Use username here
            await message.delete()
        else:
            await message.reply(f"User {user.name} is not banned.")  # Use username here
    except (ValueError, IndexError, AttributeError):
        await message.reply("Invalid unban command format. Use unban(user_id).")

async def send_help(message):
    embed = discord.Embed(title="Bot Help", description="Here are the commands you can use:", color=0x00ff00)
    embed.add_field(name="@Bot gif", value="Converts attached images or videos to GIFs.", inline=False)
    embed.add_field(name="@Bot everyone", value="Deletes the message and pings everyone.", inline=False)
    embed.add_field(name="@Bot wrong", value="Deletes the message and sends wrong.mp3.", inline=False)
    embed.add_field(name="@Bot help", value="Shows this help message.", inline=False)
    embed.add_field(name="@Bot rr", value="Plays russian roulette.", inline=False)
    embed.add_field(name="@Bot quote", value="Quotes replied message in the channel.", inline=False)
    embed.add_field(name="@Bot restart", value="Restarts the bot. [ADMIN ONLY]", inline=False)
    embed.add_field(name="@Bot readlog(number)", value="Shows you last (number) lines of log. [ADMIN ONLY]", inline=False)
    embed.add_field(name="@Bot chatlog(userid/all)", value="Sends you entire DM history with provided user. [ADMIN ONLY]", inline=False)
    embed.add_field(name="@Bot ban/unban(userid)", value="Bans user from using most of the bot features. [ADMIN ONLY]", inline=False)
    await message.channel.send(embed=embed)

async def handle_russian_roulette_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return

    random_number = random.randint(1, rr_odds)

    # Announce Russian Roulette action
    await message.reply(f"🔫 Russian Roulette: Rolling the chamber...")

    # Add a delay before revealing the result
    await asyncio.sleep(rr_waittime)  # Wait for 2 seconds 

    if random_number == 1:
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
    
    if random_number == 1:
        survived = False
    else:
        survived = True

    print_and_log(f"Someone played russian roulette | Server: {guild_name} | Channel: {channel_name} | User: {username} | Survived: {survived}")

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
    if not quotes_enabled:
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

async def handle_sps_command(message):
    if message.guild is None:
        await message.reply("This command can only be used in a server.")
        return

    match = re.search(r'sps\s+(\w+)', message.content.lower())
    if not match:
        await message.reply("Usage: @Bot sps <scissors|paper|stone>")
        return
    user_choice = match.group(1)
    choices = ['scissors', 'paper', 'stone']
    if user_choice not in choices:
        # Unknown option: bot always wins
        bot_choice = random.choice(choices)
        result = f"I win! You chose {user_choice}, I chose {bot_choice}."
        await message.reply(result)
        return
    if sps_rigged:
        # Bot always wins
        win_map = {'scissors': 'stone', 'paper': 'scissors', 'stone': 'paper'}
        bot_choice = win_map[user_choice]
    else:
        bot_choice = random.choice(choices)

    # Determine winner
    if user_choice == bot_choice:
        result = "It's a draw!"
    elif (
        (user_choice == 'scissors' and bot_choice == 'paper') or
        (user_choice == 'paper' and bot_choice == 'stone') or
        (user_choice == 'stone' and bot_choice == 'scissors')
    ):
        result = f"You win! You chose {user_choice}, I chose {bot_choice}."
    else:
        result = f"I win! You chose {user_choice}, I chose {bot_choice}."

    await message.reply(result)

# Functions
def restart():
    try:
        print("Bot is restarting...")
        os.execv(sys.executable, ['python'] + sys.argv)
        
    except Exception as e:
        print(f"Error during bot restart: {e}")

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

def check_files(config, base_path=''):
    missing_files = []

    def scan_config(d, path_prefix=''):
        for key, value in d.items():
            if isinstance(value, dict):
                # Recursively scan nested dictionaries
                scan_config(value, path_prefix)
            elif isinstance(value, str) and ('.' in value or '/' in value or '\\' in value):
                # Check if the value looks like a file path
                file_path = os.path.join(base_path, value)
                if not os.path.exists(file_path):
                    missing_files.append(file_path)

    scan_config(config)

    if missing_files:
        print("\nMissing files:")

        for file in missing_files:
            print(f"  {file}")

        exit()
    else:
        print("\nAll required files are present.")

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
    """Creates a GIF from an image using FFmpeg."""
    palette_path = os.path.join(output_path.rsplit('.', 1)[0] + "_palette.png")
    try:
        os.makedirs('temp', exist_ok=True)

        palettegen_command = [
            'ffmpeg',
            '-i', input_path,
            '-vf', 'palettegen',
            palette_path,
            '-y'
        ]
        if not verbose_creation:
            palettegen_command.insert(1, '-loglevel')
            palettegen_command.insert(2, 'quiet')

        subprocess.run(palettegen_command, check=True)

        gif_creation_command = [
            'ffmpeg',
            '-i', input_path,
            '-i', palette_path,
            '-lavfi', 'paletteuse',
            output_path,
            '-y'
        ]
        if not verbose_creation:
            gif_creation_command.insert(1, '-loglevel')
            gif_creation_command.insert(2, 'quiet')

        subprocess.run(gif_creation_command, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error creating GIF from image: {e}")
        raise
    finally:
        if os.path.exists(palette_path):
            os.remove(palette_path)

def create_gif_from_video(video_path, output_gif_path):
    """Converts a video to a GIF using FFmpeg."""
    try:
        palette_path = os.path.join('temp', os.path.splitext(os.path.basename(video_path))[0] + '_palette.png')

        palettegen_command = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={gifs_frame_limit},palettegen",
            palette_path,
            "-y"
        ]
        if not verbose_creation:
            palettegen_command.insert(1, '-loglevel')
            palettegen_command.insert(2, 'quiet')

        subprocess.run(palettegen_command, check=True)

        gif_command = [
            "ffmpeg",
            "-i", video_path,
            "-i", palette_path,
            "-lavfi", f"fps={gifs_frame_limit},paletteuse",
            output_gif_path,
            "-y"
        ]
        if not verbose_creation:
            gif_command.insert(1, '-loglevel')
            gif_command.insert(2, 'quiet')

        subprocess.run(gif_command, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error creating GIF from video: {e}")
        raise

def compress_gif(gif_path):
    """Compresses a GIF to reduce its size using FFmpeg."""
    compressed_path = os.path.join(gif_path.rsplit('.', 1)[0] + "_compressed.gif")
    palette_path = os.path.join(gif_path.rsplit('.', 1)[0] + "_comppalette.png")
    try:
        palettegen_command = [
            'ffmpeg',
            '-i', gif_path,
            '-vf', f'fps={gifs_frame_limit},palettegen',
            palette_path,
            '-y'
        ]
        if not verbose_creation:
            palettegen_command.insert(1, '-loglevel')
            palettegen_command.insert(2, 'quiet')

        subprocess.run(palettegen_command, check=True)

        gif_compress_command = [
            'ffmpeg',
            '-i', gif_path,
            '-i', palette_path,
            '-filter_complex', f'fps={gifs_frame_limit} [fg]; [fg][1:v] paletteuse',
            compressed_path,
            '-y'
        ]
        if not verbose_creation:
            gif_compress_command.insert(1, '-loglevel')
            gif_compress_command.insert(2, 'quiet')

        subprocess.run(gif_compress_command, check=True)

        return compressed_path
    except subprocess.CalledProcessError as e:
        print(f"Error compressing GIF: {e}")
        raise
    finally:
        if os.path.exists(palette_path):
            os.remove(palette_path)

def clear_temp_directory():
    """Clears all files from the temp directory."""
    temp_folder = 'temp'
    if os.path.exists(temp_folder):
        for file in os.listdir(temp_folder):
            file_path = os.path.join(temp_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

def remove_query_params(url):
    parsed_url = urlparse(url)
    clean_url = urlunparse(parsed_url._replace(query=""))
    return clean_url

def log_telemetry(message):
    if telemetry_enabled:
        timestamp = datetime.now().isoformat()
        log_entry = {timestamp: message}
        
        if os.path.exists(telemetry_file_path):
            with open(telemetry_file_path, 'r', encoding='utf-8') as file:
                telemetry_data = json.load(file)
        else:
            telemetry_data = {"telemetry": {}}
        
        telemetry_data["telemetry"].update(log_entry)
        
        with open(telemetry_file_path, 'w', encoding='utf-8') as file:
            json.dump(telemetry_data, file, indent=4, ensure_ascii=False)

def print_and_log(message):
    print(message)
    log_telemetry(message)

def log_gif_creation(filename, link, guild_name, channel_name, usernames):
    message = f"GIF Created: {filename} | Link: {link} | Server: {guild_name} | Channel: {channel_name} | Users: {usernames}"
    print_and_log(message)
