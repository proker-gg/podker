import enum
from pyker.deck import Deck
from player import Player
from pyker.hand import Hand

MAX_RAISE_ROUNDS = 3


class GameState(enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class PlayerStatus(enum):
    IN = "in"
    OUT = "out"


class MessageType(enum):
    GAME_START = 1
    ROUND_INFO = 2
    INFO = 3
    REQUEST_ACTION = 4


class Message:
    def __init__(self, type, message=None):
        self.type = type
        self.message = message

    @property
    def obj(self):
        return {"type": self.type, "message": self.message}


class Config:
    def __init__(
        self,
        max_raise_rounds=3,
        small_blind=1,
        big_blind=2,
        starting_stack=100,
        ante=0,
        rounds=10,
    ):
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.starting_stack = starting_stack
        self.ante = ante
        self.max_raise_rounds = max_raise_rounds
        self.rounds = rounds


class Game:
    def __init__(self, players, config=Config()):
        self.players = players
        self.config = config
        self.log = []
        self.stacks = [config.starting_stack] * len(players)

    def start(self):
        dealer_index = 0
        for i in range(self.config.rounds):
            self.log.append(Round(self.players, self.stacks, dealer_index, self.config))
            dealer_index = (dealer_index + 1) % len(self.players)
            round = Round(self.players, dealer_index, self.config)
            result, log = round.start()
            self.log.append(log)


class Round:
    def __init__(self, players, stacks, dealer_index=0, config=Config()):
        self.deck = deck = Deck()
        deck.shuffle()

        self.players = players
        self.num_players = len(players)
        self.bets = [0] * len(players)
        self.player_status = [PlayerStatus.IN] * len(players)
        self.hands = []
        self.pot = 0
        self.community = []
        self.state = GameState.PREFLOP
        self.log = []
        self.dealer_index = dealer_index
        self.stacks = stacks

        self.config = config

        for _ in players:
            hand = [deck.deal(), deck.deal()]
            self.hands.append(hand)

        self.start()

    def broadcast(self, message):
        for player in self.players:
            player.send(message)

    def add_cards(self, n=1):
        for _ in range(n):
            self.community.append(self.deck.deal())

    def check_all_fold(self):
        count = 0
        for status in self.player_status:
            if status == PlayerStatus.IN:
                count += 1
        return count <= 1

    def handle_win(self):
        # handle show and win logic
        winner_index = -1
        win_conditon = "default"

        if self.check_all_fold():
            for i in range(len(self.players)):
                if self.player_status[i] == PlayerStatus.IN:
                    winner_index = i
                    break
        else:
            win_conditions = []

            for i, hand in enumerate(self.hands):
                if self.player_status[i] == PlayerStatus.IN:
                    win_conditions.append((hand.score_hand(self.community), i))

            win_conditions.sort(reverse=True)

            bit_string, winner_index = win_conditions[0]

            win_conditon, tb = Hand.display_winning_hand(bit_string)

            # no split pot conditions yet
            self.stacks[winner_index] += self.pot

        win_message = {
            "player": winner_index,
            "action": "win",
            "amount": self.pot,
            "win_condition": win_conditon,
            "revealed_cards": [],
        }

        self.broadcast(Message(MessageType.INFO, message=win_message).obj)

    def start(self):
        # rest round information
        current_player = (self.dealer_index + 1) % self.num_players
        self.player_status = [PlayerStatus.IN] * self.num_players

        # handle big and small blind
        self.bets[current_player] = self.small_blind
        self.stacks[current_player] -= self.small_blind
        self.bets[(current_player + 1) % self.num_players] = self.big_blind
        self.stacks[(current_player + 1) % self.num_players] -= self.big_blind

        # broadcast round start to other players
        rounds = [GameState.PREFLOP, GameState.FLOP, GameState.TURN, GameState.RIVER]
        cards_to_deal = [3, 1, 1, 0]
        for index, round in enumerate(rounds):
            self.state = round
            # broadcast new_round message
            # TOOD: create some sort of types for messages
            message = {
                "dealer": self.dealer_index,
                "round_state": self.state,
                "community": self.community,
            }
            self.broadcast(Message(MessageType.ROUND_INFO, message=message).obj)
            self.play_round()

            if self.check_all_fold():
                self.handle_win()
                return
            # check to continue (not everyone has folded)
            self.add_cards(cards_to_deal[index])

        self.handle_win()

    def play_round(self):
        round_over = False

        for raise_round in range(self.config.max_raise_rounds):

            current_player = (self.dealer_index + 1) % self.num_players

            if self.state == GameState.PREFLOP:
                # for first round, first 2 players are last to act
                current_player = (current_player + 2) % self.num_players

            for i in range(len(self.players)):
                if self.player_status[current_player] == PlayerStatus.OUT:
                    current_player = (current_player + 1) % len(self.players)
                    continue

                player = self.players[current_player]

                request_move_message = Message(MessageType.REQUEST_ACTION)

                response = player.send_and_read(request_move_message.obj)

                action_message = {
                    "player": current_player,
                    "action": "fold",
                    "amount": 0,
                }

                if not response or response["action"] == "fold":
                    self.player_status[current_player] = PlayerStatus.OUT
                else:
                    amount = response["amount"]
                    self.bets[current_player] += amount
                    self.pot += amount
                    action_message = {
                        "player": current_player,
                        "action": "bet",
                        "amount": amount,
                    }

                # broadcast move to other players
                self.broadcast(Message(MessageType.INFO, message=action_message).obj)

                current_player = (current_player + 1) % len(self.players)

                if self.check_all_fold():
                    round_over = True
                    break

            if round_over:
                break
