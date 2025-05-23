import os
import subprocess
import sys
import json
try:
    import discord
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "discord"])
    import discord
# import discord
import re

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

from discord.ext import commands
from discord import app_commands

# Charge les variables du .env
load_dotenv()

# Récupère la variable
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("Le token Discord est manquant. Ajoutez-le dans un fichier .env")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

channelGeneral = 0

envoye = 0

limit = 15

# Au lancement du bot
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')
    await bot.change_presence(activity=discord.Game(name=" taper !aled"))

    for guild in bot.guilds:
        await setChannelGeneral(guild.system_channel)
        print(f'Le channel général est #{guild.system_channel}')

    await load_recent_messages()
    print(f'1000 derniers messages chargés')

    with open('data.json') as f:
        data = json.load(f)
    
    if data['analyseLancement'] :
        print(f'Analyse des {limit} derniers messages..')
        await analyze_last_messages_in_general(limit)
        print(f'Fin de l\'analyse')
    
    await bot.tree.sync()


async def setChannelGeneral(channel):
    global channelGeneral
    channelGeneral = channel


# Effectue la modification lorsqu'un message est envoyé
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # permet de traiter le message normalement malgré l'override
    await bot.process_commands(message)

    # traitement de l'url
    await replace_urls_in_message(message)
    


# Effectue la modification lorsqu'un message est modifié
@bot.event
async def on_message_edit(before, after):
    if after.author == bot.user:
        return
    await replace_urls_in_message(after)


# --------------------------------------
#           COMMANDES
# --------------------------------------

@bot.tree.command(name="historique", description="Traite les derniers messages du serveur")
@app_commands.describe(nombre='Nombre de messages à analyser (par défaut ' + str(limit) + ')')
async def historique(interaction: discord.Interaction, nombre: int = limit):
    await interaction.response.send_message(f"Analyse des {nombre} derniers messages dans le canal général en cours...",
                                            ephemeral=True)
    await analyze_last_messages_in_general(nombre)
    await interaction.followup.send("Analyse terminée.", ephemeral=True)
    await interaction.delete_original_response()

@bot.tree.command(name="shutdown", description="Ferme le bot")
@commands.has_permissions(administrator=True)
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message(f"Le train de tes injures roule sur le rail de mon indifférence. Je préfère partir plutôt que d'entendre ça plutôt que d'être sourd.",
                                            ephemeral=True)
    await bot.close()

@bot.command()
@commands.has_permissions(administrator=True)
async def analyseLancement(ctx):
    with open('data.json') as f:
        data = json.load(f)
    
    data['analyseLancement'] = not data['analyseLancement']

    with open('data.json', 'w') as f:
        json.dump(data,f)

    
    msg = f"L\'analyse au lancement du bot est maintenant "
    if data['analyseLancement'] :
        msg += "activée"
    else:
        msg += "désactivée"
    await ctx.message.delete()

    await ctx.send(msg, delete_after=5)


@bot.command(name="aled")
async def help(ctx):
    embed = discord.Embed(
        title="Aled je comprends rien il fait quoi le bot",
        description=(
            "Sur mon front il y a pas marqué radio-réveil.. Bon je veux bien t'expliquer :\n\n"
            "Je suis un bot qui te permet de traiter un lien twitter qui est envoyé sur serveur pour appliquer une meilleure intégration pour Discord. "
            "Au contraire si tu préfères que je ne fasse pas ce traitement, ajoute **stop** après le lien.\n\n"
            "Si tu veux également que j'envoie ton message sur un autre channel je peux le faire ! Il suffit d'indiquer le nom du channel dans ton message après ton lien.\n\n"
        
            "Voilà cela explique grossièrement ma mission principale, tu peux cependant jeter un coup d'oeil aux quelques fonctionnalités additionnelles dont je dispose, aller soit pas timide :\n"
        ),
        color=discord.Color.blurple()
    )

    embed.add_field(name="`!analyseLancement`", value="Active ou désactive le traitement des 15 derniers messages quand je me lance (**désactivé par défaut**)", inline=True)
    embed.add_field(name="`/historique` nombreMessages", value="Fait le traitement des derniers messages (15 par défaut) du channel général, tu peux indiquer un nombre spécifique si tu veux je ne te force pas.", inline=False)
    embed.add_field(name="`/shutdown`", value="Permet à un administrateur de m'éteindre, même si c'est pas super sympa.", inline=False)
    embed.add_field(name="`!aide`", value="Affiche ce message d'aide.", inline=False)

    embed.set_footer(text=f"Demandé par {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)
# --------------------------------------


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Tu dois avoir le rôle `admin` pour utiliser cette commande.", delete_after=5)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Tu dois avoir la permission `Administrateur` pour faire ça.", delete_after=5)
    elif isinstance(error, commands.NotOwner):
        await ctx.send("Seul le propriétaire du bot peut utiliser cette commande.", delete_after=5)
    else:
        # Optionnel : affiche les autres erreurs pour débug
        await ctx.send(f"Une erreur est survenue : {str(error)}")


# Analyse les 15 derniers messages et les traite
async def analyze_last_messages_in_general(limite=limit):
    global envoye
    global channelGeneral
    #TODO je sais pas si le for sert à quelque chose pcq mon serv
    # n'a qu'une guild (jsp ce que c'est) mais peut être qu'il le faut pour d'autres servs
    for guild in bot.guilds:
        general_channel = channelGeneral
        if general_channel:
            try:
                # Récupérer les 15 derniers messages du canal général
                async for message in general_channel.history(limit=limite):
                    envoye = 0
                    await replace_urls_in_message(message)
            except discord.Forbidden:
                print(f"Forbidden: Cannot read message history in channel {general_channel.name}")
            except discord.HTTPException as e:
                print(f"HTTPException: {e}")



async def replace_urls_in_message(message):
    # global envoye
    # if envoye == 0 :
    #     envoye = 1
    # else :
    #     envoye = 0
    #     return

    # Rechercher les URLs x.com dans le message

    a_traiter = 0

    urls = re.findall(r'https?://(x\.com|twitter\.com)/\S+', message.content)

    modified_message = message.content  # Récupération du message
    target_channel = message.channel  # Par défaut, le même canal que le message original

    # Extraire le mot-clé (nom du canal) s'il est spécifié
    keyword_match = re.findall(r' ([\w-]+)$', modified_message)
    modified_message = re.sub(r' [\w-]+$', '', modified_message)  # Supprimer le mot-clé du message

    # On annule l'opération si on trouve le mot clé stop
    for keyword in keyword_match :
        if keyword.lower() == 'stop' :
            return 

    # Si on trouve une url dans le message
    if urls:
        a_traiter = 1
        for url in urls:
            new_url = url.replace('twitter.com', 'vxtwitter.com').replace('x.com', 'vxtwitter.com')
            modified_message = modified_message.replace(url, new_url)

    # si on trouve un nom de channel dans le message
    if keyword_match:
        a_traiter = 1
        keyword = keyword_match[0]
        # Chercher le canal par mot-clé
        for channel in message.guild.text_channels:
            if channel.name == keyword:
                target_channel = channel
                break

    if a_traiter == 1:
        # Envoyer le message modifié dans le canal cible
        await target_channel.send(modified_message)

        # Supprimer le message original
        await message.delete()


# Charge les 1000 derniers messages dans le cache du bot
async def load_recent_messages():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=1000):  # Charger jusqu'à 1000 messages par canal
                    bot._connection._messages.append(message)  # Charger manuellement les messages dans le cache
            except discord.Forbidden:
                print(f"Forbidden: Cannot read message history in channel {channel.name}")
            except discord.HTTPException as e:
                print(f"HTTPException: {e}")


bot.run(TOKEN)
