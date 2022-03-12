import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    bot_cmd = ""
    try:
        if(message.content[0] == '!'):
            bot_cmd = message.content[1:]
    except IndexError:
        return

    if( bot_cmd == "game"):
            msg_guild = message.guild
            for vc in msg_guild.voice_channels:
                for member in vc.members:
                    if member == message.author:
                        print("TEST")

client.run(TOKEN)