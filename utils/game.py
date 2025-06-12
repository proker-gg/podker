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
        rounds=4,
        buy_ins=1,
    ):
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.starting_stack = starting_stack
        self.ante = ante
        self.max_raise_rounds = max_raise_rounds
        self.rounds = rounds
        self.buy_ins = buy_ins

    @property
    def obj(self):
        return {
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "starting_stack": self.starting_stack,
            "ante": self.ante,
            "max_raise_rounds": self.max_raise_rounds,
            "rounds": self.rounds,
            "buy_ins": self.buy_ins,
        }


class Game:
    def __init__(self, players, config=Config()):
        self.players = players
        self.config = config
        self.log = []
        self.stacks = [config.starting_stack] * len(players)
        self.buy_ins = [config.buy_ins] * len(players)

    def pnl(self):
        pnl = []
        for i in range(len(self.players)):
            buy_in_count = self.config.buy_ins - self.buy_ins[i] + 1

            pnl.append(self.stacks[i] - self.config.starting_stack * buy_in_count)

        return pnl

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
            print("STACKS", self.stacks)
            print("BUY INS", self.buy_ins)
            print("dealer:", dealer_index)
            round = Round(
                self.players, self.stacks, self.buy_ins, dealer_index, self.config
            )
            dealer_index = (dealer_index + 1) % len(self.players)
            round.start()
            for i in range(len(self.players)):
                if self.stacks[i] == 0:
                    if self.buy_ins[i] > 0:
                        print("player", i, "busted", self.buy_ins[i], "more buy ins")
                        self.buy_ins[i] -= 1
                        self.stacks[i] = self.config.starting_stack

            num_players_in = 0
            for i in range(len(self.players)):
                if self.stacks[i] > 0:
                    num_players_in += 1

            if num_players_in <= 1:
                print("GAME OVER")
                print("PNL", self.pnl())
                break


class Round:
    def __init__(self, players, stacks, buy_ins, dealer_index=0, config=Config()):
        self.deck = deck = Deck()
        deck.shuffle()

        self.players = players
        self.num_players = len(players)
        self.bets = [0] * len(players)
        self.buy_ins = buy_ins
        self.hands = []
        self.pot = 0
        self.community = []
        self.state = GameState.PREFLOP
        self.log = []
        self.dealer_index = dealer_index
        self.stacks = stacks

        self.config = config

        statuses = []
        for i in range(self.num_players):
            if stacks[i] > 0 and buy_ins[i] >= 0:
                statuses.append(PlayerStatus.IN)
            else:
                statuses.append(PlayerStatus.BUST)

        if statuses.count(PlayerStatus.IN) <= 1:
            assert "cannot start round with one player in"

        self.player_status = statuses

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

    def find_winners(self, win_conditions) -> list[int]:
        """
        win_conditions: [(bit_string, player_index)]

        returns:
            list of player indices that won,
            text description of win,
            list of players that show
        """
        win_conditions.sort(reverse=True)
        all_players = set([index for _, index in win_conditions])
        winners = []
        win_condition, tb = Hand.display_winning_hand(win_conditions[0][0])

        for bit_string, player_index in win_conditions:
            if bit_string == win_conditions[0][0]:
                winners.append(player_index)

        show = set(winners)  # everyone who won must show
        # everyone in the pot before the first winner is forced to show
        for i in range(self.num_players):
            cur_index = (self.dealer_index + i + 1) % self.num_players
            if i in all_players:
                show.add(cur_index)
            if cur_index in winners:
                break

        return winners, win_condition.value, list(show)

    def handle_win_with_side_pot(self, win_conditions):
        bets = self.bets
        player_status = self.player_status

        # find all distinct bet amounts for side pots
        sp_amounts = set()
        for _, player_index in win_conditions:
            sp_amounts.add(bets[player_index])

        side_pot_starting_amounts = sorted(list(sp_amounts))

        win_amounts = [0] * self.num_players

        sp_amount_prefix = 0

        shown_hands = [[] for i in range(self.num_players)]

        sp_win_desc = []

        for amount in side_pot_starting_amounts:
            current_sp_amount = amount - sp_amount_prefix
            sp_amount_prefix = amount
            # all players who have bet >= current_sp_amount are in the side pot
            sp_win_conds = []
            for i, (_, player_index) in enumerate(win_conditions):
                if bets[player_index] >= amount:
                    sp_win_conds.append(win_conditions[i])

            # total value of side pot
            pot_amount = current_sp_amount * len(sp_win_conds)
            print("SIDE POT bet amount:", amount, "pot amount:", pot_amount)

            winners, win_cond, show = self.find_winners(sp_win_conds)
            sp_win_desc.append(win_cond)
            # TODO: Log side pots, winners, and win conditions
            for winner in winners:
                win_amounts[winner] += pot_amount / len(winners)

            for player_index in show:
                cards = [str(c) for c in self.hands[player_index].cards]
                shown_hands[player_index] = cards

        return win_amounts, shown_hands, sp_win_desc

    def handle_win(self):
        # handle show and win logic
        winner_index = -1
        win_conditon = "default"
        shown_hands = [[] for i in range(self.num_players)]

        if self.check_all_fold():
            for i in range(len(self.players)):
                if self.player_status[i] == PlayerStatus.IN:
                    winner_index = i
                    self.stacks[winner_index] += self.pot

                    break

            for i in range(self.num_players):
                cur_index = (self.dealer_index + i + 1) % self.num_players
                if self.player_status[cur_index] == PlayerStatus.IN:
                    cards = [str(c) for c in self.hands[cur_index].cards]
                    shown_hands[cur_index] = cards
                if cur_index == winner_index:
                    break
        else:
            win_conditions = []

            for i, hand in enumerate(self.hands):
                if self.player_status[i] == PlayerStatus.IN:
                    win_conditions.append((hand.score_hand(self.community), i))

            results, shown_hands, win_conditon = self.handle_win_with_side_pot(
                win_conditions
            )

            for i in range(self.num_players):
                self.stacks[i] += results[i]

        win_message = {
            "player": -1,
            "amounts": results,
            "action": "win",
            "win_condition": win_conditon,
            "revealed_cards": shown_hands,
        }
        print(win_message)
        self.broadcast(Message(MessageType.INFO, message=win_message).obj)

    def start(self):
        # rest round information
        # self.player_status = [PlayerStatus.IN] * self.num_players

        # handle big and small blind
        # self.bets[current_player] = self.config.small_blind
        # self.stacks[current_player] -= self.config.small_blind
        # self.bets[(current_player + 1) % self.num_players] = self.config.big_blind
        # self.stacks[(current_player + 1) % self.num_players] -= self.config.big_blind
        # self.pot += self.config.small_blind
        # self.pot += self.config.big_blind

        # print("bb", self.config.big_blind, "sb", self.config.small_blind)
        # broadcast round start to other players
        rounds = [GameState.PREFLOP, GameState.FLOP, GameState.TURN, GameState.RIVER]

        cards_to_deal = [3, 1, 1, 0]

        sb = -1
        bb = -1

        sb_found = False
        current_player = (self.dealer_index + 1) % self.num_players
        for i in range(len(self.players)):
            if self.player_status[current_player] == PlayerStatus.IN:
                if sb_found:
                    # big blind
                    bb = current_player
                    self.make_bet(current_player, self.config.big_blind)
                    break
                sb_found = True
                sb = current_player
                self.make_bet(current_player, self.config.small_blind)

            current_player = (current_player + 1) % len(self.players)

        print("SB", sb, "BB", bb)

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
            print("POT: ", self.pot, "BETS: ", self.bets)
            if round == GameState.PREFLOP:
                for i, player in enumerate(self.players):
                    message["hand"] = [str(c) for c in self.hands[i].cards]
                    player.send(Message(MessageType.ROUND_INFO, message=message).obj)
            else:
                self.broadcast(Message(MessageType.ROUND_INFO, message=message).obj)
            self.play_round(bb)

            if self.check_all_fold():
                self.handle_win()
                return
            # check to continue (not everyone has folded)
            self.add_cards(cards_to_deal[index])

        self.handle_win()

    def make_bet(self, player_index, amount):
        self.bets[player_index] += amount
        self.stacks[player_index] -= amount
        self.pot += amount

    def play_round(self, bb_index):
        round_over = False
        max_bet = 0
        last_bet_index = -1

        starting_player = (self.dealer_index + 1) % self.num_players

        if self.state == GameState.PREFLOP:
            max_bet = self.config.small_blind
            last_bet_index = bb_index
            starting_player = (bb_index + 1) % self.num_players

        for raise_round in range(self.config.max_raise_rounds + 1):
            current_player = starting_player

            for i in range(len(self.players)):
                # if we got back to the last bet player, round is over
                if current_player == last_bet_index:
                    round_over = True
                    break

                # on start of raise round, first player becomes last bet player
                if raise_round == 0 and i == 0:
                    last_bet_index = current_player

                if (
                    self.player_status[current_player] == PlayerStatus.OUT
                    or self.player_status[current_player] == PlayerStatus.BUST
                ):
                    current_player = (current_player + 1) % len(self.players)
                    continue

                if self.stacks[current_player] == 0:
                    print("player", current_player, "is all in")
                    current_player = (current_player + 1) % len(self.players)
                    continue

                player = self.players[current_player]

                request_move_message = Message(MessageType.REQUEST_ACTION)

                response = player.send_and_read(request_move_message.obj)
                print("RECV", response)
                action_message = {
                    "player": current_player,
                    "action": "fold",
                    "amount": 0,
                }

                if not response or response["action"] == "fold":
                    self.player_status[current_player] = PlayerStatus.OUT
                else:
                    amount = response["amount"]
                    # check all in
                    if amount >= self.stacks[current_player]:
                        amount = self.stacks[current_player]
                    # check invalid bet amount
                    new_bet_amount = self.bets[current_player] + amount
                    # can only call on last raise round
                    if (
                        new_bet_amount > max_bet
                        and raise_round == self.config.max_raise_rounds
                    ):
                        amount = max_bet - self.bets[current_player]
                        print("LAST RR", max_bet, self.bets[current_player], amount)

                    self.bets[current_player] += amount
                    self.pot += amount
                    self.stacks[current_player] -= amount
                    action_message = {
                        "player": current_player,
                        "action": "bet",
                        "amount": amount,
                    }

                    if self.bets[current_player] > max_bet:
                        max_bet = self.bets[current_player]
                        round_over = False
                        last_bet_index = current_player

                print(action_message)
                print("round_state", self.bets, self.stacks, max_bet)

                # broadcast move to other players
                self.broadcast(Message(MessageType.INFO, message=action_message).obj)

                current_player = (current_player + 1) % len(self.players)

                if self.check_all_fold():
                    round_over = True
                    break

            if round_over:
                break
