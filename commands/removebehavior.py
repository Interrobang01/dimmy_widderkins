from bot_helper import get_user_input, send_message, write_json
import json

async def remove_behavior(data):
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
        response += f"#{i+1}. Command: !{name} -> {cmd['response'][:100]}...\n"

    for i, (id, interj) in enumerate(matching_interjections, start=len(matching_commands)+1):
        options.append(('interjection', id))
        response += f"#{i}. Interjection: {', '.join(interj['prompts'])} -> {interj['response'][:100]}...\n"

    response += "\nEnter the number to remove:"
    
    # Use only option if it's the only option
    choice = None
    if len(matching_commands) + len(matching_interjections) == 1 and False: # Disable this for now
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

# Function aliases without underscores, using prefixes, and using close synonyms
removebehavior = remove_behavior
removeinterjection = remove_behavior
removecommand = remove_behavior
remove = remove_behavior
delete = remove_behavior
