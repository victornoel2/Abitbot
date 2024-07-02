import os
import discord
import re
from dotenv import load_dotenv

# Charge les variables du .env
load_dotenv()

# Récupère la variable
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.messages = True
client = discord.Client(intents=intents, max_messages=1000)

envoye = 0

# Au lancement du bot
@client.event
async def on_ready():
    print(f'Nous avons connecté en tant que {client.user}')
    await load_recent_messages()
    
# Charge les 1000 derniers messages dans le cache du bot
# TODO : ne récupérer que les messages du channel général    
async def load_recent_messages():
    for guild in client.guilds:
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=1000):  # Charger jusqu'à 1000 messages par canal
                    client._connection._messages.append(message)  # Charger manuellement les messages dans le cache
            except discord.Forbidden:
                print(f"Forbidden: Cannot read message history in channel {channel.name}")
            except discord.HTTPException as e:
                print(f"HTTPException: {e}")    

# Effectue la modification lorsqu'un message est envoyé
@client.event
async def on_message(message):
    
    if message.author == client.user:
        return
    print(f'On modifie le message envoyé')
    await replace_urls_in_message(message)
                                      
  
# Effectue la modification lorsqu'un message est modifié  
@client.event
async def on_message_edit(before, after):
    
    if after.author == client.user:
        return
    print(f'On modifie le message modifié')
    print(after.content)
    await replace_urls_in_message(after)                    
        

                                
async def replace_urls_in_message(message):
    global envoye
    if envoye == 0 :
        envoye = 1
    else :
        envoye = 0
        return

    # Rechercher les URLs x.com dans le message
    urls = re.findall(r'https?://(x\.com|twitter\.com)/\S+', message.content)
    
    modified_message = message.content # Récupération du message
    target_channel = message.channel  # Par défaut, le même canal que le message original
    
    # Extraire le mot-clé (nom du canal) s'il est spécifié
    keyword_match = re.findall(r' ([\w-]+)$', modified_message)
    modified_message = re.sub(r' [\w-]+$', '', modified_message)  # Supprimer le mot-clé du message

    if urls:
        for url in urls:
            new_url = url.replace('twitter.com', 'vxtwitter.com').replace('x.com', 'vxtwitter.com')
            modified_message = modified_message.replace(url, new_url)
            
        if keyword_match:
            print(keyword_match)
            keyword = keyword_match[0]
            # Chercher le canal par mot-clé
            for channel in message.guild.text_channels:
                if channel.name == keyword:
                    target_channel = channel
                    break
            
        
        # Envoyer le message modifié dans le canal cible
        await target_channel.send(modified_message)        

        # Supprimer le message original
        await message.delete()  
    else :
        for word in keyword_match:
            # Chercher le canal par mot-clé
            for channel in message.guild.text_channels:
                if channel.name == word:
                    target_channel = channel
                    
                    # Envoyer le message modifié dans le canal cible
                    await target_channel.send(modified_message)
                    
                    # Supprimer le message original
                    await message.delete()
                    break         

    
                   
client.run(TOKEN)
