import json
import os
from bot_helper import send_message

OPT_FILE = 'opt.json'

def load_opted_out():
    if not os.path.exists(OPT_FILE):
        return set()
    with open(OPT_FILE, 'r') as f:
        try:
            return set(json.load(f))
        except Exception:
            return set()

def save_opted_out(opted_out):
    with open(OPT_FILE, 'w') as f:
        json.dump(list(opted_out), f)

async def opt_out(data):
    msg = data['msg']
    opted_out = load_opted_out()
    if str(msg.author) in opted_out:
        await send_message(data, "You are already opted out.")
        return
    opted_out.add(str(msg.author))
    save_opted_out(opted_out)
    await send_message(data, "You have opted out.")

async def opt_in(data):
    msg = data['msg']
    opted_out = load_opted_out()
    if str(msg.author) not in opted_out:
        await send_message(data, "You are already opted in.")
        return
    opted_out.remove(str(msg.author))
    save_opted_out(opted_out)
    await send_message(data, "You have opted in.")

# Function aliases without underscores, using prefixes, and using close synonyms
optout = opt_out
optin = opt_in
