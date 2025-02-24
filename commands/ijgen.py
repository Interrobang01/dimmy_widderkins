from bot_helper import send_message, get_user_input
from commands.markov import _infer_markov_chat
import json
import random
from bot_helper import ask_ollama

async def ijgen(data):
    msg = data['msg']
    args = msg.content.split()[1:]  # Remove !ijgen
    
    if not args:
        await send_message(data, "Usage: !ijgen <phrase to respond to>")
        return
        
    phrase = ' '.join(args)
    
    # Generate multiple Markov responses
    markov_responses = [_infer_markov_chat(phrase) for _ in range(5)]
    markov_responses = [r for r in markov_responses if r]  # Remove any None responses
    
    # Create context from Markov responses
    context = "Previous similar responses:\n"
    context += "\n".join(f"- {r}" for r in markov_responses[:5]) + "\n" if markov_responses else ""
    ai_response = await ask_ollama(f"{context}Generate a short and similar response for: {phrase}", None)
    
    responses = []
    if markov_responses:
        responses.extend(markov_responses)
    if ai_response:
        responses.append(ai_response.strip())
    
    if not responses:
        await send_message(data, "Sorry, I couldn't generate a response.")
        return
        
    chosen_response = random.choice(responses)
    
    await send_message(data, f"Generated response: {chosen_response}\nWould you like to save this as an interjection? (yes/no)")
    
    confirmation = await get_user_input(data, [""], force_response=True)
    if not confirmation or confirmation[0].lower() != "yes":
        return
        
    with open('behavior.json', 'r') as f:
        behavior = json.load(f)
    
    new_interjection = {
        "type": "message",
        "response": chosen_response,
        "prompts": [phrase],
        "reputation_range": [0, 100],
        "reputation_change": 0,
        "whole_message": True
    }
    
    import time
    timestamp = str(time.time())
    behavior['interjections'][timestamp] = new_interjection
    
    with open('behavior.json', 'w') as f:
        json.dump(behavior, f, indent=4)
    
    await send_message(data, "Interjection saved successfully!")