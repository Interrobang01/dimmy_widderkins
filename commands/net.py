import subprocess
import sys
import requests
from ..bot_helper import send_message

async def net_command(data):
    msg = data['msg']
    args = msg.content.split()[1:]  # Remove !net
    
    if not args:
        await send_message(data, "Usage: !net <ip/domain> [-d]")
        return
        
    target = args[0]
    download_flag = "-d" in args
    
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
                target = 'http://' + target
                
            response = requests.get(target, timeout=10)
            content = response.text[:1500]  # Limit content length
            await send_message(data, f"Content from {target}:\n```\n{content}...\n```")
            
    except Exception as e:
        await send_message(data, f"Error: {str(e)}")