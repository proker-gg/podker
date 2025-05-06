import random


class poker_bot:
    def __init__(self):
        pass

    def make_move(self, valid_moves, game_state):
        # return 0

        # valid_move will be []
        # 0 - fold
        # 1 - bet, min_cost (cost to call)

        return min(random.randrange(0, 3) + random.randrange(0, 2), 2)
