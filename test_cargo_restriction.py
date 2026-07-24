# -*- coding: utf-8 -*-
import unittest
from logis.core.indicators.urban import cargo_restriction_index

class TestCargoRestrictionIndex(unittest.TestCase):
    def test_fully_accessible(self):
        # 10000m total, 0m restricted -> 100% accessible
        self.assertAlmostEqual(cargo_restriction_index(10000.0, 0.0), 100.0)

    def test_fully_restricted(self):
        # 10000m total, 10000m restricted -> 0% accessible
        self.assertAlmostEqual(cargo_restriction_index(10000.0, 10000.0), 0.0)

    def test_partially_restricted(self):
        # 10000m total, 3000m restricted -> 70% accessible
        self.assertAlmostEqual(cargo_restriction_index(10000.0, 3000.0), 70.0)
        # 5000m total, 1250m restricted -> 75% accessible
        self.assertAlmostEqual(cargo_restriction_index(5000.0, 1250.0), 75.0)

    def test_invalid_total_length(self):
        # total_length_m <= 0 should raise ValueError
        with self.assertRaises(ValueError):
            cargo_restriction_index(0.0, 0.0)
        with self.assertRaises(ValueError):
            cargo_restriction_index(-100.0, 50.0)

    def test_negative_restricted_length(self):
        # restricted_length_m < 0 should raise ValueError
        with self.assertRaises(ValueError):
            cargo_restriction_index(1000.0, -10.0)

    def test_restricted_greater_than_total(self):
        # restricted_length_m > total_length_m should raise ValueError
        with self.assertRaises(ValueError):
            cargo_restriction_index(1000.0, 1001.0)

if __name__ == '__main__':
    unittest.main()
