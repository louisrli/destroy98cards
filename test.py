import unittest

import main

class TestRangeFunctions(unittest.TestCase):

  def test_range_interval(self):
    s = main.WidestRangeStrategy()

    up_stack = main.Stack(True)
    down_stack = main.Stack(False)
    self.assertEqual(s.get_range_interval(up_stack), (2, 99))
    self.assertEqual(s.get_range_interval(down_stack), (2, 99))

    up_stack.cards.append(15)
    down_stack.cards.append(15)
    self.assertEqual(s.get_range_interval(up_stack), (16, 99))
    self.assertEqual(s.get_range_interval(down_stack), (2, 14))

if __name__ == '__main__':
  unittest.main()

