import os
import discord
from dotenv import load_dotenv
import random
import math
import asyncio
import json

#TODO: Make settings be per-server
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#TODO: if we pass in a dict of defaults on init this will work for both global settings and per-server settings
class settings_container:
    def __init__(self, filename):
        self.filename = filename + ".json"
        with open(self.filename, "r+") as settings_file:
            try:
                self.settings_dict = json.load(settings_file)
            except json.JSONDecodeError:
                self.settings_dict = dict()
        self.validate_dict()
        self.dump_settings()
    def validate_dict(self):
        if("split_vc" not in self.settings_dict):
            self.settings_dict["split_vc"] = False
        if("active_channels" not in self.settings_dict):
            self.settings_dict["active_channels"] = []
        if("red_vc" not in self.settings_dict):
            self.settings_dict["red_vc"] = "red"
        if("blu_vc" not in self.settings_dict):
            self.settings_dict["blu_vc"] = "blu"
    def dump_settings(self):
        with open(self.filename, "w") as settings_file:
            json.dump(self.settings_dict, settings_file, indent=2)


ready_session = None
active_session = None

# Adding members to intents prevents reliability issues in fetching member lists and such
intents = discord.Intents().default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)
global_settings = settings_container("global_settings")

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
        global global_settings
        self.guild = message.guild
        self.cmd_channel = message.channel
        if(message.author.voice != None):
            self.neutral_vc = message.author.voice.channel
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
            if global_settings.settings_dict["split_vc"]:
                check_emoji="\U00002705"
                await self.teams_msg.add_reaction(check_emoji)
            ready_session = self
        else: # User not in a channel on that server
            await self.cmd_channel.send("You must be in a voice channel to generate teams")
            raise gameStateException()
    async def start_session(self):
        global ready_session
        global active_session
        global global_settings
        if global_settings.settings_dict["split_vc"]:
            if(ready_session != self):
                raise gameStateException
            if(active_session != None):
                #TODO: ping user who reacted telling them you can't start a new session until you close out the old session
                raise gameStateException
            #Need to re-get the teams message otherwise reactions won't be updated
            self.teams_msg = await self.cmd_channel.fetch_message(self.teams_msg.id)
            #Require that every player in the game add a checkmark reaction to actually start the game
            game_ready = True
            player_ready_list = []
            for p in self.team_blu:
                player_ready_state = (p, False)
                player_ready_list.append(player_ready_state)
            for p in self.team_red:
                player_ready_state = (p, False)
                player_ready_list.append(player_ready_state)
            for r in self.teams_msg.reactions:
                if(r.emoji == "\U00002705"):
                    async for u in r.users():
                        for p in player_ready_list:
                            if p[0].id == u.id:
                                ready_state = (p[0], True)
                                player_ready_list.append(ready_state)
                                player_ready_list.remove(p)
                                break
            for p in player_ready_list:
                if p[1] == False:
                    game_ready = False
            if game_ready:
                #TODO: Should this be atomic?
                ready_session = None
                active_session = self
                #TODO: create the channels first if they don't exist, wait, then move into channel
                await self.move_players(self.team_blu, global_settings.settings_dict["blu_vc"])
                await self.move_players(self.team_red, global_settings.settings_dict["red_vc"])
                #Wait before re-configuring reactions so that people don't accidentally immediately click the cancel reaction
                await asyncio.sleep(5)
                for r in self.teams_msg.reactions:
                    await self.teams_msg.clear_reaction(r)
                red_x_emoji = "\U0000274C"
                await self.teams_msg.add_reaction(red_x_emoji)
            print("Game session started")
    async def end_session(self):
        global active_session
        global global_settings
        if global_settings.settings_dict["split_vc"]:
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

async def print_vc_config(message):
    global global_settings
    embed = discord.Embed(title=f"**Voice Channel Configuration:**", color=0x00109c)
    embed.add_field(name=f"**BLU**", value=global_settings.settings_dict["blu_vc"], inline=True)
    embed.add_field(name=f"**RED**", value=global_settings.settings_dict["red_vc"], inline=True)
    await message.channel.send(embed=embed)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    global global_settings
    global active_session
    global ready_session
    bot_cmd = ""
    #catch exceptions for empty messages - we don't want to do anything with empty messages so just leave the event
    try:
        if(message.content[0] == '!'):
            bot_cmd = message.content[1:]
    except IndexError:
        return
    if(len(bot_cmd) > 0):
        bot_cmd_split = bot_cmd.split()
        if(bot_cmd_split[0] == "addchannel"): #this is the only message the bot listens for on every channel - so that server owners can restrict the bot to certain channels
            print(message.channel.id)
            global_settings.settings_dict["active_channels"].append(message.channel.id)
            global_settings.dump_settings()
            await message.channel.send("Adding current channel to active channels")
        else:
            if(message.channel.id in global_settings.settings_dict["active_channels"]):
                if(bot_cmd_split[0] == "game"):
                    exclude_players = []
                    exclude_players_str = ""
                    
                    for i in range(len(bot_cmd_split)):
                        if(bot_cmd_split[i] == "exc"):
                            exclude_players_str = bot_cmd_split[i+1:]
                            break
                    for p in exclude_players_str:
                        if(p[0] == '<'):
                            exclude_players.append(discord.utils.get(message.guild.members, id=int(p[2:-1])))
                            print(exclude_players)
                    try:
                        session = game_session()
                        await session.create_session(message, exclude_players)
                    except gameStateException as e:
                        return
                elif(bot_cmd_split[0] == "end"):
                    if(active_session != None):
                        await active_session.end_session()
                elif(bot_cmd_split[0] == "cancel"):
                    ready_session = None
                elif(bot_cmd_split[0] == "splitvcenable"):
                    if(active_session != None):
                        await message.channel.send("Cannot configure voicechat settings while game session is active")
                    else:
                        global_settings.settings_dict["split_vc"] = True
                        global_settings.dump_settings()
                        await message.channel.send("Voice chat splitting enabled")
                elif(bot_cmd_split[0] == "splitvcdisable"):
                    if(active_session != None):
                        await message.channel.send("Cannot configure voicechat settings while game session is active")
                    else:
                        global_settings.settings_dict["split_vc"] = False
                        global_settings.dump_settings()
                        await message.channel.send("Voice chat splitting disabled")
                elif(bot_cmd_split[0] == "removechannel"):
                    global_settings.settings_dict["active_channels"].remove(message.channel.id)
                    await message.channel.send("Current channel removed from active channels")
                elif(bot_cmd_split[0] == "showvc"):
                    await print_vc_config(message)
                elif(bot_cmd_split[0] == "redvc"):
                    if(len(bot_cmd_split) > 1):
                        global_settings.settings_dict["red_vc"] = bot_cmd_split[1]
                        global_settings.dump_settings()
                        await print_vc_config(message)
                    else:
                        await message.channel.send("missing voice channel argument")
                elif(bot_cmd_split[0] == "bluvc"):
                    if(len(bot_cmd_split) > 1):
                        global_settings.settings_dict["blu_vc"] = bot_cmd_split[1]
                        global_settings.dump_settings()
                        await print_vc_config(message)
                    else:
                        await message.channel.send("missing voice channel argument")
                elif(bot_cmd_split[0] == "currentvc"):
                    if(message.author.voice == None):
                        await message.channel.send("You must be in a voice channel to use this command")
                    elif(len(bot_cmd_split) < 2):
                        await message.channel.send("missing team argument")
                    else:
                        if(bot_cmd_split[1] == "blu"):
                            global_settings.settings_dict["blu_vc"] = message.author.voice.channel.name
                            global_settings.dump_settings()
                            await print_vc_config(message)
                        elif(bot_cmd_split[1] == "red"):
                            global_settings.settings_dict["red_vc"] = message.author.voice.channel.name
                            global_settings.dump_settings()
                            await print_vc_config(message)
                        else:
                            await message.channel.send("Invalid team specified")
    # elif(bot_cmd == "resetconfig")
    # elif(bot_cmd == "showconfig")
    # elif(bot_cmd == "help")
    # elif(bot_cmd == "rollmap")
    # elif(bot_cmd == "addmap")
    # elif(bot_cmd == "delmap")
    # elif(bot_cmd == "gamemap")
    # elif(bot_cmd == "rollclass")
                
@client.event
async def on_reaction_add(reaction, user):
    if( not user.bot ):
        if(reaction.emoji == "\U00002705"): #green check
            if(ready_session != None and reaction.message == ready_session.teams_msg):
                await ready_session.start_session()
        elif(reaction.emoji == "\U0000274C"): #red x
            if(active_session != None and reaction.message == active_session.teams_msg):
                await active_session.end_session()

client.run(TOKEN)
