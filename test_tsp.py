# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch

from logis.core.routing.tsp import (
    compute_tour_cost,
    nearest_neighbor,
    two_opt_tour,
    or_opt_tour,
    solve_tsp,
    solve_tsp_ortools,
    split_legs,
    summarize_legs,
)
from logis.core.optim_backend import has_ortools


class TestTSP(unittest.TestCase):
    def setUp(self):
        # 4 nodes matrix (symmetric)
        self.distance_matrix = [
            [0.0, 10.0, 15.0, 20.0],
            [10.0, 0.0, 35.0, 25.0],
            [15.0, 35.0, 0.0, 30.0],
            [20.0, 25.0, 30.0, 0.0],
        ]

        # 4 points in a unit square: (0,0), (0,1), (1,1), (1,0)
        # Optimal closed tour is perimeter = 4.0
        self.square_matrix = [
            [0.0, 1.0, 1.41421356, 1.0],
            [1.0, 0.0, 1.0, 1.41421356],
            [1.41421356, 1.0, 0.0, 1.0],
            [1.0, 1.41421356, 1.0, 0.0],
        ]

        # 5 nodes on a straight line: 0, 1, 2, 3, 4
        self.line_matrix = [
            [0.0, 1.0, 2.0, 3.0, 4.0],
            [1.0, 0.0, 1.0, 2.0, 3.0],
            [2.0, 1.0, 0.0, 1.0, 2.0],
            [3.0, 2.0, 1.0, 0.0, 1.0],
            [4.0, 3.0, 2.0, 1.0, 0.0],
        ]

    def test_compute_tour_cost(self):
        # (a) compute_tour_cost fechado e aberto sobre uma matriz de 4 nós com custos conferidos na mão
        self.assertAlmostEqual(compute_tour_cost([], self.distance_matrix), 0.0)
        self.assertAlmostEqual(compute_tour_cost([0], self.distance_matrix), 0.0)

        # Closed tour [0, 1, 3, 2] -> 0->1 (10) + 1->3 (25) + 3->2 (30) + 2->0 (15) = 80.0
        closed_cost = compute_tour_cost([0, 1, 3, 2], self.distance_matrix, closed=True)
        self.assertAlmostEqual(closed_cost, 80.0)

        # Open tour [0, 1, 3, 2] -> 0->1 (10) + 1->3 (25) + 3->2 (30) = 65.0
        open_cost = compute_tour_cost([0, 1, 3, 2], self.distance_matrix, closed=False)
        self.assertAlmostEqual(open_cost, 65.0)

    def test_nearest_neighbor(self):
        # (b) nearest_neighbor devolve permutação completa começando em start, e com end dado termina em end
        # Closed tour starting at 0
        tour_closed = nearest_neighbor(self.distance_matrix, start=0, end=None)
        self.assertEqual(len(tour_closed), 4)
        self.assertEqual(tour_closed[0], 0)
        self.assertEqual(sorted(tour_closed), [0, 1, 2, 3])

        # Open tour starting at 0 and ending at 3
        tour_open = nearest_neighbor(self.distance_matrix, start=0, end=3)
        self.assertEqual(len(tour_open), 4)
        self.assertEqual(tour_open[0], 0)
        self.assertEqual(tour_open[-1], 3)
        self.assertEqual(sorted(tour_open), [0, 1, 2, 3])

    def test_local_search_improvement_and_fixed_end(self):
        # (c) 2-opt e Or-opt melhoram um tour propositalmente ruim (ordem cruzada)
        # e nunca movem a posição 0 nem a última quando fixed_end=True

        # Closed tour improvement on crossed order [0, 2, 1, 3] (cost 95 -> 80)
        bad_closed_tour = [0, 2, 1, 3]
        initial_closed_cost = compute_tour_cost(bad_closed_tour, self.distance_matrix, closed=True)
        self.assertAlmostEqual(initial_closed_cost, 95.0)

        improved_2opt_closed, cost_2opt_closed = two_opt_tour(
            bad_closed_tour, self.distance_matrix, closed=True, fixed_end=False
        )
        self.assertLess(cost_2opt_closed, initial_closed_cost)
        self.assertAlmostEqual(cost_2opt_closed, 80.0)

        improved_or_closed, cost_or_closed = or_opt_tour(
            bad_closed_tour, self.distance_matrix, closed=True, fixed_end=False
        )
        self.assertLess(cost_or_closed, initial_closed_cost)
        self.assertAlmostEqual(cost_or_closed, 80.0)

        # Open tour improvement with fixed_end=True on line matrix
        # Bad crossed order [0, 3, 1, 2, 4] -> open cost: 3 + 2 + 1 + 2 = 8.0
        bad_open_tour = [0, 3, 1, 2, 4]
        initial_open_cost = compute_tour_cost(bad_open_tour, self.line_matrix, closed=False)
        self.assertAlmostEqual(initial_open_cost, 8.0)

        # 2-opt with fixed_end=True
        improved_2opt_open, cost_2opt_open = two_opt_tour(
            bad_open_tour, self.line_matrix, closed=False, fixed_end=True
        )
        self.assertLess(cost_2opt_open, initial_open_cost)
        self.assertAlmostEqual(cost_2opt_open, 4.0)
        self.assertEqual(improved_2opt_open[0], 0)
        self.assertEqual(improved_2opt_open[-1], 4)

        # Or-opt with fixed_end=True
        improved_or_open, cost_or_open = or_opt_tour(
            bad_open_tour, self.line_matrix, closed=False, fixed_end=True
        )
        self.assertLess(cost_or_open, initial_open_cost)
        self.assertAlmostEqual(cost_or_open, 4.0)
        self.assertEqual(improved_or_open[0], 0)
        self.assertEqual(improved_or_open[-1], 4)

    def test_solve_tsp_python_closed_optimal(self):
        # (d) solve_tsp(..., backend="python") fechado numa instância cuja ótima é conhecida
        # (4 pontos em quadrado, ótimo é o perímetro 4.0) devolve exatamente o custo ótimo
        tour, cost = solve_tsp(self.square_matrix, start=0, end=None, backend="python")
        self.assertEqual(len(tour), 4)
        self.assertEqual(sorted(tour), [0, 1, 2, 3])
        self.assertAlmostEqual(cost, 4.0)

    def test_solve_tsp_python_open_with_end(self):
        # (e) solve_tsp(..., backend="python") aberto com end dado: order[0] == start, order[-1] == end,
        # todos os nós presentes uma vez, e o custo não inclui a volta (comparar com o valor calculado na mão)
        tour, cost = solve_tsp(self.square_matrix, start=0, end=2, backend="python")
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 2)
        self.assertEqual(len(tour), 4)
        self.assertEqual(sorted(tour), [0, 1, 2, 3])

        # Hand-calculated open cost: 0 -> 1 -> 3 -> 2 (1.0 + 1.41421356 + 1.0 = 3.41421356)
        # Does NOT include the return edge (2 -> 0 = 1.41421356)
        expected_hand_cost = 1.0 + 1.41421356 + 1.0
        self.assertAlmostEqual(cost, expected_hand_cost)
        self.assertAlmostEqual(cost, compute_tour_cost(tour, self.square_matrix, closed=False))

    def test_solve_tsp_end_equals_start_raises_value_error(self):
        # (f) end == start levanta ValueError
        with self.assertRaises(ValueError):
            solve_tsp(self.distance_matrix, start=0, end=0)

        with self.assertRaises(ValueError):
            nearest_neighbor(self.distance_matrix, start=0, end=0)

        with self.assertRaises(ValueError):
            solve_tsp_ortools(self.distance_matrix, start=0, end=0)

    def test_solve_tsp_matrix_1x1(self):
        # (g) matriz 1x1 → ([0], 0.0)
        tour, cost = solve_tsp([[0.0]], start=0, backend="python")
        self.assertEqual(tour, [0])
        self.assertAlmostEqual(cost, 0.0)

        tour_default, cost_default = solve_tsp([[0.0]], start=0)
        self.assertEqual(tour_default, [0])
        self.assertAlmostEqual(cost_default, 0.0)

    @unittest.skipUnless(has_ortools(), "OR-Tools não instalado")
    def test_solve_tsp_ortools_default_backend(self):
        # (h) backend automático (D-D): solve_tsp(matriz) sem passar backend usa o padrão "ortools"
        # com o pacote instalado devolve solução válida (mesmo conjunto de nós, custo <= custo do backend python + 1e-6)
        tour_default, cost_default = solve_tsp(self.distance_matrix, start=0)
        tour_python, cost_python = solve_tsp(self.distance_matrix, start=0, backend="python")

        self.assertEqual(sorted(tour_default), sorted(tour_python))
        self.assertLessEqual(cost_default, cost_python + 1e-6)

        # Direct call to solve_tsp_ortools for open tour
        tour_open, cost_open = solve_tsp_ortools(self.distance_matrix, start=0, end=3)
        self.assertEqual(tour_open[0], 0)
        self.assertEqual(tour_open[-1], 3)
        self.assertEqual(sorted(tour_open), [0, 1, 2, 3])

    def test_solve_tsp_ortools_fallback(self):
        # (h) com patch("logis.core.optim_backend.has_ortools", return_value=False) cai para o python sem levantar,
        # devolvendo tour válido
        with patch("logis.core.optim_backend.has_ortools", return_value=False):
            tour_fallback, cost_fallback = solve_tsp(self.distance_matrix, start=0)

        tour_python, cost_python = solve_tsp(self.distance_matrix, start=0, backend="python")
        self.assertEqual(tour_fallback, tour_python)
        self.assertAlmostEqual(cost_fallback, cost_python)

    def test_split_legs_and_summarize_legs(self):
        # (i) split_legs/summarize_legs (D-E):
        # num tour fechado de 4 nós (início + 3 paradas) saem 4 pernas, exatamente uma 'acesso' e uma 'retorno',
        # e a soma dos leg_dist bate com o compute_tour_cost fechado
        closed_order = [0, 1, 3, 2]
        legs_closed = split_legs(closed_order, self.distance_matrix, closed=True)
        self.assertEqual(len(legs_closed), 4)

        roles_closed = [leg[2] for leg in legs_closed]
        self.assertEqual(roles_closed.count("acesso"), 1)
        self.assertEqual(roles_closed.count("retorno"), 1)
        self.assertEqual(roles_closed, ["acesso", "rota", "rota", "retorno"])

        sum_dist_closed = sum(leg[3] for leg in legs_closed)
        closed_cost = compute_tour_cost(closed_order, self.distance_matrix, closed=True)
        self.assertAlmostEqual(sum_dist_closed, closed_cost)

        summary_closed = summarize_legs(legs_closed)
        self.assertAlmostEqual(
            summary_closed["tour_dist"],
            summary_closed["access_dist"] + summary_closed["service_dist"] + summary_closed["return_dist"],
            delta=1e-6,
        )
        self.assertAlmostEqual(
            summary_closed["dead_ratio"],
            (summary_closed["access_dist"] + summary_closed["return_dist"]) / summary_closed["tour_dist"],
            delta=1e-6,
        )

        # num caminho aberto com end, idem sem a volta
        open_order = [0, 1, 2, 3]
        legs_open = split_legs(open_order, self.distance_matrix, closed=False)
        self.assertEqual(len(legs_open), 3)

        roles_open = [leg[2] for leg in legs_open]
        self.assertEqual(roles_open.count("acesso"), 1)
        self.assertEqual(roles_open.count("retorno"), 1)
        self.assertEqual(roles_open, ["acesso", "rota", "retorno"])

        sum_dist_open = sum(leg[3] for leg in legs_open)
        open_cost = compute_tour_cost(open_order, self.distance_matrix, closed=False)
        self.assertAlmostEqual(sum_dist_open, open_cost)

        summary_open = summarize_legs(legs_open)
        self.assertAlmostEqual(
            summary_open["tour_dist"],
            summary_open["access_dist"] + summary_open["service_dist"] + summary_open["return_dist"],
            delta=1e-6,
        )
        self.assertAlmostEqual(
            summary_open["dead_ratio"],
            (summary_open["access_dist"] + summary_open["return_dist"]) / summary_open["tour_dist"],
            delta=1e-6,
        )

        # com uma única parada, saem duas pernas e service_dist == 0.0
        single_stop_order = [0, 1]
        legs_single = split_legs(single_stop_order, self.distance_matrix, closed=True)
        self.assertEqual(len(legs_single), 2)
        summary_single = summarize_legs(legs_single)
        self.assertAlmostEqual(summary_single["service_dist"], 0.0)

        # e a identidade tour_dist == access_dist + service_dist + return_dist vale dentro de 1e-6,
        # com dead_ratio igual a (access_dist + return_dist) / tour_dist
        self.assertAlmostEqual(
            summary_single["tour_dist"],
            summary_single["access_dist"] + summary_single["service_dist"] + summary_single["return_dist"],
            delta=1e-6,
        )
        self.assertAlmostEqual(
            summary_single["dead_ratio"],
            (summary_single["access_dist"] + summary_single["return_dist"]) / summary_single["tour_dist"],
            delta=1e-6,
        )

    def test_split_legs_edge_cases(self):
        # Empty order or single node
        self.assertEqual(split_legs([], self.distance_matrix), [])
        self.assertEqual(split_legs([0], self.distance_matrix), [])

    def test_vrp_tsp_algorithm_metadata(self):
        from logis.algorithms.vrp_tsp import VrpTsp
        alg = VrpTsp()
        self.assertEqual(alg.name(), "vrp_tsp")
        self.assertEqual(alg.groupId(), "routing")
        self.assertIsNotNone(alg.displayName())
        help_str = alg.shortHelpString()
        self.assertIsNotNone(help_str)
        self.assertIn("visit_seq", help_str)
        self.assertIn("access_dist", help_str)
        self.assertIn("return_dist", help_str)

class TestVrpTspAlgorithm(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(__file__)
        self.alg_path = os.path.join(self.base_dir, "logis", "algorithms", "vrp_tsp.py")
        self.provider_path = os.path.join(self.base_dir, "logis", "provider.py")

        with open(self.alg_path, "r", encoding="utf-8") as f:
            self.alg_source = f.read()

        with open(self.provider_path, "r", encoding="utf-8") as f:
            self.provider_source = f.read()

    def test_vrp_tsp_algorithm_metadata_and_parameters(self):
        from logis.algorithms.vrp_tsp import VrpTsp
        alg = VrpTsp()
        self.assertEqual(alg.name(), "vrp_tsp")
        self.assertEqual(alg.groupId(), "routing")

        params = [
            "INPUT_START",
            "INPUT_POINTS",
            "INPUT_END",
            "INPUT_NETWORK",
            "IMPROVE",
            "OUTPUT_ORDER",
            "OUTPUT_ROUTE",
        ]
        for param in params:
            self.assertTrue(hasattr(alg, param), f"VrpTsp deve declarar o atributo {param}")
            self.assertIn(f"{param} =", self.alg_source)

        # Verificar que INPUT_END é optional=True
        self.assertIn("INPUT_END", self.alg_source)
        self.assertIn("optional=True", self.alg_source)

        # Verificar que NÃO existe a string USE_ORTOOLS em vrp_tsp.py (D-D)
        self.assertNotIn("USE_ORTOOLS", self.alg_source)

        # Verificar 5 campos de OUTPUT_ORDER
        order_fields = ["visit_seq", "node_role", "leg_role", "leg_dist", "cum_dist"]
        for field in order_fields:
            self.assertIn(field, self.alg_source, f"Campo '{field}' de OUTPUT_ORDER deve estar no fonte")

        # Verificar 14 campos de OUTPUT_ROUTE
        route_fields = [
            "leg_seq",
            "from_seq",
            "to_seq",
            "leg_role",
            "leg_dist",
            "cum_dist",
            "stop_count",
            "tour_dist",
            "access_dist",
            "service_dist",
            "return_dist",
            "dead_ratio",
            "closed",
            "backend",
        ]
        for field in route_fields:
            self.assertIn(field, self.alg_source, f"Campo '{field}' de OUTPUT_ROUTE deve estar no fonte")

    def test_provider_imports_and_registers_vrptsp(self):
        self.assertIn("from .algorithms.vrp_tsp import VrpTsp", self.provider_source)
        self.assertIn("self.addAlgorithm(VrpTsp())", self.provider_source)


if __name__ == "__main__":
    unittest.main()
