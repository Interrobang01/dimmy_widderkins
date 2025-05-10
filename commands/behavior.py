from bot_helper import get_user_input, send_message, write_json, get_command_functions
import json
import time
from commands.markov import _infer_markov_chat
from ollama_handler import ask_ollama
import random
import discord

async def _search_behavior(data, target):
    msg = data['msg']



    # Load behavior file
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)

    # Find matching commands and interjections
    matching_commands = [(name, cmd) for name, cmd in behavior['commands'].items() 
                        if name.lower() == target and cmd.get('type') != 'function']
    matching_interjections = [(id, interj) for id, interj in behavior['interjections'].items() 
                            if any(prompt.lower() == target for prompt in interj['prompts'])]

    if not matching_commands and not matching_interjections:
        return "No matching commands or interjections found.", None, matching_commands, matching_interjections

    # Build list of options
    options = []
    response = "Found these matches:\n"
    
    for i, (name, cmd) in enumerate(matching_commands):
        options.append(('command', name))
        response += f"#{i+1}. Command: !{name} -> {cmd['response'][:100]}...\n"

    for i, (id, interj) in enumerate(matching_interjections, start=len(matching_commands)+1):
        options.append(('interjection', id))
        response += f"#{i}. Interjection: {', '.join(interj['prompts'])} -> {interj['response'][:100]}...\n"
    
    return response, options, matching_commands, matching_interjections


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

    thing_to_send_to_user, options, matching_commands, matching_interjections = await _search_behavior(data, target)
    if not thing_to_send_to_user:
        return

    thing_to_send_to_user += "\nEnter the number to remove:"
    
    # Use only option if it's the only option
    choice = None
    if len(matching_commands) + len(matching_interjections) == 1 and False: # Disable this for now
        choice = 1
    else:
        # Use get_user_input instead of manual input
        responses = await get_user_input(data, [thing_to_send_to_user], True) # True is for not reusing this message as choice
        if responses is None:
            return

        choice = responses[0]
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(options):
            await send_message(data, "Invalid selection.")
            return

    # Open behavior
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)

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

# Returns fixed prompts and response along with error message if any
def validate_interjection(data, prompts, response):
    visited_prompts = [] # Used to track duplicates
    for prompt in prompts:

        # Notifying users of bad prompts
        if len(prompt) == 1:
            prompts, response, 'Prompts must be at least 2 characters long.'
        if not any(char.isalpha() for char in prompt):
            return prompts, response, 'Prompts must contain at least one letter.'
        
        # Removing bad prompts that the user won't miss
        if prompt in visited_prompts:
            prompts.remove(prompt) # Remove duplicates
        if len(prompt) == 0:
            prompts.remove(prompt) # Remove empty prompts
        if not prompt.strip():
            prompts.remove(prompt) # Remove whitespace prompts
        visited_prompts.append(prompt)

    # Validate response length and content
    if len(response) > 2000:
        return prompts, response, 'Response too long (max 2000 characters).'
    
    if not response.strip():
        return prompts, response, 'Response cannot be empty.'
    
    return prompts, response, None

async def new_command(data):
    msg = data['msg']
    prompts = [
        "What should the command be?",
        "What should the command response be? If you'd like to add an argument, place a {} and it will be replaced with anything that comes after your command.",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    # # Return error if command contains spaces
    # if ' ' in responses[0]:
    #     await send_message(message, 'Command cannot contain spaces.')
    #     return
    
    # commandname = responses[0].split(' ')[0]
    commandname = responses[0]

    # Load commands list
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        commands = behavior['commands']
    
    # Check if command already exists
    if commandname in commands:
        await send_message(data, 'This command already exists.')
        return
    
    # Add command
    commands[commandname] = {
        'type': 'message',
        'response': responses[1]
    }
    write_json(behavior)
    
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

    # Validate
    interjection_prompts, responses[2], error = validate_interjection(data, interjection_prompts, responses[2])
    if error:
        await send_message(data, error)
        return

    whole_message = 'y' in responses[1].lower()
    # Pranked
    if not whole_message:
        whole_message = True
        await send_message(data, 'Just kidding. You are not allowed to make non-whole-message interjections.')


    # Load interjections list
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        interjections = behavior['interjections']
    
    # Add interjection
    interjections[time.time()] = {
        'type': 'message',
        'response': responses[2],
        "prompts": interjection_prompts,
        "reputation_range": [
            0,
            100
        ],
        "reputation_change": 0,
        "whole_message": whole_message 
    }

    write_json(behavior)
    
    await send_message(data, 'Your interjection has been added.')

async def generate_interjection(data):
    msg = data['msg']
    prompts = [
        "What should the prompt be? Only one prompt is supported as of now.",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    interjection_prompt = responses[0].strip().lower()
    
    # Generate multiple Markov responses
    markov_responses = [_infer_markov_chat(interjection_prompt) for _ in range(5)]
    markov_responses = [r for r in markov_responses if r]
    markov_responses = list(set(markov_responses))

    # Create context from Markov responses
    context = "Previous similar responses:\n"
    context += "\n".join(f"- {r}" for r in markov_responses[:5]) + "\n" if markov_responses else ""
    #ai_response = await ask_ollama(
    #    f"Please generate a short and snappy response for: {interjection_prompt}. Do not say anything other than the response.\n{context}",
    #    model="gem:latest",
    #    host="http://localhost:11434"
    #)
    #ai_response = ai_response[:2000]
    ai_response = "AAAAAAAAAH"
    
    responses = []
    if markov_responses:
        responses.extend(markov_responses)
    if ai_response:
        responses.append(ai_response.strip())
    
    if not responses:
        await send_message(data, "Sorry, I couldn't generate a response.")
        return

    # Get user choice    
    user_prompt = "Enter the number to add the response as an interjection"
    user_prompt += "\nGenerated these responses:"
    
    for i, response in enumerate(responses):
        user_prompt += f"\n#{i+1}. {interjection_prompt} -> {response}"

    
    # Use only option if it's the only option
    choice = None
    if len(responses) == 1 and False: # Disable this for now
        choice = 1
    else:
        # Use get_user_input instead of manual input
        user_responses = await get_user_input(data, [user_prompt], True) # True is for not reusing this message as choice
        if user_responses is None:
            return

        choice = user_responses[0]
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(responses):
            await send_message(data, "Invalid selection.")
            return
        
    chosen_response = responses[int(choice)-1]

    # Validate
    _, chosen_response, error = validate_interjection(data, [interjection_prompt], chosen_response)
    if error:
        await send_message(data, error)
        return

    # Load interjections list
    with open('behavior.json', 'r') as file:
        behavior = json.load(file)
        interjections = behavior['interjections']
    
    # Add interjection
    interjections[time.time()] = {
        "type": "message",
        "response": chosen_response,
        "prompts": [interjection_prompt],
        "reputation_range": [0, 100],
        "reputation_change": 0,
        "whole_message": True
    }

    write_json(behavior)
    
    await send_message(data, 'Your randomized interjection has been added.')

class HelpMenu(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.current_page = 1
        self.speed = 1

    async def update_message(self, interaction):
        # Update the embed to the current page
        embed, _ = await help(None, self.current_page, True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="<<", style=discord.ButtonStyle.primary)
    async def previous_exp(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Go to the previous page, speed up exponentially
        if self.speed > -1:
            self.speed = -1
        else:
            self.speed *= 2
        self.current_page += self.speed
        await self.update_message(interaction)

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Go to the previous page
        self.speed = -1
        self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Go to the next page
        self.speed = 1
        _, length = await help(None, self.current_page, True) # Inefficient? Yes.
        if self.current_page + 1 < length:
            self.current_page += 1
            await self.update_message(interaction)

    @discord.ui.button(label=">>", style=discord.ButtonStyle.primary)
    async def next_exp(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Go to the next page, speed up exponentially
        _, length = await help(None, self.current_page, True) # Inefficient? Yes.
        if self.speed < 1:
            self.speed = 1
        else:
            self.speed *= 2
        if self.current_page + self.speed < length:
            self.current_page += self.speed
            await self.update_message(interaction)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Close the menu by clearing the view
        await interaction.message.delete()

async def help(data, page=None, edit=False):
    if page == None:
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
        interjections = behavior['interjections']
    
    # List function commands with aliases at top
    function_lines = {}
    for func_name, func in function_commands.items():
        if func not in function_lines:
            function_lines[func] = [func_name]
        else:
            function_lines[func].append(func_name)

    all_behavior = []
    for func, aliases in function_lines.items():
        all_behavior.append(f'`!{aliases[0]}` (aliases: {", ".join(aliases[1:])})')

    # List other commands
    for command in commands:
        all_behavior.append(f'`!{command}`')

    interjection_cutoff = len(all_behavior) + 1

    # List interjections
    for _, interjection in interjections.items():
        prompts_string = ", ".join(interjection['prompts'])
        response_string = interjection['response']
        if len(response_string) > 300:
            response_string = response_string[:300] + '...'
        all_behavior.append(f'`{prompts_string}` -> `{response_string}`')


    # Pagination

    items_per_page = 10
    total_pages = (len(all_behavior) + items_per_page - 1) // items_per_page
    total_command_pages = (interjection_cutoff + items_per_page - 1) // items_per_page
    if page < -10:
        # Page -11 is equal to page 1, and continues upward from the negatives
        page = abs(page + 10)%total_pages + 1
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    embed = None
    title = f"Help - Page **{page}/{total_pages}**"
    if start_index >= len(all_behavior):
        embed = discord.Embed(title=title, description="No more behavior.")
    else:
        embed = discord.Embed(title=title, description='\n'.join(all_behavior[start_index:end_index]))

    # Page <1 easter eggs
    if page == 0:
        embed = discord.Embed(title=title, description="Thank goodness we're not dividing by page number anywhere.")
    if page == -1:
        embed = discord.Embed(title=title, description="An enormous dark and dimly-lit room. A large, unknown machine rests in the center: https://demonin.com/games/endlessStairwell/")
    if page == -10:
        embed = discord.Embed(title=title, description="Quod est superius est sicut quod inferius, et quod inferius est sicut quod est superius.")

    embed.set_footer(text=f"Use !help [page] to view more pages. Interjections start on page {total_command_pages}.")
    if edit:
        return embed, total_pages
    else:
        view = HelpMenu()

        await msg.channel.send(embed=embed, view=view)


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
removebehavior = remove_behavior
removeinterjection = remove_behavior
removecommand = remove_behavior
remove = remove_behavior
delete = remove_behavior

command = new_command
interjection = new_interjection
addcommand = new_command
addinterjection = new_interjection
newcommand = new_command
newinterjection = new_interjection
geninterjection = generate_interjection
geninter = generate_interjection
ijgen = generate_interjection
generateinterjection = generate_interjection

interjections = list_interjections
helpinterjections = list_interjections
listinterjections = list_interjections
helpcommands = help
listcommands = help
commands = help
