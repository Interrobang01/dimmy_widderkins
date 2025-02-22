from ..bot_helper import send_message
import json

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

