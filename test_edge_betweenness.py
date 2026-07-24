# -*- coding: utf-8 -*-
import unittest
from logis.core.indicators.urban import edge_betweenness

class TestEdgeBetweenness(unittest.TestCase):
    def test_normal_case(self):
        # aresta 0 aparece em 2 de 3 caminhos, aresta 1 em 1 de 3, aresta 2 em 3 de 3
        paths = [
            [0, 2],
            [1, 2],
            [0, 2],
        ]
        result = edge_betweenness(paths, num_edges=3)
        self.assertAlmostEqual(result[0], 2 / 3)
        self.assertAlmostEqual(result[1], 1 / 3)
        self.assertAlmostEqual(result[2], 3 / 3)

    def test_unused_edge_scores_zero(self):
        paths = [[0], [0]]
        result = edge_betweenness(paths, num_edges=2)
        self.assertAlmostEqual(result[0], 1.0)
        self.assertAlmostEqual(result[1], 0.0)

    def test_empty_paths_returns_zeros(self):
        result = edge_betweenness([], num_edges=3)
        self.assertEqual(result, [0.0, 0.0, 0.0])

    def test_invalid_num_edges_raises(self):
        with self.assertRaises(ValueError):
            edge_betweenness([[0]], num_edges=0)

    def test_edge_index_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            edge_betweenness([[0, 5]], num_edges=3)
        with self.assertRaises(ValueError):
            edge_betweenness([[-1]], num_edges=3)

if __name__ == '__main__':
    unittest.main()
