import json
from bot_helper import send_message, get_reputation, write_json
import asyncio
from datetime import datetime, timedelta

# Dictionary to keep track of calls
call_tracker = {}
uncall_tracker = {}

nuke_blacklist = [
    1389395510929916007
]

def update_call_trackers():
    global call_tracker, uncall_tracker
    current_time = datetime.now()

    # Remove entries older than 15 seconds
    call_tracker = {k: v for k, v in call_tracker.items() if v > current_time - timedelta(seconds=15)}
    uncall_tracker = {k: v for k, v in uncall_tracker.items() if v > current_time - timedelta(seconds=15)}

async def launch_nukes(data):
    global call_tracker
    msg = data['msg']
    current_time = datetime.now()

    if msg.guild.id in nuke_blacklist:
        await send_message(data, "https://tenor.com/view/bunny-rabbit-golf-hole-in-one-gif-821257481761453386")
        return

    update_call_trackers()

    if msg.author.id in call_tracker:
        await send_message(data, "You did that already.")
        return

    # Add current call
    call_tracker[msg.author.id] = current_time

    # Check if there are 3 different senders in the last 15 seconds
    vote = len(call_tracker) - len(uncall_tracker)
    if vote >= 3:
        await send_message(data, "Nuclear weapons launched. May God have mercy on our souls.")
        await send_message(data, "https://tenor.com/view/nuclear-catastrophic-disastrous-melt-down-gif-13918708")
        await send_message(data, "OH THE HUMANITY!!!")

        # you know who you are
        # Get server name and channel name and print them
        server_name = msg.guild.name if msg.guild else "Direct Message"
        channel_name = msg.channel.name if msg.channel else "Direct Message"
        print(f"Server: {server_name}, Channel: {channel_name}")
        # Get ID so we can blacklist this if needed
        print(f"Message ID: {msg.id}, Author: {msg.author.name}#{msg.author.discriminator} ({msg.author.id})")
        # channel ID too
        print(f"Channel ID: {msg.channel.id}")
        # also guild ID
        print(f"Guild ID: {msg.guild.id if msg.guild else 'N/A'}")

        # Code to shut down the bot
        # await data['client'].close()

        # Add guild id to blacklist.json if it doesn't exist (different from nuke_blacklist)
        with open('blacklist.json', 'r+') as file:
            blacklist = json.load(file)
            if str(msg.guild.id) not in blacklist:
                blacklist.append(str(msg.guild.id))
                # Write updated blacklist to file
                write_json(blacklist, 'blacklist.json')
                print("done, added to blacklist.json")
        return
    else:
        await send_message(data, f"Key turned. {3 - vote} more keys needed to launch nukes.")

async def unlaunch_nukes(data):
    global call_tracker, uncall_tracker
    msg = data['msg']
    current_time = datetime.now()

    if msg.guild.id in nuke_blacklist:
        await send_message(data, "https://tenor.com/view/bunny-rabbit-golf-hole-in-one-gif-821257481761453386")
        return

    update_call_trackers()

    if msg.author.id in uncall_tracker:
        await send_message(data, "You did that already.")
        return

    # Add current uncall
    uncall_tracker[msg.author.id] = current_time

    # Check if there are 3 different senders in the last 15 seconds
    vote = len(call_tracker) - len(uncall_tracker)
    if vote <= -3:
        await send_message(data, "Happiness missiles launched. May Satan have mercy on our souls.")
        await send_message(data, "https://tenor.com/view/pixelmoo-moodeng-uponly-up-only-pump-it-gif-18134094526770564575")

        # clear blacklist.json (different from nuke_blacklist)
        with open('blacklist.json', 'r+') as file:
            write_json([], 'blacklist.json')
        return
    else:
        await send_message(data, f"Tactical Stanislav deployed. {3 + vote} more Petrovs needed to unlaunch nukes.")

# Function aliases without underscores, using prefixes, and using close synonyms
nukes = launch_nukes
launchnukes = launch_nukes
nuke = launch_nukes
launchnuke = launch_nukes
unukes = unlaunch_nukes
unlaunchnukes = unlaunch_nukes
unuke = unlaunch_nukes
unlaunchnuke = unlaunch_nukes
