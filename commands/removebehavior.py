from bot_helper import get_user_input, send_message, execute_query
import json

async def remove_behavior(data):
    msg = data['msg']

    prompts = [
        "What's the prompt or command name of the thing you want to remove?",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return

    target = responses[0].lower()

    # Find matching commands and interjections
    matching_commands = execute_query("SELECT name, response FROM commands WHERE LOWER(name) = ? AND type != 'function'", (target,))
    matching_interjections = execute_query("SELECT id, prompts, response FROM interjections WHERE ? IN (prompts)", (target,))

    if not matching_commands and not matching_interjections:
        await send_message(data, "No matching commands or interjections found.")
        return

    options = []
    response = "Found these matches:\n"
    
    for i, (name, cmd) in enumerate(matching_commands):
        options.append(('command', name))
        response += f"{i+1}. Command: !{name} -> {cmd[:100]}...\n"

    for i, (id, interj) in enumerate(matching_interjections, start=len(matching_commands)+1):
        options.append(('interjection', id))
        response += f"{i}. Interjection: {interj['prompts']} -> {interj['response'][:100]}...\n"

    response += "\nEnter the number to remove:"
    
    choice = None
    if len(matching_commands) + len(matching_interjections) == 1:
        choice = 1
    else:
        responses = await get_user_input(data, [response], True)
        if responses is None:
            return

        choice = responses[0]
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(options):
            await send_message(data, "Invalid selection.")
            return

    selected = options[int(choice)-1]
    if selected[0] == 'command':
        execute_query("DELETE FROM commands WHERE name = ?", (selected[1],))
        removed_type = 'Command'
        removed_name = selected[1]
    else:
        execute_query("DELETE FROM interjections WHERE id = ?", (selected[1],))
        removed_type = 'Interjection'
        removed_name = selected[1]

    await send_message(data, f"{removed_type} '{removed_name}' removed successfully.")
