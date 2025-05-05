import sys
import json
import traceback


def log(data):
    with open("log.txt", "a") as file:
        file.write(data + "\n")


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
            self.round = len(self.logs)
            return


def start_listener():
    log("start bot")
    print(json.dumps({"message": "ready"}), flush=True)
    try:
        from user_code import rps_bot

        bot = rps_bot()
        state = game_state(bot)

        for line in sys.stdin:
            parse = json.loads(line)
            response = state.handle_message(parse)
            if response:
                print(json.dumps(response), flush=True)

    except Exception as e:
        log("Exception in user code: \n\n" + traceback.format_exc())
        print(e, flush=True)


if __name__ == "__main__":
    start_listener()
