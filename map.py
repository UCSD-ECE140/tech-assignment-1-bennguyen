"""
Author: Charles Lee
"""

from copy import deepcopy
from player import Player
import random
from gameItems import *
from typing import Optional

def getDefaultWallChoices():
    wall = []
    for row in range(1,9):
        for col in range(1,8,2):
            wall.append((row,col))
    for col in range(2,9,2):
        wall.append((4,col))
    for row in range(0,9,2):
        wall.append((row,8))
    return wall


class Map:
    COIN_MIN_RATIO = 0.1
    COIN_MAX_RATIO = 0.2
    WALL_MIN_RATIO = 0.1
    WALL_MAX_RATIO = 0.3

    def __init__(self, height: int, width: int, playersList: list[Player], wallChoices: list[tuple[int]] = None):
        assert isinstance(width, int) and isinstance(height, int)
        assert isinstance(playersList, list)
        self.__height = height
        self.__width = width
        self.__map: list[list[object]] = [[None for _ in range(width)] for _ in range(height)]

        self.__numCoins = 0

        self.wallChoices = getDefaultWallChoices() if wallChoices is None else wallChoices

        self.__fillMap(playersList)


    @property
    def numCoins(self):
        return self.__numCoins
    
    def decreaseCoin(self):
        self.__numCoins -= 1

    @property
    def map(self):
        return deepcopy(self.__map)

    @property
    def height(self):
        return self.__height

    @property
    def width(self):
        return self.__width

    def __repr__(self):
        result = []
        for row in self.__map:
            row_str = []
            for cell in row:
                if cell is None:
                    cellName = 'None'
                elif isinstance(cell, Player):
                    cellName = cell.name
                else:
                    cellName = cell.__class__.__name__
                row_str.append(cellName)
            result.append('\t'.join(row_str))

        output = '\n'.join(result)

        return output

    def set(self, loc: tuple[int, int], item: object):
        assert isinstance(loc, tuple) and len(loc) == 2 and isinstance(loc[0], int) and isinstance(loc[1], int)
        self.__map[loc[0]][loc[1]] = item

    def get(self, loc: tuple[int, int]):
        assert isinstance(loc, tuple) and len(loc) == 2 and isinstance(loc[0], int) and isinstance(loc[1], int)
        return self.__map[loc[0]][loc[1]]

    def __fillMap(self, players: list[Player]):
        assert isinstance(players, list)

        empty = self.__width*self.__height

        maxWalls = int(Map.WALL_MAX_RATIO * empty)
        maxWalls = maxWalls if self.wallChoices is None else len(self.wallChoices)

        minWalls = int(Map.WALL_MIN_RATIO * empty)
        minWalls = 0 if maxWalls < minWalls else minWalls

        numWalls = random.randint(minWalls, maxWalls)
        wallChoices = deepcopy(self.wallChoices)
        for _ in range(numWalls):
            self.__placeRandom(Wall(), wallChoices)

        # Fill players
        for player in players:
            player.loc = self.__placeRandom(player)

        numPlayers = len(players)
        empty = empty - numWalls - numPlayers

        self.__numCoins = random.randint(int(Map.COIN_MIN_RATIO * empty), int(Map.COIN_MAX_RATIO * empty))
        for _ in range(self.__numCoins):
            coin = random.choices((Coin1, Coin2, Coin3), (6,3,1))[0]()
            self.__placeRandom(coin)

    def __placeRandom(self, obj, choice: Optional[list] = None):
        while True:
            if choice is None:
                x, y = random.randint(0, self.__height - 1), random.randint(0, self.__width - 1)
            else:
                x, y = random.choice(choice)
                choice.remove((x,y))
            if self.__map[x][y] is None:
                self.__map[x][y] = obj
                return x, y


if __name__ == '__main__':
    m = Map(10, 10, [Player('Charles', None), Player('James', None)])
    print(m)
    defaultm=getDefaultWallChoices()
    print("default")
    print(defaultm)
    pass