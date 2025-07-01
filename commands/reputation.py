import json
from bot_helper import send_message, get_reputation

REPUTATION_FILE = 'reputation.json'

async def reputation(data):
    msg = data['msg']
    reputation = get_reputation(msg.author)
    await send_message(data, f'Your reputation is {reputation}.')


# Function aliases without underscores, using prefixes, and using close synonyms
rep = reputation
