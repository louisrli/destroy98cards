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

  def test_overlap_size(self):
    s = main.WidestRangeStrategy()
    not_overlap = ((1, 10), (12, 80))
    self.assertEqual(s.get_overlap_size(*not_overlap), 0)

    contained = ((10, 80), (30, 50))
    self.assertEqual(s.get_overlap_size(*contained), 20)

    overlap_right = ((10, 80), (20, 90))
    self.assertEqual(s.get_overlap_size(*overlap_right), 60)
    
    overlap_left = ((5, 20), (15, 70))
    self.assertEqual(s.get_overlap_size(*overlap_left), 5)

  def test_range_len_sum(self):
    s = main.WidestRangeStrategy()
    not_overlap = ((1, 10), (12, 80))
    self.assertEqual(s.range_len_sum(not_overlap), 9 + 68)

    contained = ((10, 80), (30, 50))
    self.assertEqual(s.range_len_sum(contained), 70 + 20)

    overlap_right = ((10, 80), (20, 90))
    self.assertEqual(s.range_len_sum(overlap_right), 70 + 70)
    
    overlap_left = ((5, 20), (15, 70))
    self.assertEqual(s.range_len_sum(overlap_left), 15 + 55)

if __name__ == '__main__':
  unittest.main()

