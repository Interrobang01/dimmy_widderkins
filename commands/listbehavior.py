from bot_helper import send_message, get_command_functions
import json

async def help(data):
    msg = data['msg']
    page = 1
    page_str = msg.content.split()[-1].strip()
    if page_str.isdigit():
        page = int(page_str)

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
            function_lines[func] = [func_name]
        else:
            function_lines[func].append(func_name)

    all_commands = []
    for func, aliases in function_lines.items():
        all_commands.append(f'`!{aliases[0]}` (aliases: {", ".join(aliases[1:])})')

    # List other commands
    for command in commands:
        all_commands.append(f'`!{command}`')

    # Pagination
    items_per_page = 10
    total_pages = (len(all_commands) + items_per_page - 1) // items_per_page
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    if start_index >= len(all_commands):
        response += '\nNo more commands.'
    else:
        response += '\n' + '\n'.join(all_commands[start_index:end_index])
        response += f'\n\nPage {page}/{total_pages}'

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

# Function aliases without underscores, using prefixes, and using close synonyms
interjections = list_interjections
helpinterjections = list_interjections
listinterjections = list_interjections
helpcommands = help
listcommands = help
commands = help
