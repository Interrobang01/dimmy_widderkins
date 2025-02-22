from bot_helper import send_message, get_reputation
import asyncio
from datetime import datetime, timedelta

# Dictionary to keep track of calls
call_tracker = {}

async def launch_nukes(data):
    global call_tracker
    msg = data['msg']
    current_time = datetime.now()

    # Remove entries older than 5 seconds
    call_tracker = {k: v for k, v in call_tracker.items() if v > current_time - timedelta(seconds=5)}

    # Add current call
    call_tracker[msg.author.id] = current_time

    # Check if there are 3 different senders in the last 5 seconds
    if len(call_tracker) >= 3:
        await send_message(data, "Nuclear weapons launched. May God have mercy on our souls.")
        await send_message(data, "https://tenor.com/view/nuclear-catastrophic-disastrous-melt-down-gif-13918708")
        # Code to shut down the bot
        await data['client'].close()
    else:
        await send_message(data, f"Key turned. {3 - len(call_tracker)} more keys needed to launch nukes.")

# Function aliases without underscores, using prefixes, and using close synonyms
nukes = launch_nukes
launchnukes = launch_nukes
