# -*- coding: utf-8 -*-
import unittest
from logis.core.indicators.urban import mean_circuity

class TestMeanCircuity(unittest.TestCase):
    def test_normal_case(self):
        # 1.2 / 1.0 = 1.2
        # 3.0 / 2.0 = 1.5
        # 1.0 / 1.0 = 1.0
        # mean = (1.2 + 1.5 + 1.0) / 3 = 3.7 / 3 = 1.2333333333333334
        net_dists = [1.2, 3.0, 1.0]
        euc_dists = [1.0, 2.0, 1.0]
        self.assertAlmostEqual(mean_circuity(net_dists, euc_dists), 3.7 / 3.0)

    def test_empty_input(self):
        # Empty input should raise ValueError
        with self.assertRaises(ValueError):
            mean_circuity([], [])
        with self.assertRaises(ValueError):
            mean_circuity([1.0], [])
        with self.assertRaises(ValueError):
            mean_circuity([], [1.0])

    def test_length_mismatch(self):
        # Different lengths should raise ValueError
        with self.assertRaises(ValueError):
            mean_circuity([1.2, 3.0], [1.0])

    def test_negative_network_distance(self):
        # Negative net distance should raise ValueError
        with self.assertRaises(ValueError):
            mean_circuity([-1.0, 2.0], [1.0, 1.5])

    def test_zero_euclidean_distance(self):
        # Zero Euclidean distance should raise ValueError
        with self.assertRaises(ValueError):
            mean_circuity([1.0, 2.0], [0.0, 1.5])

    def test_negative_euclidean_distance(self):
        # Negative Euclidean distance should raise ValueError
        with self.assertRaises(ValueError):
            mean_circuity([1.0, 2.0], [-1.0, 1.5])

    def test_integers_input(self):
        # Int inputs should work too
        net_dists = [12, 15]
        euc_dists = [10, 10]
        # (1.2 + 1.5) / 2 = 1.35
        self.assertAlmostEqual(mean_circuity(net_dists, euc_dists), 1.35)

if __name__ == '__main__':
    unittest.main()
