from collections import Counter
import logging
import random
from optparse import OptionParser
import pandas as pd


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
  out += ' '.join(hand_str)
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
  logging.debug("Strategy: %s", strategy)
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
        if len(deck) > 0:
          hand.add(deck.pop())

class Strategy():
  """Abstract superclass that picks the highest scoring move.
  
  Note that this only works assuming we pick one move ahead, but actually we
  probably want to factor in the two best moves, or the n best move chain using
  rule of 10s."""
  def get_move(self, valid_moves, hand, stacks, deck):
    scores = [self.score_move(v, hand, stacks, deck) for v in valid_moves]
    return max(zip(valid_moves, scores), key=lambda t: t[1])[0]

  def score_move(self, move, hand, stacks, deck):
    raise Exception("Abstract method.")

class DumbStrategy(Strategy):
  """Dumb strategy that just takes the first card to test if things work."""
  def get_move(self, valid_moves, hand, stacks, deck):
    return next(iter(valid_moves))

class GreedyDifferenceStrategy(Strategy):
  """Greedy difference strategy.

  For a set of moves, pick the one that results in the lowest resulting stack
  difference. e.g., putting a 95 on a 98 down-stack is a stack difference of 3.

  Still doesn't take into account cards remaining or keeping one stack low
  (although it may automatically do this).
  """
  def score_move(self, move, hand, stacks, deck):
    stack = stacks[move[1]]
    # Treat value of empty stacks as highest or lowest card. This means that
    # initializing a downstack with 99 would have score 0, which is better
    # than adding to any existing stack (except by rule of 10s).
    if len(stack.cards) == 0:
      current_top = LOWEST_CARD if stack.is_up else HIGHEST_CARD
    else:
      current_top = stack.cards[-1]

    # Higher score is good. Score can be thought of as the effect on the
    # remaining range of a stack.
    # Score is reversed depending on whether stack is up or down.
    score = move[0] - current_top  # Down-stack score.
    if stack.is_up:
      score *= -1
    return score

class WidestRangeStrategy(Strategy):
  """Widest range strategy.

  Still greedy in the sense that it only looks one move ahead.

  Returns the move that preserves the "widest range." For example, adding a 95
  to a 98 down-stack reduces the range of that stack from [2, 98) to [2, 95).
  It tries to optimize the widest range across stacks of a certain type. For
  example, if the move being evaluated is to put it on the up-stack, it will
  score based on the range width of all up-stacks.
  """

  def score_move(self, move, hand, stacks, deck):
    # Get the range of each stack, projecting the new stack for the candidate
    # card to be added. Copying a stack is not memory efficient but easier to
    # reason about.
    ranges = []
    for i, s in enumerate(stacks):
      if i == move[1]:
        # Simulated stack with the card on top
        simulated_stack = Stack(s.is_up)
        simulated_stack.cards = [move[0]]
        ranges.append(self.get_range_interval(simulated_stack))
      else:
        ranges.append(self.get_range_interval(s))

    # This code works specifically for two up/down stacks.  The current
    # heuristic attempts to preserve the largest range per stack category
    # (up/down).  This should capture what one means when they say "play on two
    # stacks for as long as possible."
    move_is_up = stacks[move[1]].is_up
    ranges_for_type = []
    for r, s in zip(ranges, stacks):
      if s.is_up == move_is_up:
        ranges_for_type.append(r)

    assert len(ranges_for_type) == 2  # Only handle 2 for now.
    score = 0
    score += self.range_len_sum(ranges_for_type)**2
    # The factor with the difference in range_sizes should keep us on one stack
    # as long as possible.
    # (50, 0), (51, 0) = undesirable, adds 1 to the score
    # (99, 0), (50, 0) = desirable, adds 49^2 to the score
    # Squaring this might be useful but empirically gives worse results.
    score += abs(self.range_len(ranges_for_type[0]) - self.range_len(ranges_for_type[1]))
    return score
  
  def range_len_sum(self, ranges):
    """Returns sum of range lengths.

    All this could easily be done by sets, but we are running into performance
    issues, and arithmetic is much, much faster than inserting into sets.
    """
    return sum(self.range_len(r) for r in ranges)

  def range_len(self, r):
    return r[1] - r[0] 

  def get_range_interval(self, stack):
    """Returns the range of cards still available on a stack as a tuple, inclusive ends.
    
    This is a faster version of get_range() but less easy to reason about (performance
    started becoming an issue with the set manipulation)."""
    if len(stack.cards) == 0:
     current_top = LOWEST_CARD - 1 if stack.is_up else HIGHEST_CARD + 1
    else:
     current_top = stack.cards[-1]
    if stack.is_up:
      return (current_top + 1, HIGHEST_CARD)
    else:
      return (LOWEST_CARD, current_top - 1)

  def get_overlap_size(self, r0, r1):
    """Returns the amount of overlap between two ranges."""
    if r0[0] > r1[1] or r1[0] > r0[1]:
      return 0
    return min(r0[1], r1[1]) - max(r0[0], r1[0])


def get_strategy(name):
  """Maps name string to a new instance of Strategy (which may be stateful)."""
  if name == "dumb":
    return DumbStrategy()
  elif name == "greedydiff":
    return GreedyDifferenceStrategy()
  elif name == "widest":
    return WidestRangeStrategy()
  raise ValueError("Unknown strategy: %s" % name)


def evaluate_strategies(strategy_names, num_evaluations=1500):
  """Evaluates instances of Strategy classes and compares them."""
  scores = {}
  for name in strategy_names:
    logging.info("Evaluating %s", name)
    scores[name] = []
    for seed in xrange(num_evaluations):
      strategy = get_strategy(name)
      scores[name].append(play_game(strategy, seed))


  scores_df = pd.DataFrame.from_dict(scores)
  num_cards = HIGHEST_CARD + LOWEST_CARD - 1
  result_df = pd.DataFrame()
  for c in scores_df: 
    column = scores_df[c]
    below10 = column[column < 10].size / float(num_cards)
    result_df = result_df.append(
      pd.DataFrame([[c, column.min(), below10, column.mean(), column.std()]],
                   columns=["name", "best_score", "below10", "mean", "std"]), ignore_index=True)
  logging.info("\n%s", result_df)


def main():
  parser = OptionParser()
  parser.add_option("--evaluate", dest="evaluate",
                    help="Runs an 1000-game evaluation of the strategy",
                    action="store_true")
  parser.add_option("--strategy", dest="strategy",
                    help="Comma separated strategies to evaluate. If not set, all are evaluated.",
                    metavar="STRATEGY")

  options, _ = parser.parse_args()

  if options.strategy:
    strategy_names = options.strategy.split(',')
  else:
    strategy_names = ["dumb", "greedydiff", "widest"]

  if options.evaluate:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    evaluate_strategies(strategy_names)
  elif options.strategy:
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s')
    num_left = play_game(get_strategy(strategy_names[0]))
    logging.debug("Lost: %d", num_left)

if __name__ == '__main__':
  main()
