from bot_helper import get_user_input

async def react(data):
    msg = data['msg']

    prompts = [
        'What do you want me to react with?',
    ]

    responses = await get_user_input(data, prompts)
    if responses is None:
        return
    
    requested_reaction = [prompt.strip().lower() for prompt in responses[0].split(',')][0]

    if msg.reference:
        referenced_message = await msg.channel.fetch_message(msg.reference.message_id)
        for reaction in referenced_message.reactions:
            if str(reaction.emoji) == requested_reaction:
                async for reactor in reaction.users():
                    if reactor.id == data['client'].user.id:
                        # User has reacted, so remove their reaction
                        await referenced_message.remove_reaction(requested_reaction, data['client'].user) # Remove reaction if already there
                        return
        await referenced_message.add_reaction(requested_reaction)  # React
        return
