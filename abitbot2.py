import os
import discord
import re
from dotenv import load_dotenv
from discord.ext import commands

# Charge les variables du .env
load_dotenv()

# Récupère la variable
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents, max_messages=1000)

envoye = 0


# Au lancement du bot
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')
    await load_recent_messages()
    await bot.tree.sync()


# Effectue la modification lorsqu'un message est envoyé
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await replace_urls_in_message(message)


# Effectue la modification lorsqu'un message est modifié
@bot.event
async def on_message_edit(before, after):
    if after.author == bot.user:
        return
    await replace_urls_in_message(after)


@bot.tree.command(name="historique", description="Traite les 15 derniers messages du serveur")
async def historique(interaction: discord.Interaction):
    await interaction.response.send_message("Analyse des 15 derniers messages dans le canal général en cours...",
                                            ephemeral=True)
    await analyze_last_messages_in_general()
    await interaction.followup.send("Analyse terminée.", ephemeral=True)
    await interaction.delete_original_response()


# Analyse les 15 derniers messages et les traite
async def analyze_last_messages_in_general():
    global envoye
    for guild in bot.guilds:
        general_channel = discord.utils.get(guild.text_channels, name='le-général')
        if general_channel:
            try:
                # Récupérer les 15 derniers messages du canal général
                async for message in general_channel.history(limit=15):
                    envoye = 0
                    await replace_urls_in_message(message)
            except discord.Forbidden:
                print(f"Forbidden: Cannot read message history in channel {general_channel.name}")
            except discord.HTTPException as e:
                print(f"HTTPException: {e}")


async def replace_urls_in_message(message):
    # global envoye
    # if envoye == 0 :
    # envoye = 1
    # else :
    # envoye = 0
    # return

    # Rechercher les URLs x.com dans le message

    a_traiter = 0

    urls = re.findall(r'https?://(x\.com|twitter\.com)/\S+', message.content)

    modified_message = message.content  # Récupération du message
    target_channel = message.channel  # Par défaut, le même canal que le message original

    # Extraire le mot-clé (nom du canal) s'il est spécifié
    keyword_match = re.findall(r' ([\w-]+)$', modified_message)
    modified_message = re.sub(r' [\w-]+$', '', modified_message)  # Supprimer le mot-clé du message

    if urls:
        a_traiter = 1
        for url in urls:
            new_url = url.replace('twitter.com', 'vxtwitter.com').replace('x.com', 'vxtwitter.com')
            modified_message = modified_message.replace(url, new_url)

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
