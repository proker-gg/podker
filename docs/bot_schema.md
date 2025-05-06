## Bot Schema

```python
class bot:
	def __init__(self, game_config):
		pass
	def make_move(self, round_state):
		return 0 # fold
	def round_result(self) # called at the end of round?
	# do we need more functions, for example on_move, on_card_reveal, etc

class moves(enum):
	fold = 0
	bet = 1

class player:
	"""
	instance variables
	- id: number
	- stack
	- bets?
		- Array of bets per round?
			- [[("call", 40), ("raise", 10)], ("call", 50)]
	- status
	"""

```

`make_move`

- Returns a `move`
  - either `0` for folding
  - or `1, amount` betting an amount. To call, bet the call amount, `state.call_amount`

`round_state` - Contains all game state

- config - ante, sb/bb cost, max bet rounds, other rules?
- round_state - `"preflop"| "flop" | "turn"  | "river"`
- bet_round - round of bets
- hand - `pyker.Hand`
- community - `pyker.Hand`
- pot
- players: `player[]`
- player_index
- call_amount
- logs - all events per round?

`make_move` gets called whenever it is the player's turn to move.

for each round, `state.players` array will be ordered starting with sb, bb, player_index will be updated accordingly
