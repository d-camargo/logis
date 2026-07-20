# -*- coding: utf-8 -*-
import unittest
from core.routing.vrp import (
    compute_route_distance,
    clarke_wright_savings,
    two_opt,
    or_opt,
    solve_cvrp,
)


class TestVRP(unittest.TestCase):
    def setUp(self):
        # 4 nodes: 0 is depot, 1, 2, 3 are customers
        self.distance_matrix = [
            [0.0, 10.0, 10.0, 20.0],
            [10.0, 0.0, 5.0, 25.0],
            [10.0, 5.0, 0.0, 25.0],
            [20.0, 25.0, 25.0, 0.0],
        ]
        self.demands = [0.0, 5.0, 5.0, 8.0]
        self.capacity = 10.0

    def test_compute_route_distance(self):
        # Empty route -> distance 0.0
        self.assertAlmostEqual(compute_route_distance([], self.distance_matrix), 0.0)

        # Route [1] -> depot -> 1 -> depot: 10 + 10 = 20
        self.assertAlmostEqual(compute_route_distance([1], self.distance_matrix), 20.0)

        # Route [1, 2] -> depot -> 1 -> 2 -> depot: 10 + 5 + 10 = 25
        self.assertAlmostEqual(compute_route_distance([1, 2], self.distance_matrix), 25.0)

    def test_clarke_wright_savings_basic(self):
        routes, total_dist, loads = clarke_wright_savings(
            self.distance_matrix, self.demands, self.capacity, depot=0
        )
        # 1 and 2 should merge into route [1, 2] (load 10), 3 stays in route [3] (load 8)
        self.assertEqual(len(routes), 2)
        self.assertEqual(loads, [10.0, 8.0])
        self.assertAlmostEqual(total_dist, 65.0)
        self.assertIn([1, 2], routes)
        self.assertIn([3], routes)

    def test_clarke_wright_savings_no_customers(self):
        demands_zero = [0.0, 0.0, 0.0, 0.0]
        routes, total_dist, loads = clarke_wright_savings(
            self.distance_matrix, demands_zero, self.capacity, depot=0
        )
        self.assertEqual(routes, [])
        self.assertAlmostEqual(total_dist, 0.0)
        self.assertEqual(loads, [])

    def test_clarke_wright_savings_validation(self):
        # Empty matrix
        with self.assertRaises(ValueError):
            clarke_wright_savings([], self.demands, self.capacity)

        # Non-square matrix
        bad_matrix = [[0.0, 10.0], [10.0]]
        with self.assertRaises(ValueError):
            clarke_wright_savings(bad_matrix, [0.0, 5.0], self.capacity)

        # Negative distance
        neg_matrix = [[0.0, -5.0], [5.0, 0.0]]
        with self.assertRaises(ValueError):
            clarke_wright_savings(neg_matrix, [0.0, 5.0], self.capacity)

        # Invalid depot
        with self.assertRaises(ValueError):
            clarke_wright_savings(self.distance_matrix, self.demands, self.capacity, depot=10)

        # Mismatched demand length
        with self.assertRaises(ValueError):
            clarke_wright_savings(self.distance_matrix, [0.0, 5.0], self.capacity)

        # Negative demand
        with self.assertRaises(ValueError):
            clarke_wright_savings(self.distance_matrix, [0.0, -5.0, 5.0, 8.0], self.capacity)

        # Capacity <= 0
        with self.assertRaises(ValueError):
            clarke_wright_savings(self.distance_matrix, self.demands, capacity=0.0)

        # Demand exceeds capacity
        with self.assertRaises(ValueError):
            clarke_wright_savings(self.distance_matrix, self.demands, capacity=5.0)

    def test_two_opt_improvement(self):
        # Grid line 0, 1, 2, 3, 4
        dist_matrix = [
            [0.0, 1.0, 2.0, 3.0, 4.0],
            [1.0, 0.0, 1.0, 2.0, 3.0],
            [2.0, 1.0, 0.0, 1.0, 2.0],
            [3.0, 2.0, 1.0, 0.0, 1.0],
            [4.0, 3.0, 2.0, 1.0, 0.0],
        ]
        # Suboptimal route: [1, 3, 2, 4] -> dist = 1 + 2 + 1 + 2 + 4 = 10
        route = [1, 3, 2, 4]
        improved_route, dist = two_opt(route, dist_matrix, depot=0)
        self.assertEqual(improved_route, [1, 2, 3, 4])
        self.assertAlmostEqual(dist, 8.0)

    def test_two_opt_short_route(self):
        route = [1]
        improved_route, dist = two_opt(route, self.distance_matrix, depot=0)
        self.assertEqual(improved_route, [1])
        self.assertAlmostEqual(dist, 20.0)

    def test_two_opt_validation(self):
        with self.assertRaises(ValueError):
            two_opt([1, 10], self.distance_matrix, depot=0)

    def test_or_opt_improvement(self):
        # Grid line 0, 1, 2, 3, 4
        dist_matrix = [
            [0.0, 1.0, 2.0, 3.0, 4.0],
            [1.0, 0.0, 1.0, 2.0, 3.0],
            [2.0, 1.0, 0.0, 1.0, 2.0],
            [3.0, 2.0, 1.0, 0.0, 1.0],
            [4.0, 3.0, 2.0, 1.0, 0.0],
        ]
        # Suboptimal route: [3, 4, 1, 2] -> dist = 3 + 1 + 3 + 1 + 2 = 10
        # Moving segment [1, 2] to start or [3, 4] to end gives [1, 2, 3, 4] (dist 8)
        route = [3, 4, 1, 2]
        improved_route, dist = or_opt(route, dist_matrix, depot=0)
        self.assertAlmostEqual(dist, 8.0)
        self.assertLess(compute_route_distance(improved_route, dist_matrix, depot=0), 10.0)

    def test_or_opt_short_route(self):
        route = [2]
        improved_route, dist = or_opt(route, self.distance_matrix, depot=0)
        self.assertEqual(improved_route, [2])
        self.assertAlmostEqual(dist, 20.0)

    def test_or_opt_validation(self):
        with self.assertRaises(ValueError):
            or_opt([-1], self.distance_matrix, depot=0)

    def test_solve_cvrp_without_improve(self):
        routes, total_dist, loads = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, improve=False
        )
        self.assertEqual(len(routes), 2)
        self.assertEqual(loads, [10.0, 8.0])
        self.assertAlmostEqual(total_dist, 65.0)

    def test_solve_cvrp_with_improve(self):
        routes, total_dist, loads = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, improve=True
        )
        self.assertEqual(len(routes), 2)
        self.assertEqual(loads, [10.0, 8.0])
        self.assertAlmostEqual(total_dist, 65.0)
        # Check capacity constraint for all routes
        for r, load in zip(routes, loads):
            self.assertLessEqual(load, self.capacity)

    def test_vrp_cvrp_algorithm_metadata(self):
        from algorithms.vrp_cvrp import VrpCvrp
        alg = VrpCvrp()
        self.assertEqual(alg.name(), "vrp_cvrp")
        self.assertEqual(alg.groupId(), "routing")
        self.assertIsNotNone(alg.displayName())
        self.assertIsNotNone(alg.shortHelpString())


if __name__ == "__main__":
    unittest.main()
