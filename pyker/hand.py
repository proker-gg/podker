# 1111 1000 1000 1000 1000 1000 # 4 bits per each valu -> 24 bits
from enum import IntEnum
from itertools import combinations
from collections import Counter

from pyker.card import Rank
from pyker.deck import Deck

# 41,213,141,516
# unsigned long long


class WinCategory(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


class Hand:
    def __init__(self, cards):
        self.cards = cards

    def __str__(self):
        return " ".join(str(card) for card in self.cards)

    def desc(self):
        a = self.cards[0]
        b = self.cards[1]

        ranks = [a.rank, b.rank]
        ranks.sort(reverse=True)
        offsuit = a.suit != b.suit
        description = "-".join(str(rank) for rank in ranks) + (
            "o" if offsuit and a.rank != b.rank else ""
        )

        return description

    @classmethod
    def score_5_hand(cls, hand):
        hand.sort(reverse=True)
        rank_dict = Counter(card.rank for card in hand)
        suit_dict = Counter(card.suit for card in hand)
        ranks_sorted = sorted([[v, k] for k, v in rank_dict.items()], reverse=True)

        result = 0
        index = 4
        # print(ranks_sorted)
        for k, item in ranks_sorted:
            for _ in range(k):
                result |= item << (index * 4)
                index -= 1

        # print("RES", result)

        def make_result(winCategory):
            return result | winCategory.value << (20)

        # straight 14 13 12 11 10 or 14 5 4 3 2
        is_straight = len(rank_dict) == 5 and (
            (hand[0].rank - hand[-1].rank == 4)
            or (hand[0] == 14 and hand[1].rank == 5 and hand[-1].rank == 2)
        )

        is_flush = len(suit_dict) == 1

        if is_straight and is_flush:
            if hand[0].rank == Rank.ACE and hand[1].rank == Rank.KING:
                return make_result(WinCategory.ROYAL_FLUSH)
            return make_result(WinCategory.STRAIGHT_FLUSH)

        if ranks_sorted[0][0] == 4:
            return make_result(WinCategory.FOUR_OF_A_KIND)

        if (
            len(ranks_sorted) == 2
            and ranks_sorted[0][0] == 3
            and ranks_sorted[1][0] == 2
        ):
            return make_result(WinCategory.FULL_HOUSE)
        if is_flush:
            return make_result(WinCategory.FLUSH)
        if is_straight:
            return make_result(WinCategory.STRAIGHT)

        if ranks_sorted[0][0] == 3:
            return make_result(WinCategory.THREE_OF_A_KIND)

        if len(ranks_sorted) == 3 and ranks_sorted[0][0] == 2:
            return make_result(WinCategory.TWO_PAIR)
        if len(ranks_sorted) == 4 and ranks_sorted[0][0] == 2:
            return make_result(WinCategory.PAIR)

        return make_result(WinCategory.HIGH_CARD)

    def score_hand(self, community_cards):
        all_cards = self.cards + community_cards
        assert len(all_cards) == 7

        all_scores = []

        for c in combinations(all_cards, 5):
            all_scores.append(self.score_5_hand(list(c)))

        all_scores.sort(reverse=True)

        return all_scores[0]

    def winning_hand(self, community_cards, other_hands):

        other_win_conditions = [h.score_hand(community_cards) for h in other_hands]

        other_win_conditions.sort(reverse=True)

        win_cond = self.score_hand(community_cards)

        if win_cond > other_win_conditions[0]:
            return 1
        if win_cond == other_win_conditions[0]:
            return 0
        return -1

    @classmethod
    def display_winning_hand(n):
        win_cond = n >> 20
        tibreaker = []

        for i in range(5):
            tibreaker.append((n >> (i * 4)) & 15)
        return (WinCategory(win_cond), tibreaker[::-1])

    def monte_carlo(self, community_cards, other_player_count, n=1000):
        used_cards = community_cards + self.cards

        wins = 0
        tie = 0
        deck = Deck(removed_cards=used_cards)

        for _ in range(n):
            deck.reset()
            deck.shuffle()
            other_hands = []
            for _ in range(other_player_count):
                other_hands.append(Hand(deck.deal_many(n=2)))

            remaining_cards = 5 - len(community_cards)

            new_hole = community_cards + deck.deal_many(n=remaining_cards)

            result = self.winning_hand(new_hole, other_hands)

            if result == 1:
                wins += 1
            elif result == 0:
                tie += 1

        return (wins / n, tie / n)

    def sort(self):
        self.cards.sort(reverse=True)
