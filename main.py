import os
import discord
from dotenv import load_dotenv
import random
import math

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    bot_cmd = ""
    #catch exceptions for empty messages - we don't want to do anything with empty messages to just leave the event
    try:
        if(message.content[0] == '!'):
            bot_cmd = message.content[1:]
    except IndexError:
        return

    if(bot_cmd == "game"):
        #TODO: This has to be server aware
        msg_guild = message.guild
        msg_channel = message.channel
        user_vc = None
        #TODO: Discord's get and find utils work way better than this
        for vc in msg_guild.voice_channels:
            for member in vc.members:
                if member == message.author:
                    user_vc = vc
                    break
            if(user_vc != None):
                break
        if((user_vc != None) and (len(user_vc.members) > 1)):
            player_list = user_vc.members
            team_blu = []
            team_red = []
            #With odd number of players, this makes blu team always 1 bigger than red
            #TODO: On odd number of players, leave out one member, rotate who gets left out
            team_blu_sz = math.ceil(len(player_list)/2)
            for i in range(team_blu_sz):
                print(len(player_list))
                idx = random.randint(0, len(player_list)-1)
                team_blu.append(player_list[idx])
                del player_list[idx]
            team_red = player_list
            print(team_blu)
            print(team_red)

            embed = discord.Embed(title=f"__**Teams:**__", color=0x00109c)
            #TODO: gross, make this a function
            team_blu_list_str = ""
            team_red_list_str = ""
            for player in team_blu:
                team_blu_list_str = team_blu_list_str + player.name + "\n"
            for player in team_red:
                team_red_list_str = team_red_list_str + player.name + "\n"
            embed.add_field(name=f"**BLU**", value=team_blu_list_str, inline=True)
            embed.add_field(name=f"**RED**", value=team_red_list_str, inline=True)
            await msg_channel.send(embed=embed)
        elif((user_vc != None) and (len(user_vc.members) < 2)): # Have to have two members in voice channel, makes it so I don't have to deal with empty lists
            await msg_channel.send("You must have at least two members in your voice channel to generate teams")
        else: # User not in a channel on that server
            await msg_channel.send("You must be in a voice channel to generate teams")
            
    # elif(bot_cmd == "rollmap")
    # elif(bot_cmd == "addmap")
    # elif(bot_cmd == "delmap")
    # elif(bot_cmd == "gamemap")
    # elif(bot_cmd == "rollclass")
                

client.run(TOKEN)