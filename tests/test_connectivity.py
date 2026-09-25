# -*- coding: utf-8 -*-
import unittest
from logis.core.indicators.urban import network_connectivity

class TestNetworkConnectivity(unittest.TestCase):
    def test_empty_input(self):
        # Empty input should raise ValueError
        with self.assertRaises(ValueError):
            network_connectivity([])
        with self.assertRaises(ValueError):
            network_connectivity({})

    def test_negative_degree(self):
        # Negative degrees should raise ValueError
        with self.assertRaises(ValueError):
            network_connectivity([3, 3, -1, 3])
        with self.assertRaises(ValueError):
            network_connectivity({"a": 2, "b": -3})

    def test_odd_sum_degrees(self):
        # Odd sum of degrees should raise ValueError
        with self.assertRaises(ValueError):
            network_connectivity([3, 3, 3]) # sum = 9 (odd)

    def test_simple_triangle(self):
        # A triangle has 3 nodes each with degree 2.
        # v = 3, e = 3.
        # alpha = (3 - 3 + 1) / (6 - 5) = 1 / 1 = 1.0
        # beta = 3 / 3 = 1.0
        # gamma = 3 / (3 * 1) = 1.0
        # pct_4_way = 0.0
        # pct_dead_ends = 0.0
        v, e, alpha, beta, gamma, pct_4, pct_dead = network_connectivity([2, 2, 2])
        self.assertEqual(v, 3)
        self.assertEqual(e, 3)
        self.assertAlmostEqual(alpha, 1.0)
        self.assertAlmostEqual(beta, 1.0)
        self.assertAlmostEqual(gamma, 1.0)
        self.assertAlmostEqual(pct_4, 0.0)
        self.assertAlmostEqual(pct_dead, 0.0)

    def test_tree_network(self):
        # Tree with 4 nodes: 1 central node (deg 3) and 3 leaves (deg 1).
        # v = 4, e = 3 (sum of degrees = 6)
        # alpha = (3 - 4 + 1) / (8 - 5) = 0 / 3 = 0.0
        # beta = 3 / 4 = 0.75
        # gamma = 3 / (3 * 2) = 3 / 6 = 0.5
        # pct_4_way = 0.0 (no node has degree >= 4)
        # pct_dead_ends = 3 / 4 * 100 = 75.0%
        v, e, alpha, beta, gamma, pct_4, pct_dead = network_connectivity([3, 1, 1, 1])
        self.assertEqual(v, 4)
        self.assertEqual(e, 3)
        self.assertAlmostEqual(alpha, 0.0)
        self.assertAlmostEqual(beta, 0.75)
        self.assertAlmostEqual(gamma, 0.5)
        self.assertAlmostEqual(pct_4, 0.0)
        self.assertAlmostEqual(pct_dead, 75.0)

    def test_dict_input(self):
        # Dictionary input: K4 (complete graph on 4 vertices)
        # 4 nodes, each with degree 3.
        # v = 4, e = 6
        # alpha = (6 - 4 + 1) / (8 - 5) = 3 / 3 = 1.0
        # beta = 6 / 4 = 1.5
        # gamma = 6 / (3 * 2) = 6 / 6 = 1.0
        # pct_4_way = 0.0
        # pct_dead_ends = 0.0
        node_degrees = {"n1": 3, "n2": 3, "n3": 3, "n4": 3}
        v, e, alpha, beta, gamma, pct_4, pct_dead = network_connectivity(node_degrees)
        self.assertEqual(v, 4)
        self.assertEqual(e, 6)
        self.assertAlmostEqual(alpha, 1.0)
        self.assertAlmostEqual(beta, 1.5)
        self.assertAlmostEqual(gamma, 1.0)
        self.assertAlmostEqual(pct_4, 0.0)
        self.assertAlmostEqual(pct_dead, 0.0)

    def test_small_network(self):
        # Two connected nodes (degree 1, 1).
        # v = 2, e = 1
        # alpha = 0.0 (v < 3)
        # beta = 1 / 2 = 0.5
        # gamma = 0.0 (v <= 2)
        # pct_4_way = 0.0
        # pct_dead_ends = 100.0
        v, e, alpha, beta, gamma, pct_4, pct_dead = network_connectivity([1, 1])
        self.assertEqual(v, 2)
        self.assertEqual(e, 1)
        self.assertAlmostEqual(alpha, 0.0)
        self.assertAlmostEqual(beta, 0.5)
        self.assertAlmostEqual(gamma, 0.0)
        self.assertAlmostEqual(pct_4, 0.0)
        self.assertAlmostEqual(pct_dead, 100.0)

    def test_crossroads(self):
        # Graph with 5 nodes: one node has degree 4, four nodes have degree 1 (a star graph K_1,4).
        # v = 5, e = 4 (sum of degrees = 8)
        # alpha = (4 - 5 + 1) / (10 - 5) = 0 / 5 = 0.0
        # beta = 4 / 5 = 0.8
        # gamma = 4 / (3 * 3) = 4 / 9 = 0.44444444
        # pct_4_way = 1 / 5 * 100 = 20.0%
        # pct_dead_ends = 4 / 5 * 100 = 80.0%
        v, e, alpha, beta, gamma, pct_4, pct_dead = network_connectivity([4, 1, 1, 1, 1])
        self.assertEqual(v, 5)
        self.assertEqual(e, 4)
        self.assertAlmostEqual(alpha, 0.0)
        self.assertAlmostEqual(beta, 0.8)
        self.assertAlmostEqual(gamma, 4.0/9.0)
        self.assertAlmostEqual(pct_4, 20.0)
        self.assertAlmostEqual(pct_dead, 80.0)

if __name__ == '__main__':
    unittest.main()
