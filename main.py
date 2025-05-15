import atexit
import time
import traceback

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

    script_code1 = open("poker_bot.py", "r").read()
    script_code2 = open("poker_bot_call.py", "r").read()

    # create 1 random bet bot and 2 call bots
    num_players = 3

    players = []
    for i in range(1):
        players.append(Player(i, script_code1))
    for i in range(num_players - 1):
        players.append(Player(i, script_code2))

    print("START GAME", time.time() - start)
    start = time.time()
    try:
        poker = Game(players)
        poker.start()
    except Exception as e:
        print(e)
        print(traceback.format_exc())

    for i, p in enumerate(players):
        print("LOGS", i)
        print(p.read_logs())

    print("END", time.time() - start)


atexit.register(clean_up)

if __name__ == "__main__":
    main()
