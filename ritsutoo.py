import discord
from discord.ext import commands
import configparser
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
import matchClass
from discord_components import *
import random

m = ""
match = None

def get_config():
    c = configparser.ConfigParser()
    c.read('/home/ubuntu/discord_bot/config.ini')

    return c['discord']['kenma']

token = get_config()

client = commands.Bot(command_prefix='!')
slash = SlashCommand(client, sync_commands=True)

guild_ids = [731539222141468673]

@client.event
async def on_ready():
    DiscordComponents(client, change_discord_methods=True)
    print("it started working")

@client.command()
async def button(ctx):
     await ctx.send(type=InteractionType.ChannelMessageWithSource, content="Message Here", 
     components=[Button(style=ButtonStyle.URL, label="Example Invite Button", url="https://google.com"), 
     Button(style=ButtonStyle.blue, label="Default Button", custom_id="xbutton")])


@client.command()
async def open(ctx):
    blue = ["Possibly", "No"]
    blueresult = random.choice(blue)
    em = discord.Embed(title= f"Congratulations!",description =f"The result is **{blueresult}**!",color = discord.Color.blue())

    yes = Button(style=ButtonStyle.green, label="Yes")
    no = Button(style=ButtonStyle.red, label="No")

    global m
    m = await ctx.send(embed = em,components=[[no,yes]])

@client.command()
async def lower(ctx, *, word):
    
    word = word.lower()
    await ctx.send(word)
'''
@slash.slash(description="Information on last 5 games",
             guild_ids=guild_ids,
             options = [create_option(name="username", description="Enter Username (username#tag)", option_type=3, required=True),
             create_option(name="game", description="Select game to get info on", option_type=3, required=True, 
                choices=[create_choice(name="1",value="1"), create_choice(name="2",value="2"),
                         create_choice(name="3",value="3"),create_choice(name="4",value="4"), create_choice(name="5",value="5")]),

             create_option(name="type", description="Select type of information", option_type=3, required=True,
                choices=[create_choice(name="overview",value="overview"), create_choice(name="round-by-round",value="round-by-round")])])
async def games(ctx, username, game, type):
'''
@client.command()
async def games(ctx, *, input):

    username, game, type = input.split(' ')

    if len(username.split('#')) != 2:
        await ctx.send("invalid player name")
    
    else:
        the_message = await ctx.send("please wait...")
        ign, tag = username.split('#')
        data = matchClass.get_data(ign.lower(), tag.lower(), game)

        if data == "invalid game index":
            await the_message.edit(content="invalid game index")

        elif data == False:
            await the_message.edit(content="Player not found")

        else:
            global match
            match = matchClass.Match(data['metadata']['map'], data['metadata']['mode'], 
                                     data['metadata']['matchid'], data['metadata']['game_start'])

            match.setScore(username, data['teams'])
            match.addPlayers(data['players']['red'], 'red')
            match.addPlayers(data['players']['blue'], 'blue')
            
            i = 1
            for round in data['rounds']:
                tempRound = matchClass.Round(round['winning_team'], round['end_type'], 
                            round['bomb_planted'], round['bomb_defused'], i)

                tempRound.addEvents(round['player_stats'])
                match.addRound(tempRound)
                i += 1
        
            if type == 'overview':
                embed = discord.Embed(title = "Match Overview", 
                description=f'Time: {match.time}', color=0x00f900)
                embed.add_field(name = "Statistics:", 
                value = f'Type: {match.mode}\nMap: {match.map}\nWinner: {match.winner}\nScore: {match.getScore()}', inline = False)

                stats = match.getRedTeamStats()

                msg = ""
                for player in stats:
                    msg += f'{player[0]}/{player[1]}: \n'
                embed.add_field(name = "Red Team:", value = '```\n' + msg + '\n```', inline = True)
                
                msg = ""
                for player in stats:
                    msg += f'{player[2]} - {player[3]}\n'
                embed.add_field(name = "  ACS  -  K/D/A", value = '```\n' + msg + '\n```', inline = True)

                embed.add_field(name='\u200b', value='\u200b')

                stats = match.getBlueTeamStats()
                
                msg = ""
                for player in stats:
                    msg += f'{player[0]}/{player[1]}: \n'
                embed.add_field(name = "Blue Team:", value = '```\n' + msg + '\n```', inline = True)
                
                msg = ""
                for player in stats:
                    msg += f'{player[2]} - {player[3]}\n'
                embed.add_field(name = "  ACS  -  K/D/A", value = '```\n' + msg + '\n```', inline = True)

                embed.add_field(name='\u200b', value='\u200b')

                await the_message.edit(embed = embed)

            if type == 'round-by-round':
                nextR = Button(style=ButtonStyle.green, label="Next Round")
                lastR = Button(style=ButtonStyle.red, label="Last Round")
                nextE = Button(style=ButtonStyle.blue, label="Next Event")
                lastE = Button(style=ButtonStyle.blue, label="Last Event")

                round = match.rounds[0]
                event = round.events[0]
                match.setCurrentRound(round.number)
                round.setCurrentEvent(event.number)

                embed = discord.Embed(title = f"Round {round.number} Overview", color=0x00f900)
                eventStats = f'Killer: {event.killer}\nDeather: {event.deather}\nWeapon: {event.getWeapon()}'

                if round.plant == False:
                    roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\n'
                else:
                    roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\nDefuse: {round.defuse}'
                
                embed.add_field(name = "event details:", value = eventStats, inline = True)
                embed.add_field(name = "Damage events:", value = event.getStats(), inline = True)
                embed.add_field(name = "Round Stats:",value = roundStats, inline = False)

                await ctx.send(embed=embed, components=[[lastE,nextE],[lastR,nextR]])

@client.event
async def on_button_click(interaction):

    embed = discord.Embed(title = "this is the first one", description='woah', color=0x00f900)
    embed2 = discord.Embed(title = "this is the second one", description='yooo', color=0x00f900)

    nextR = Button(style=ButtonStyle.green, label="Next Round")
    lastR = Button(style=ButtonStyle.red, label="Last Round")
    nextE = Button(style=ButtonStyle.blue, label="Next Event")
    lastE = Button(style=ButtonStyle.blue, label="Last Event")
    
    if interaction.component.label.startswith("Yes"):
        await m.edit(embed = embed2)
    if interaction.component.label.startswith("No"):
        await m.edit(embed=embed)

    global match
    if interaction.component.label.startswith("Next Round"):
        round = match.nextRound()
        event = round.events[0]
        round.currentEvent = event

        if round == None:
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, content="That was the last round", components=[lastR])
        elif event == None:
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, content="That was the last event", components=[[lastE], [lastR,nextR]])
        else:
            embed = discord.Embed(title = f"Round {round.number} Overview", color=0x00f900)
            eventStats = f'Killer: {event.killer}\nDeather: {event.deather}\nWeapon: {event.getWeapon()}'

            if round.plant == False:
                roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\n'
            else:
                roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\nDefuse: {round.defuse}'
            
            embed.add_field(name = "event details:", value = eventStats, inline = True)
            embed.add_field(name = "Damage events:", value = event.getStats(), inline = True)
            embed.add_field(name = "Round Stats:",value = roundStats, inline = False)
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, embed=embed, components=[[lastE,nextE],[lastR,nextR]])
    
    if interaction.component.label.startswith("Last Round"):
        round = match.lastRound()
        event = round.events[0]
        round.currentEvent = event

        if round == None:
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, content="That was the first round", components=[nextR])
        elif event == None:
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, content="That was the first event", components=[[nextE], [lastR,nextR]])
        else:
            embed = discord.Embed(title = f"Round {round.number} Overview", color=0x00f900)
            eventStats = f'Killer: {event.killer}\nDeather: {event.deather}\nWeapon: {event.getWeapon()}'

            if round.plant == False:
                roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\n'
            else:
                roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\nDefuse: {round.defuse}'

            embed.add_field(name = "event details:", value = eventStats, inline = True)
            embed.add_field(name = "Damage events:", value = event.getStats(), inline = True)
            embed.add_field(name = "Round Stats:",value = roundStats, inline = False)
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, embed=embed, components=[[lastE,nextE],[lastR,nextR]])

    if interaction.component.label.startswith("Next Event"):
        round = match.currentRound
        event = round.nextEvent()

        if round == None:
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, content="That was the last round", components=[lastR])
        elif event == None:
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, content="That was the last event", components=[[lastE], [lastR,nextR]])
        else:
            embed = discord.Embed(title = f"Round {round.number} Overview", color=0x00f900)
            eventStats = f'Killer: {event.killer}\nDeather: {event.deather}\nWeapon: {event.getWeapon()}'

            if round.plant == False:
                roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\n'
            else:
                roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\nDefuse: {round.defuse}'
            
            embed.add_field(name = "event details:", value = eventStats, inline = True)
            embed.add_field(name = "Damage events:", value = event.getStats(), inline = True)
            embed.add_field(name = "Round Stats:",value = roundStats, inline = False)
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, embed=embed, components=[[lastE,nextE],[lastR,nextR]])

    if interaction.component.label.startswith("Last Event"):
        round = match.currentRound
        event = round.lastEvent()

        if round == None:
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, content="That was the first round", components=[nextR])
        elif event == None:
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, content="That was the first event", components=[[nextE], [lastR,nextR]])
        else:
            embed = discord.Embed(title = f"Round {round.number} Overview", color=0x00f900)
            eventStats = f'Killer: {event.killer}\nDeather: {event.deather}\nWeapon: {event.getWeapon()}'

            if round.plant == False:
                roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\n'
            else:
                roundStats = f'Winner: {round.winner}\nEnding: {round.ending}\nPlant:{round.plant}\nDefuse: {round.defuse}'
            
            embed.add_field(name = "event details:", value = eventStats, inline = True)
            embed.add_field(name = "Damage events:", value = event.getStats(), inline = True)
            embed.add_field(name = "Round Stats:",value = roundStats, inline = False)
            await interaction.respond(type=InteractionType.ChannelMessageWithSource, embed=embed, components=[[lastE,nextE],[lastR,nextR]])

client.run(token)