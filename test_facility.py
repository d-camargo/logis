# -*- coding: utf-8 -*-
import unittest
from core.location.facility import solve_p_median, solve_p_center, solve_mclp, solve_lscp


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
        # With p=1, choosing 0 or 1 covers 100 out of 200 demand weight (ratio 0.5)
        # With p=2, choosing {0, 1} covers all 200 demand weight (ratio 1.0)
        selected, covered, total, ratio, mask = solve_mclp(
            self.cost_matrix, self.demand_weights, p=2, max_distance=6.0
        )
        self.assertEqual(len(selected), 2)
        self.assertAlmostEqual(covered, 200.0)
        self.assertAlmostEqual(total, 200.0)
        self.assertAlmostEqual(ratio, 1.0)
        self.assertTrue(all(mask))

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


if __name__ == "__main__":
    unittest.main()
