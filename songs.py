import discord
import asyncio
import yt_dlp

queues = {}
voice_clients = {}
yt_dl_options = {"format": "bestaudio/best"}
ytdl = yt_dlp.YoutubeDL(yt_dl_options)

ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}


async def song(message, command, url):
    try:
        # Verificar si el bot ya está conectado a un canal de voz
        if message.guild.id in voice_clients:
            if voice_clients[message.guild.id].is_connected():
                voice_client = voice_clients[message.guild.id]
            else:
                voice_client = await message.author.voice.channel.connect()
                voice_clients[message.guild.id] = voice_client
        else:
            voice_client = await message.author.voice.channel.connect()
            voice_clients[message.guild.id] = voice_client

        if command == "play":
            try:
                # Obtener la URL del video desde el mensaje
                url = message.content.split()[1]

                # Extraer información del video usando youtube_dl
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

                # Obtener la URL directa al archivo de audio
                song_url = data['url']
                await message.delete()
                
                # Obtener la URL de la miniatura del video
                thumbnails = data.get('thumbnails')
                thumbnail_url = thumbnails[-1]['url'] if thumbnails else None  # Tomar la última miniatura

                # Crear un objeto de audio para reproducir en Discord
                player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)

                # Verificar si hay una cola de reproducción para este servidor
                if message.guild.id in queues:
                    queues[message.guild.id].append((song_url, thumbnail_url))
                    return f"Añadido a la cola: {url}"
                else:
                    # Iniciar la reproducción si no hay nada en la cola
                    queues[message.guild.id] = [(song_url, thumbnail_url)]
                    voice_client.play(player)
                    return f"Reproduciendo: {url}"

            except Exception as e:
                print(f"Error al reproducir: {e}")
                return f"Error al reproducir: {e}"

        elif command == "pause":
            try:
                voice_client.pause()
                return "Pausado"

            except Exception as e:
                print(f"Error al pausar: {e}")
                return f"Error al pausar: {e}"

        elif command == "resume":
            try:
                voice_client.resume()
                return "Reanudado"

            except Exception as e:
                print(f"Error al reanudar: {e}")
                return f"Error al reanudar: {e}"

        elif command == "stop":
            try:
                voice_client.stop()
                await voice_client.disconnect()
                return "Detenido y desconectado"
            
            except Exception as e:
                print(f"Error al detener y desconectar: {e}")
                return f"Error al detener y desconectar: {e}"

        elif command == "skip":
            try:
                if message.guild.id in queues:
                    voice_client.stop()
                    # Eliminar la canción actual de la cola
                    queues[message.guild.id].pop(0)
                    # Obtener la siguiente canción en la cola
                    if queues[message.guild.id]:
                        next_song = queues[message.guild.id][0]
                        next_song_url = next_song[0]
                        # Crear un nuevo objeto de audio para la siguiente canción
                        player = discord.FFmpegOpusAudio(next_song_url, **ffmpeg_options)
                        voice_client.play(player)
                        return f"Canción saltada. Reproduciendo siguiente canción en la cola."
                    else:
                        return "No hay más canciones en la cola para reproducir."

                else:
                    return "No hay cola de reproducción para saltar canción."

            except Exception as e:
                print(f"Error al saltar canción: {e}")
                return f"Error al saltar canción: {e}"

        elif command == "loop":
            try:
                if message.guild.id in queues:
                    current_queue = queues[message.guild.id]
                    if current_queue:
                        # Obtener la primera canción en la cola
                        current_song = current_queue[0]
                        # Eliminarla de la cola para volver a agregarla al final
                        current_queue.pop(0)
                        # Agregarla al final de la cola para repetirla
                        current_queue.append(current_song)
                        return "Reproducción en bucle activada para la canción actual"
                    else:
                        return "No hay canciones en la cola para activar el bucle"

                else:
                    return "No hay cola de reproducción para activar el bucle"

            except Exception as e:
                print(f"Error al activar el bucle: {e}")
                return f"Error al activar el bucle: {e}"

    except Exception as e:
        print(f"Error general: {e}")
        return f"Error general: {e}"