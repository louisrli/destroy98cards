import logging
import random

LOWEST_CARD = 2
HIGHEST_CARD = 99
# "Rule of 10s"
DIFFERENCE_RULE = 10
HAND_SIZE = 8
# Number of cards you need to be missing before it redraws.
REDRAW_MARGIN = 2

class Stack(object):
  """Represents the state of an up-stack or down-stack"""
  def __init__(self, is_up):
    self.is_up = is_up
    # The last card is the most recently added.
    self.cards = []

  def __repr__(self):
    top = str(self.cards[-1]) if len(self.cards) > 0 else "EMPTY"
    direction = "up" if self.is_up else "down"
    return "%s(%s)" % (direction, top)

def is_valid_move(candidate, stack):
  """Returns true if candidate can be added to stack"""
  if len(stack.cards) == 0:
    return True
  top = stack.cards[-1]
  if abs(candidate - top) == DIFFERENCE_RULE:
    return True
  if stack.is_up:
    return candidate > top
  return candidate < top


def format_board(stacks, hand, next_move):
  """Formats the board and valid moves for debugging.

  Args:
    stacks: Instances of the class Stack
    hand: The current hand, an iterable of integers
    next_move: (card value, stack index) to visualize.

  Returns:
    A string representing the board.
  """
  def highlight(s):
    return ('\033[92m' + s + '\033[0m')

  out = '\n'
  move_card, s_i = next_move
  for i, s in enumerate(stacks):
    # Highlight the targeted stack
    stack_str = str.rjust(repr(s), 12)
    if i == s_i:
      out += highlight(stack_str)
    else: 
      out += stack_str
    # Put two stacks per line.
    if i == (len(stacks) / 2) - 1:
      out += "\n"
  out += '\n'

  hand_str = list(
    highlight(str(n)) if n == move_card else str(n) for n in hand)
  out += ' '.join(sorted(hand_str))
  out += '\n'
  return out


def play_game(strategy, seed=None):
  """Plays a game of 98 cards with the given strategy

  Args:
    strategy: Instance of Strategy class that knows HOW TO PLAY.
    seed: Random seed used to generate the deck.
  Returns:
    The number of cards remaining in the deck with no moves left.
  """
  random.seed(seed)
  deck = list(xrange(LOWEST_CARD, HIGHEST_CARD + 1))
  random.shuffle(deck)
  stacks = [Stack(True), Stack(True), Stack(False), Stack(False)]
  hand = set(deck.pop() for _ in xrange(HAND_SIZE))

  while len(deck) > 0:
    # A move is a (card value, stack index).
    valid_moves = set()
    for card in hand:
      for stack_i, s in enumerate(stacks):
        if is_valid_move(card, s):
          valid_moves.add((card, stack_i))

    # u lost bro...
    if len(valid_moves) == 0:
      return len(deck) + len(hand)

    best_card, target_stack = strategy.get_move(valid_moves, hand, stacks, deck)

    logging.debug(format_board(stacks, hand, (best_card, target_stack)))

    # Update the stack and hand, redrawing new cards if needed.
    stacks[target_stack].cards.append(best_card)
    hand.remove(best_card)
    if HAND_SIZE - len(hand) == REDRAW_MARGIN and len(deck) > 0:
      for _ in xrange(REDRAW_MARGIN):
        hand.add(deck.pop())

class DumbStrategy():
  """Dumb strategy that just takes the first card to test if things work."""
  def get_move(self, valid_moves, hand, stacks, deck):
    return next(iter(valid_moves))

def main():
  logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s')
  num_left = play_game(DumbStrategy())
  logging.debug("Lost: %d", num_left)

if __name__ == '__main__':
  main()
