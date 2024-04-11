"""
Author: Charles Lee
"""

from map import Map
from moveset import Moveset
from player import Player
from team import Team
from gameItems import *
import random

class Game:
    def __init__(self, playerNames: dict[str,list[str]], width: int = 10, height: int = 10):
        """
        :param playerNames: Dictionary for each team name with a list of player names
        """
        self.numTeams = len(playerNames)

        self.teams, self.all_players = self.__initializePlayers(playerNames)

        self.__height = height
        self.__width = width
        self.map = Map(height, width, list(self.all_players.values()))

    def __initializePlayers(self, playerNames: dict[str,list[str]]):
        teams = {}
        all_players = {}
        for teamName, playerList in playerNames.items():
            teams[teamName] = Team(teamName)
            for playerName in playerList:
                all_players[playerName] = Player(playerName, teams[teamName])

        return teams, all_players

    def movePlayer(self, playerName: str, move: Moveset):
        assert isinstance(move, Moveset)
        player = self.getPlayer(playerName)

        x, y = player.loc
        dx, dy = move.value
        new_loc = x+dx, y+dy

        if not (0 <= new_loc[0] < self.__height) or not (0 <= new_loc[1] < self.__width):
            return

        cell = self.map.get(new_loc)
        if isinstance(cell, Player) or isinstance(cell, Wall):
            return

        if isinstance(cell, Coin):
            player.team.increaseScore(cell.value)
            self.map.decreaseCoin()

        self.map.set(player.loc, None)
        self.map.set(new_loc, player)
        player.loc = new_loc

    def getPlayer(self, playerName: str) -> Player:
        assert isinstance(playerName, str)
        try:
            return self.all_players[playerName]
        except KeyError:
            raise KeyError(f'{playerName} is not a valid player name')

    def getGameData(self, playerName:str, visionRadius: int = 2) -> dict:
        """
        :param playerName:
        :param vision:
        :return: {
            teammateNames: [],
            teammatePositions: [(x,y),...],
            enemyPositions: [(x,y),...],
            currentPosition: (x,y),
            coin1: [(x,y),...],
            coin2: [(x,y),...],
            coin3: [(x,y),...],
            walls: [(x,y),...]
        }
        """
        assert isinstance(playerName, str)
        assert isinstance(visionRadius, int)
        player = self.getPlayer(playerName)
        centerX, centerY = player.loc
        minX = max(centerX - visionRadius, 0)
        maxX = min(centerX + visionRadius, self.__height-1)
        minY = max(centerY - visionRadius, 0)
        maxY = min(centerY + visionRadius, self.__width-1)
        gameData = {'teammateNames': [],
                    'teammatePositions': [],
                    'enemyPositions': [],
                    'currentPosition': player.loc,
                    'coin1': [],
                    'coin2': [],
                    'coin3': [],
                    'walls': []}

        for x in range(minX, maxX+1):
            for y in range(minY, maxY+1):
                cell = self.map.get((x,y))
                self.__addGameData(gameData, cell, (x,y), player)

        return gameData

    def __addGameData(self, gameData: dict, cell: object, loc: tuple[int, int], player: Player):
        if isinstance(cell, Player):
            if cell.team is player.team and cell is not player:
                gameData['teammateNames'].append(cell.name)
                gameData['teammatePositions'].append(loc)
            elif cell.team is not player.team:
                gameData['enemyPositions'].append(loc)
        elif isinstance(cell, Coin1):
            gameData['coin1'].append(loc)
        elif isinstance(cell, Coin2):
            gameData['coin2'].append(loc)
        elif isinstance(cell, Coin3):
            gameData['coin3'].append(loc)
        elif isinstance(cell, Wall):
            gameData['walls'].append(loc)
    
    def gameOver(self):
        return self.map.numCoins <= 0

    def getScores(self):
        scores = {}
        for teamName, team in self.teams.items():
            scores[teamName] = team.score
        return scores


if __name__ == '__main__':
    random.seed(1)
    g = Game({'TeamA': ['Charles', 'Girish'], 'TeamB': ['James']})
    print(g.map)
    print(g.getScores())
    multiMove = lambda name, moves: [g.movePlayer(name, move) for move in moves]
    multiMove('James', (Moveset.RIGHT, Moveset.UP))
    multiMove('Charles', (Moveset.RIGHT, Moveset.RIGHT, Moveset.DOWN))

    print(g.getScores())
    print(g.getGameData('Charles',10))
    print(g.map.numCoins)
    print(g.gameOver())

    # g.movePlayer('James', Moveset.DOWN)
    # g.movePlayer('James', Moveset.LEFT)
    # print(g.map.numCoins)
    # print(g.gameOver())
    #
    # g.movePlayer('James', Moveset.RIGHT)
    # print(g.map.numCoins)
    # print(g.gameOver())
    # g.movePlayer('James', Moveset.LEFT)
    # print(g.map.numCoins)
    # print(g.gameOver())
    # cP = g.getPlayer('Charles')
    # gP = g.getPlayer('Girish')
    # jP = g.getPlayer('James')
    # print(cP.team is gP.team)
    # print(cP.team is jP.team)

    # print(g.map)
    # print()
    # g.movePlayer('Charles', Moveset.RIGHT)
    # print(g.getPlayer('Charles').team.score)
    # print(g.map)
    # print()
    # g.movePlayer('Charles', Moveset.RIGHT)
    # print(g.getPlayer('Charles').team.score)
    # print(g.map)
    # print()
    # g.movePlayer('Charles', Moveset.RIGHT)
    # g.movePlayer('James', Moveset.LEFT)
    # g.movePlayer('James', Moveset.DOWN)
    # print(g.map)
    # print(g.getPlayer('Charles').team.score)
    # print(g.getPlayer('James').team.score)