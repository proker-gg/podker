import random


class rps_bot:
    def __init__(self):
        pass

    def make_move(self, game_state=None):
        # return 0

        return min(random.randrange(0, 3) + random.randrange(0, 2), 2)
