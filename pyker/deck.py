import random
from pyker.card import Card, Rank, Suit


class Deck:
    def __init__(self, removed_cards=[]):
        self.cards = self._create_deck(removed_cards)
        self.reset()

    def _create_deck(self, removed_cards=[]):
        disallowed_cards = set((c.rank, c.suit) for c in removed_cards)
        cards = []

        for suit in Suit:
            for rank in Rank:
                if (rank, suit) not in disallowed_cards:
                    cards.append(Card(suit=suit, rank=rank))

        return cards

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if self.pointer < 0:
            return None
        self.pointer -= 1
        return self.cards[self.pointer + 1]

    def deal_many(self, n=1):
        return [self.deal() for _ in range(n)]

    def reset(self):
        self.pointer = len(self.cards) - 1

    def __str__(self):
        return " ".join(str(card) for card in self.cards)
