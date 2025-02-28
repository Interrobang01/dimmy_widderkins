import aiohttp

async def ask_ollama_for_emoji(message_content, last_reaction):
    try:
        async with aiohttp.ClientSession() as session:
            with open('reactionprompt.txt', 'r') as promptheader:
                async with session.post('http://localhost:11434/api/generate', 
                    json={
                        "model": "llama3.2:1b",
                        "prompt": promptheader.read()+f" The last emoji you used was {last_reaction}. " + " Here is the text:\n"+ message_content,
                        "stream": False,
                        "max_tokens": 1,  # Limit to one token
                        "stop": [" "],   # Stop at first space
                        "temperature": 0.2  # WHY USNT UT WIRJUNG
                    }) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['response'].strip()
    except Exception as e:
        return None
    return None

async def ask_ollama(prompt, model="llama3.2:1b", host="http://localhost:11434"):
async def ask_ollama(prompt, model="llama3.2:1b", host="http://localhost:11434"):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{host}/api/generate', 
            async with session.post(f'{host}/api/generate', 
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "max_tokens": 10,
                    "temperature": 0.2
                }) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['response'].strip()
    except Exception as e:
        return None
    return None

