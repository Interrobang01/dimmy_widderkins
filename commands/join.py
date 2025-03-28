import mcproto
import mcproto.packets
from bot_helper import send_message, get_user_input
from commands.markov import _infer_markov_chat
from ollama_handler import ask_ollama
import asyncio
import random
async def join(data):
    if not hasattr(join, 'active_connections'):
        join.active_connections = {}
    active_connections = join.active_connections

    msg = data['msg']
    
    prompts = [
        "What's the server IP and port? (e.g. localhost:25565)",
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
        
    server = responses[0].split(':')
    host = server[0]
    port = int(server[1]) if len(server) > 1 else 25565

    try:
        client = mcproto.MinecraftClient()
        await client.connect(host, port, username="dimmyWidderkins", protocol_version=760)  # 1.20.1
        active_connections[msg.channel.id] = client
        
        await send_message(data, f"Connected to {host}:{port} using Minecraft 1.20.1 (this feature was made by Opo, praise Opo for his work and stop giving terro credits :sob:)")

        asyncio.create_task(movement_loop(data, client))
        asyncio.create_task(chat_loop(data, client))

    except Exception as e:
        await send_message(data, f"Failed to connect: {str(e)}")

async def _movement_loop(data, client):
    while client.connected:
        try:
            action = await ask_ollama(
                "You are controlling a Minecraft bot. What should it do next? Respond with only: walk, jump, or wait. You can only respond with one of those 3 words.",
                model="llama3.2:1b"
            )
            
            if action == "walk":
                x = random.uniform(-1, 1)
                z = random.uniform(-1, 1)
                await client.send_packet(mcproto.packets.PlayerPositionPacket(x=x, y=0, z=z))
            elif action == "jump":
                await client.send_packet(mcproto.packets.PlayerPositionPacket(x=0, y=1, z=0))
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Movement error: {str(e)}")
async def _chat_loop(data, client):
    while client.connected:
        try:
            message = _infer_markov_chat("hii guys")
            if message:
                await client.send_packet(mcproto.packets.ChatMessagePacket(message=message))
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Chat error: {str(e)}")
joingame = join
joinmc = join
minecraft = join
mc = join
