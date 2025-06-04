import asyncio
from ollama_handler import get_ollama_session

async def test_emoji_reaction():
    # Initialize the session
    session = await get_ollama_session()
    
    # Test emoji reaction
    emoji = await session.get_emoji_reaction(
        channel_id=123,  # Test channel ID
        message_content="Hello there, how are you doing today?",
        author_name="TestUser",
        debug=True  # Enable debugging output
    )
    
    print(f"\nEmoji reaction result: {emoji}")
    
    # Test text response
    text = await session.ask_ollama("What is the capital of France?")
    
    print(f"\nText response result: {text}")
    
    # Clean up
    await session.close()

if __name__ == "__main__":
    asyncio.run(test_emoji_reaction())
