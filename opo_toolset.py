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
        "the moon",
        "the sunset",
        "the sunrise",
        "the clouds",
        "the birds",
    ]
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(possible_things_to_watch))
    )
    await asyncio.sleep(5)
    await client.change_presence(status=original_status)
