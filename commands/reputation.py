from bot_helper import send_message, get_reputation, execute_query
import sqlite3

async def command_reputation(data):
    msg = data['msg']
    reputation = execute_query("SELECT reputation FROM users WHERE user_id = ?", (msg.author.id,), fetchone=True)
    if reputation:
        reputation = reputation[0]
    else:
        reputation = 100  # Default reputation if not found
    await send_message(data, f'Your reputation is {reputation}.')
