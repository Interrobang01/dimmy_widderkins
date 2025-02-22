from bot_helper import send_message, get_command_functions
import json

async def help(data):
    msg = data['msg']

    # Get function commands
    function_commands = get_command_functions()

    # Get commands
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        commands = behavior['commands']
    
    response = 'Commands: '
    # List function commands with aliases at top
    function_lines = {}
    for func_name, func in function_commands.items():
        if func not in function_lines:
            function_lines[func] = func_name + " ("
            continue
        function_lines[func] += f" {func_name}"

    for line in function_lines.values():
        response += f'\n`!{line})`'

    # List other commands
    for command in commands:
        response += f'\n`!{command}`'
    await send_message(data, response)

# Todo: make help a general guide and add list_commands

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

# Function aliases without underscores, using prefixes, and using close synonyms
interjections = list_interjections
helpinterjections = list_interjections
listinterjections = list_interjections
helpcommands = help
listcommands = help
commands = help
