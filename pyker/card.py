from enum import Enum, auto, IntEnum

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


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def __lt__(self, other):
        # return if self is smaller than other
        return (self.rank, self.suit) < (other.rank, other.suit)
