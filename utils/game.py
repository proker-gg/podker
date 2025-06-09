from enum import Enum
from pyker.deck import Deck
from pyker.hand import Hand

MAX_RAISE_ROUNDS = 3


class GameState(Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class PlayerStatus(Enum):
    IN = "in"
    OUT = "out"
    BUST = "bust"  # player lost and has no more buy-ins


class MessageType(Enum):
    GAME_START = "game_start"
    ROUND_INFO = "round_info"
    INFO = "info"
    REQUEST_ACTION = "request_action"


class Message:
    def __init__(self, type, message=None):
        self.type = type
        self.message = message

    @property
    def obj(self):
        return {"type": self.type.value, "message": self.message}


class Config:
    def __init__(
        self,
        max_raise_rounds=3,
        small_blind=1,
        big_blind=2,
        starting_stack=100,
        ante=0,
        rounds=1,
        buy_in=100,
    ):
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.starting_stack = starting_stack
        self.ante = ante
        self.max_raise_rounds = max_raise_rounds
        self.rounds = rounds

    @property
    def obj(self):
        return {
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "starting_stack": self.starting_stack,
            "ante": self.ante,
            "max_raise_rounds": self.max_raise_rounds,
            "rounds": self.rounds,
        }


class Game:
    def __init__(self, players, config=Config()):
        self.players = players
        self.config = config
        self.log = []
        self.stacks = [config.starting_stack] * len(players)

    def start(self):
        for i, player in enumerate(self.players):
            message = Message(
                MessageType.GAME_START,
                {
                    "player_count": len(self.players),
                    "player_index": i,
                    "config": self.config.obj,
                },
            )
            player.send(message.obj)
            print(message.obj)

        dealer_index = 0
        for i in range(self.config.rounds):
            print("START ROUND", i)
            print(self.stacks)
            print("dealer:", dealer_index)
            round = Round(self.players, self.stacks, dealer_index, self.config)
            dealer_index = (dealer_index + 1) % len(self.players)
            round.start()
            # self.log.append(log)


def find_winners(win_conditions, start_player) -> list[int]:
    """
    win_conditions: [(bit_string, player_index)]

    returns list of player indices that won, text description of win
    """
    win_conditions.sort(reverse=True)

    winners = []
    win_condition, tb = Hand.display_winning_hand(win_conditions[0][0])

    for bit_string, player_index in win_conditions:
        if bit_string == win_conditions[0][0]:
            winners.append(player_index)

    return winners, win_condition.value


def handle_win_side_pot(bets, stacks, win_conditions, player_status):
    num_players = len(bets)

    # find people who went all in - player_status == IN and st == 0
    all_in_counts = set()
    for i in range(num_players):
        if player_status[i] == PlayerStatus.IN and stacks[i] == 0:
            all_in_counts.add(bets[i])

    side_pot_starting_amounts = sorted(list(all_in_counts))

    win_amounts = [0] * num_players

    # no side pot case
    if len(side_pot_starting_amounts) == 0:
        winners, win_cond = find_winners(win_conditions)
        for winner in winners:
            win_amounts[winner] += stacks[winner]

        return win_amounts

    sp_amount_prefix = 0
    for i, amount in enumerate(side_pot_starting_amounts):
        current_sp_amount = amount - sp_amount_prefix
        sp_amount_prefix = amount
        # all players who have bet >= current_sp_amount are in the side pot
        sp_win_conds = []
        for i in range(num_players):
            if player_status[i] == PlayerStatus.IN and bets[i] >= current_sp_amount:
                sp_win_conds.append(win_conditions[i])

        winners, win_cond = find_winners(sp_win_conds)
        # TODO: Log side pots, winners, and win conditions
        for winner in winners:
            win_amounts[winner] += current_sp_amount / len(winners)

    return win_amounts


class Round:
    def __init__(self, players, stacks, dealer_index=0, config=Config()):
        self.deck = deck = Deck()
        deck.shuffle()

        self.players = players
        self.num_players = len(players)
        self.bets = [0] * len(players)
        self.player_status = [PlayerStatus.IN] * len(players)
        self.buy_ins = [config.buy_in] * len(players)
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
            self.hands.append(Hand(hand))

    def broadcast(self, message, debug=False):
        if debug:
            print("BROADCAST:", message)
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
        shown_hands = [[] for i in range(self.num_players)]

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

            win_condition_enum, tb = Hand.display_winning_hand(bit_string)
            win_conditon = win_condition_enum.value

            # reveal hands until winner

            for i in range(self.num_players):
                cur_index = (self.dealer_index + i + 1) % self.num_players
                if self.player_status[cur_index] == PlayerStatus.IN:
                    cards = [str(c) for c in self.hands[cur_index].cards]
                    shown_hands[cur_index] = cards
                if cur_index == winner_index:
                    break

            # no split pot conditions yet
        self.stacks[winner_index] += self.pot

        win_message = {
            "player": winner_index,
            "action": "win",
            "amount": self.pot,
            "win_condition": win_conditon,
            "revealed_cards": shown_hands,
        }
        print(win_message)
        self.broadcast(Message(MessageType.INFO, message=win_message).obj)

    def start(self):
        # rest round information
        current_player = (self.dealer_index + 1) % self.num_players
        self.player_status = [PlayerStatus.IN] * self.num_players

        # handle big and small blind
        self.bets[current_player] = self.config.small_blind
        self.stacks[current_player] -= self.config.small_blind
        self.bets[(current_player + 1) % self.num_players] = self.config.big_blind
        self.stacks[(current_player + 1) % self.num_players] -= self.config.big_blind
        self.pot += self.config.small_blind
        self.pot += self.config.big_blind

        # broadcast round start to other players
        rounds = [GameState.PREFLOP, GameState.FLOP, GameState.TURN, GameState.RIVER]

        cards_to_deal = [3, 1, 1, 0]

        for index, round in enumerate(rounds):
            self.state = round
            # broadcast new_round message
            # TOOD: create some sort of types for messages
            message = {
                "dealer": self.dealer_index,
                "round_state": self.state.value,
                "community": [str(c) for c in self.community],
            }
            print("ROUND_INFO", message)
            if round == GameState.PREFLOP:
                for i, player in enumerate(self.players):
                    message["hand"] = [str(c) for c in self.hands[i].cards]
                    player.send(Message(MessageType.ROUND_INFO, message=message).obj)
            else:
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
        max_bet = self.config.big_blind
        last_bet_index = (self.dealer_index + 1) % self.num_players
        for raise_round in range(self.config.max_raise_rounds):
            current_player = (self.dealer_index + 1) % self.num_players

            if self.state == GameState.PREFLOP:
                # for first round, first 2 players are last to act
                # skip dealer, bb, sb, then utg is first to go
                current_player = (current_player + 3) % self.num_players
                last_bet_index = (self.dealer_index + 3) % self.num_players

            for i in range(len(self.players)):
                if self.player_status[current_player] == PlayerStatus.OUT:
                    current_player = (current_player + 1) % len(self.players)
                    continue

                if current_player == last_bet_index and raise_round > 0:
                    round_over = True
                    break

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
                    self.stacks[current_player] -= amount
                    action_message = {
                        "player": current_player,
                        "action": "bet",
                        "amount": amount,
                    }

                    if amount > max_bet:
                        max_bet = amount
                        round_over = False
                        last_bet_index = current_player

                print(action_message)

                # broadcast move to other players
                self.broadcast(Message(MessageType.INFO, message=action_message).obj)

                current_player = (current_player + 1) % len(self.players)

                if self.check_all_fold():
                    round_over = True
                    break

            if round_over:
                break
