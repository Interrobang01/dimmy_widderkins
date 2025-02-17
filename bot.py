# This example requires the 'message_content' intent.

import discord
import json
import time
import datetime

# General message function
async def send_message(message, response):
    # Replace @ with @​ to prevent pinging (note zero-width space)
    response = response.replace('@', '@​')

    # Get page argument
    page = message.content.split(' ')[-1]
    if page.isdigit():
        page = int(page)
        if page < 1:
            page = 1
    else:
        page = 1

    # Limit message length to 2000 characters
    response = response[0 + 2000*(page-1):2000 + 2000*(page-1)]

    # # Amount of time to wait before sending the message
    # wait_time = len(response) * 0.05


    # # Start typing indicator
    # async with message.channel.typing():
    #     wait_until_time = time.time() + wait_time
    #     await discord.utils.sleep_until(datetime.datetime.fromtimestamp(wait_until_time))

    await message.channel.send(response)

# Reputation system
def get_reputation(user):
    # Load reputation list
    with open('reputation.json', 'r') as file:
        reputations = json.load(file)
    
    user_id = str(user.id)

    # Check if user has reputation
    if user_id not in reputations:
        # Add user to reputation list
        reputations[user_id] = 50 # Default reputation
        with open('reputation.json', 'w') as file:
            json.dump(reputations, file)
    
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
        reputations[user_id] = 50 # Default reputation
    
    # Change reputation
    reputations[user_id] += amount
    reputations[user_id] = max(0, min(reputations[user_id], 100)) # Clamp reputation to 0-100
    with open('reputation.json', 'w') as file:
        json.dump(reputations, file)

# Ask a series of questions defined in prompts to the user, then return their responses
async def get_user_input(message, prompts):
    cancel_keywords = [
        'cancel',
        'stop',
        'exit',
        'no',
        'quit',
    ]
    user = message.author
    username = user.name
    responses = []
    for prompt in prompts:
        await send_message(message, username + ": " + prompt)
        response = await client.wait_for('message', check=lambda m: m.author == user)
        if response in cancel_keywords:
            await send_message(message, 'Cancelled.')
            return None
        responses.append(response.content)
    return responses


# Command functions
async def command_reputation(message):
    reputation = get_reputation(message.author)
    await send_message(message, f'Your reputation is {reputation}.')

async def new_command(message):
    prompts = [
        "What should the command be?",
        "What should the command response be?",
    ]

    responses = await get_user_input(message, prompts)
    if responses is None:
        return

    # Load commands list
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        commands = behavior['commands']
    
    # Check if command already exists
    if responses[0] in commands:
        await send_message(message, 'This command already exists.')
        return
    
    # Add command
    commands[responses[0]] = {
        'type': 'message',
        'response': responses[1]
    }
    with open('behavior.json', 'w') as file:
        json.dump(behavior, file)
    
    await send_message(message, 'Your command has been added.')

async def new_interjection(message):
    prompts = [
        "What should the prompts be? Separate multiple prompts with commas.",
        "Do the prompts have to take up the whole message? (y/n)",
        "What should the interjection be?",
    ]

    responses = await get_user_input(message, prompts)
    if responses is None:
        return
    
    interjection_prompts = [prompt.strip().lower() for prompt in responses[0].split(',')]

    # Iterate through prompts and remove duplicates and short prompts
    visited_prompts = []
    for prompt in interjection_prompts:
        if len(prompt) < 2:
            await send_message(message, 'Prompts must be at least 2 characters long.')
            return
        if prompt in visited_prompts:
            await send_message(message, 'Prompts must be unique.')
            return
        visited_prompts.append(prompt)

    whole_message = 'y' in responses[1].lower()
    # Pranked
    if not whole_message:
        whole_message = True
        await send_message(message, 'Just kidding. You are not allowed to make non-whole-message interjections.')


    # Load interjections list
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        interjections = behavior['interjections']
    
    # Add interjection
    interjections[time.time()] = {
        'type': 'message',
        'response': responses[2],
        "prompts": interjection_prompts,
        "reputation_range": [
            0,
            100
        ],
        "reputation_change": 0,
        "whole_message": whole_message 
    }
    with open('behavior.json', 'w') as file:
        json.dump(behavior, file)
    
    await send_message(message, 'Your interjection has been added.')

beercount = 99
async def beer(message):
    global beercount
    if beercount == 0:
        await send_message(message, 'No more bottles of beer on the wall, no more bottles of beer. Go to the store and buy some more, 99 bottles of beer on the wall!')
        beercount = 100 # gets subtracted to 99
    elif beercount == 1:
        await send_message(message, '1 bottle of beer on the wall, 1 bottle of beer! Take one down and pass it around, no more bottles of beer on the wall!')
    else:
        await send_message(message, f'{beercount} bottles of beer on the wall, {beercount} bottles of beer! Take one down and pass it around, {beercount-1} bottles of beer on the wall!')
    beercount -= 1

async def help(message):
    # Get commands
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        commands = behavior['commands']
    
    response = 'Commands: '
    for command in commands:
        response += f'\n`!{command}`'
    await send_message(message, response)

async def list_interjections(message):
    # Get interjections
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        interjections = behavior['interjections']
    
    response = 'Interjections: '
    for name, interjection in interjections.items():
        prompts_string = ", ".join(interjection['prompts'])
        response_string = interjection['response']
        response += f'\n{prompts_string} -> {response_string}'
    await send_message(message, response)

command_functions = {
    'newinterjection': new_interjection,
    'newcommand': new_command,
    'beer': beer,
    'help': help,
    'reputation': command_reputation,
    'interjections': list_interjections,
}

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.typing = True

# Don't let the bot ping


client = discord.Client(intents=intents)

# Define event handlers
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    

async def interject(message):

    # Load interjections list
    with open('behavior.json', 'r') as file:
        interjections = json.load(file)['interjections']
    
    # Go through every interjection
    for name, interjection in interjections.items():

        # Skip if user reputation is out of range
        reputation = get_reputation(message.author)
        if reputation <= interjection['reputation_range'][0] or reputation >= interjection['reputation_range'][1]:
            continue
        
        whole_message = interjection['whole_message'] # Whether the prompt must be the entirety of the message

        for prompt in interjection['prompts']:

            # Check if prompt matches message based on whole_message setting
            matches = (prompt.lower() == message.content.lower()) if whole_message else (prompt.lower() in message.content.lower())
            
            if matches:
                print(f"Interjection caused by {message.content} by user {message.author}")
                change_reputation(message.author, interjection['reputation_change'])
                await send_message(message, interjection['response'])

async def run_command(message):
    # Return if not a command
    if not message.content.startswith('!'):
        return
    
    print(f"Command {message.content} by user {message.author}")
    
    command_name = message.content.split(' ')[0][1:]
    
    # Load commands list
    with open('behavior.json', 'r') as file:
        commands = json.load(file)['commands']

    # Check if command exists
    if command_name not in commands:
        await send_message(message, 'Command not found.')
        return

    # Execute command
    command = commands[command_name]
    if command['type'] == 'message':
        await send_message(message, command['response'])
    elif command['type'] == 'function':
        await command_functions[command_name](message)

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author.id == client.user.id:
        return

    await run_command(message) # Run command if possible
    await interject(message) # Interject if possible

    

if __name__ == '__main__':
    with open(r"/home/interrobang/VALUABLE/dimmy_widderkins_token.txt", 'r') as file:
        client.run(file.read())
            
