# -*- coding: utf-8 -*-
import unittest
from core.indicators.urban import network_density

class TestNetworkDensity(unittest.TestCase):
    def test_normal_case(self):
        # 5000 meters (5 km) / 2 km2 = 2.5 km/km2
        self.assertAlmostEqual(network_density(5000.0, 2.0), 2.5)
        # 10000 meters (10 km) / 10 km2 = 1.0 km/km2
        self.assertAlmostEqual(network_density(10000.0, 10.0), 1.0)

    def test_zero_length(self):
        # 0 meters / 5 km2 = 0.0 km/km2
        self.assertEqual(network_density(0.0, 5.0), 0.0)

    def test_negative_length(self):
        # Negative length should raise ValueError
        with self.assertRaises(ValueError):
            network_density(-100.0, 5.0)

    def test_zero_area(self):
        # Zero area should raise ValueError
        with self.assertRaises(ValueError):
            network_density(5000.0, 0.0)

    def test_negative_area(self):
        # Negative area should raise ValueError
        with self.assertRaises(ValueError):
            network_density(5000.0, -2.0)

if __name__ == '__main__':
    unittest.main()
