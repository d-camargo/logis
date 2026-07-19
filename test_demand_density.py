# -*- coding: utf-8 -*-
import unittest
from core.indicators.urban import demand_density

class TestDemandDensity(unittest.TestCase):
    def test_normal_case(self):
        # 10000 population / 2.0 km2 = 5000.0 hab/km2
        self.assertAlmostEqual(demand_density(10000, 2.0), 5000.0)
        # 5000.5 population / 10.0 km2 = 500.05 hab/km2
        self.assertAlmostEqual(demand_density(5000.5, 10.0), 500.05)

    def test_zero_population(self):
        # 0 population / 5.0 km2 = 0.0 hab/km2
        self.assertEqual(demand_density(0, 5.0), 0.0)

    def test_negative_population(self):
        # Negative population should raise ValueError
        with self.assertRaises(ValueError):
            demand_density(-10, 5.0)

    def test_zero_area(self):
        # Zero area should raise ValueError
        with self.assertRaises(ValueError):
            demand_density(100, 0.0)

    def test_negative_area(self):
        # Negative area should raise ValueError
        with self.assertRaises(ValueError):
            demand_density(100, -2.0)

if __name__ == '__main__':
    unittest.main()
