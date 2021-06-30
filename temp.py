import requests
import json

class Player():
    def __init__(self, ign, tag, name = None, onlineList = False, online = False, status = None, partyid = False, partysize = 0):
        self.ign = ign
        self.tag = tag
        
        if name == None:
            self.name = ign
        else:
            self.name = name
        self.onlineList = onlineList
        self.online = online

        self.status = status
        self.partyid = partyid
        self.partysize = partysize

    def isOnline(self) -> bool:
        return self.isOnline
    
    def getCsv(self) -> str:
        return f"{self.ign},{self.tag},{self.name},{self.onlineList}\n"

    def __str__(self) -> str:
        return f"{self.ign}#{self.tag}"

    def __eq__(self, o: object) -> bool:
        return str(self) == str(o)

    def updateStuff(self):
        url = "https://api.henrikdev.xyz/valorant/v1/live-match/{}/{}".format(self.ign, self.tag)
        r = requests.get(url)
        data = json.loads(r.text)

        igstatus = ""

        if data['status'] == '200' and data['message'] != "Send friend request to user, the player have to accept this friendrequest to track live game data":
            
            self.partyid = data['data']['party_id']

            if data['data']['current_state'] == 'MENUS':
                self.partysize = data['data']['party_size']

            state = data['data']['current_state']

            if state == 'PREGAME':
                igstatus = "Online and in agent select"

            elif state == 'MENUS':
                igstatus = "Online and in menu"

            elif state == 'INGAME':
                map = data['data']['map']

                if map == 'Range':
                    igstatus = "Online in the range"

                else:
                    game_mode = data['data']['gamemode']
                    score = str(data['data']['score_ally_team']) + '-' + str(data['data']['score_enemy_team'])
                    map = data['data']['map']
                    igstatus = "Online in " + game_mode + " going " + score + " on " + map
        else:
            igstatus = False
        
        self.status = igstatus



class PlayerList():
    def __init__(self, filePath):
        self.filePath = filePath
        self.players = []
    
    def add(self, player:Player):
        self.players.append(player)
    
    def remove(self, player:Player):
        self.players.remove(player)

    def save(self):
        with open(self.filePath, "w+") as f:
            f.writelines([x.getCsv() for x in self.players])

    def load(self):
        with open(self.filePath, 'r') as f:
            for line in f.readlines():
                playerData = line.split(',')
                ign = playerData[0]
                tag = playerData[1]
                name = playerData[2]
                onlineList = playerData[3][:-1]
                self.players.append(Player(ign, tag, name, onlineList))
    
    def getPlayers(self):
        return self.players
    
    def getOnlinePlayers(self):
        onlinePLayers = []
        for player in self.players:
            if player.onlineList == 'True':
                player.updateStuff()
                onlinePLayers.append(player)
        return onlinePLayers

    def inList(self, player:Player):
        for i in self.players:
            if i == player:
                return True
        
        return False

def addPlayer(msg):
    playerList = PlayerList("playerlist.csv")
    playerList.load()
    inpot = msg.split(' ')
    ignn, tagg = inpot[1].split('#')

    if len(inpot) == 3:
        namee = inpot[2]
    else:
        namee = ignn

    url = "https://api.henrikdev.xyz/valorant/v1/mmr-history/ap/{}/{}".format(ignn, tagg)
    r = requests.get(url)

    if str(r) == "<Response [204]>":
        return False

    john = json.loads(r.text)

    if john['status'] == '404' or john['status'] == '500':
        return False
    
    if inpot[0] == "=onlineadd":
        if playerList.inList(Player(ignn, tagg)):
            playerList.remove(Player(ignn, tagg))
        
        playerList.add(Player(ignn, tagg, namee, True))
    
    else:
        if playerList.inList(Player(ignn, tagg)):
            return True
        
        playerList.add(Player(ignn, tagg, namee))
        
    playerList.save()

def removePlayer(msg):
    playerList = PlayerList("playerlist.csv")
    playerList.load()
    inpot = msg.split(' ')
    ignn, tagg = inpot[1].split('#')

    if len(inpot) == 3:
        namee = inpot[2]
    else:
        namee = ignn

    if playerList.inList(Player(ignn, tagg)) == False:
        return False

    if inpot[0] == "=onlineremove":
        playerList.remove(Player(ignn, tagg, namee))
        playerList.add(Player(ignn, tagg, namee))

    else:
        playerList.remove(Player(ignn, tagg, namee))
    
    playerList.save()

if __name__ == '__main__':
    playerlist = PlayerList('playerlist.csv')
    playerlist.load()

    faq = "=remove quackinator#2197"
    print(addPlayer(faq))