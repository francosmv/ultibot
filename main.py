import os
import discord
from dotenv import load_dotenv
import random
import math

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class gameStateException(Exception):
    pass

class game_session:
    def __init__(self, message):
        self.guild = msg_guild = message.guild
        self.cmd_channel = message.channel
        self.neutral_vc = None
        #TODO: Discord's get and find utils work way better than this
        for vc in self.guild.voice_channels:
            for member in vc.members:
                if member == message.author:
                    self.neutral_vc = vc
                    break
            if(self.neutral_vc != None):
                break
        if((self.neutral_vc != None) and (len(self.neutral_vc.members) > 1)):
            player_list = self.neutral_vc.members
            self.team_blu = []
            self.team_red = []
            #With odd number of players, this makes blu team always 1 bigger than red
            #TODO: On odd number of players, leave out one member, rotate who gets left out
            team_blu_sz = math.ceil(len(player_list)/2)
            for i in range(team_blu_sz):
                print(len(player_list))
                idx = random.randint(0, len(player_list)-1)
                self.team_blu.append(player_list[idx])
                del player_list[idx]
            self.team_red = player_list
        elif(self.neutral_vc != None): # Have to have two members in voice channel, makes it so I don't have to deal with empty lists
            raise gameStateException("You must have at least two members in your voice channel to generate teams")
        else: # User not in a channel on that server
            raise gameStateException("You must be in a voice channel to generate teams")

    def print_teams(self):
        # Create and send the team table to the channel
            embed = discord.Embed(title=f"__**Teams:**__", color=0x00109c)
            #TODO: gross, make this a function
            team_blu_list_str = ""
            team_red_list_str = ""
            for player in self.team_blu:
                team_blu_list_str = team_blu_list_str + player.name + "\n"
            for player in self.team_red:
                team_red_list_str = team_red_list_str + player.name + "\n"
            embed.add_field(name=f"**BLU**", value=team_blu_list_str, inline=True)
            embed.add_field(name=f"**RED**", value=team_red_list_str, inline=True)
            return embed
    def register_session_ready(self, message):
        self.teams_msg = message
        # Set the global ready session to self


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
        #TODO: Set game_session up to work correctly with async stuff so that these steps can just be put in the constructor
        try:
            session = game_session(message)
        except gameStateException as e:
            await message.channel.send(e)
            return
        teams_msg = await session.cmd_channel.send(embed=session.print_teams())
        check_emoji="\U00002705"
        await teams_msg.add_reaction(check_emoji)
        session.register_session_ready(teams_msg)

    # elif(bot_cmd == "rollmap")
    # elif(bot_cmd == "addmap")
    # elif(bot_cmd == "delmap")
    # elif(bot_cmd == "gamemap")
    # elif(bot_cmd == "rollclass")
                
@client.event
async def on_reaction_add(reaction, user):
    #If reaction is the green checkmark:
        # check if reaction message is game session ready object's table message
            #if so, tell game session ready object to set itself as the active session
    #If reaction is the red x:
        # check if reaction message is game session active object's table message
            #if so, tell game session active object to die
    pass

client.run(TOKEN)