# -*- coding: utf-8 -*-
import unittest
from logis.core.indicators.regional import (
    road_density,
    paved_duplicated_share,
    find_critical_links
)

class TestRegionalIndicators(unittest.TestCase):
    def test_road_density(self):
        # 50,000 meters = 50 km
        # Area = 100 km2 -> 50 / 100 = 0.5 km/km2 = 500 km / 1,000 km2
        # Pop = 20,000 hab -> 50 km / 2 (10k hab) = 25.0 km/10k hab
        dense_area, dense_pop = road_density(50000.0, 100.0, 20000.0)
        self.assertAlmostEqual(dense_area, 500.0)
        self.assertAlmostEqual(dense_pop, 25.0)

        # Invalid cases
        with self.assertRaises(ValueError):
            road_density(-1.0, 100.0, 20000.0)
        with self.assertRaises(ValueError):
            road_density(50000.0, 0.0, 20000.0)
        with self.assertRaises(ValueError):
            road_density(50000.0, 100.0, 0.0)

    def test_paved_duplicated_share(self):
        # Total = 10,000m, Paved = 8,000m (80%), Duplicated = 3,000m (30%)
        pct_paved, pct_dup = paved_duplicated_share(10000.0, 8000.0, 3000.0)
        self.assertAlmostEqual(pct_paved, 80.0)
        self.assertAlmostEqual(pct_dup, 30.0)

        # Invalid cases
        with self.assertRaises(ValueError):
            paved_duplicated_share(0.0, 0.0, 0.0)
        with self.assertRaises(ValueError):
            paved_duplicated_share(10000.0, -100.0, 500.0)
        with self.assertRaises(ValueError):
            paved_duplicated_share(10000.0, 500.0, -100.0)
        with self.assertRaises(ValueError):
            paved_duplicated_share(10000.0, 12000.0, 500.0)
        with self.assertRaises(ValueError):
            paved_duplicated_share(10000.0, 500.0, 12000.0)

    def test_find_critical_links_line_graph(self):
        # 0-1-2-3: grafo em linha, toda aresta é ponte.
        edges = [(0, 1), (1, 2), (2, 3)]
        self.assertEqual(find_critical_links(edges, 4), [True, True, True])

    def test_find_critical_links_cycle_graph(self):
        # 0-1-2-3-0: ciclo, nenhuma aresta é ponte.
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        self.assertEqual(find_critical_links(edges, 4), [False, False, False, False])

    def test_find_critical_links_two_cycles_connected_by_bridge(self):
        # Ciclo {0,1,2} -- ponte (2,3) -- ciclo {3,4,5}.
        edges = [
            (0, 1), (1, 2), (2, 0),  # ciclo 1
            (2, 3),                  # ponte
            (3, 4), (4, 5), (5, 3),  # ciclo 2
        ]
        expected = [False, False, False, True, False, False, False]
        self.assertEqual(find_critical_links(edges, 6), expected)

    def test_find_critical_links_disconnected_graph(self):
        # Componente 1: ciclo {0,1,2}. Componente 2: linha 3-4 (ponte). Vértice 5 isolado.
        edges = [(0, 1), (1, 2), (2, 0), (3, 4)]
        self.assertEqual(find_critical_links(edges, 6), [False, False, False, True])

    def test_find_critical_links_invalid_cases(self):
        with self.assertRaises(ValueError):
            find_critical_links([(0, 1)], 0)
        with self.assertRaises(ValueError):
            find_critical_links([(0, 1)], -1)
        with self.assertRaises(ValueError):
            find_critical_links([(0, 2)], 2)  # vértice 2 fora de [0, 2)
        with self.assertRaises(ValueError):
            find_critical_links([(-1, 1)], 2)  # vértice negativo

if __name__ == '__main__':
    unittest.main()
