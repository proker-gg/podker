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
        # temporary function to figure out the call cost
        bet_amounts = [sum(x) for x in round_state["bets"]]
        max_bet = max(bet_amounts)
        call_cost = max_bet - bet_amounts[round_state["player_index"]]

        log("Make Move", round_state, "CALL_COST", call_cost)

        return {"action": "bet", "amount": call_cost}

    def round_result(self):
        pass
