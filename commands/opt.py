import json
import os
from bot_helper import send_message, load_opted_in, save_opted_in

async def opt_out(data):
    msg = data['msg']
    opted_in = load_opted_in()
    if str(msg.author) not in opted_in:
        await send_message(data, "You are already opted out.")
        return
    opted_in.remove(str(msg.author))
    save_opted_in(opted_in)
    await send_message(data, "You have opted out.")

async def opt_in(data):
    msg = data['msg']
    opted_in = load_opted_in()
    if str(msg.author) in opted_in:
        await send_message(data, "You are already opted in.")
        return
    opted_in.add(str(msg.author))
    save_opted_in(opted_in)
    await send_message(data, "You have opted in.")

async def opt(data):
    """Toggle opt-in status."""
    msg = data['msg']
    opted_in = load_opted_in()
    
    if str(msg.author) in opted_in:
        # User is currently opted in, so opt them out
        opted_in.remove(str(msg.author))
        save_opted_in(opted_in)
        await send_message(data, "You have been opted out.")
    else:
        # User is currently opted out, so opt them in
        opted_in.add(str(msg.author))
        save_opted_in(opted_in)
        await send_message(data, "You have been opted in.")

# Function aliases without underscores, using prefixes, and using close synonyms
optout = opt_out
optin = opt_in
toggleopt = opt
toggle_opt = opt
