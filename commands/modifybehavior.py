from bot_helper import send_message, get_user_input, write_json
import json
import time

async def new_command(data):
    msg = data['msg']
    prompts = [
        "What should the command be?",
        "What should the command response be? If you'd like to add an argument, place a {} and it will be replaced with anything that comes after your command.",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    # # Return error if command contains spaces
    # if ' ' in responses[0]:
    #     await send_message(message, 'Command cannot contain spaces.')
    #     return
    
    # commandname = responses[0].split(' ')[0]
    commandname = responses[0]

    # Load commands list
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        commands = behavior['commands']
    
    # Check if command already exists
    if commandname in commands:
        await send_message(data, 'This command already exists.')
        return
    
    # Add command
    commands[commandname] = {
        'type': 'message',
        'response': responses[1]
    }
    write_json(behavior)
    
    await send_message(data, 'Your command has been added.')

async def new_interjection(data):
    msg = data['msg']
    prompts = [
        "What should the prompts be? Separate multiple prompts with commas.",
        "Do the prompts have to take up the whole message? (y/n)",
        "What should the interjection be?",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    interjection_prompts = [prompt.strip().lower() for prompt in responses[0].split(',')]

    # Validate prompts
    visited_prompts = [] # Used to track duplicates
    for prompt in interjection_prompts:

        # Notifying users of bad prompts
        if len(prompt) == 1:
            await send_message(data, 'Prompts must be at least 2 characters long.')
            return
        if not any(char.isalpha() for char in prompt):
            await send_message(data, 'Prompts must contain at least one letter.')
            return
        
        # Removing bad prompts that the user won't miss
        if prompt in visited_prompts:
            interjection_prompts.remove(prompt) # Remove duplicates
        if len(prompt) == 0:
            interjection_prompts.remove(prompt) # Remove empty prompts
        visited_prompts.append(prompt)

    # Validate response length and content
    if len(responses[2]) > 2000:
        await send_message(data, 'Response too long (max 2000 characters).')
        return
    
    if not responses[2].strip():
        await send_message(data, 'Response cannot be empty.')
        return
    
    whole_message = 'y' in responses[1].lower()
    # Pranked
    if not whole_message:
        whole_message = True
        await send_message(data, 'Just kidding. You are not allowed to make non-whole-message interjections.')


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

    write_json(behavior)
    
    await send_message(data, 'Your interjection has been added.')

# Function aliases without underscores, using prefixes, and using close synonyms
command = new_command
interjection = new_interjection
addcommand = new_command
addinterjection = new_interjection
newcommand = new_command
newinterjection = new_interjection
