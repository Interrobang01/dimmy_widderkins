import re
from bot_helper import send_message

async def supercommand(data):
    message_content = data.content[len("!supercommand "):]
    
    # Check if there is any content after the command
    if not message_content.strip():
        help_message = """guide:

**Usage:**
`!supercommand <command_name>`
```
<your script>
```

Supercommands are simple scripts that run when you call them.

- variables: assign variables like a normal lang
  `my_variable = "Hello"`
  `number = 10 * 2`

- printing: use the `print()` function to send a message to the channel.
  `print("foo")`
  `print(my_variable)`

- preset vars: you have access to a few variables automatically:
  - `data`: the full message data object that triggered the command. you can access details like `data.author.name`.
  - `client`: the discord client instance.

**Example:**
To create a `!hello` command that greets the user who called it:
`!supercommand hello`
```
user_name = data.author.name
print("Hello, " + user_name + "!")
```
"""
        await send_message(data, help_message)
        return

    lines = message_content.split('\n')
    command_name = lines[0].strip()
    code_block = '\n'.join(lines[1:]).strip()

    if not command_name or not code_block:
        await send_message(data, "Invalid format. You need a command name on the first line and a script in a code block on the following lines. Type `!supercommand` for more help.")
        return


    if not re.match(r"^[a-zA-Z0-9_]+$", command_name):
        await send_message(data, "Invalid command name. Use only letters, numbers, and underscores.")
        return

    with open('supercommands.json', 'a') as f:
        f.write(f"{command_name}:{code_block}\n")

    await send_message(data, f"Supercommand '{command_name}' created successfully.")

# Instead of eval, use safer alternatives
def safe_eval(expr, variables):
    # Use ast.literal_eval for safe expressions or implement custom parser
    # This only handles basic data types, not arbitrary code
    import ast
    try:
        return ast.literal_eval(expr)
    except (ValueError, SyntaxError):
        # For variable substitution
        return variables.get(expr.strip(), expr)
    
async def run_supercommand(data):
    command_name = data.content.split(' ')[0][1:]
    await send_message(data, "todo: make this work without allowing arbitrary code execution")
#     with open('supercommands.json', 'r') as f:
#         for line in f:
#             name, code = line.strip().split(':', 1)
#             if name == command_name:
#                 # Execute the code block
#                 await execute_supercommand(data, code)
#                 return

# async def execute_supercommand(data, code):
#     local_vars = {
#         "send_message": send_message,
#         "data": data,
#         "print": lambda msg: send_message(data, str(msg))
#     }
    
#     for line in code.split('\n'):
#         try:
#             if '=' in line:
#                 var, value = line.split('=', 1)
#                 local_vars[var.strip()] = eval(value.strip(), {}, local_vars)
#             else:
#                 exec(line, {}, local_vars)
#         except Exception as e:
#             await send_message(data, f"Error executing supercommand: {e}")
#             return
