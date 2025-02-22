import random
import json
from bot_helper import send_message
import asyncio
import atexit

_markov_model = None
_markov_model_chat = None

# Markov model functions
def _load_markov():
    global _markov_model
    if _markov_model is None:
        _markov_model = json.load(open(r'../markov/markov_model_notw.json', 'r'))
    return _markov_model

# Markov model functions
def _load_markov_chat():
    global _markov_model_chat
    if _markov_model_chat is None:
        _markov_model_chat = json.load(open(r'../markov/markov_model_chat_notw.json', 'r'))
    return _markov_model_chat

# Close files when bot is closed
def _close_files():
    global _markov_model
    global _markov_model_chat
    if _markov_model is not None:
        _markov_model.close()
    if _markov_model_chat is not None:
        _markov_model_chat.close()

atexit.register(_close_files)

def _infer_markov(current_word):
    markov_model = _load_markov()
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

def _infer_markov_chat(current_message):
    markov_model_chat = _load_markov_chat()

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

async def markov(data):
    msg = data['msg']

    length = 100 # Default length of response in characters

    next_word = msg.content.split(' ')[-1]
    if next_word.isdigit():
        length = int(next_word)
        next_word = msg.content.split(' ')[-2]

    response = ""
    while next_word != None and len(response) < length:
        next_word = _infer_markov(next_word)
        if next_word != None:
            response += str(next_word) + ' '
            
    
    await send_message(data, response)

from collections import deque
_message_history = deque(maxlen=5)

async def markov_chat(data):
    msg = data['msg']

    if not hasattr(markov_chat, 'last_markov_message'):
        markov_chat.last_markov_message = 99

    split = msg.content.split(' ')
    # Remove command if it exists
    if msg.content.startswith('!'):
        split = split[1:]

    input_message = ' '.join(split)
    
    # Add current message to history
    _message_history.append(input_message)
    context = ' '.join(list(_message_history))
    next_message = context if len(split) > 0 else markov_chat.last_markov_message

    response = ""
    next_message = _infer_markov_chat(next_message)
    response += str(next_message) + ' '
            
    markov_chat.last_markov_message = response.strip()
    _message_history.append(response.strip())

    # Delay message to simulate typing
    typing_delay = min(len(response) * 0.01, 3)

    async with msg.channel.typing():
        await asyncio.sleep(typing_delay)
    
    await send_message(data, response, True)

# Function aliases without underscores, using prefixes, and using close synonyms
markovchat = markov_chat
mc = markov_chat
