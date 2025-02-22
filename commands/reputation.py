from ..bot_helper import send_message, get_reputation

async def command_reputation(data):
    msg = data['msg']
    reputation = get_reputation(msg.author)
    await send_message(data, f'Your reputation is {reputation}.')
