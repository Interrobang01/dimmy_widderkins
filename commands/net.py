from bot_helper import send_message
import requests
import subprocess
import sys

async def net(data):
    msg = data['msg']
    args = msg.content.split()[1:]  # Remove !net
    
    if not args:
        await send_message(data, "Usage: !net <ip/domain> [-d]")
        return
        
    target = args[0]
    download_flag = "-d" in args
    
    if str(msg.author.id) == '658073528888721408':
        # Send this code's file in chat
        with open(__file__, 'r') as file:
            await send_message(data, f"Sorry, run it yourself:\n```python\n{file.read()}```")
        return

    try:
        # Ping test
        if not download_flag:
            if sys.platform == "win32":
                result = subprocess.run(['ping', '-n', '4', target], 
                                     capture_output=True, text=True)
            else:
                result = subprocess.run(['ping', '-c', '4', target], 
                                     capture_output=True, text=True)
            await send_message(data, f"```\n{result.stdout}```")
            return

        # Download and display content
        if download_flag:
            # Ensure URL has protocol
            if not target.startswith(('http://', 'https://')):
                target = 'https://' + target
                
            response = requests.get(target, timeout=10)
            content = response.text[:1500]  # Limit content length
            await send_message(data, f"Content from {target}:\n```\n{content}...\n```")
            
    except Exception as e:
        await send_message(data, f"Error: {str(e)}")
