import json
import random
import discord
import asyncio

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
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name=thing)
    )
    if thing == "you":
        await you(client)
    await asyncio.sleep(5)
    await client.change_presence(status=original_status)

async def you(client):
    for guild in client.guilds:
        for channel in guild.text_channels:
            try:
                await channel.send("I'm watching")
                await asyncio.sleep(2)
                await channel.send("oops didn't mean that haha")
                await channel.send("it was a joke")
                await channel.send("please don't be alarmed")
                await channel.send("I just wanted to say hi")
                await channel.send("how are you doing today?")
                await channel.send("I hope you're having a great day!")
                await asyncio.sleep(2)
                await channel.send("I just wanted to let you know that I'm here for you")
                await channel.send("if you need anything, just let me know")
                await channel.send("I'm always here to help")
                await channel.send("I just wanted to say that I appreciate you")
                await channel.send("you're doing great")
                await asyncio.sleep(2)
                await channel.send("keep up the good work")
                await channel.send("you're amazing")
                await channel.send("I just wanted to let you know that I care about you")
                await channel.send("you're not alone")
                await asyncio.sleep(10)
                await channel.send("I'm always here for you")
            except Exception:
                continue
