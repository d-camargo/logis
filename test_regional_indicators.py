# -*- coding: utf-8 -*-
import unittest
from core.indicators.regional import (
    road_density,
    paved_duplicated_share
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

if __name__ == '__main__':
    unittest.main()
