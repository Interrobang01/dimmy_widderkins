import discord
import json
from brook import Brook
from bot_helper import send_message, get_user_input, execute_query, get_reputation, change_reputation
from ollama_handler import ask_ollama
import emoji
import importlib
import inspect
import os
import sqlite3

# Get functions to bind to commands
def get_command_functions():
    folder = "commands"
    functions = {}
    commands_path = os.path.abspath(folder)

    for filename in os.listdir(folder):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f"{folder}.{filename[:-3]}"
            module = importlib.import_module(module_name)

            # Ensure the module is from the correct folder
            module_path = os.path.abspath(module.__file__)
            if os.path.commonpath([commands_path, module_path]) == commands_path:
                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj):
                        functions[name] = obj
    
    return functions

command_functions = get_command_functions()

def initialize_database():
    conn = sqlite3.connect('/home/interrobang/Scripts/DimmyWidderkins/database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        reputation INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS commands (
        name TEXT PRIMARY KEY,
        type TEXT,
        response TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interjections (
        id INTEGER PRIMARY KEY,
        type TEXT,
        response TEXT,
        prompts TEXT,
        reputation_range TEXT,
        reputation_change INTEGER,
        whole_message BOOLEAN
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS markets (
        name TEXT PRIMARY KEY,
        starting_liquidity INTEGER,
        initialized_probability REAL,
        liquidity INTEGER,
        probability REAL,
        creator TEXT,
        resolved BOOLEAN,
        resolution BOOLEAN
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_shares (
        market_name TEXT,
        user_id TEXT,
        shares INTEGER,
        PRIMARY KEY (market_name, user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def import_json_to_sql():
    conn = sqlite3.connect('/home/interrobang/Scripts/DimmyWidderkins/database.db')
    cursor = conn.cursor()

    # Import users (reputation.json)
    with open('/home/interrobang/Scripts/DimmyWidderkins/persistence/reputation.json', 'r') as file:
        reputations = json.load(file)
        for user_id, reputation in reputations.items():
            cursor.execute("INSERT OR IGNORE INTO users (user_id, reputation) VALUES (?, ?)", (user_id, reputation))

    # Import commands and interjections (behavior.json)
    with open('/home/interrobang/Scripts/DimmyWidderkins/persistence/behavior.json', 'r') as file:
        behavior = json.load(file)
        for name, command in behavior['commands'].items():
            cursor.execute("INSERT OR IGNORE INTO commands (name, type, response) VALUES (?, ?, ?)", (name, command['type'], command['response']))
        for id, interjection in behavior['interjections'].items():
            cursor.execute("INSERT OR IGNORE INTO interjections (id, type, response, prompts, reputation_range, reputation_change, whole_message) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                           (id, interjection['type'], interjection['response'], json.dumps(interjection['prompts']), json.dumps(interjection['reputation_range']), interjection['reputation_change'], int(interjection['whole_message'])))

    conn.commit()
    conn.close()

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
    interjections = execute_query("SELECT * FROM interjections")
    
    matching_interjections = []

    for interjection in interjections:
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
    
    commands = execute_query("SELECT name FROM commands")
    commands.extend({'name': name, 'type': 'function'} for name in command_functions.keys())
    print(f"Commands: {commands}")
    # Find the longest matching command
    command_name = None
    for cmd in commands:
        if full_command.lower().startswith(cmd['name'].lower()):
            # Update if this is the longest matching command so far
            if command_name is None or len(cmd['name']) > len(command_name):
                command_name = cmd['name']

    # Check if command exists
    if command_name is None:
        await send_message(data, 'Command not found.')
        return True

    # Get the input parameter (everything after the command)
    input_param = full_command[len(command_name):].strip()

    # Check if the command is a function in command_functions
    print(f"Command name: {command_name}")
    print(f"Command functions: {command_functions}")
    if command_name in command_functions:
        await command_functions[command_name](data)
    else:
        # Execute command from the database
        command = execute_query("SELECT * FROM commands WHERE name = ?", (command_name,), fetchone=True)
        if command:
            response = command['response']
            if '{}' in response:
                response = response.replace('{}', input_param)
            await send_message(data, response)
        else:
            await send_message(data, 'Command not found.')
    
    return True

last_reaction = "🤪"

@client.event
async def on_message(msg):
    global last_reaction
    # Ignore messages from the bot itself
    if msg.author.id == client.user.id:
        return
    
    data = {'msg': msg, 'client': client, 'brook': brook}
    
    await brook.on_message(msg)

    if 'dimmy' in msg.content.lower() or 'widderkins' in msg.content.lower() or '<@1330727173115613304>' in msg.content.lower():
        # Ollama processing
        response = await ask_ollama(msg.content, last_reaction)
        print(f"Ollama response: {response}")
        response = response.strip()[0]
        if response in emoji.EMOJI_DATA:
            last_reaction = response
            #await msg.add_reaction('<:upvote:1309965553770954914>')
            await msg.add_reaction(response)

    command_found = await run_command(data) # Run command if possible

    if not command_found and msg.reference and msg.reference.resolved and msg.reference.resolved.author == client.user:
        await command_functions.markov_chat(data)
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
    initialize_database()
    import_json_to_sql()
    with open(r"/home/interrobang/VALUABLE/dimmy_widderkins_token.txt", 'r') as file:
        client.run(file.read())

