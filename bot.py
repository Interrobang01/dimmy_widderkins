# This example requires the 'message_content' intent.

import discord
import subprocess
import json
import time
import datetime
from brook import Brook
from bot_helper import send_message, get_user_input, write_json, get_reputation, change_reputation
import random
import asyncio
from ollama_handler import ask_ollama
import subprocess
import sys
import requests
import emoji

# # Rate limiting system
# message_timestamps = []
# self_destruct = False
# async def log_message(message):
#     if self_destruct: return

#     # Keep track of message timestamps
#     current_time = time.time()
#     message_timestamps.append(current_time)
    
#     # Remove timestamps older than 5 seconds
#     while message_timestamps and message_timestamps[0] < current_time - 5:
#         message_timestamps.pop(0)
    
#     # Check if we've sent more than 5 messages in 5 seconds
#     if len(message_timestamps) > 5:
#         self_destruct = True
#         print("Rate limit exceeded. Shutting down bot.")
#         await message.channel.send("TOO MANY MESSAGES INITIATING SELF-DESTRUCT SEQUENCE")
#         await message.channel.send("5")
#         await message.channel.send("4")
#         await message.channel.send("3")
#         await message.channel.send("2")
#         await message.channel.send("1")
#         await message.channel.send("https://tenor.com/bko4E.gif")
#         await client.close()
#         return

# Markov model functions
def load_markov_model_from_json(file_path,file_path_chat):
    global markov_model
    global markov_model_chat
    with open(file_path, 'r', encoding='utf-8') as json_file:
        markov_model = json.load(json_file)
    with open(file_path_chat, 'r', encoding='utf-8') as json_file:
        markov_model_chat = json.load(json_file)

load_markov_model_from_json(r'markov_model_notw.json', r'markov_model_chat_notw.json')

def get_next_word(current_word):
    if not current_word: current_word = random.choice(list(markov_model))
    if current_word in markov_model:
        next_words = markov_model[current_word]
        total = sum(next_words.values())
        rand_val = random.randint(1, total)
        cumulative = 0
        for word, count in next_words.items():
            cumulative += count
            if rand_val <= cumulative:
                return word
    return None

def get_next_word_chat(current_message):
    keys = markov_model_chat.keys()
    
    # Gets skipped if current_message is already inside
    i = 0
    while current_message not in markov_model_chat:
        i += 1

        # Look for shortest message containing current_message
        matching_keys = []
        for key in keys:
            if current_message in key:
                matching_keys.append(key)
        
        if len(matching_keys) != 0:
            current_message = min(matching_keys, key=lambda x: len(x[0]))

        # Shorten if still not found
        if current_message not in markov_model_chat:
            split = current_message.split(' ')

            # Remove last word to increase match chance
            current_message = ' '.join(split[:-1])
            
            # Return if we've cut away the entire message
            if len(split) == 0:
                return None
            
    print(f"Found in {i} iterations")
        


    if current_message in markov_model_chat:
        next_messages = markov_model_chat[current_message]
        total = sum(next_messages.values())
        rand_val = random.randint(1, total)
        cumulative = 0
        for message, count in next_messages.items():
            cumulative += count
            if rand_val <= cumulative:
                return message
    return None

# Prediction market functions
async def calculate_market_probability_change(data, market, amount):
    msg = data['msg']
    current_liquidity = market['liquidity']
    current_probability = market['probability']
    
    # Calculate new probability with the same formula but clamp between 0 and 1
    new_probability = (current_liquidity * current_probability + amount) / (current_liquidity + abs(amount))
    
    # Clamp probability between 0 and 1
    new_probability = max(0.0, min(1.0, new_probability))
    
    return new_probability

async def market_resolve(data):
    msg = data['msg']

    prompts = [
        "What is the market name?",
        "What are you resolving it to? (y/n)",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    market_name, resolution_str = responses
    resolution = 'y' in resolution_str.lower()

    # Get market
    with open('markets.json', 'r') as file:
        markets = json.load(file)
    
    if market_name not in markets:
        await send_message(data, "Market not found.")
        return
    
    market = markets[market_name]
    if str(msg.author.id) != market['creator']:
        await send_message(data, "You cannot resolve markets you do not own!")
        return
    
    market['resolved'] = True
    market['resolution'] = resolution

    liquidity_remaining = market['liquidity']
    
    # Pay shareholders
    for user_id, shares in market['user_shares'].items():
        payout = abs(shares) if (resolution and shares > 0) or (not resolution and shares < 0) else 0
        if payout > 0:
            if payout > liquidity_remaining:
                await send_message(data, f"Not enough liquidity remaining to pay user {user_id}!")
                continue
            await brook.pay(user_id, payout, msg.channel)
            liquidity_remaining -= payout

    # Pay remaining liquidity to market creator
    if liquidity_remaining > 0:
        await brook.pay(market['creator'], liquidity_remaining, msg.channel)

    write_json(markets, 'markets.json')

async def market_buy(data):
    msg = data['msg']

    prompts = [
        "What is the market name?",
        "How many shares do you want to buy?",
    ]
    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    # Ensure amount is an integer
    try:
        responses[1] = int(responses[1])
    except ValueError:
        await send_message(data, "Amount must be an integer.")
        return
    
    market_name, amount = responses
    # Get market
    with open('markets.json', 'r') as file:
        markets = json.load(file)
    
    if market_name not in markets:
        await send_message(data, "Market not found.")
        return
    
    market = markets[market_name]
    if market['resolved']:
        await send_message(data, "Market is already resolved.")
        return
    
    # Calculate price
    if amount > 0:
        price = market['probability'] * amount
    else:
        price = (1 - market['probability']) * abs(amount)

    # Request money
    future = await brook.request_payment(msg.author, price, msg.channel, "Market shares for market '" + market_name + "'")
    try:
        await future
    except Exception as e:
        await send_message(data, "Payment request denied. Purchase cancelled.")
        return
    
    user_id = str(msg.author.id)

    # Update user_shares
    if user_id not in market['user_shares']:
        market['user_shares'][user_id] = amount
    else:
        market['user_shares'][user_id] += amount
    
    # Calculate new probability
    new_probability = await calculate_market_probability_change(data, market, amount)

    # Update market
    market['liquidity'] += price
    market['probability'] = new_probability
    write_json(markets, 'markets.json')

    await send_message(data, f"Purchace made. New probability: {new_probability * 100}%")


# 1a. Asks the following prompts:
#     "What is the market name?",
#     "What is the starting liquidity?",
#     "What is the initialized probability?",
# 1b. Requests payment from the user equal to the starting liqudity, cancelling if payment is rejected
# 1c. Reserves that money for the market
# 1d. Creates a market message
async def new_market(data):
    msg = data['msg']

    await send_message(data, "WARNING: super buggy and infinite money exploits abound. Ye've been warned!")

    prompts = [
        "What is the market name/resolution criteria?",
        "What is the starting liquidity?",
        "What is the initialized probability?",
    ]
    responses = await get_user_input(data, prompts)
    if not responses:
        return
    
    # Ensure liquidity/probability is a integer/number
    try:
        responses[1] = int(responses[1])
        probability_str = responses[2]
        if probability_str.endswith('%'):
            probability_str = probability_str[:-2]
        responses[2] = float(probability_str)
    except ValueError:
        await send_message(data, "Liquidity must be an integer and probability must be a number.")
        return
    
    market_name, starting_liquidity, initialized_probability = responses

    # Convert to fraction
    if initialized_probability >= 1:
        initialized_probability = initialized_probability / 100

    # Request payment from the user equal to the starting liquidity
    future = await brook.request_payment(msg.author, starting_liquidity, msg.channel, "Market liquidity for market '" + market_name + "'")

    # Cancel if request is denied
    try:
        await future
    except Exception as e:
        await send_message(data, "Payment request denied. Market creation cancelled.")
        return



    # Send a market message with the market name, starting liquidity, and initialized probability
    # The message has a "Buy" button that allows users to buy shares in the market
    # The message has a "Resolve" button that allows the market creator to resolve the market
    market = {
        "name": market_name,
        "starting_liquidity": starting_liquidity,
        "initialized_probability": initialized_probability,
        "liquidity": starting_liquidity,
        "probability": initialized_probability,
        "user_shares": {},
        "creator": str(msg.author.id),
        "resolved": False,
        "resolution": None,
    }

    with open('markets.json', 'r') as file:
        markets = json.load(file)
    
    # Check duplicate market names
    if market_name in markets:
        await send_message(data, "Market name already exists.")
        return
    
    markets[market_name] = market
    write_json(markets, 'markets.json')

    await send_message(data, "New market created: " + market_name)

async def view_markets(data):
    msg = data['msg']
    # Get markets
    with open('markets.json', 'r') as file:
        markets = json.load(file)
    
    response = 'Markets: '
    for market in markets:
        response += f'\n{market}: {markets[market]["probability"] * 100}%'
    await send_message(data, response)

# Command functions
async def command_reputation(data):
    msg = data['msg']
    reputation = get_reputation(msg.author)
    await send_message(data, f'Your reputation is {reputation}.')

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

async def remove_command_or_interjection(data):
    msg = data['msg']

    prompts = [
        "What's the prompt or command name of the thing you want to remove?",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return

    # Get target name from message
    target = responses[0].lower()

    # Load behavior file
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)

    # Find matching commands and interjections
    matching_commands = [(name, cmd) for name, cmd in behavior['commands'].items() 
                        if name.lower() == target and cmd.get('type') != 'function']
    matching_interjections = [(id, interj) for id, interj in behavior['interjections'].items() 
                            if any(prompt.lower() == target for prompt in interj['prompts'])]

    if not matching_commands and not matching_interjections:
        await send_message(data, "No matching commands or interjections found.")
        return


    # Build list of options
    options = []
    response = "Found these matches:\n"
    
    for i, (name, cmd) in enumerate(matching_commands):
        options.append(('command', name))
        response += f"{i+1}. Command: !{name} -> {cmd['response'][:100]}...\n"

    for i, (id, interj) in enumerate(matching_interjections, start=len(matching_commands)+1):
        options.append(('interjection', id))
        response += f"{i}. Interjection: {', '.join(interj['prompts'])} -> {interj['response'][:100]}...\n"

    response += "\nEnter the number to remove:"
    
    # Use only option if it's the only option
    choice = None
    if len(matching_commands) + len(matching_interjections) == 1:
        choice = 1
    else:
        # Use get_user_input instead of manual input
        responses = await get_user_input(data, [response], True) # True is for not reusing this message as choice
        if responses is None:
            return

        choice = responses[0]
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(options):
            await send_message(data, "Invalid selection.")
            return

    # Remove selected item
    selected = options[int(choice)-1]
    if selected[0] == 'command':
        removed_item = behavior['commands'].pop(selected[1])
        removed_type = 'Command'
        removed_name = selected[1]
    else:
        removed_item = behavior['interjections'].pop(selected[1])
        removed_type = 'Interjection'
        removed_name = ', '.join(removed_item['prompts'])

    write_json(behavior)
    await send_message(data, f"{removed_type} '{removed_name}' removed successfully.")

beercount = 99
async def beer(data):
    msg = data['msg']
    global beercount
    if beercount == 0:
        await send_message(data, 'No more bottles of beer on the wall, no more bottles of beer. Go to the store and buy some more, 99 bottles of beer on the wall!')
        beercount = 100 # gets subtracted to 99
    elif beercount == 1:
        await send_message(data, '1 bottle of beer on the wall, 1 bottle of beer! Take one down and pass it around, no more bottles of beer on the wall!')
    else:
        await send_message(data, f'{beercount} bottles of beer on the wall, {beercount} bottles of beer! Take one down and pass it around, {beercount-1} bottles of beer on the wall!')
    beercount -= 1

async def help(data):
    msg = data['msg']
    # Get commands
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        commands = behavior['commands']
    
    response = 'Commands: '
    for command in commands:
        response += f'\n`!{command}`'
    await send_message(data, response)

async def list_interjections(data):
    msg = data['msg']
    # Get interjections
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        interjections = behavior['interjections']
    
    response = 'Interjections: '
    for name, interjection in interjections.items():
        prompts_string = ", ".join(interjection['prompts'])
        response_string = interjection['response']
        response += f'\n{prompts_string} -> {response_string}'
    await send_message(data, response)

async def opt_out(data):
    msg = data['msg']
    if get_reputation(msg.author) >= 100:
        await send_message(data, "You are already opted out.")
        return
    change_reputation(msg.author, 100)
    await send_message(data, "You have opted back out.")

async def opt_in(data):
    msg = data['msg']
    if get_reputation(msg.author) < 100:
        await send_message(data, "You are already opted in.")
        return
    change_reputation(msg.author, -100)
    await send_message(data, "You have opted in.")

# Use Brook.request_payment
async def pay_command(data):
    msg = data['msg']
    user = msg.author
    amount = 100  # Example amount
    request_channel = msg.channel
    description = "please donate to help fund my medication"
    
    await brook.request_payment(user, amount, request_channel, description)

async def markov(data):
    msg = data['msg']

    length = 100 # Default length of response in characters

    next_word = msg.content.split(' ')[-1]
    if next_word.isdigit():
        length = int(next_word)
        next_word = msg.content.split(' ')[-2]

    response = ""
    while next_word != None and len(response) < length:
        next_word = get_next_word(next_word)
        if next_word != None:
            response += str(next_word) + ' '
            
    
    await send_message(data, response)

last_markov_message = ""
async def markov_chat(data):
    global last_markov_message
    print(f"last markov message is {last_markov_message}")
    print(f"last markov message is now {last_markov_message}")
    msg = data['msg']

    split = msg.content.split(' ')
    # Remove command if it exists
    if msg.content.startswith('!'):
        split = split[1:]

    input_message = ' '.join(split)
    next_message = input_message

    if len(split) == 0 and last_markov_message:
        next_message = last_markov_message

    response = ""
    #while next_message is not None:
    next_message = get_next_word_chat(next_message)
    response += str(next_message) + ' '
            
    last_markov_message = response.strip()
    print(last_markov_message)
    # Calculate typing delay based on response length
    typing_delay = min(len(response) * 0.01, 3)  # Max delay of 3 seconds

    # Trigger typing indicator
    async with msg.channel.typing():
        await asyncio.sleep(typing_delay)
    
    await send_message(data, response, True) # True causes bot to reply

async def react(data):
    msg = data['msg']

    prompts = [
        'What do you want me to react with?',
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    requested_reaction = [prompt.strip().lower() for prompt in responses[0].split(',')][0]

    if msg.reference:
        referenced_message = await msg.channel.fetch_message(msg.reference.message_id)
        for reaction in referenced_message.reactions:
            if str(reaction.emoji) == requested_reaction:
                async for reactor in reaction.users():
                    if reactor.id == data['client'].user.id:
                        # User has reacted, so remove their reaction
                        await referenced_message.remove_reaction(requested_reaction, data['client'].user) # Remove reaction if already there
                        return
        await referenced_message.add_reaction(requested_reaction)  # React
        return

async def net_command(data):
    msg = data['msg']
    args = msg.content.split()[1:]  # Remove !net

    if str(msg.author.id) != '658073528888721408':
        await send_message(data, "Wait, maybe dont let literally everyone make network requests from my machine")
        return
    
    if not args:
        await send_message(data, "Usage: !net <ip/domain> [-d]")
        return
        
    target = args[0]
    download_flag = "-d" in args
    
    try:
        # Ping test
        if not download_flag:
            if sys.platform == "win32":
                result = subprocess.run(['ping', '-n', '4', target], 
                                     capture_output=True, text=True)
            else:
                result = subprocess.run(['ping', '-c', '4', target], 
                                     capture_output=True, text=True)
            await send_message(data, f"```\n{result.stdout}```")
            return

        # Download and display content
        if download_flag:
            # Ensure URL has protocol
            if not target.startswith(('http://', 'https://')):
                target = 'http://' + target
                
            response = requests.get(target, timeout=10)
            content = response.text[:1500]  # Limit content length
            await send_message(data, f"Content from {target}:\n```\n{content}...\n```")
            
    except Exception as e:
        await send_message(data, f"Error: {str(e)}")

command_functions = {
    'newinterjection': new_interjection,
    'newcommand': new_command,
    'addinterjection': new_interjection,
    'addcommand': new_command,
    'beer': beer,
    'net': net_command,
    'help': help,
    'reputation': command_reputation,
    'interjections': list_interjections,
    'optout': opt_out,
    'optin': opt_in,
    'remove': remove_command_or_interjection,
    'pay': pay_command,
    'newmarket': new_market,
    'addmarket': new_market,
    'viewmarkets': view_markets,
    'marketbuy': market_buy,
    'marketresolve': market_resolve,
    'markov': markov,
    'markovchat': markov_chat,
    'react': react,
}

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.typing = True

client = discord.Client(intents=intents)

# Define event handlers

transport_channel = None  # This needs to be set after client is ready
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    global transport_channel
    transport_channel = client.get_channel(1322717023351865395)
    global brook
    brook = Brook(transport_channel, client)

    

async def interject(data):
    msg = data['msg']
    # Load interjections list
    with open('behavior.json', 'r') as file:
        interjections = json.load(file)['interjections']
    
    # Track matching interjections
    matching_interjections = []

    # Go through every interjection
    for _, interjection in interjections.items():
        # Skip if user reputation is out of range
        reputation = get_reputation(msg.author)
        if reputation < interjection['reputation_range'][0]-1 or reputation > interjection['reputation_range'][1]-1:
            continue
        
        whole_message = interjection['whole_message']

        for prompt in interjection['prompts']:
            # Convert message to lowercase
            message_lower = msg.content.lower()
            prompt_lower = prompt.lower()

            # Check if prompt matches message based on whole_message setting
            # Create a version of the message where non-letters are removed
            def clean_text(text):
                # Preserve mentions but clean other parts
                words = []
                current_word = ''
                i = 0
                while i < len(text):
                    if text[i].isalpha():
                        current_word += text[i]
                    else:
                        if current_word:
                            words.append(current_word)
                            current_word = ''
                    i += 1
                if current_word:
                    words.append(current_word)
                return words

            message_words = clean_text(message_lower)
            prompt_words = clean_text(prompt_lower)

            # Continue if prompt_words is empty
            if not prompt_words:
                continue
            
            if whole_message:
            # Check if both message and prompt have same words
                matches = message_words == prompt_words
            else:
                # Check if prompt words appear as a consecutive sequence in message words
                if len(prompt_words) > len(message_words):
                    matches = False
                else:
                    matches = any(prompt_words == message_words[i:i+len(prompt_words)]
                        for i in range(len(message_words) - len(prompt_words) + 1))

            if matches:
                matching_interjections.append((prompt, interjection))

    # If we found matches, respond to the one with the longest prompt
    if matching_interjections:
        longest_prompt, chosen_interjection = max(matching_interjections, key=lambda x: len(x[0]))
        print(f"Interjection caused by {msg.content} by user {msg.author}")
        change_reputation(msg.author, chosen_interjection['reputation_change'])
        await send_message(data, chosen_interjection['response'])

async def run_command(data):
    msg = data['msg']
    # Return if not a command
    if not msg.content.startswith('!'):
        return False
    
    print(f"Command {msg.content} by user {msg.author}")
    
    # Get full command string without the ! prefix
    full_command = msg.content[1:].strip()
    
    # Load commands list
    with open('behavior.json', 'r') as file:
        commands = json.load(file)['commands']

    # Find the longest matching command
    command_name = None
    for cmd in commands:
        if full_command.lower().startswith(cmd.lower()):
            # Update if this is the longest matching command so far
            if command_name is None or len(cmd) > len(command_name):
                command_name = cmd

    # Check if command exists
    if command_name is None:
        await send_message(data, 'Command not found.')
        return True

    # Get the input parameter (everything after the command)
    input_param = full_command[len(command_name):].strip()

    # Execute command
    command = commands[command_name]
    if command['type'] == 'message':
        response = command['response']
        if '{}' in response:
            response = response.replace('{}', input_param)
        await send_message(data, response)
    elif command['type'] == 'function':
        try:
            await command_functions[command_name](data)
        except KeyError:
            await send_message(data, 'Interrobang screwed up and forgot to bind this function. Or the keyerror is some unrelated bug.')
            await send_message(data, command['response'])
    
    return True

last_reaction = "🤪"
@client.event
async def on_message(msg):
    # Ignore messages from the bot itself
    if msg.author.id == client.user.id:
        return
    
    data = {'msg': msg, 'client': client}
    
    await brook.on_message(msg)

    if 'dimmy' in msg.content.lower() or 'widderkins' in msg.content.lower():
        # Ollama processing
        response = await ask_ollama(msg.content, last_reaction)
        response = response.strip()[0]
        print(f"Ollama response: {response}")
        if response in emoji.EMOJI_DATA:
            last_reaction = response
            #await msg.add_reaction('<:upvote:1309965553770954914>')
            await msg.add_reaction(response)

    command_found = await run_command(data) # Run command if possible

    if not command_found and msg.reference and msg.reference.resolved and msg.reference.resolved.author == client.user:
        await markov_chat(data)
        return
    
    # Interject if possible
    if not command_found: 
        await interject(data)

# Delete on trash emoji
@client.event
async def on_reaction_add(reaction, user):
    # Check if the reaction is the specific emoji and the message was written by the bot
    if reaction.emoji == '🗑️' and reaction.message.author == client.user:
        await reaction.message.delete()

if __name__ == '__main__':
    with open(r"/home/interrobang/VALUABLE/dimmy_widderkins_token.txt", 'r') as file:
        client.run(file.read())

