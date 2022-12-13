from discord.ext import commands

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
```
Commandes:
/help - Affiche toutes les commandes disponibles
/p <mots-clés>|<lien> - Recherche la chanson sur youtube et la joue dans le chat vocal actuel. Reprend la lecture de la chanson en cours si elle a été mise en pause.
/seek <0:00> - (À FAIRE AVANT LA CHANSON) Seek pour le prochain son (exemple /seek 1:00)
/q - Affiche la queue.
/skip - Skip la chanson en cours de lecture.
/clear - Coupe la musique et vide la queue.
/leave - Déconnecte le bot du chat vocal.
/pause - Met en pause/reprend la chanson en cours.
/resume - Reprend la lecture de la chanson en cours.

```
"""
        self.text_channel_list = []

     

    @commands.command(name="help", help="Affiche l'aide aux commandes")
    async def help(self, ctx):
        await ctx.send(self.help_message)