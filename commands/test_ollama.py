import asyncio
from bot_helper import send_message

async def test_ollama(data):
    """Test command to check if Ollama is responding without thinking mode."""
    msg = data['msg']
    
    # Only allow certain users to use this command
    allowed_users = [
        658073528888721408,  # interrobang's user ID
        # Add other trusted user IDs here
    ]
    
    if msg.author.id not in allowed_users:
        await send_message(data, "You don't have permission to use this command.")
        return
    
    # Get test prompt argument from message
    args = msg.content.split(' ', 1)
    test_prompt = args[1] if len(args) > 1 else "Say 'hello' without thinking about it."
    
    # Get the Ollama session
    from ollama_handler import get_ollama_session
    ollama_session = await get_ollama_session()
    
    # Test the response with and without raw mode
    await send_message(data, "Testing Ollama response... please wait.")
    
    # First test with raw mode (should be direct)
    response = await ollama_session.ask_ollama(
        prompt=test_prompt,
    )
    
    # Format the results
    result_message = f"**Test Results:**\n\n"
    result_message += f"**Prompt:** {test_prompt}\n\n"
    result_message += f"**Response:** {response}\n\n"
    
    await send_message(data, result_message)
