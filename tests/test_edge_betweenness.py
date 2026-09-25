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

    def test_sample_od_pairs_deterministic(self):
        from logis.core.network.betweenness import sample_od_pairs

        class MockGraph:
            def vertexCount(self):
                return 10

        graph = MockGraph()
        pairs1 = sample_od_pairs(graph, num_samples=5, seed=42)
        pairs2 = sample_od_pairs(graph, num_samples=5, seed=42)

        self.assertEqual(len(pairs1), 5)
        self.assertEqual(pairs1, pairs2)
        for orig, dest in pairs1:
            self.assertNotEqual(orig, dest)
            self.assertTrue(0 <= orig < 10)
            self.assertTrue(0 <= dest < 10)

    def test_sample_od_pairs_invalid_inputs(self):
        from logis.core.network.betweenness import sample_od_pairs

        class MockGraph:
            def __init__(self, count):
                self._count = count
            def vertexCount(self):
                return self._count

        with self.assertRaises(ValueError):
            sample_od_pairs(MockGraph(10), num_samples=0)

        with self.assertRaises(ValueError):
            sample_od_pairs(MockGraph(1), num_samples=5)


if __name__ == '__main__':
    unittest.main()
