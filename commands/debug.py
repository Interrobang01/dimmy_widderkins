# import discord
# import asyncio
# from bot_helper import send_message

# async def debug(data):
#     """Debug command to show LLM context and conversation history."""
#     msg = data['msg']
    
#     # Only allow certain users to use this command (add your user ID here)
#     allowed_users = [
#         658073528888721408,  # interrobang's user ID
#         # Add other trusted user IDs here
#     ]
    
#     if msg.author.id not in allowed_users:
#         await send_message(data, "You don't have permission to use this command.")
#         return
    
#     # Get the Ollama session
#     from ollama_handler import get_ollama_session
#     ollama_session = await get_ollama_session()
    
#     # Get the channel context
#     channel_id = msg.channel.id
#     context = ollama_session.conversation_context.get(channel_id, [])
#     last_reaction = ollama_session.last_reactions.get(channel_id, "None")
    
#     # Format the debug info
#     debug_text = f"**Debug Info for Channel {channel_id}**\n"
#     debug_text += f"Last used reaction: {last_reaction}\n\n"
#     debug_text += f"**Conversation History ({len(context)} messages):**\n"
    
#     # Add context messages
#     if context:
#         for i, msg_data in enumerate(context):
#             author = msg_data['author']
#             content = msg_data['content']
#             # Truncate long messages for display
#             if len(content) > 100:
#                 content = content[:97] + "..."
#             debug_text += f"{i+1}. **{author}**: {content}\n"
#     else:
#         debug_text += "No conversation history yet."
    
#     # Send the debug info as a message
#     await send_message(data, debug_text)
