import aiohttp

async def ask_ollama(message_content):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:11434/api/generate', 
                json={
                    "model": "llama3.2:1b",
                    "prompt": message_content,
                    "stream": False
                }) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['response'].strip()
    except Exception as e:
        print(f"Ollama error: {e}")
        return None
    return None