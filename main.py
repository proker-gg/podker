import docker
import atexit
import uuid
import time
from utils.docker import *
from utils.player import Player

client = docker.from_env()

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

    script_code2 = open("user_code_2.py", "r").read()

    player1 = Player(1, script_code1)
    player2 = Player(2, script_code2)

    print("started players", time.time() - start, "seconds")

    win_count = [0] * 3

    start = time.time()

    for iteration in range(300):
        try:
            request_move_message = {"message": "request_move", "val": None}
            res1 = player1.send_and_read(request_move_message)["move"]
            res2 = player2.send_and_read(request_move_message)["move"]
            winner = 0

            res1 = int(res1)
            res2 = int(res2)

            if res1 == res2:
                winner = 0
            elif res2 != (res1 + 1) % 3:
                winner = 1
            else:
                winner = 2

            message1 = {"message": "result", "val": get_val(1, winner)}
            message2 = {"message": "result", "val": get_val(2, winner)}
            player1.send(message1)
            player2.send(message2)

            win_count[winner] += 1
        except Exception as e:
            print("GAME ERROR", e)
            break

    print(win_count)
    print("LOG1", player1.read_logs())
    # print("LOG", player2.read_logs())
    print("TIME ELAPSED", time.time() - start)
    print("Should exit")


atexit.register(clean_up)

if __name__ == "__main__":
    main()
