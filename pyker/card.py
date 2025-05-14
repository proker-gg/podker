from enum import IntEnum

SUIT_DISPLAY_TEXT = {
    "CLUB": "♣",
    "SPADE": "♠",
    "HEART": "♥",
    "DIAMOND": "♦",
}


class Suit(IntEnum):
    CLUB = 0
    DIAMOND = 1
    HEART = 2
    SPADE = 3

    def __str__(self):
        return SUIT_DISPLAY_TEXT[self.name]


INVERSE_SUIT_DISPLAY_TEXT = {
    "♣": Suit.CLUB,
    "♠": Suit.SPADE,
    "♥": Suit.HEART,
    "♦": Suit.DIAMOND,
}

RANK_DISPLAY_TEXT = {
    "TWO": "2",
    "THREE": "3",
    "FOUR": "4",
    "FIVE": "5",
    "SIX": "6",
    "SEVEN": "7",
    "EIGHT": "8",
    "NINE": "9",
    "TEN": "10",
    "JACK": "J",
    "QUEEN": "Q",
    "KING": "K",
    "ACE": "A",
}


class Rank(IntEnum):
    ACE = 14
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    def __str__(self):
        return RANK_DISPLAY_TEXT[self.name]


INVERSE_RANK_DISPLAY_TEXT = {
    "2": Rank.TWO,
    "3": Rank.THREE,
    "4": Rank.FOUR,
    "5": Rank.FIVE,
    "6": Rank.SIX,
    "7": Rank.SEVEN,
    "8": Rank.EIGHT,
    "9": Rank.NINE,
    "10": Rank.TEN,
    "J": Rank.JACK,
    "Q": Rank.QUEEN,
    "K": Rank.KING,
    "A": Rank.ACE,
}


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def __lt__(self, other):
        # return if self is smaller than other
        return (self.rank, self.suit) < (other.rank, other.suit)


def parse_card(card_str):
    try:
        rank = INVERSE_RANK_DISPLAY_TEXT[card_str[:-1]]
        suit = INVERSE_SUIT_DISPLAY_TEXT[card_str[-1]]

        return Card(rank, suit)
    except Exception as e:
        return None
