import json
from bot_helper import send_message

REPUTATION_FILE = 'reputation.json'

# Reset old data on import
with open(REPUTATION_FILE, 'w') as f:
    json.dump({}, f)

async def reputation(data):
    msg = data['msg']
    user_id = str(msg.author.id)
    # Load reputation data
    with open(REPUTATION_FILE, 'r') as f:
        rep_data = json.load(f)
    rep = rep_data.get(user_id, 0)
    await send_message(data, f'Your reputation is {rep}.')

# Function aliases without underscores, using prefixes, and using close synonyms
rep = reputation

def update_reputation_on_reaction(message, emoji, added=True):
    user_id = str(message.author.id)
    with open(REPUTATION_FILE, 'r') as f:
        rep_data = json.load(f)
    change = 0
    # Check for custom emoji by name (e.g. :upvote: or :downvote:)
    emoji_name = emoji.name if hasattr(emoji, 'name') else str(emoji)
    if emoji_name == 'upvote':
        change = 1 if added else -1
    elif emoji_name == 'downvote':
        change = -1 if added else 1
    if change != 0:
        rep_data[user_id] = rep_data.get(user_id, 0) + change
        with open(REPUTATION_FILE, 'w') as f:
            json.dump(rep_data, f)
