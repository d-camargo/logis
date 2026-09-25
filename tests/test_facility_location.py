# -*- coding: utf-8 -*-
"""Unit tests for facility location algorithms (p-median, p-center, MCLP, LSCP)."""

import unittest
from logis.core.location.facility import (
    solve_p_median,
    solve_p_center,
    solve_mclp,
    solve_lscp,
    _validate_inputs,
)


class TestFacilityLocation(unittest.TestCase):
    def setUp(self):
        # 3 demand points, 3 candidate locations
        # Cost matrix:
        # Demand 0: [0.0, 10.0, 20.0]
        # Demand 1: [10.0, 0.0, 5.0]
        # Demand 2: [20.0, 5.0, 0.0]
        self.cost_matrix = [
            [0.0, 10.0, 20.0],
            [10.0, 0.0, 5.0],
            [20.0, 5.0, 0.0],
        ]
        self.demand_weights = [100.0, 50.0, 50.0]

    def test_p_median_single_facility(self):
        # With p=1, candidate 0 cost = 100*0 + 50*10 + 50*20 = 1500
        # candidate 1 cost = 100*10 + 50*0 + 50*5 = 1250
        # candidate 2 cost = 100*20 + 50*5 + 50*0 = 2250
        # Optimal candidate is 1 with total cost 1250.
        selected, cost, assignments = solve_p_median(self.cost_matrix, self.demand_weights, p=1)
        self.assertEqual(selected, [1])
        self.assertAlmostEqual(cost, 1250.0)
        self.assertEqual(assignments, [1, 1, 1])

    def test_p_median_two_facilities(self):
        # With p=2: candidates [0, 1] cost = 100*0 + 50*0 + 50*5 = 250
        selected, cost, assignments = solve_p_median(self.cost_matrix, self.demand_weights, p=2)
        self.assertEqual(len(selected), 2)
        self.assertIn(0, selected)
        self.assertIn(1, selected)
        self.assertAlmostEqual(cost, 250.0)
        self.assertEqual(assignments, [0, 1, 1])

    def test_p_median_candidate_subset(self):
        # Restrict candidates to only [0, 2]
        selected, cost, assignments = solve_p_median(
            self.cost_matrix, self.demand_weights, p=1, candidate_indices=[0, 2]
        )
        self.assertEqual(selected, [0])
        self.assertAlmostEqual(cost, 1500.0)
        self.assertEqual(assignments, [0, 0, 0])

    def test_p_median_validation(self):
        with self.assertRaises(ValueError):
            solve_p_median([], self.demand_weights, p=1)
        with self.assertRaises(ValueError):
            solve_p_median(self.cost_matrix, [10.0], p=1)
        with self.assertRaises(ValueError):
            solve_p_median(self.cost_matrix, self.demand_weights, p=0)
        with self.assertRaises(ValueError):
            solve_p_median(self.cost_matrix, self.demand_weights, p=5)

    def test_p_center_unweighted(self):
        # Unweighted p-center (demand weights = [1.0, 1.0, 1.0])
        # Candidate 0: max(0, 10, 20) = 20
        # Candidate 1: max(10, 0, 5) = 10
        # Candidate 2: max(20, 5, 0) = 20
        # Optimal facility for p=1 is 1 with max cost 10.0.
        selected, max_cost, assignments = solve_p_center(self.cost_matrix, p=1)
        self.assertEqual(selected, [1])
        self.assertAlmostEqual(max_cost, 10.0)
        self.assertEqual(assignments, [1, 1, 1])

    def test_p_center_weighted(self):
        # Weighted p-center with demand_weights = [100.0, 50.0, 50.0]
        # Candidate 0: max(100*0, 50*10, 50*20) = 1000
        # Candidate 1: max(100*10, 50*0, 50*5) = 1000
        # Candidate 2: max(100*20, 50*5, 50*0) = 2000
        selected, max_cost, assignments = solve_p_center(self.cost_matrix, self.demand_weights, p=1)
        self.assertEqual(len(selected), 1)
        self.assertAlmostEqual(max_cost, 1000.0)

    def test_p_center_validation(self):
        with self.assertRaises(ValueError):
            solve_p_center([], p=1)
        with self.assertRaises(ValueError):
            solve_p_center(self.cost_matrix, p=0)
        with self.assertRaises(ValueError):
            solve_p_center(self.cost_matrix, p=5)

    def test_mclp(self):
        # Max distance = 6.0
        # Candidate 0 covers {0} (demand weight 100)
        # Candidate 1 covers {1, 2} (demand weight 50+50=100)
        # Candidate 2 covers {1, 2} (demand weight 50+50=100)
        # With p=2, choosing {0, 1} covers all 200 demand weight (ratio 1.0)
        selected, covered, total, ratio, mask = solve_mclp(
            self.cost_matrix, self.demand_weights, p=2, max_distance=6.0
        )
        self.assertEqual(len(selected), 2)
        self.assertAlmostEqual(covered, 200.0)
        self.assertAlmostEqual(total, 200.0)
        self.assertAlmostEqual(ratio, 1.0)
        self.assertTrue(all(mask))

    def test_mclp_zero_demand(self):
        selected, covered, total, ratio, mask = solve_mclp(
            self.cost_matrix, [0.0, 0.0, 0.0], p=1, max_distance=10.0
        )
        self.assertEqual(selected, [])
        self.assertEqual(covered, 0.0)
        self.assertEqual(total, 0.0)
        self.assertEqual(ratio, 0.0)
        self.assertFalse(any(mask))

    def test_mclp_validation(self):
        with self.assertRaises(ValueError):
            solve_mclp(self.cost_matrix, self.demand_weights, p=1, max_distance=-1.0)

    def test_lscp(self):
        # Max distance = 6.0
        # Set cover requires candidate 0 (for demand 0) and candidate 1 or 2 (for demand 1, 2).
        selected, is_covered, uncovered = solve_lscp(self.cost_matrix, max_distance=6.0)
        self.assertTrue(is_covered)
        self.assertEqual(len(uncovered), 0)
        self.assertEqual(len(selected), 2)
        self.assertIn(0, selected)

    def test_lscp_unreachable(self):
        # Max distance = 1.0 -> Demand 1 and 2 cannot cover demand 0 (cost 10)
        # Candidate 0 covers 0, Candidate 1 covers 1, Candidate 2 covers 2
        selected, is_covered, uncovered = solve_lscp(self.cost_matrix, max_distance=1.0)
        self.assertTrue(is_covered)
        self.assertEqual(len(selected), 3)

    def test_lscp_validation(self):
        with self.assertRaises(ValueError):
            solve_lscp(self.cost_matrix, max_distance=0.0)

    def test_validate_inputs_edge_cases(self):
        # Test non-rectangular cost matrix
        invalid_matrix = [[0.0, 10.0], [10.0]]
        with self.assertRaises(ValueError):
            _validate_inputs(invalid_matrix, [1.0, 1.0])

        # Test negative cost in matrix
        neg_cost_matrix = [[-1.0, 10.0], [10.0, 0.0]]
        with self.assertRaises(ValueError):
            _validate_inputs(neg_cost_matrix, [1.0, 1.0])

        # Test negative demand weight
        with self.assertRaises(ValueError):
            _validate_inputs(self.cost_matrix, [-10.0, 50.0, 50.0])

        # Test invalid candidate index
        with self.assertRaises(ValueError):
            _validate_inputs(self.cost_matrix, self.demand_weights, candidate_indices=[99])

    def test_facility_p_median_algorithm_metadata(self):
        from logis.algorithms.facility_p_median import FacilityPMedian
        alg = FacilityPMedian()
        self.assertEqual(alg.name(), "facility_p_median")
        self.assertEqual(alg.groupId(), "location")
        self.assertIsNotNone(alg.displayName())
        self.assertIsNotNone(alg.shortHelpString())

    def test_facility_mclp_algorithm_metadata(self):
        from logis.algorithms.facility_mclp import FacilityMCLP
        alg = FacilityMCLP()
        self.assertEqual(alg.name(), "facility_mclp")
        self.assertEqual(alg.groupId(), "location")
        self.assertIsNotNone(alg.displayName())
        self.assertIsNotNone(alg.shortHelpString())

    def test_facility_lscp_algorithm_metadata(self):
        from logis.algorithms.facility_lscp import FacilityLSCP
        alg = FacilityLSCP()
        self.assertEqual(alg.name(), "facility_lscp")
        self.assertEqual(alg.groupId(), "location")
        self.assertIsNotNone(alg.displayName())
        self.assertIsNotNone(alg.shortHelpString())


if __name__ == "__main__":
    unittest.main()
