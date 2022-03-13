import os
import discord
from dotenv import load_dotenv
import random
import math

global ready_session

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

ready_session = None

class gameStateException(Exception):
    pass

class game_session:
    def __init__(self):
        self.guild = None
        self.cmd_channel = None
        self.neutral_vc = None
        self.team_blu = []
        self.team_red = []
        self.teams_msg = None
    async def create_session(self, message):
        global ready_session
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
            #With odd number of players, this makes blu team always 1 bigger than red
            #TODO: On odd number of players, leave out one member, rotate who gets left out
            team_blu_sz = math.ceil(len(player_list)/2)
            for i in range(team_blu_sz):
                idx = random.randint(0, len(player_list)-1)
                self.team_blu.append(player_list[idx])
                del player_list[idx]
            self.team_red = player_list
            self.teams_msg = await self.cmd_channel.send(embed=self.print_teams())
            check_emoji="\U00002705"
            await self.teams_msg.add_reaction(check_emoji)
            ready_session = self
        elif(self.neutral_vc != None): # Have to have two members in voice channel, makes it so I don't have to deal with empty lists
            await self.cmd_channel.send("You must have at least two members in your voice channel to generate teams")
            raise gameStateException()
        else: # User not in a channel on that server
            await self.cmd_channel.send("You must be in a voice channel to generate teams")
            raise gameStateException()
    def print_teams(self):
        # Create and send the team table to the channel
            embed = discord.Embed(title=f"**Teams:**", color=0x00109c)
            embed.add_field(name=f"**BLU**", value=self.create_team_list_str(self.team_blu), inline=True)
            embed.add_field(name=f"**RED**", value=self.create_team_list_str(self.team_red), inline=True)
            return embed
    def create_team_list_str(self, team):
        team_list_str = ""
        for player in team:
            team_list_str = team_list_str + player.name + "\n"
        return team_list_str


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
        #TODO: Add "exc" argument to tell bot to explicitly exclude a player
        print(ready_session)
        try:
            session = game_session()
            await session.create_session(message)
        except gameStateException as e:
            return
        print(ready_session)
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