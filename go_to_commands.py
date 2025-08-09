# yells at people to go to #commands when they use too many commands in #general or others
# when too many bot messages are sent within 60 seconds, send the message

import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
from bot_helper import send_message

commands_tracker = []
last_yell_time = 0

brook_id = 1224881201379016825
commands_channel_id = 1224889071885881425

def update_tracker():
    current_time = datetime.now()

    global commands_tracker

    # Remove entries older than 60 seconds
    current_time = datetime.now()
    commands_tracker = [t for t in commands_tracker if t > current_time - timedelta(seconds=60)]

def is_user_bot(user):
    return user.bot

async def on_message(data):
    message = data['msg']
    client = data['client']
    
    current_time = datetime.now()

    global commands_tracker, last_yell_time

    if last_yell_time and current_time - timedelta(minutes=15) < last_yell_time:
        return  # Don't process if the last yell was too recent
    
    if message.author == client.user:
        return # Ignore messages from the bot itself
    
    if message.guild is None or message.guild.id != brook_id:
        return

    if message.channel.id == commands_channel_id:
        return

    if is_user_bot(message.author):
        update_tracker()

        
        # Add the current command with timestamp
        commands_tracker.append(current_time)

        # Check if they have sent too many commands in the last 60 seconds
        if len(commands_tracker) >= 10:
            if message.content[0] != '!':
                return # only yell when invoked
            await send_message(data, f"# GO TO #COMMANDS!!!!!!!!!")
            commands_tracker.clear()
            last_yell_time = current_time.timestamp()
