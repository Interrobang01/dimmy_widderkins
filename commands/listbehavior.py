from bot_helper import send_message, execute_query
import json

async def help(data):
    msg = data['msg']
    commands = execute_query("SELECT name FROM commands")
    
    response = 'Commands: '
    for command in commands:
        response += f'\n`!{command["name"]}`'
    await send_message(data, response)

async def list_interjections(data):
    msg = data['msg']
    interjections = execute_query("SELECT prompts, response FROM interjections")
    
    response = 'Interjections: '
    for interjection in interjections:
        prompts_string = ", ".join(interjection['prompts'])
        response_string = interjection['response']
        response += f'\n{prompts_string} -> {response_string}'
    await send_message(data, response)

