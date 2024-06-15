import os
from dotenv import load_dotenv
from songs import song

PREFIX = os.getenv("PREFIX")

song_actions = [f'play','pause','resume','stop', 'loop', 'skip']

async def get_response(message):
    
    res = "not ok"
    
    lowered_user_msg = message.content.lower().strip()
    
    command, msg_content = "",""
    
    if len(lowered_user_msg.split(" ", 1)) > 1:
        command = lowered_user_msg.split(" ", 1)[0][1:]
        msg_content = lowered_user_msg.split(" ", 1)[1]
    else:
        command = lowered_user_msg[1:]
    
    
    # si comienza por song_actions
    if command in song_actions:
        
        action = await song(message, command, msg_content)
        res = action
            
    # si comienza por help
    if command == f"{PREFIX}help":
        print("Accediendo a sección help")
        res = "ok"

    
    return res