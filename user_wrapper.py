import sys
import json
import traceback
from enum import Enum, IntEnum
from pyker.hand import Hand
from pyker.card import Card, parse_card


class GameState(Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class PlayerStatus(Enum):
    IN = "in"
    OUT = "out"


class MessageType(Enum):
    GAME_START = "game_start"
    ROUND_INFO = "round_info"
    INFO = "info"
    REQUEST_ACTION = "request_action"


def log(*args):
    s = " ".join([str(arg) for arg in args])
    with open("log.txt", "a") as file:
        file.write("DEBUG: " + s + "\n")


class game_state:
    def __init__(self):
        self.logs = []
        self.round = 0
        self.round_state = None
        self.stacks = []
        self.bets = []
        self.player_status = []
        self.bot = None
        self.hand = None
        self.community = None
        self.dealer_index = None
        self.pot = 0

    def start_bot(self):
        from user_code import poker_bot

        self.bot = poker_bot(self.config)

    def handle_message(self, message, debug=True):
        key = message["type"]
        value = message["message"]

        if debug:
            log("HANDLE MESSAGE", key, value)

        if key == "echo":
            print(message, flush=True)
            return

        if key == MessageType.GAME_START.value:
            self.player_count = value["player_count"]
            self.player_index = value["player_index"]
            self.config = value["config"]
            self.config["player_count"] = self.player_count

            self.stacks = [self.config["starting_stack"]] * self.player_count

            self.start_bot()

            if debug:
                log(
                    "GAME_START_HANDLER",
                    "player_count:",
                    self.player_count,
                    "player_index:",
                    self.player_index,
                    "stacks",
                    self.stacks,
                )
            return

        if key == MessageType.ROUND_INFO.value:
            self.round_state = value["round_state"]
            community = value["community"]
            self.community = Hand([parse_card(card) for card in community])
            self.dealer_index = value["dealer"]

            if self.round_state == GameState.PREFLOP.value:
                hand = value["hand"]
                self.hand = Hand([parse_card(card) for card in hand])
                self.bets = [[] for _ in range(self.player_count)]

                self.player_status = [PlayerStatus.IN] * self.player_count
                self.pot = 0

                sb_index = (self.dealer_index + 1) % self.player_count
                bb_index = (self.dealer_index + 2) % self.player_count

                self.bets[sb_index].append(self.config["small_blind"])
                self.stacks[sb_index] -= self.config["small_blind"]
                self.bets[bb_index].append(self.config["big_blind"])
                self.stacks[bb_index] -= self.config["big_blind"]

                self.pot += self.config["small_blind"] + self.config["big_blind"]
            else:
                community = value["community"]
            if debug:
                log(
                    "ROUND_INFO_HANDLER",
                    "round_state:",
                    self.round_state,
                    "community:",
                    self.community,
                    "hand:",
                    self.hand,
                    "dealer_index:",
                    self.dealer_index,
                )
            return

        if key == MessageType.INFO.value:
            player = value["player"]
            action = value["action"]
            if action == "fold":
                self.player_status[player] = PlayerStatus.OUT
            if action == "bet":
                self.bets[player].append(value["amount"])
                self.stacks[player] -= value["amount"]
                self.pot += value["amount"]
            if action == "win":
                amount = value["amount"]
                self.stacks[player] += amount

            return

        if key == MessageType.REQUEST_ACTION.value:
            round_state_copy = {
                "round_state": self.round_state,
                "community": self.community,
                "hand": self.hand,
                "dealer_index": self.dealer_index,
                "player_status": self.player_status,
                "player_index": self.player_index,
                "stacks": self.stacks,
                "bets": self.bets,
                "pot": self.pot,
            }
            return self.bot.make_move(round_state_copy)


def start_listener():
    log("start bot")
    print(json.dumps({"message": "ready"}), flush=True)

    try:
        state = game_state()

        for line in sys.stdin:
            parse = json.loads(line)
            log(parse)
            # print(None, flush=True)
            response = state.handle_message(parse)
            # print(None, flush=True)
            if response:
                print(json.dumps(response), flush=True)

    except Exception as e:
        log("Uncaught in user code: \n\n", traceback.format_exc(), "\n\n")
        log("Bot will only fold from now on")

    # user code crashed, consume rest of socket
    for line in sys.stdin:
        print(None, flush=True)


if __name__ == "__main__":
    start_listener()
