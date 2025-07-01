import json
import random
import discord
import asyncio
from bot_helper import send_message

# Track whether the bot is currently watching something
currently_watching = ""

def split_opted_members():
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        opted = behavior.get('opted', {})
    opted_members = list(opted.keys())
    random.shuffle(opted_members)
    mid_point = len(opted_members) // 2
    group1 = opted_members[:mid_point]
    group2 = opted_members[mid_point:]
    return (group1, group2)

async def universe(client):
    global currently_watching
    original_status = client.status
    possible_things_to_watch = [
        "the horizon",
        "the stars",
        "the sunset",
        "the clouds",
        "the waves",
        "you",
    ]
    thing = random.choice(possible_things_to_watch)
    currently_watching = thing
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name=thing)
    )
    await asyncio.sleep(5)
    await client.change_presence(status=original_status)
    currently_watching = ""

async def you(data):
    messages = [
        "I'm watching",
        2,
        "oops didn't mean that haha",
        "it was a joke",
        "please don't be alarmed",
        "I just wanted to say hi",
        "how are you doing today?",
        "I hope you're having a great day!",
        2,
        "I just wanted to let you know that I'm here for you",
        "if you need anything, just let me know",
        "I'm always here to help",
        "I just wanted to say that I appreciate you",
        "you're doing great",
        2,
        "keep up the good work",
        "you're amazing",
        "I just wanted to let you know that I care about you",
        "you're not alone",
        2,
        "I'm always here for you"
    ]
    for message in messages:
        if isinstance(message, int):
            await asyncio.sleep(message)
        else:
            await send_message(data, message)
            await asyncio.sleep(0.5)
