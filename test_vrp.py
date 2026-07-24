# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
from logis.core.routing.vrp import (
    compute_route_distance,
    clarke_wright_savings,
    two_opt,
    or_opt,
    solve_cvrp,
    solve_cvrp_ortools,
)
from logis.core.optim_backend import has_ortools



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
        from logis.algorithms.vrp_cvrp import VrpCvrp
        alg = VrpCvrp()
        self.assertEqual(alg.name(), "vrp_cvrp")
        self.assertEqual(alg.groupId(), "routing")
        self.assertIsNotNone(alg.displayName())
        self.assertIsNotNone(alg.shortHelpString())

    @unittest.skipUnless(has_ortools(), "OR-Tools não instalado")
    def test_solve_cvrp_ortools(self):
        expected_customers = [1, 2, 3]

        for improve in [False, True]:
            # Direct call to solve_cvrp_ortools
            routes, total_dist, loads = solve_cvrp_ortools(
                self.distance_matrix, self.demands, self.capacity, depot=0, improve=improve
            )
            self.assertIsInstance(routes, list)
            self.assertIsInstance(total_dist, float)
            self.assertIsInstance(loads, list)
            self.assertEqual(len(routes), len(loads))
            visited = []
            for r, load in zip(routes, loads):
                self.assertLessEqual(load, self.capacity)
                self.assertAlmostEqual(load, sum(self.demands[c] for c in r))
                visited.extend(r)
            self.assertEqual(sorted(visited), expected_customers)

            # Call via solve_cvrp(backend="ortools")
            routes_b, total_dist_b, loads_b = solve_cvrp(
                self.distance_matrix, self.demands, self.capacity, depot=0, improve=improve, backend="ortools"
            )
            self.assertIsInstance(routes_b, list)
            self.assertIsInstance(total_dist_b, float)
            self.assertIsInstance(loads_b, list)
            self.assertEqual(len(routes_b), len(loads_b))
            visited_b = []
            for r, load in zip(routes_b, loads_b):
                self.assertLessEqual(load, self.capacity)
                self.assertAlmostEqual(load, sum(self.demands[c] for c in r))
                visited_b.extend(r)
            self.assertEqual(sorted(visited_b), expected_customers)

    def test_solve_cvrp_ortools_fallback(self):
        # Fallback silencioso: com OR-Tools ausente (mockado), backend="ortools"
        # não deve levantar exceção e deve produzir o mesmo resultado que "python".
        with patch("core.optim_backend.has_ortools", return_value=False):
            routes_o, dist_o, loads_o = solve_cvrp(
                self.distance_matrix, self.demands, self.capacity, depot=0, backend="ortools"
            )
        routes_p, dist_p, loads_p = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, backend="python"
        )
        self.assertEqual(routes_o, routes_p)
        self.assertAlmostEqual(dist_o, dist_p)
        self.assertEqual(loads_o, loads_p)

    def test_solve_cvrp_default_backend_regression(self):
        # O default (sem backend) deve ser idêntico a backend="python".
        default_res = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0
        )
        python_res = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, backend="python"
        )
        self.assertEqual(default_res[0], python_res[0])
        self.assertAlmostEqual(default_res[1], python_res[1])
        self.assertEqual(default_res[2], python_res[2])
        # E continua com o resultado já coberto pelos testes de solve_cvrp.
        self.assertEqual(len(default_res[0]), 2)
        self.assertEqual(default_res[2], [10.0, 8.0])
        self.assertAlmostEqual(default_res[1], 65.0)

    def test_solve_cvrp_ortools_validation(self):
        # Validação acontece antes do import lazy do OR-Tools, então roda sempre.
        # Matriz vazia
        with self.assertRaises(ValueError):
            solve_cvrp_ortools([], self.demands, self.capacity)
        # Demanda incompatível com a matriz
        with self.assertRaises(ValueError):
            solve_cvrp_ortools(self.distance_matrix, [0.0, 5.0], self.capacity)
        # Demanda negativa
        with self.assertRaises(ValueError):
            solve_cvrp_ortools(self.distance_matrix, [0.0, -5.0, 5.0, 8.0], self.capacity)
        # Demanda excede capacidade
        with self.assertRaises(ValueError):
            solve_cvrp_ortools(self.distance_matrix, self.demands, capacity=5.0)
        # Depósito inválido
        with self.assertRaises(ValueError):
            solve_cvrp_ortools(self.distance_matrix, self.demands, self.capacity, depot=10)
        # Sem clientes -> ([], 0.0, []) antes de tocar no OR-Tools
        routes, total_dist, loads = solve_cvrp_ortools(
            self.distance_matrix, [0.0, 0.0, 0.0, 0.0], self.capacity, depot=0
        )
        self.assertEqual(routes, [])
        self.assertAlmostEqual(total_dist, 0.0)
        self.assertEqual(loads, [])


if __name__ == "__main__":
    unittest.main()

