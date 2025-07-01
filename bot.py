import discord
import json
import random
import asyncio
import collections
from brook import Brook
from bot_helper import send_message, get_command_functions, get_reputation, change_reputation, update_reputation_on_reaction, is_opted_in
from supercommands import supercommand
# We'll import specifically from ollama_handler as needed to avoid circular imports
from opo_toolset import universe, you
from startupmessage import send_startup_message
import emoji
import random
import sys

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

command_functions = get_command_functions()

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.typing = True

client = discord.Client(intents=intents)

# Message history tracking (stores last messages per channel)
message_history = collections.defaultdict(lambda: collections.deque(maxlen=5))

# Define event handlers

transport_channel = None  # This needs to be set after client is ready
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    global transport_channel
    transport_channel = client.get_channel(1322717023351865395)
    global brook
    brook = Brook(transport_channel, client)
    
    # Initialize the stateful Ollama session
    from ollama_handler import get_ollama_session
    await get_ollama_session()
    print("Initialized stateful Ollama session")
    
    async def periodic_universe():
        print("periodic_universe task started")
        while True:
            minutes = random.randint(5, 50)
            await asyncio.sleep(minutes * 60)
            await universe(client)
    asyncio.create_task(periodic_universe())

    # Send startup message
    await send_startup_message(client)
    print("Sent startup message")

async def interject(data):
    msg = data['msg']
    # Load interjections list
    with open('behavior.json', 'r') as file:
        interjections = json.load(file)['interjections']
    
    # Track matching interjections
    matching_interjections = []

    # Go through every interjection
    for _, interjection in interjections.items():
        # Skip if user is opted out
        if not is_opted_in(msg.author):
            continue

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

    # If we found matches, respond to one randomly weighted by length
    if matching_interjections:
        total_length = sum(len(prompt) for prompt, _ in matching_interjections)
        weights = [len(prompt) / total_length for prompt, _ in matching_interjections]
        chosen_interjection = random.choices(matching_interjections, weights=weights, k=1)[0][1]
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

    # Add function names in command_functions to commands if not already present
    for func_name in command_functions.keys():
        if func_name not in commands:
            commands[func_name] = {'response': 'you should not see this message'}

    # Find the longest matching command
    command_name = None
    for cmd in commands:
        if full_command.lower().startswith(cmd.lower()):
            # Update if this is the longest matching command so far
            if command_name is None or len(cmd) > len(command_name):
                command_name = cmd

    # Check for supercommands if no built-in command is found
    if command_name is None:
        with open('supercommands.json', 'r') as f:
            for line in f:
                name, _ = line.strip().split(':', 1)
                if full_command.lower().startswith(name.lower()):
                    command_name = name
                    break

    # Check if command exists
    if command_name is None:
        await send_message(data, 'Command not found.')
        return True

    # Get the input parameter (everything after the command)
    input_param = full_command[len(command_name):].strip()

    # Check if the command is a function in command_functions
    if command_name in command_functions:
        await command_functions[command_name](data)
    else:
        # Check if it is a supercommand
        is_supercommand = False
        with open('supercommands.json', 'r') as f:
            for line in f:
                name, _ = line.strip().split(':', 1)
                if name == command_name:
                    is_supercommand = True
                    break
        
        if is_supercommand:
            from supercommands import run_supercommand
            await run_supercommand(data)
        else:
            # Execute command
            command = commands[command_name]
            response = command['response']
            if '{}' in response:
                response = response.replace('{}', input_param)
            await send_message(data, response)
    
    return True

async def get_watching():
    # Check if the bot is currently watching something (opo_toolset.py)
    from opo_toolset import currently_watching
    return currently_watching

async def handle_universe(data):
    pass

async def handle_reply(data):
    if not get_watching() == "you":
        await command_functions['markov_chat'](data)
    else:
        await you(data)


last_reaction = "🤪"
guild_blacklist = []

@client.event
async def on_message(msg):
    global last_reaction, message_history
    # Ignore messages from the bot itself
    if msg.author.id == client.user.id:
        return
    
    # Return if bot hasn't been initialized yet
    if not hasattr(client, 'user'):
        return
    
    # Return if the guild is blacklisted
    if msg.guild and (msg.guild.id in guild_blacklist):
        print(f"Message from blacklisted guild {msg.guild.id} ignored")
        return
    
    # Add message to history for this channel
    message_history[msg.channel.id].append({
        'author': str(msg.author.display_name),
        'content': msg.content,
        'timestamp': msg.created_at.isoformat()
    })
    
    data = {'msg': msg, 'client': client, 'brook': brook}
    
    await brook.on_message(msg)

    if 'dimmy' in msg.content.lower() or 'widderkins' in msg.content.lower() or '<@1330727173115613304>' in msg.content.lower():
        # Use the stateful Ollama handler
        from ollama_handler import get_ollama_session
        ollama_session = await get_ollama_session()
        
        # Get emoji reaction using the stateful session with channel context
        response = await ollama_session.get_emoji_reaction(
            channel_id=msg.channel.id,
            message_content=msg.content,
            author_name=msg.author.display_name,
            last_reaction=last_reaction,
            debug=True  # Enable debugging output
        )
        
        print(f"Ollama response: {response}")
        if response:
            response = response.strip()[0]
            if response in emoji.EMOJI_DATA:
                last_reaction = response
                await msg.add_reaction(response)

    command_found = await run_command(data) # Run command if possible

    if not command_found and msg.reference and msg.reference.resolved and msg.reference.resolved.author == client.user:
        # Handle replies to bot messages
        await handle_reply(data)
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
    # Update reputation for upvote/downvote reactions
    if reaction.emoji in (':upvote:', '👍', ':downvote:', '👎'):
        update_reputation_on_reaction(reaction.message, reaction.emoji, added=True)

@client.event
async def on_reaction_remove(reaction, user):
    if reaction.emoji in (':upvote:', '👍', ':downvote:', '👎'):
        update_reputation_on_reaction(reaction.message, reaction.emoji, added=False)

async def cleanup():
    # Close the Ollama session properly
    from ollama_handler import _ollama_instance
    if _ollama_instance:
        await _ollama_instance.close()
        print("Closed Ollama session")

if __name__ == '__main__':
    try:
        with open(r"/home/interrobang/VALUABLE/dimmy_widderkins_token.txt", 'r') as file:
            client.run(file.read())
    finally:
        # Run cleanup in a new event loop to ensure it runs
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup())
        loop.close()

