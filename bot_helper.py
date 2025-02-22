# Helper functions for other scripts

import discord
import json
import time
import sqlite3

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
    user_id = str(user.id)
    reputation = execute_query("SELECT reputation FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    if reputation:
        return reputation['reputation']
    else:
        # Add user to reputation list with default reputation
        execute_query("INSERT INTO users (user_id, reputation) VALUES (?, ?)", (user_id, 100))
        return 100

def change_reputation(user, amount):
    user_id = str(user.id)
    reputation = execute_query("SELECT reputation FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    if reputation:
        new_reputation = max(0, min(reputation['reputation'] + amount, 100))  # Clamp reputation to 0-100
        execute_query("UPDATE users SET reputation = ? WHERE user_id = ?", (new_reputation, user_id))
    else:
        # Add user to reputation list with default reputation
        execute_query("INSERT INTO users (user_id, reputation) VALUES (?, ?)", (user_id, max(0, min(100 + amount, 100))))

def execute_query(query, params=(), fetchone=False):
    conn = sqlite3.connect('/home/interrobang/Scripts/DimmyWidderkins/database.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone() if fetchone else cursor.fetchall()
    conn.commit()
    conn.close()
    if fetchone:
        return dict(result) if result else None
    else:
        return [dict(row) for row in result] if result else []

# Ask a series of questions defined in prompts to the user, then return their responses
async def get_user_input(data, prompts, force_response=False):
    msg = data['msg']
    message_prefix = "" # Prefix to add to prompt message

    # First see if responses are answered in message already, if that's allowed
    if not force_response:
        msg_trimmed = msg.content # A msg.content that we can rip stuff out of 

        # Remove command (if any)
        split_space = msg_trimmed.split() # Splits by whitespace and newline

        if split_space[0].startswith('!'):
            msg_trimmed = msg_trimmed[len(split_space[0]):].strip()

        split_newline = msg_trimmed.split('\n')
        responses = []

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
