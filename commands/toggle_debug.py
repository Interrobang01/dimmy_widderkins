from bot_helper import send_message

# Global variable to track debug mode
debug_mode = True

async def toggle_debug(data):
    """Toggle debug mode on/off."""
    msg = data['msg']
    global debug_mode
    
    # Only allow certain users to use this command
    allowed_users = [
        658073528888721408,  # interrobang's user ID
        # Add other trusted user IDs here
    ]
    
    if msg.author.id not in allowed_users:
        await send_message(data, "You don't have permission to use this command.")
        return
    
    # Parse command arguments
    args = msg.content.split()[1:] if len(msg.content.split()) > 1 else []
    
    if args and args[0].lower() in ['on', 'true', '1', 'yes']:
        debug_mode = True
        status = "enabled"
    elif args and args[0].lower() in ['off', 'false', '0', 'no']:
        debug_mode = False
        status = "disabled"
    else:
        # Toggle current state if no argument provided
        debug_mode = not debug_mode
        status = "enabled" if debug_mode else "disabled"
    
    # Apply the change to the Ollama session
    from ollama_handler import get_ollama_session
    ollama_session = await get_ollama_session()
    
    # Modify any debugging flags in the Ollama session here if needed
    # For now we're just reporting the status
    
    await send_message(data, f"Debug mode is now {status}.")
