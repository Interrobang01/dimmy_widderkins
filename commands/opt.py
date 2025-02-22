from ..bot_helper import send_message, get_reputation, change_reputation

async def opt_out(data):
    msg = data['msg']
    if get_reputation(msg.author) >= 100:
        await send_message(data, "You are already opted out.")
        return
    change_reputation(msg.author, 100)
    await send_message(data, "You have opted back out.")

async def opt_in(data):
    msg = data['msg']
    if get_reputation(msg.author) < 100:
        await send_message(data, "You are already opted in.")
        return
    change_reputation(msg.author, -100)
    await send_message(data, "You have opted in.")
