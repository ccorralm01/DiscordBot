import discord
import asyncio
import yt_dlp

queues = {}
voice_clients = {}
yt_dl_options = {"format": "bestaudio/best"}
ytdl = yt_dlp.YoutubeDL(yt_dl_options)
loop_current_song = {}
current_song = None
looping = False

ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}


async def is_connected(message):
    
    # Verificar si el autor del mensaje está en un canal de voz
    if not message.author.voice:
        await message.channel.send("Debes estar en un canal de voz para usar este comando.")
        return None
    
    try:
        # Comprueba si el servidor (guild) actual tiene un cliente de voz activo en el diccionario `voice_clients`
        if message.guild.id in voice_clients:
            # Si el cliente de voz está conectado
            if voice_clients[message.guild.id].is_connected():
                # Asigna el cliente de voz existente a `voice_client`
                voice_client = voice_clients[message.guild.id]
                # await message.channel.send(f"El bot ya está conectado al canal de voz: {voice_client.channel.name}")
            else:
                # Si el cliente de voz no está conectado, conéctate al canal de voz del autor del mensaje
                voice_client = await message.author.voice.channel.connect()
                # Actualiza el diccionario `voice_clients` con el nuevo cliente de voz
                voice_clients[message.guild.id] = voice_client
                # await message.channel.send(f"El bot se ha reconectado al canal de voz: {voice_client.channel.name}")
        else:
            # Si el bot no tiene un cliente de voz para el servidor actual, conéctate al canal de voz del autor del mensaje
            voice_client = await message.author.voice.channel.connect()
            # Añade el nuevo cliente de voz al diccionario `voice_clients`
            voice_clients[message.guild.id] = voice_client
            # await message.channel.send(f"El bot se ha conectado al canal de voz: {voice_client.channel.name}")
        
        return voice_client
            
    except Exception as e:
        await message.channel.send(f"Error general: {e}")
        return f"Error general: {e}"


async def play(message, voice_client):
    global current_song, looping

    try:
        # Obtener la URL del video desde el mensaje
        url = message.content.split()[1]

        # Extraer información del video usando youtube_dl
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        # Obtener la URL directa al archivo de audio
        song_url = data['url']
        new_current_song = data['url']

        await message.delete()

        # Verificar si hay una cola de reproducción para este servidor
        if message.guild.id in queues:
            queues[message.guild.id].append(song_url)
        else:
            queues[message.guild.id] = [song_url]

        # Si hay bucle activo y la nueva canción es diferente a la actualmente en bucle, desactivar el bucle
        if looping and new_current_song != current_song:
            looping = False
            await message.channel.send("Bucle desactivado continuando con la reproducción normal. :track_next:")
            
            # Esperar a que termine la canción actual en bucle antes de continuar
            while voice_client.is_playing():
                await asyncio.sleep(1)

        # Actualizar la canción actual
        current_song = new_current_song

        # Si no hay bucle activo, reproducir la siguiente canción de la cola
        if not looping:
            next_song_url = queues[message.guild.id].pop(0)
            player = discord.FFmpegOpusAudio(next_song_url, **ffmpeg_options)
            voice_client.play(player)
            return f"Reproduciendo: {url}"

        return f"Añadido a la cola: {url}"

    except Exception as e:
        print(f"Error al reproducir: {e}")
        return f"Error al reproducir: {e}"


def pause(voice_client):
    try:
        
        voice_client.pause()
        return f"Canción pausada :pause_button:"

    except Exception as e:
        print(f"Error al pausar: {e}")
        return f"Error al pausar: {e}"


def resume(voice_client):
    try:
        voice_client.resume()
        return "Reanudado :arrow_forward:"
    except Exception as e:
        print(f"Error al reanudar: {e}")
        return f"Error al reanudar: {e}"
  
           
async def stop(voice_client):
    try:
        # Detener el proceso de reproducción actual
        voice_client.stop()

        # Desconectar el cliente de voz y eliminarlo del diccionario
        await voice_client.disconnect()
        if voice_client.guild.id in voice_clients:
            del voice_clients[voice_client.guild.id]
        
        if voice_client.guild.id in queues:
            del queues[voice_client.guild.id]

        return "Detenido y desconectado :wave:"
    except Exception as e:
        print(f"Error al detener y desconectar: {e}")
        return f"Error al detener y desconectar: {e}"


async def skip(message, voice_client):
    try:
        global loop_current_song  # Usamos la variable global loop_current_song

        if message.guild.id in queues:
            voice_client.stop()

            # Verificar si el bucle de la canción actual está activo
            if voice_client.guild.id in loop_current_song and loop_current_song[voice_client.guild.id]:
                # Reponer la canción al principio de la cola
                queues[message.guild.id].insert(0, queues[message.guild.id][0])

            # Eliminar la canción actual de la cola
            queues[message.guild.id].pop(0)

            # Obtener la siguiente canción en la cola
            if queues[message.guild.id]:
                next_song = queues[message.guild.id][0]
                next_song_url = next_song[0]
                # Crear un nuevo objeto de audio para la siguiente canción
                player = discord.FFmpegOpusAudio(next_song_url, **ffmpeg_options)
                voice_client.play(player)
                return f"Canción saltada :fast_forward:. Reproduciendo siguiente canción en la cola."
            else:
                return "No hay más canciones en la cola para reproducir."

        else:
            return "No hay cola de reproducción para saltar canción."

    except Exception as e:
        print(f"Error al saltar canción: {e}")
        return f"Error al saltar canción: {e}"

async def loop(voice_client):
    global current_song, looping

    while looping:
        try:
            player = discord.FFmpegOpusAudio(current_song, **ffmpeg_options)
            voice_client.play(player)
            await asyncio.sleep(player.duration)
        except Exception as e:
            print(f"Error en el bucle de reproducción: {e}")
            await asyncio.sleep(1)  # Espera un segundo antes de reintentar

async def song(message, command):
    global looping
    
    voice_client = await is_connected(message)
    
    if not voice_client:
        return "No se pudo conectar al canal de voz."
    
    if command == "play":
        res = await play(message, voice_client)
        
    elif command == "pause":
        res = pause(voice_client)
        
    elif command == "resume":
        res = resume(voice_client)
        
    elif command == "stop":
        res = await stop(voice_client)
        
    elif command == "skip":
        res = await skip(message, voice_client)
        
    elif command == "loop":
        if looping:
            looping = False
            res = "Bucle desactivado para la canción actual. :track_next:"
        else:
            res = "Bucle activado para la canción actual. :repeat_one:"
            loop_task = asyncio.create_task(loop(voice_client))
            looping = True
            
    return res