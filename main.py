import atexit
import time

from utils.docker import clean_up
from utils.player import Player
from utils.game import Game


IMAGE = "python:3.11"


def get_val(id, winnerid):
    if winnerid == 0:
        return "tie"
    if winnerid == id:
        return "win"
    return "loss"


def main():
    print("Create 2 bots")
    start = time.time()

    script_code = open("poker_bot.py", "r").read()

    num_players = 4

    players = []
    for i in range(num_players):
        players.append(Player(i, script_code))

    print("START GAME", time.time() - start)
    start = time.time()
    poker = Game(players)
    poker.start()

    print("END", time.time() - start)


atexit.register(clean_up)

if __name__ == "__main__":
    main()
