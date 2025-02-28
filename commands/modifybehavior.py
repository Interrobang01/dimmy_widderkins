from bot_helper import send_message, get_user_input, write_json
import json
import time
from commands.markov import _infer_markov_chat
from ollama_handler import ask_ollama
import random

# Returns fixed prompts and response along with error message if any
def validate_interjection(data, prompts, response):
    visited_prompts = [] # Used to track duplicates
    for prompt in prompts:

        # Notifying users of bad prompts
        if len(prompt) == 1:
            prompts, response, 'Prompts must be at least 2 characters long.'
        if not any(char.isalpha() for char in prompt):
            return prompts, response, 'Prompts must contain at least one letter.'
        
        # Removing bad prompts that the user won't miss
        if prompt in visited_prompts:
            prompts.remove(prompt) # Remove duplicates
        if len(prompt) == 0:
            prompts.remove(prompt) # Remove empty prompts
        if not prompt.strip():
            prompts.remove(prompt) # Remove whitespace prompts
        visited_prompts.append(prompt)

    # Validate response length and content
    if len(response) > 2000:
        return prompts, response, 'Response too long (max 2000 characters).'
    
    if not response.strip():
        return prompts, response, 'Response cannot be empty.'
    
    return prompts, response, None

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

    # Validate
    interjection_prompts, responses[2], error = validate_interjection(data, interjection_prompts, responses[2])
    if error:
        await send_message(data, error)
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

async def generate_interjection(data):
    msg = data['msg']
    prompts = [
        "What should the prompt be? Only one prompt is supported as of now.",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    interjection_prompt = responses[0].strip().lower()
    
    # Generate multiple Markov responses
    markov_responses = [_infer_markov_chat(interjection_prompt) for _ in range(5)]
    markov_responses = [r for r in markov_responses if r]
    markov_responses = list(set(markov_responses))

    # Create context from Markov responses
    context = "Previous similar responses:\n"
    context += "\n".join(f"- {r}" for r in markov_responses[:5]) + "\n" if markov_responses else ""
    ai_response = await ask_ollama(
        f"Please generate a short and snappy response for: {interjection_prompt}. Do not say anything other than the response.\n{context}",
        model="gem:latest",
        host="http://localhost:11434"
    )
    ai_response = ai_response[:2000]
    
    responses = []
    if markov_responses:
        responses.extend(markov_responses)
    if ai_response:
        responses.append(ai_response.strip())
    
    if not responses:
        await send_message(data, "Sorry, I couldn't generate a response.")
        return

    # Get user choice    
    user_prompt = "Enter the number to add the response as an interjection"
    user_prompt += "\nGenerated these responses:"
    
    for i, response in enumerate(responses):
        user_prompt += f"\n#{i+1}. {interjection_prompt} -> {response}"

    
    # Use only option if it's the only option
    choice = None
    if len(responses) == 1 and False: # Disable this for now
        choice = 1
    else:
        # Use get_user_input instead of manual input
        user_responses = await get_user_input(data, [user_prompt], True) # True is for not reusing this message as choice
        if user_responses is None:
            return

        choice = user_responses[0]
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(responses):
            await send_message(data, "Invalid selection.")
            return
        
    chosen_response = responses[int(choice)-1]

    # Validate
    _, chosen_response, error = validate_interjection(data, [interjection_prompt], chosen_response)
    if error:
        await send_message(data, error)
        return

    # Load interjections list
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        interjections = behavior['interjections']
    
    # Add interjection
    interjections[time.time()] = {
        "type": "message",
        "response": chosen_response,
        "prompts": [interjection_prompt],
        "reputation_range": [0, 100],
        "reputation_change": 0,
        "whole_message": True
    }

    write_json(behavior)
    
    await send_message(data, 'Your randomized interjection has been added.')

# Function aliases without underscores, using prefixes, and using close synonyms
command = new_command
interjection = new_interjection
addcommand = new_command
addinterjection = new_interjection
newcommand = new_command
newinterjection = new_interjection
geninterjection = generate_interjection
geninter = generate_interjection
ijgen = generate_interjection
generateinterjection = generate_interjection
