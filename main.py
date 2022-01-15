import discord
from discord.ext import commands
import configparser
import graphs
import valorant
import elo_history_updater
import requests
import json
import malsearch
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
import random
import playerclass
import personClass
import csv

def get_config():
    c = configparser.ConfigParser()
    c.read('/home/ubuntu/discord_bot/config.ini')

    return c['discord']['token'], c['cat']['api']

token = get_config()[0]

help_command = commands.DefaultHelpCommand(no_category = 'Commands')
client = commands.Bot(command_prefix='$',help_command = help_command)
slash = SlashCommand(client, sync_commands=True)
guild_ids = [509314650265878530, 731539222141468673]

@client.event
async def on_ready():
    print("it started working")

@slash.slash(description="Choices for Valorant",
             guild_ids=guild_ids,
             options = [
             create_option(name="randomise", description="returns random thing", option_type=3, required=False, 
                        choices=[create_choice(name="account",value="account"), create_choice(name="gamemode",value="gamemode"),
                        create_choice(name="weapon",value="weapon"), create_choice(name="agent",value="agent"),
                        create_choice(name="map",value="map")]),
             create_option(name="tactic", description="returns the plays for this round", option_type=3, required=False, 
                        choices=[create_choice(name="attacking",value="attacking"), create_choice(name="defending",value="defending")])])
async def choice(ctx, randomise="", tactic=""):
    
    if randomise == "account":
        await ctx.send(random.choice(['Smurfs', 'Smurfs', 'Smurfs', 'Smurfs', 'Mains', 'Mains', 'Mains', 'Mains', 'Mains', 'Mains']))
    
    if randomise == "gamemode":
        await ctx.send(random.choice(['Unrated', 'Competitive']))

    if randomise == "weapon":
        sidearm = ["Classic", "Shorty", "Frenzy", "Ghost", "Sheriff"]
        SMG = ["Stinger", "Spectre"]
        Shotgun = ["Bucky"]
        Rifle = ["Bulldog", "Guardian", "Phantom", "Vandal"]
        Sniper = ["Marshal", "Operator"]
        MG = ["Ares", "Odin"]
        selected = random.choice([sidearm, SMG, Shotgun, Rifle, Sniper, MG])
        await ctx.send(random.choice(selected))
    
    if randomise == "agent":
        await ctx.send(random.choice(["Astra", "Breach", "Brimstone", "Chamber", "Cypher", "Jett", "Killjoy", "Kay/O",
                                     "Omen", "Phoenix", "Raze", "Reyna", "Sage", "Skye", "Sova", "Viper", "Yoru"]))

    if randomise == "map":
        await ctx.send(random.choice(["Bind", "Haven", "Split", "Ascent", "Icebox", "Breeze"]))

    if tactic == "attacking":
        await ctx.send(random.choice(["Rush A", "Rush B", "Rush C", "Cowboy Time", "Hide in spawn", "Split push",
                                        "Odin go brrr", "just ff", "Camp in corners", "Snipers only", "Pistol Prodigy"]))
    if tactic == "defending":
        await ctx.send(random.choice(["Everyone on A", "Everyone on B", "Everyone on C", "Cowboy Time", "Hide in spawn till plant",
                                        "Odin go brrr", "just ff", "Camp in corners", "Snipers only", "Pistol Prodigy"]))

@client.command()
async def cat(ctx):
    url = "https://api.thecatapi.com/v1/images/search?format=json"

    payload={}
    files={}
    headers = {
    'Content-Type': 'application/json',
    'x-api-key': get_config()[1]
    }

    response = requests.request("GET", url, headers=headers, data=payload, files=files)

    embed = discord.Embed(title="cat")
    embed.set_image(url=json.loads(response.text)[0]['url'])

    await ctx.send(embed=embed)

@slash.slash(description="MMR history list",
             guild_ids=guild_ids,
             options = [
             create_option(name="username", description="enter username (ign#tag)", option_type=3, required=True)])
async def elolist(ctx, username=""):
    
    username = username.split('#')[0].lower()
    elolist = valorant.get_elo_list(username)
    await ctx.send("```\n" + elolist + "\n```")

@slash.slash(description="Ranked statistics for all acts",
             guild_ids=guild_ids,
             options = [
             create_option(name="username", description="enter username (ign#tag)", option_type=3, required=True)])
async def stats(ctx, username=""):

    the_message = await ctx.send("fetching stats...")
    username = username.split('#')

    ign = username[0].lower()

    if len(username) == 2:
        tag = username[1].lower()
    else:
        tag = ""

    fields = valorant.stats(ign, tag)

    if type(fields) == str:
        await the_message.edit(content=fields)
    
    else:
        data = fields[0]
        card = fields[1]
        embed=discord.Embed(title = "Competitive Statistics", description="", color=0x00f900)
        embed.set_author(name=ign, url = "https://youtu.be/MtN1YnoL46Q", icon_url=card)

        for field in data:
            embed.add_field(name = field[0], value = field[1], inline = True)

        await the_message.edit(contents = "", embed = embed)

@slash.slash(description="graph",
             guild_ids=guild_ids,
             options = [
             create_option(name="usernames", description="Enter username(s), seperate with commas for more than one", option_type=3, required=True)])
async def graph(ctx, usernames=""):
    users = usernames.split(',')
    
    for i in range(0, len(users)):
        users[i] = users[i].split('#')[0].lower().strip()

    if len(users) == 1:
        the_message = await ctx.send("please wait...")
        msg = ""
        flag = graphs.make_graph(users[0])
        if flag == False:
            await the_message.edit(content="Player not found or api being stupid, or it might even be aws :(")

        elif flag == None:
            await the_message.edit(content="Not enough data to plot graph")

        else:
            with open(f"/home/ubuntu/discord_bot/elo_graphs/{users[0]}.png", 'rb') as f:
                picture = discord.File(f)
                await the_message.edit(content= "", file=picture)

    else:
        the_message = await ctx.send("please wait...")
        flag = graphs.multigraph(users)
        msg = ""
        if len(flag[0]) > 0:
            msg = "Players not found: "
            for elem in flag[0]:
                msg += elem + ", "
            msg = msg[:-2]

        if len(flag[1]) > 0:
            msg += '\n Players with not enough data to plot graph: '
            for elem in flag[1]:
                msg += elem + ", "
            msg = msg[:-2]

        if msg == "":
            with open("/home/ubuntu/discord_bot/elo_graphs/multigraph.png", 'rb') as f:
                picture = discord.File(f)
                await the_message.edit(content="", file=picture)
        
        else:
            await the_message.edit(content=msg)

@slash.slash(description="Valorant Leaderboards",
             guild_ids=guild_ids,
             options = [
             create_option(name="options", description="Region/options for leaderboard (leave blank for local)", option_type=3, required=False, 
                        choices=[create_choice(name="Update local leaderboard",value="update")
                        ,create_choice(name="Asia Pacific",value="ap"),
                        create_choice(name="Europe",value="eu"), create_choice(name="Korea",value="kr"),
                        create_choice(name="North America",value="na")
                        ])])
async def leaderboard(ctx, options=""):
    
    if options == "":

        log_file = open("/home/ubuntu/discord_bot/updater_log-2022.out",'r')
        lines = log_file.readlines()
        log_file.close()

        leaderboard = "Last updated at " + lines[-1].split(' ')[4] + ', ' + lines[-1].split(' ')[2] + '\n'
        valorant.local_leaderboard()
        f = open("leaderboard.txt", 'r')
        for x in f:
            leaderboard += x
        f.close()

        await ctx.send("```\n" + leaderboard + "\n```")
    
    if options == "update":
        the_message = await ctx.send("this is gonna take a while...")
        elo_history_updater.update_all_elo_history()
        valorant.local_leaderboard()
        leaderboard = ""
        f = open("leaderboard.txt", "r")
        for x in f:
            leaderboard += x
        f.close()
        
        await the_message.edit(content="```\n" + leaderboard + "\n```")

    if options == "ap" or options == "eu" or options == "kr" or options == "na":
        
        the_message = await ctx.send("fetching leaderboard...")
        rleaderboard = valorant.region_leaderboard(options)

        if rleaderboard:
            await the_message.edit(content="```\n" + rleaderboard + "\n```")

@slash.slash(description="Add player to database for leaderboard and stuff",
             guild_ids=guild_ids,
             options = [
             create_option(name="username", description="enter username (ign#tag)", option_type=3, required=True)])
async def add(ctx, username=""):

    username = username.split('#')

    if len(username) == 2:
        the_message = await ctx.send("please wait...")
        msg = valorant.add_player(username[0].lower(), username[1].lower())
        await the_message.edit(content=msg)

    else:
        await ctx.send("Player not found, check syntax: (ign#tag)")

@slash.slash(description="Remove player from list",
             guild_ids=guild_ids,
             options = [
             create_option(name="username", description="enter username (ign#tag)", option_type=3, required=True)])
async def remove(ctx, username=""):

    if ctx.author.id == 410771947522359296:
        username = username.split('#')

        ign = username[0].lower()
        tag = valorant.get_tag(ign)

        if tag:
            msg = valorant.remove_player(ign, tag)
            await ctx.send(msg)
        else:
            await ctx.send("Player not found, check syntax: (ign#tag)")
            
    else:
        await ctx.send("no.")

@client.command()
async def gettag(ctx, *, user):
    user = user.lower()
    if not valorant.get_tag(user):
        await ctx.send("Player not in database. add using /add")
    else:
        await ctx.send(f'{user}#{valorant.get_tag(user)}')

@client.command()
async def banner(ctx, *, username):

    username = username.split('#')
    ign = username[0].lower()

    if len(username) == 2:
        tag = username[1].lower()
    else:
        tag = valorant.get_tag(ign)

    if not tag:
        await ctx.send("Player not found, check syntax: (ign#tag)")
    
    else:
        msg = valorant.get_banner(ign, tag)

        if type(msg) == str:
            await ctx.send(msg)
        
        else:
            await ctx.send(file=discord.File('banner.png'))

@slash.slash(description="Changing your in-game name",
             guild_ids=guild_ids,
             options = [
             create_option(name="old_username", description="enter your old username", option_type=3, required=True),
             create_option(name="new_username", description="enter your new username (user#tag)", option_type=3, required=True)])
async def namechange(ctx, old_username="", new_username=""):

    if ctx.author.id == 410771947522359296:

        old = old_username.split('#')[0].lower()
        new_username = new_username.split('#')

        if len(new_username) != 2:
            await ctx.send("check syntax: (ign#tag)")
        
        else:
            the_message = await ctx.send("please wait...")
            new_ign = new_username[0].lower()
            new_tag = new_username[1].lower()

            if valorant.account_check(new_ign, new_tag):
                playerList = playerclass.PlayerList('playerlist.csv')
                playerList.load()
                if playerList.change_ign(old, new_ign, new_tag):
                    playerList.save()
                    await the_message.edit(content = f'{old} is now {new_ign}#{new_tag}')
                
                else:
                    await the_message.edit(content = f'{old} not found in database, check player list using `$getcsv`')
            
            else:
                await the_message.edit(content = f'{new_ign}#{new_tag} does not exist.')
            
    else:
        await ctx.send("ask faaez to do it.")

@client.command()
async def getcsv(ctx):

    playerList = playerclass.PlayerList('playerlist.csv')
    playerList.load()
    msg = ""

    for player in playerList.players:
        msg += str(player) + '\n'

    await ctx.send(content="```\n" + msg + "\n```")

@slash.slash(description="Valorant Servers Status", guild_ids=guild_ids)
async def serverstatus(ctx):
    the_message = await ctx.send("fetching statuses")
    await the_message.edit(content = valorant.servercheck())

@slash.slash(description="Lineup thing",
             guild_ids=guild_ids,
             options = [
             create_option(name="agent", description="Select agent to show lineup for", option_type=3, required=True, 
                        choices=[create_choice(name="Viper",value="viper")]),
             create_option(name="map", description="Select map to show lineup for", option_type=3, required=True, 
                        choices=[create_choice(name="Ascent",value="ascent")])])
async def lineup(ctx, agent="", map=""):

    if agent != "" and map != "":
        await ctx.send(f'https://atomic-potatos.github.io/Valorant-Lineups/agents/{agent}/{map}.html')

@slash.slash(description="Other Commands", guild_ids=guild_ids)
async def other(ctx):
    msg = "```List of other commands:\n"
    msg += "$banner ign#tag -> returns your current banner\n"
    msg += "$cat -> returns a random cat photo\n"
    msg += "$getcsv -> returns playerlist\n"
    msg += "$gettag ign -> returns full username if they're in playerlist)```"
    await ctx.send(msg)

@slash.slash(description="search MAL database",
             guild_ids=guild_ids,
             options = [create_option(name="anime_title", description="Enter an anime to search for", option_type=3, required=False),
             create_option(name="manga_title", description="Enter an manga to search for", option_type=3, required=False),
             create_option(name="character", description="Enter a character to search for", option_type=3, required=False),
             create_option(name="anime_stats", description="Enter an anime to get stats for", option_type=3, required=False),
             create_option(name="manga_stats", description="Enter an manga to get stats for", option_type=3, required=False)])
async def search(ctx, *, anime_title = "", manga_title = "", character = "", anime_stats = "", manga_stats = ""):
    
    if anime_title != "":
        msg = await ctx.send("Getting info for " + anime_title)
        anime = malsearch.animeSearch(anime_title)

        if anime == False:
            await ctx.send("dumb dumb api failed, try again.")
        
        elif anime == None:
            await ctx.send("Anime not found.")

        else:
            embed = discord.Embed(title="{} ({})".format(anime['eng_title'], anime['jap_title']), url=anime['url'], 
            description="Source: {}, Type: {}, Score: {}, Episodes: {}".format(anime['source'], anime['type'], anime['score'], anime["ep_count"]))

            embed.set_image(url=anime['image_url'])
            embed.add_field(name="Airing Dates:", value=anime["Airing_Dates"])
            embed.add_field(name="Genres:", value=anime["genres"])
            embed.add_field(name="Sequel", value=anime["sequel"])
            embed.add_field(name="Synopsis:", value=anime["synopsis"])
            embed.add_field(name="Opening Theme", value=anime["opening_themes"], inline=False)
            embed.add_field(name="Ending Theme", value=anime["ending_themes"], inline=False)
            embed.set_footer(text="Studios: {}, Licensors: {}".format(anime["studios"], anime["licensors"]))
            await msg.edit(content="", embed=embed)

    if manga_title != "":
        msg = await ctx.send("Getting info for " + manga_title)
        manga = malsearch.mangaSearch(manga_title)

        if manga == False:
            await ctx.send("dumb dumb api failed, try again.")
        
        elif manga == None:
            await ctx.send("Manga not found.")

        else:
            embed = discord.Embed(title="{} ({})".format(manga['eng_title'], manga['jap_title']), url=manga['url'], 
            description="Type: {}, Score: {}, Volumes: {}, Chapters: {}".format(manga['type'], manga['score'], manga["vol_count"], manga["chap_count"]))

            embed.set_image(url=manga['image_url'])
            embed.add_field(name="Publishing Dates:", value=manga["publishing"])
            embed.add_field(name="Genres:", value=manga["genres"])
            embed.add_field(name="Authors:", value=manga["authors"])
            embed.add_field(name="Synopsis:", value=manga["synopsis"])
            embed.set_footer(text="Serialisations: {}".format(manga["serialisations"]))
            await msg.edit(content="", embed=embed)

    if character != "":
        msg = await ctx.send("Getting info for " + character)
        character = malsearch.characterSearch(character)

        if character == False:
            await ctx.send("dumb dumb api failed, try again.")
        
        elif character == None:
            await ctx.send("Character not found.")

        else:
            embed = discord.Embed(title=character['name'], url=character['url'],
                                    description="Member favourites: " + str(character['member_favourites']))

            embed.set_image(url=character['image_url'])
            embed.add_field(name="Description", value=character["description"], inline=False)
            embed.add_field(name="Anime:", value=character["anime"], inline=False)
            embed.add_field(name="Manga:", value=character["manga"], inline=False)
            embed.add_field(name="Voice Actors:", value=character["voice_actors"], inline=False)
            
            await msg.edit(content="", embed=embed)

    if anime_stats != "":
        msg = await ctx.send("Getting stats for " + anime_stats)
        anime = malsearch.animeStats(anime_stats)

        if anime == False:
            await ctx.send("dumb dumb api failed, try again.")
        
        elif anime == None:
            await ctx.send("Character not found.")

        else:
            file=discord.File(fp="/home/ubuntu/discord_bot/image.png", filename='image.png')
            embed = discord.Embed(title=anime['title'], url=anime['url'])

            embed.set_image(url="attachment://image.png")

            embed.add_field(name="Other stats:", 
            value="Completed: {}\nWatching: {}\nPlan to watch: {}\nDropped: {}\nOn Hold: {}\nTotal: {}".format(
                anime["completed"], anime["watching"], anime["plan_to_watch"], anime["dropped"],
                anime["on_hold"], anime["total"]),
            inline=False)
            
            await msg.edit(content="", file=file, embed=embed)

    if manga_stats != "":
        msg = await ctx.send("Getting stats for " + manga_stats)
        manga = malsearch.mangaStats(manga_stats)

        if manga == False:
            await ctx.send("dumb dumb api failed, try again.")
        
        elif manga == None:
            await ctx.send("Character not found.")

        else:
            file=discord.File(fp="/home/ubuntu/discord_bot/image.png", filename='image.png')
            embed = discord.Embed(title=manga['title'], url=manga['url'])

            embed.set_image(url="attachment://image.png")

            embed.add_field(name="Other stats:", 
            value="Completed: {}\nReading: {}\nPlan to read: {}\nDropped: {}\nOn Hold: {}\nTotal: {}".format(
                manga["completed"], manga["reading"], manga["plan_to_read"], manga["dropped"],
                manga["on_hold"], manga["total"]),
            inline=False)
            
            await msg.edit(content="", file=file, embed=embed)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith('good evening'):
        await message.channel.send(file=discord.File('good_evening.mp4'))
    
    if "wow" in message.content.lower() and message.author.id == 897988862658367549:
        await message.add_reaction("<:stevens:785800069957943306>")

    if message.content.lower().startswith('$lastupdate'):
        f = open("/home/ubuntu/discord_bot/updater_log-2022.out", "r")
        last = f.readlines()[-1]
        f.close()

        await message.channel.send(last)

    if message.guild is None and not message.author.bot:
        file = open('peoplecodes.txt','r')
        anonIDs = file.readlines()
        file.close()

        for i in range(0, len(anonIDs)):
            anonIDs[i] = anonIDs[i].strip()

        dontlook = []
        with open("dontlook.csv", "r") as f:
            reader = csv.reader(f, delimiter="\t")
            for i, line in enumerate(reader):
                dontlook.append(line[0].split(','))

        Faaez =     personClass.Person("faaez",     410771947522359296, anonIDs[0])
        #faq =       personClass.Person("faq",       776365641576742932, anonIDs[1])
        Dhiluka =   personClass.Person("dhiluka",   305132419474784257, anonIDs[2])
        Rasindu =   personClass.Person("rasindu",   285341337899761673, anonIDs[3])
        Dylan =     personClass.Person("dylan",     236820135254425600, anonIDs[4])
        Josh =      personClass.Person("josh",      389600778651959296, anonIDs[5])
        Vivian =    personClass.Person("vivian",    261818489159811072, anonIDs[6])
        Ethan =     personClass.Person("ethan",     400499749263769600, anonIDs[7])
        Albert =    personClass.Person("albert",    284881791335006209, anonIDs[8])
        Henry =     personClass.Person("henry",     290323655437713419, anonIDs[9])
        Joseph =    personClass.Person("joseph",    219270614362488832, anonIDs[10])
        Darren =    personClass.Person("darren",    286762644067713035, anonIDs[11])
        Delwyn =    personClass.Person("delwyn",    389687347605798913, anonIDs[12])
        Hadi =      personClass.Person("hadi",      251576622698856449, anonIDs[13])
        Will =      personClass.Person("will",      409908597397389313, anonIDs[14])
        Chris =     personClass.Person("chris",     320792211174195210, anonIDs[15])

        receiver = None
        people = [Faaez, Rasindu, Dhiluka, Dylan, Josh, Vivian, Ethan, Albert, Henry, Joseph, Darren, Delwyn, Hadi, Will, Chris]

        name = message.content.split(' ')[0]
        words = message.content.replace(name, '')

        if name.lower() == 'reply':
            anonReceiverID = message.content.split(' ')[1]
            words = message.content.replace(name, '')
            words = words.replace(anonReceiverID, '')

            for person in people:
                if int(person.anonID) == int(anonReceiverID):
                    receiver = person
                    break
            
            if receiver == None:
                await message.author.send("invalid ID")

            else:
                flag = False
                for i in range(0, len(dontlook)):
                    if message.author.id == int(dontlook[i][0]):
                        if int(dontlook[i][2]) < 7:
                            dontlook[i][2] = int(dontlook[i][2]) + 1
                            flag = True
                            break

                if flag:
                    receiverUser = await client.fetch_user(receiver.discordID)
                    await receiverUser.send("reply: \n" + words.strip())
                    await message.author.send("message sent")
                
                else:
                    await message.author.send("message limit reached")

        else:
            for person in people:
                if person.discordID == message.author.id:
                    sender = person
                    break

            for person in people:
                if person.name == name:
                    receiver = person
                    break
            
            if receiver == None:
                await message.author.send("incorrect format, please provide name")
            
            else:
                flag = False
                for i in range(0, len(dontlook)):
                    if dontlook[i][0] == str(sender.discordID):
                        if dontlook[i][1] == '0':
                            dontlook[i][1] = str(receiver.anonID)
                            dontlook[i][2] = int(dontlook[i][2]) + 1
                            flag = True
                        else:
                            if dontlook[i][1] == str(receiver.anonID) and int(dontlook[i][2]) < 7:
                                dontlook[i][2] = int(dontlook[i][2]) + 1
                                flag = True
                        break

                if flag:
                    receiverUser = await client.fetch_user(receiver.discordID)
                    await receiverUser.send(words.strip() + '\nfrom: ' + str(sender.anonID)) 
                    await message.author.send("message sent")
                else:
                    await message.author.send("you cant send a message to that person or message limit reached")

        csvfile = open('dontlook.csv', 'w')
        for line in dontlook:
            csvfile.write(str(line[0]) + ',' + str(line[1]) + ',' + str(line[2]) + '\n')
        csvfile.close()

    await client.process_commands(message)


client.run(token)