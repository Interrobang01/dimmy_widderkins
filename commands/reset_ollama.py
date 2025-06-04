import asyncio
from bot_helper import send_message

async def reset_ollama(data):
    """Reset the Ollama session for debugging purposes."""
    msg = data['msg']
    
    # Only allow certain users to use this command (add your user ID here)
    allowed_users = [
        658073528888721408,  # interrobang's user ID
        # Add other trusted user IDs here
    ]
    
    if msg.author.id not in allowed_users:
        await send_message(data, "You don't have permission to use this command.")
        return
    
    # Get and reset the Ollama session
    from ollama_handler import _ollama_instance, get_ollama_session
    
    if _ollama_instance and _ollama_instance.initialized:
        await _ollama_instance.close()
        await send_message(data, "Closing Ollama session...")
    
    # Create a new session
    new_session = await get_ollama_session()
    await send_message(data, "Ollama session reset complete. New session initialized.")
