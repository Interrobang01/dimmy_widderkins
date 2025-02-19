# Helper functions for other scripts

import discord
import json
import time

# General message function
async def send_message(data, response, reply=False):
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
    if reply:
        await msg.reply(response)
    else:
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
async def get_user_input(data, prompts, force_response=False):
    msg = data['msg']
    message_prefix = "" # Prefix to add to prompt message

    # First see if responses are answered in message already, if that's allowed
    if not force_response:
        msg_trimmed = msg.content # A msg.content that we can rip stuff out of 

        # Remove command (if any)
        split_space = msg_trimmed.split() # Splits by whitespace and newline
        print(f"spliot space are first {split_space}")

        if split_space[0].startswith('!'):
            msg_trimmed = msg_trimmed[len(split_space[0]):].strip()

        print(f"spliot space are {split_space}")

        split_newline = msg_trimmed.split('\n')
        responses = []

        print(f"spliot newlkine are {split_newline}")

        # User put the arguments on lines after command
        if split_newline[0] == '' and len(split_newline) > 1:
            split_newline.pop(0)
        
        if len(split_newline) >= len(prompts):
            responses = split_newline[0:len(prompts)]
            return responses
        
        if split_newline[0] != '':
            message_prefix = "Not enough arguments.\n"

    print(f"responses are {responses}")
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
    while len(responses) < len(prompts):
        await send_message(data, message_prefix + username + ": " + "Please answer the following questions (separate answers with newlines): " + '\n- ' + "\n- ".join(prompts), True)
        message_prefix = ""
        response = await client.wait_for('message', check=lambda m: m.author == user)
        responses = response.content.split('\n')
        if response.content.lower() in cancel_keywords:
            await send_message(data, 'Cancelled.')
            return None
        
        if len(responses) < len(prompts):
            message_prefix = "Not enough arguments. Try again or say 'cancel' to cancel.\n"

    return responses
