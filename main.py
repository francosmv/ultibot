import os
import discord
from dotenv import load_dotenv
import random
import math
import asyncio

#TODO: This won't work if the bot is active in multiple guilds
global ready_session
global active_session

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

ready_session = None
active_session = None

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
    async def create_session(self, message, exclude_players):
        global ready_session
        self.guild = message.guild
        self.cmd_channel = message.channel
        self.neutral_vc = message.author.voice.channel
        if(self.neutral_vc != None):
            player_list = self.neutral_vc.members
            for p in player_list:
                if p in exclude_players:
                    player_list.remove(p)
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
        else: # User not in a channel on that server
            await self.cmd_channel.send("You must be in a voice channel to generate teams")
            raise gameStateException()
    async def start_session(self):
        global ready_session
        global active_session
        if(ready_session != self):
            raise gameStateException
        if(active_session != None):
            #TODO: ping user who reacted telling them you can't start a new session until you close out the old session
            raise gameStateException
        #TODO: Should this be atomic?
        ready_session = None
        active_session = self
        #Need to re-get the teams message otherwise reactions won't be updated
        self.teams_msg = await self.cmd_channel.fetch_message(self.teams_msg.id)
        await self.move_players(self.team_blu, "blu")
        await self.move_players(self.team_red, "red")
        #Wait before re-configuring reactions so that people don't accidentally immediately click the cancel reaction
        await asyncio.sleep(5)
        for r in self.teams_msg.reactions:
            await self.teams_msg.clear_reaction(r)
        red_x_emoji = "\U0000274C"
        await self.teams_msg.add_reaction(red_x_emoji)
        print("Game session started")
    async def end_session(self):
        global active_session
        await self.move_players(self.team_blu, self.neutral_vc.name)
        await self.move_players(self.team_red, self.neutral_vc.name)
        print("game session ended")
        active_session = None
    async def move_players(self, player_list, chan_name):
        chan = discord.utils.get(self.guild.voice_channels, name=chan_name)
        if(chan == None):
            await self.guild.create_voice_channel(chan_name)
        for player in player_list:
            await player.move_to(chan)
    def create_team_list_str(self, team):
        team_list_str = ""
        for player in team:
            team_list_str = team_list_str + player.name + "\n"
        if team_list_str == "":
            team_list_str = "-"
        return team_list_str
    def print_teams(self):
        # Create and send the team table to the channel
            embed = discord.Embed(title=f"**Teams:**", color=0x00109c)
            embed.add_field(name=f"**BLU**", value=self.create_team_list_str(self.team_blu), inline=True)
            embed.add_field(name=f"**RED**", value=self.create_team_list_str(self.team_red), inline=True)
            return embed

# Adding members to intents prevents reliability issues in fetching member lists and such
intents = discord.Intents().default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    bot_cmd = ""
    #catch exceptions for empty messages - we don't want to do anything with empty messages so just leave the event
    try:
        if(message.content[0] == '!'):
            bot_cmd = message.content[1:]
    except IndexError:
        return

    bot_cmd_split = bot_cmd.split()
    if(bot_cmd_split[0] == "game"):
        exclude_players = []
        exclude_players_str = ""
        
        for i in range(len(bot_cmd_split)):
            if(bot_cmd_split[i] == "exc"):
                exclude_players_str = bot_cmd_split[i+1:]
                break
        for p in exclude_players_str:
            exclude_players.append(discord.utils.get(message.guild.members, id=int(p[3:-1])))
        try:
            session = game_session()
            await session.create_session(message, exclude_players)
        except gameStateException as e:
            return
    elif(bot_cmd_split[0] == "end"):
        if(active_session != None):
            active_session.end_session()
    # elif(bot_cmd == "rollmap")
    # elif(bot_cmd == "addmap")
    # elif(bot_cmd == "delmap")
    # elif(bot_cmd == "gamemap")
    # elif(bot_cmd == "rollclass")
                
@client.event
async def on_reaction_add(reaction, user):
    if( not user.bot ):
        if(reaction.emoji == "\U00002705"): #green check
            # TODO: Probably don't want to let people who aren't in the game start a game
            if(ready_session != None and reaction.message == ready_session.teams_msg):
                await ready_session.start_session()
        elif(reaction.emoji == "\U0000274C"): #red x
            if(active_session != None and reaction.message == active_session.teams_msg):
                await active_session.end_session()

client.run(TOKEN)
