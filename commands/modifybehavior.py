from bot_helper import send_message, get_user_input, execute_query
import time

async def new_command(data):
    msg = data['msg']
    prompts = [
        "What should the command be?",
        "What should the command response be? If you'd like to add an argument, place a {} and it will be replaced with anything that comes after your command.",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    commandname = responses[0]

    existing_command = execute_query("SELECT name FROM commands WHERE name = ?", (commandname,))
    if existing_command:
        await send_message(data, 'This command already exists.')
        return
    
    execute_query("INSERT INTO commands (name, type, response) VALUES (?, 'message', ?)", (commandname, responses[1]))
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

    visited_prompts = []
    for prompt in interjection_prompts:
        if len(prompt) == 1:
            await send_message(data, 'Prompts must be at least 2 characters long.')
            return
        if not any(char.isalpha() for char in prompt):
            await send_message(data, 'Prompts must contain at least one letter.')
            return
        
        if prompt in visited_prompts:
            interjection_prompts.remove(prompt)
        if len(prompt) == 0:
            interjection_prompts.remove(prompt)
        visited_prompts.append(prompt)

    if len(responses[2]) > 2000:
        await send_message(data, 'Response too long (max 2000 characters).')
        return
    
    if not responses[2].strip():
        await send_message(data, 'Response cannot be empty.')
        return
    
    whole_message = 'y' in responses[1].lower()
    if not whole_message:
        whole_message = True
        await send_message(data, 'Just kidding. You are not allowed to make non-whole-message interjections.')

    execute_query("INSERT INTO interjections (id, type, response, prompts, reputation_range, reputation_change, whole_message) VALUES (?, 'message', ?, ?, ?, ?, ?)", 
                  (time.time(), responses[2], interjection_prompts, [0, 100], 0, whole_message))
    
    await send_message(data, 'Your interjection has been added.')
