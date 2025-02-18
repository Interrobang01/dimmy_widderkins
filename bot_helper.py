# Helper functions for other scripts

import discord
import json
import time

# General message function
async def send_message(data, response):
    msg = data['msg']
    # Replace @ with @​ to prevent pinging (note zero-width space)
    response = response.replace('@', '@​')

    # Get page argument
    page = msg.content.split(' ')[-1]
    if page.isdigit():
        page = int(page)
        if page < 1:
            page = 1
    else:
        page = 1

    # Calculate total number of pages
    total_pages = (len(response) + 1999) // 2000

    # If requested page is beyond total pages, show last page
    if page > total_pages:
        page = total_pages

    # Limit message length to 2000 characters
    response = response[0 + 2000*(page-1):2000 + 2000*(page-1)]

    # Don't send empty messages
    if response == '':
        print("Empty message attempted, returning")
        return

    print(f"Sending message: {response}")
    await msg.channel.send(response)

# Write json
def write_json(data, filename='behavior.json'):
    # Cancel if data is empty, malformed, or over 1MB
    if not data or not isinstance(data, dict) or len(json.dumps(data)) > 1000000:
        return

    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Reputation system
def get_reputation(user):
    # Load reputation list
    with open('reputation.json', 'r') as file:
        reputations = json.load(file)
    
    user_id = str(user.id)

    # Check if user has reputation
    if user_id not in reputations:
        # Add user to reputation list
        reputations[user_id] = 100 # Default reputation
        write_json(reputations, 'reputation.json')
    
    return reputations[user_id]

def change_reputation(user, amount):
    # Load reputation list
    with open('reputation.json', 'r') as file:
        reputations = json.load(file)
    
    # Convert user.id to string for consistent handling
    user_id = str(user.id)
    
    # Check if user has reputation
    if user_id not in reputations:
        # Add user to reputation list
        reputations[user_id] = 100 # Default reputation
    
    # Change reputation
    reputations[user_id] += amount
    reputations[user_id] = max(0, min(reputations[user_id], 100)) # Clamp reputation to 0-100
    write_json(reputations, 'reputation.json')

# Ask a series of questions defined in prompts to the user, then return their responses
async def get_user_input(data, prompts):
    msg = data['msg']
    client = data['client']
    cancel_keywords = [
        'cancel',
        'stop',
        'exit',
        'no',
        'quit',
        '!cancel',
        '!stop',
        '!exit',
        '!no',
        '!quit',
        'shit',
        'fuck',
        'oops'
    ]
    user = msg.author
    username = user.name
    responses = []
    for prompt in prompts:
        await send_message(data, username + ": " + prompt)
        response = await client.wait_for('message', check=lambda m: m.author == user)
        if response.content in cancel_keywords:
            await send_message(data, 'Cancelled.')
            return None
        responses.append(response.content)
    return responses
