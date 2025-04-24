import random
import sys
import json


class rps_bot:
    def __init__(self):
        pass

    def make_move(self, game_state=None):
        # return 0
        return min(random.randrange(0, 3) + random.randrange(0, 2), 2)


# class rps_bot:
#     def __init__(self):
#         self.s = [0, 0, 0]
#         self.o = {"win": 1, "loss": -1, "tie": 0}

#     def best_outcome(self):
#         m = max(self.s)
#         for i, v in enumerate(self.s):
#             if v == m:
#                 return i
#         return 0

#     def make_move(self, game_state=None):
#         if not game_state.logs:
#             return 0
#         move, outcome = game_state.logs[-1]
#         self.s[move] += self.o[outcome]
#         return self.best_outcome()


class game_state:
    def __init__(self, bot):
        self.logs = []
        self.round = 0
        self.bot = bot
        self.prev_move = -1

    def handle_message(self, message):
        key = message["message"]
        val = message["val"]

        if key == "echo":
            print(message, flush=True)
            return

        if key == "request_move":
            move = self.bot.make_move(self)
            self.prev_move = move
            response = {"move": move}
            return response
        if key == "result":
            self.logs.append((self.prev_move, val))
            return


def start_listener():
    bot = rps_bot()
    state = game_state(bot)
    print(json.dumps({"message": "ready"}), flush=True)

    try:
        for line in sys.stdin:
            parse = json.loads(line)
            response = state.handle_message(parse)
            if response:
                print(json.dumps(response), flush=True)

    except Exception as e:
        print(e, flush=True)


if __name__ == "__main__":
    start_listener()
