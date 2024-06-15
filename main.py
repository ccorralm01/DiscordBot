import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
from response import get_response


# Cargar envs
load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")

# Configuración inicial del bot
intents = Intents.default()
intents.message_content = True

client = Client(intents=intents)

# Mensajería
async def send_message(message, user_message):
    
    # Si solo ! 
    if not user_message:
        print("no msg")
        return
    
    # Si mensaje empieza !
    if user_message[0] == PREFIX:
        
        # Acciones bot
        try:
            response = get_response(user_message)
            await message.channel.send(response)
        except Exception as e:
            print(e)
    else:
        return
        
# Inicializado 
@client.event
async def on_ready():
    print(f"{client.user} is running")

# Evento mensaje
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    username = str(message.author)
    user_message = str(message.content)
    channel = str(message.channel)
    
    print(f'{channel}, {username}: {user_message}, {message}')
    await send_message(message, user_message)

def main():
    client.run(token=TOKEN)


if __name__ == '__main__':
    main()