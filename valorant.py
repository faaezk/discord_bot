import os
import math
import json
import random
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta

import config
import playerclass
from exceptionclass import *

endpoints = {   "LEADERBOARD" : "v3/leaderboard/{region}",
                "REGION_STATUS" : "v1/status/{region}",
                "CROSSHAIR" : "v1/crosshair/generate?id={crosshair_code}",
                "ACCOUNT_BY_NAME" : "v2/account/{ign}/{tag}",
                "ACCOUNT_BY_PUUID" : "v2/by-puuid/account/{puuid}",
                "MMR_BY_NAME" : "v3/mmr/ap/pc/{ign}/{tag}",
                "MMR_BY_PUUID" : "v3/by-puuid/mmr/ap/pc/{puuid}",
                "MMR_HISTORY_BY_NAME" : "v1/mmr-history/ap/{ign}/{tag}",
                "MMR_HISTORY_BY_PUUID" : "v1/by-puuid/mmr-history/ap/{puuid}"}

headers = {'accept' : 'application/json', 'Authorization' : config.get("HENRIK_KEY")}
errors = {
            1 : "Invalid API Key", 2 : "Forbidden endpoint", 3 : "Restricted endpoint", 
            101 : "No region found for this Player", 102 : "No matches found, can't get puuid", 
            103 : "Possible name change detected, can't get puuid. Please play one match, wait 1-2 minutes and try it again",
            104 : "Invalid region", 105 : "Invalid filter", 106 : "Invalid gamemode", 107 : "Invalid map", 108 : "Invalid locale",
            109 : "Missing name", 110 : "Missing tag", 111 : "Player not found in leaderboard", 112 : "Invalid raw type",
            113 : "Invalid match or player id", 114 : "Invalid country code", 115 : "Invalid season", 
            400 : "Not able to connect to API", 403 : 'Forbidden', 404 : 'User not found', 429 : 'welp', 500 : 'No matches available'
        }

def get_data(endpoint, **kwargs):
    global endpoints
    global headers
    global errors
    
    if "puuid_list" in kwargs.keys():
        session = requests.Session()
        data_list = []
        for puuid in kwargs['puuid_list']:
            try:
                url = config.get("HENRIK_URL") + endpoints[endpoint].format(**{'puuid' : puuid})
                data_list.append((puuid, parse_req(session.get(url, headers=headers), endpoint)))
            except Exception as e:
                data_list.append((puuid, {'error' : str(e)}))
        
        return data_list

    try:
        url = config.get("HENRIK_URL") + endpoints[endpoint].format(**kwargs)
    except KeyError:
        raise KeyException

    try:
        return parse_req(requests.get(url, headers=headers), endpoint)
    except Exception as E:
        raise E

def get_card_data(playercard_uuid):

    url = config.get() + f'playercards/{playercard_uuid}'
    try:
        r = requests.get(url)
        john = json.loads(r.text)
        return john
    except:
        if r.status_code in errors.keys():
            raise DynamicException(errors[r.status_code], r.status_code)
        else:
            raise UnknownException

def parse_req(r, endpoint):
    global endpoints
    global headers
    global errors

    if r.status_code == 504:
        raise DynamicException('Gateway Time-out', r.status_code)
    
    try:
        john = json.loads(r.text)
    except:
        if r.status_code in errors.keys():
            raise DynamicException(errors[r.status_code], r.status_code)
        else:
            raise UnknownException
    
    if ('errors' in john.keys()) and (len(john['errors']) > 0) and ('message' in john['errors'][0].keys()):
        raise DynamicException(john['errors'][0]['message'], r.status_code)
    
    if endpoint == 'CROSSHAIR':
        return r
    
    if r.status_code == 200:
        if endpoint == 'LEADERBOARD':
            return john

        if 'error' in john.keys() and john['error'] != None:
            DynamicException.set_message(john['error']['message'])
            raise DynamicException
        
        if 'errors' in john.keys():
            DynamicException.set_message(' '.join(john['errors']))
            raise DynamicException
        
        return john

    raise UnknownException

def get_file_mmr(puuid, date=False):

    if os.path.isfile(f"{config.get('MMR_HISTORY')}/{puuid}.txt") == False:
        return False
    
    with open(f"{config.get('MMR_HISTORY')}/{puuid}.txt", 'r') as f:
        for line in f:
            pass

    if line == '\n':
        return False

    #return the latest MMR value in file
    if date:
        return line.split(',')

    return int(line.split(',')[0])

def initialise_file(puuid):

    f = open(f"{config.get('MMR_HISTORY')}/{puuid}.txt", "x")
    f.close()

    f = open(f"{config.get('MMR_HISTORY')}/{puuid}.txt", "w")
    f.write('\n')
    f.close()

def replace_all(string: str, oldValues, newValue):
    for value in oldValues:
        string = string.replace(value, newValue)
    
    return string

def update_database(puuid, data=None):

    if data == None:
        try: 
            data = get_data('MMR_HISTORY_BY_PUUID', puuid=puuid)
        except Exception as E:
            raise E

    data = data['data']
    if len(data) == 0:
        raise NoneException

    if not os.path.isfile(f"{config.get('MMR_HISTORY')}/{puuid}.txt"):
        initialise_file(puuid)

    # Dates of last update
    date_raw = data[0]['date_raw']
    lines = []

    with open(f"{config.get('MMR_HISTORY')}/{puuid}.txt", 'r') as f:
        for line in f:
            lines.append(line)
    
    last_file_update = 0 if lines[0] == '\n' else int(lines[0])
    new_list = []

    if last_file_update == 0:
        for game in enumerate(data):
            thedate = replace_all(game['date'], [', ', ' '], '-')
            new_list.append(f"{game['elo']},{thedate}\n")

    else:
        if len(str(last_file_update)) == 13:
            if (len(str(date_raw)) == 10):
                last_file_update = math.floor(last_file_update/1000)
                last_num = last_file_update // 10**0 % 10
                last_num += 1
                last_file_update = math.floor(last_file_update/10) + last_num

        for _, game in enumerate(data):
            date_raw = game['date_raw']
            if last_file_update < date_raw:
                thedate = replace_all(game['date'], [', ', ' '], '-')
                new_list.append(f"{game['elo']},{thedate}\n")
            else:
                break
    
    if new_list != []:
        lines[0] = f"{data[0]['date_raw']}\n"
        lines += new_list[::-1]

        with open(f"{config.get('MMR_HISTORY')}/{puuid}.txt", "w") as f:
            f.writelines(lines)
    
    return len(new_list)

def get_elo_list(puuid):
    
    try: 
        update_database(puuid)
    except Exception as E:
        raise E

    if not get_file_mmr(puuid):
        return MissingException
    
    lines = []
    with open(f"{config.get('MMR_HISTORY')}/{puuid}.txt", 'r') as f:
        for line in f:
            lines.append(line.strip())

    if len(lines) == 1:
        raise NoneException
        
    lines.pop(0)
    elolist = ""
    for elem in lines:
        elolist += f"{elem.split(',')[0]}, "

    return elolist[:-2]

def leaderboard(region, length=20, last_played=90):

    result = {}
    if region == 'local':
        date_format = "%A-%B-%d-%Y-%I:%M-%p"
        playerlist = playerclass.PlayerList(config.get("PLAYERLIST_FP"))
        playerlist.load()
        players = []
        cut_off = datetime.now() - timedelta(days=last_played)

        for player in playerlist:
            data = get_file_mmr(player.puuid, date=True)
            if data and len(data) == 2:
                date_str = data[1].strip()
                if date_str != "":
                    date = datetime.strptime(date_str, date_format)
                    if date > cut_off:
                        players.append((player.ign, int(data[0])))
                    
        players.sort(key=lambda x:x[1], reverse=True)
        result['title'] = "Player Leaderboard (Last 3 months)\n"
    
    else:
        try:
            data = get_data('LEADERBOARD', region=region)
        except Exception as E:
            return {"error" : E.message}

        regions = {"ap" : "Asia Pacific", "eu" : "Europe", "kr" : "Korea", "na" : "North America"}
        players = []
        
        for i in range(length):
            player = data['players'][i]
            if player['is_anonymized'] == True:
                players.append(("(Anonymous)", player['rr']))
            else:
                players.append((player['name'], player['rr']))

        result['title'] = f'{regions[region]} Ranked Leaderboard\n'

    result['leaderboard'] = ""
    for i, player in enumerate(players):
        rank = i + 1
        result['leaderboard'] += (str(rank) + '.').ljust(3) + str(player[0]).ljust(16) + str(player[1]).rjust(5) + '\n'

    return result

def stats(puuid):

    try:
        john = get_data('MMR_BY_PUUID', puuid=puuid)
    except Exception as E:
        raise E
    
    data = john['data']['seasonal']
    final = []

    for season in data:
        if 'error' not in season.keys():
            wins = season['wins']
            games = season['games']
            rank = season['end_tier']['name']

            title = season['season']['short']
            title = title.replace("e", " Ep ")
            title = title.replace("a", ", Act ")
            final.append([f'{title}:', f'{rank}\nGames Played: {games}\nWinrate: {round((wins/games) * 100, 2)}%'])
    
    try:
        john = get_data('ACCOUNT_BY_PUUID', puuid=puuid)
    except Exception as E:
        raise E
    
    try:
        card_data = get_card_data(john['data']['card'])
        card = card_data['displayIcon']
    except:
        card = False

    return [final, card]

def get_banner(ign, tag):
    try:
        data = get_data('ACCOUNT_BY_NAME', ign=ign, tag=tag)
        card_data = get_card_data(data['data']['card'])
    except Exception as E:
        return False
    
    url = card_data['largeArt']
    r = requests.get(url, allow_redirects=True)
    open(f"{config.get('RES')}/banner.png", 'wb').write(r.content)
    return True

def servercheck():
    counter = 0
    report = ""
    regions = {"ap" : "Asia Pacific", "eu" : "Europe", "kr" : "Korea", "na" : "North America"}

    for elem in regions.keys():
        
        try:
            data = get_data('REGION_STATUS', region=elem)
        except Exception as E:
            report += f'{regions[elem]}:\n Error: {E.message}\n'

        maintenances = len(data['data']['maintenances'])
        incidents = len(data['data']['incidents'])
        counter += maintenances + incidents

        report += f'{regions[elem]}:\nMaintenances - {maintenances}\nIncidents - {incidents}\n'
        report += f'{regions[elem]}:\n{maintenances} maintenances and {incidents} incidents\n'

    if counter == 0:
        return "no maintenances or incidents reported"
        
    return report

def random_crosshair():
    crosshairs = {  "Reyna Flash" : "0;P;c;6;t;6;o;0.3;f;0;0t;1;0l;5;0o;5;0a;1;0f;0;1t;10;1l;4;1o;5;1a;0.5;1m;0;1f;0", 
                    "Windmill"    : "0;P;c;1;t;6;o;1;d;1;z;6;a;0;f;0;m;1;0t;10;0l;20;0o;20;0a;1;0m;1;0e;0.1;1t;10;1l;10;1o;40;1a;1;1m;0",
                    "Flappy Bird" : "0;P;c;1;t;3;o;1;f;0;0t;6;0l;20;0o;13;0a;1;0f;0;1t;9;1l;4;1o;9;1a;1;1m;0;1f;0",
                    "Flower"      : "0;P;c;6;o;1;d;1;z;4;f;0;m;1;0t;8;0l;3;0o;2;0a;0;0f;0;1l;3;1o;3;1a;0;1m;0;1f;0",
                    "Diamond"     : "0;P;c;5;h;0;f;0;0t;1;0l;3;0o;0;0a;1;0f;0;1t;3;1o;0;1a;1;1m;0;1f;0",
                    "Smiley"      : "0;P;c;7;t;2;o;1;d;1;z;3;a;0;f;0;0t;10;0l;2;0o;2;0a;1;0f;0;1b;0",
                    "Globe"       : "0;P;o;1;f;0;0t;10;0l;4;0a;0;0f;0;1t;4;1o;6;1a;0;1m;0;1f;0",
                    "Shuriken"    : "0;P;c;7;h;0;f;0;0l;4;0o;2;0a;1;0f;0;1t;8;1l;1;1o;1;1a;1;1m;0;1f;0",
                    "Fishnet"     : "0;P;o;1;d;1;a;0;f;0;0t;8;0l;2;0o;5;0a;0;0f;0;1l;8;1o;2;1a;0;1m;0;1f;0"}

    name, code = random.choice(list(crosshairs.items()))

    try:
        r = get_data("CROSSHAIR", crosshair_code=code)
        img = Image.open(BytesIO(r.content))
        img = img.save(config.get("CROSSHAIR"))
        return (name, code)
    
    except Exception as E:
        return E.message
