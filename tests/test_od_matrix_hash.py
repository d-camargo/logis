# -*- coding: utf-8 -*-
"""
/***************************************************************************
 logis
                                 A QGIS plugin
 Complemento do QGIS para apoiar projetos de logística no Brasil
                                -------------------
        begin                : 2026-09-19
        copyright            : (C) 2026 by Diego Camargo
        license              : GPL-3.0
 ***************************************************************************/
"""
import unittest
from unittest.mock import patch

from qgis.core import QgsPointXY
from qgis.analysis import QgsGraph

from logis.core.network.od_matrix import _get_graph_hash, _get_sample_indices


def _build_synthetic_graph(v_count, e_count):
    """Auxiliary helper to construct a synthetic QgsGraph."""
    graph = QgsGraph()
    for i in range(v_count):
        graph.addVertex(QgsPointXY(float(i), float(i * 2)))

    if v_count > 0:
        for i in range(e_count):
            u = i % v_count
            v = (i + 1) % v_count
            graph.addEdge(u, v, [float(i + 1), float(i + 1) * 0.5])
    return graph


class TestODMatrixHash(unittest.TestCase):

    def test_sample_indices_properties(self):
        """Verifies deterministic sampling bounds, first/last inclusion, and step behavior."""
        self.assertEqual(_get_sample_indices(0), [])
        self.assertEqual(_get_sample_indices(1), [0])
        self.assertEqual(_get_sample_indices(2), [0, 1])

        # Below sample ceiling -> exact range
        self.assertEqual(_get_sample_indices(100), list(range(100)))

        # Above sample ceiling -> bounded length and includes first and last element
        idx_1000 = _get_sample_indices(1000, max_samples=256)
        self.assertEqual(idx_1000[0], 0)
        self.assertEqual(idx_1000[-1], 999)
        self.assertLessEqual(len(idx_1000), 260)

        idx_50000 = _get_sample_indices(50000, max_samples=256)
        self.assertEqual(idx_50000[0], 0)
        self.assertEqual(idx_50000[-1], 49999)
        self.assertLessEqual(len(idx_50000), 260)

    def test_hash_stability(self):
        """Verifies that the hash is stable across multiple calls for the same graph."""
        graph = _build_synthetic_graph(20, 50)
        hash1 = _get_graph_hash(graph, 0)
        hash2 = _get_graph_hash(graph, 0)
        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex string length

    def test_hash_different_for_different_counts(self):
        """Verifies that graphs with different counts or criteria produce different hashes."""
        g1 = _build_synthetic_graph(10, 20)
        g2 = _build_synthetic_graph(10, 30)
        g3 = _build_synthetic_graph(15, 20)

        h1 = _get_graph_hash(g1, 0)
        h2 = _get_graph_hash(g2, 0)
        h3 = _get_graph_hash(g3, 0)
        h1_crit1 = _get_graph_hash(g1, 1)

        self.assertNotEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertNotEqual(h2, h3)
        self.assertNotEqual(h1, h1_crit1)

    def test_computation_time_does_not_grow_with_edges(self):
        """Verifies via unittest.mock that edge access calls do not scale linearly with edge count."""
        g_small = _build_synthetic_graph(50, 20)
        g_large = _build_synthetic_graph(500, 10000)

        with patch.object(g_small, 'edge', wraps=g_small.edge) as mock_small:
            _get_graph_hash(g_small, 0)
            calls_small = mock_small.call_count

        with patch.object(g_large, 'edge', wraps=g_large.edge) as mock_large:
            _get_graph_hash(g_large, 0)
            calls_large = mock_large.call_count

        # g_small has 20 edges (all sampled: 20 calls)
        self.assertEqual(calls_small, 20)

        # g_large has 10,000 edges, but reads are capped at ~256 (not 10,000)
        self.assertLessEqual(calls_large, 260)
        self.assertLess(calls_large, g_large.edgeCount())


if __name__ == "__main__":
    unittest.main()
