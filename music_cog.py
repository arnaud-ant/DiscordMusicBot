import asyncio
import discord
from discord.ext import commands
from youtube_dl import YoutubeDL

class music_cog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot #Init du bot
        self.timestamp="0:00" # Init du timestamp (seek)
        self.id = []
        self.is_playing = False #Booléen musique en cours
        self.is_paused = False  #Booléen musique en pause

        # Tableau 2D[son,channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'} #Options youtube_dl
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'} #Init options FFMPEG
        self.vc = None


    async def server_info(self):
        str = "\nConnecté a : "
        for guild in self.bot.guilds:
            str+=guild.name+", "
        str+="en tant que " + self.bot.user.name
        print (str+"\n")

    def changeTime(self,emit):
        self.timestamp = emit

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
                self.id.append(info['id'])
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #URL format audio
            m_url = self.music_queue[0][0]['source']

            #On retire l'élément de la lsite en cours d'écoute
            self.music_queue.pop(0)
            #Pareil pour l'id
            self.id.pop(0)
            self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -ss '+self.timestamp}
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
            self.changeTime("0:00")
        else:
            self.is_playing = False

    # Boucle infinie de vérif 
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            
            #On essaye de se co au channel
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                #Si impossible
                if self.vc == None:
                    await ctx.send("J'ai pas pu me co au channel",delete_after=20)
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            #Embed discord avec titre, lien, horaire de début, la preview de la video
            embed = discord.Embed(title="Son en cours : "+self.music_queue[0][0]['title'], color=0, url="https://www.youtube.com/watch?v="+self.id[0], description="Commence à "+self.timestamp)
            embed.set_image(url = "https://img.youtube.com/vi/{videoID}/0.jpg".format(videoID = self.id[0]))
            #embed.set_thumbnail(url=thumbnail) 
            try:
                await ctx.send(embed=embed,delete_after=20)
            except AttributeError:
                pass
            #On retire l'élément de la lsite en cours d'écoute
            self.music_queue.pop(0)
            #Pareil pour l'id
            self.id.pop(0)
            #On modifie les options FFMPEG (surtout) pour changer le timestamp (début du son)
            self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -ss '+self.timestamp}
            #On play le son
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
            #On reset le timestamp pour la prochaine
            self.changeTime("0:00")
        else:
            self.is_playing = False

    @commands.Cog.listener()
    async def on_ready(self):
        await self.server_info()

    @commands.command(name="play", aliases=["p","playing"], help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        sep = "&ab_channel"
        queryTemp = " ".join(args)
        query = queryTemp.split(sep,1)[0]
        try:
            voice_channel = ctx.author.voice.channel
            if self.is_paused:
                self.vc.resume()
            else:
                song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Impossible de télécharger le son. Format incorrect, essaye un autre mot-clé. Les playlists / Livestreams ne marchent pas.",delete_after=20)
            else:
                await ctx.send("Son ajouté à la queue",delete_after=20)
                await ctx.message.delete()
                self.music_queue.append([song, voice_channel])
                if self.is_playing == False:
                    await self.play_music(ctx)
        except AttributeError: # Si l'auteur du message n'est pas connecté à un channel
            await ctx.send("Co toi sur un channel vocal",delete_after=20)

    @commands.command(name="pause", help="Pause le son en cours")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
            await ctx.message.delete()
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
            await ctx.message.delete()

    @commands.command(name = "resume", help="Reprend le son")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
            await ctx.message.delete()

    @commands.command(name="skip", aliases=["s"], help="Skip le son actuel")
    async def skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            #On essaye de lancer le prochain son
            await self.play_music(ctx)
            await ctx.message.delete()


    @commands.command(name="queue", help="Affiche la queue")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            # On affiche au max 5 sons de la queue
            if (i > 4): break
            retval += self.music_queue[i][0]['title'] + "\n"

        if retval != "":
            await ctx.send(retval,delete_after=20)
            await ctx.message.delete()
        else:
            await ctx.send("Pas de son dans la queue",delete_after=20)
            await ctx.message.delete()

    @commands.command(name="clear",help="Vide la queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("La queue a été vidée",delete_after=20)
        self.changeTime("0:00")
        await ctx.message.delete()

    @commands.command(name="leave", aliases=["disconnect", "d"], help="Déconnecte le bot du channel")
    async def dc(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
        await ctx.message.delete()

    @commands.command(name="seek", help="Commence la prochaine chanson à l'horraire passé en paramètre")
    async def seek(self, ctx, *args):
        self.timestamp = " ".join(args)
        await ctx.send("Seek pour la prochaine musique à "+self.timestamp,delete_after=20)
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        
        if not member.id == self.bot.user.id:
            return

        elif before.channel is None:
            voice = after.channel.guild.voice_client
            time = 0
            while True:
                await asyncio.sleep(1)
                time = time + 1
                if voice.is_playing() and not voice.is_paused():
                    time = 0
                if time == 300:
                    await voice.disconnect()
                if not voice.is_connected():
                    break

    @commands.Cog.listener()
    async def on_message(self,message):
        if message.content.startswith('bonjour'):
            await message.channel.send(f'Bonjour {message.author.name}',delete_after=20)
        query=""
        if message.content.startswith('circus'):
            query = "https://www.youtube.com/watch?v=S280Pqq3T_w"
            await message.delete()
        if message.content.startswith('cry'):
            query = "https://www.youtube.com/watch?v=j3glwtXrj0c"
            await message.delete()
        if message.content.startswith('ronfle'):
            query = "https://www.youtube.com/watch?v=3eqcIC5Plzw"
            await message.delete()
        if query != "":
            try:
                voice_channel = message.author.voice.channel
                if self.is_paused:
                    self.vc.resume()
                else:
                    song = self.search_yt(query)
                    if type(song) == type(True):
                        await message.send("Impossible de télécharger le son. Format incorrect, essaye un autre mot-clé. Les playlists / Livestreams ne marchent pas.",delete_after=20)
                    else:
                        self.music_queue.append([song, voice_channel])
                        if self.is_playing == False:
                            await self.play_music(message)
            except AttributeError:
                await message.send("Co toi sur un channel vocal",delete_after=20)