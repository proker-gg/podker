import random


def log(*args):
    s = " ".join([str(arg) for arg in args])
    with open("log.txt", "a") as file:
        file.write("BOT: " + s + "\n")


class poker_bot:
    def __init__(self, config):
        log("recieved config", config)
        pass

    def make_move(self, round_state):
        return 1

    def round_result(self):
        pass
