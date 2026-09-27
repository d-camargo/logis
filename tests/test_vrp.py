# -*- coding: utf-8 -*-
import math
import unittest
from unittest.mock import patch
from logis.core.routing.vrp import (
    compute_route_distance,
    clarke_wright_savings,
    two_opt,
    or_opt,
    solve_cvrp,
    solve_cvrp_ortools,
    solve_multi_depot_cvrp,
)
from logis.core.optim_backend import has_ortools



class FakeFeedback:
    def __init__(self, cancel_after_n_progress=9999):
        self.progresses = []
        self.infos = []
        self.cancel_after = cancel_after_n_progress
        self.progress_count = 0
        self._canceled = False
    def setProgress(self, progress: float):
        self.progresses.append(progress)
        self.progress_count += 1
        if self.progress_count >= self.cancel_after:
            self._canceled = True
    def pushInfo(self, info: str):
        self.infos.append(info)
    def isCanceled(self) -> bool:
        return self._canceled


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
        with patch("logis.core.optim_backend.has_ortools", return_value=False):
            routes_o, dist_o, loads_o = solve_cvrp(
                self.distance_matrix, self.demands, self.capacity, depot=0, backend="ortools"
            )
        routes_p, dist_p, loads_p = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, backend="python"
        )
        self.assertEqual(routes_o, routes_p)
        self.assertAlmostEqual(dist_o, dist_p)
        self.assertEqual(loads_o, loads_p)

    def test_solve_cvrp_ortools_load_solver_failure(self):
        # Quando load_routing_solver falha em solve_cvrp_ortools, converte para RuntimeError com a indicação do diálogo
        with patch("logis.core.routing.vrp.load_routing_solver", side_effect=RuntimeError("OR-Tools import falhou")):
            with self.assertRaises(RuntimeError) as ctx:
                solve_cvrp_ortools(self.distance_matrix, self.demands, self.capacity, depot=0)
            self.assertIn("Complementos → logis → Dependências…", str(ctx.exception))

    def test_solve_cvrp_blocked_guard_uses_python_fallback(self):
        # Com o selo bloqueado, solve_cvrp devolve rotas válidas pela heurística Python sem tocar em ortools
        with patch("logis.core.optim_backend.guard_state", return_value="blocked"), \
             patch("logis.core.routing.vrp.load_routing_solver") as mock_load:
            routes, dist, loads = solve_cvrp(
                self.distance_matrix, self.demands, self.capacity, depot=0, backend="ortools"
            )
            mock_load.assert_not_called()
            routes_py, dist_py, loads_py = solve_cvrp(
                self.distance_matrix, self.demands, self.capacity, depot=0, backend="python"
            )
            self.assertEqual(routes, routes_py)
            self.assertAlmostEqual(dist, dist_py)
            self.assertEqual(loads, loads_py)

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

    def test_solve_cvrp_ortools_runtime_error_fallback(self):
        # Mock de solve_cvrp_ortools levantando RuntimeError -> solve_cvrp devolve rotas válidas pela heurística
        with patch("logis.core.routing.vrp.pick_backend", return_value="ortools"), \
             patch("logis.core.routing.vrp.solve_cvrp_ortools", side_effect=RuntimeError("Erro OR-Tools")):
            routes, dist, loads = solve_cvrp(
                self.distance_matrix, self.demands, self.capacity, depot=0, backend="ortools"
            )

        routes_py, dist_py, loads_py = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, backend="python"
        )
        self.assertEqual(routes, routes_py)
        self.assertAlmostEqual(dist, dist_py)
        self.assertEqual(loads, loads_py)

    def test_solve_cvrp_ortools_happy_path_mock(self):
        # Caminho feliz OR-Tools intacto (mock devolvendo rotas)
        expected_routes = [[1, 2], [3]]
        expected_dist = 65.0
        expected_loads = [10.0, 8.0]
        with patch("logis.core.routing.vrp.pick_backend", return_value="ortools"), \
             patch("logis.core.routing.vrp.solve_cvrp_ortools", return_value=(expected_routes, expected_dist, expected_loads)):
            routes, dist, loads = solve_cvrp(
                self.distance_matrix, self.demands, self.capacity, depot=0, backend="ortools"
            )

        self.assertEqual(routes, expected_routes)
        self.assertAlmostEqual(dist, expected_dist)
        self.assertEqual(loads, expected_loads)

    def test_solve_cvrp_with_feedback(self):
        # (a) solve_cvrp com feedback reporta progresso e termina
        fb = FakeFeedback()
        routes, dist, loads = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, backend="python", improve=True, feedback=fb
        )
        self.assertEqual(len(routes), 2)
        self.assertTrue(len(fb.progresses) > 0)
        self.assertTrue(len(fb.infos) > 0)

    def test_solve_cvrp_canceled_feedback(self):
        # (b) feedback já cancelado devolve rotas válidas rapidamente, sem exceção
        fb = FakeFeedback(cancel_after_n_progress=0)
        fb._canceled = True
        routes, dist, loads = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, backend="python", improve=True, feedback=fb
        )
        self.assertTrue(len(routes) > 0)
        visited = [c for r in routes for c in r]
        self.assertEqual(sorted(visited), [1, 2, 3])

        fb2 = FakeFeedback(cancel_after_n_progress=1)
        routes2, dist2, loads2 = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, backend="ortools", improve=True, feedback=fb2
        )
        self.assertTrue(len(routes2) > 0)
        visited2 = [c for r in routes2 for c in r]
        self.assertEqual(sorted(visited2), [1, 2, 3])

    def test_solve_cvrp_none_feedback(self):
        # (c) feedback=None (padrão) continua idêntico
        routes, dist, loads = solve_cvrp(
            self.distance_matrix, self.demands, self.capacity, depot=0, backend="python", improve=True
        )
        self.assertEqual(len(routes), 2)

    def test_solve_cvrp_fallback_with_feedback(self):
        # (d) o fallback RuntimeError -> heurística segue valendo com feedback
        fb = FakeFeedback()
        with patch("logis.core.routing.vrp.pick_backend", return_value="ortools"), \
             patch("logis.core.routing.vrp.solve_cvrp_ortools", side_effect=RuntimeError("Erro")):
            routes, dist, loads = solve_cvrp(
                self.distance_matrix, self.demands, self.capacity, depot=0, backend="ortools", improve=True, feedback=fb
            )
        self.assertEqual(len(routes), 2)
        self.assertTrue(len(fb.progresses) > 0)


class TestMultiDepotCVRP(unittest.TestCase):
    def setUp(self):
        # 2 depósitos (0 e 1) em pontas opostas e 6 clientes:
        # Clientes 2, 3, 4 perto do depósito 0
        # Clientes 5, 6, 7 perto do depósito 1
        self.coords = [
            (0.0, 0.0),    # 0: Depósito 0
            (100.0, 0.0),  # 1: Depósito 1
            (1.0, 0.0),    # 2: Cliente A1 (dist D0=1, D1=99)
            (2.0, 0.0),    # 3: Cliente A2 (dist D0=2, D1=98)
            (3.0, 0.0),    # 4: Cliente A3 (dist D0=3, D1=97)
            (97.0, 0.0),   # 5: Cliente B1 (dist D0=97, D1=3)
            (98.0, 0.0),   # 6: Cliente B2 (dist D0=98, D1=2)
            (99.0, 0.0),   # 7: Cliente B3 (dist D0=99, D1=1)
        ]
        self.matrix = [
            [math.hypot(c1[0] - c2[0], c1[1] - c2[1]) for c2 in self.coords]
            for c1 in self.coords
        ]
        self.demands = [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        self.capacity = 10.0
        self.depots = [0, 1]

    def test_case_i_two_depots_nearest_assignment(self):
        # (i) dois depósitos em pontas opostas e 6 clientes, 3 perto de cada um, sem
        # assignment -> cada cliente cai no depósito mais próximo e toda rota começa e termina nele
        routes, total_dist, loads, route_depots = solve_multi_depot_cvrp(
            self.matrix, self.demands, self.capacity, depots=self.depots, assignment=None
        )
        self.assertTrue(len(routes) >= 2)
        visited = [c for r in routes for c in r]
        self.assertEqual(sorted(visited), [2, 3, 4, 5, 6, 7])

        for route, depot in zip(routes, route_depots):
            self.assertGreater(len(route), 0)
            if depot == 0:
                for c in route:
                    self.assertIn(c, {2, 3, 4})
            elif depot == 1:
                for c in route:
                    self.assertIn(c, {5, 6, 7})
            else:
                self.fail(f"Depósito inesperado: {depot}")

        computed_total = sum(
            compute_route_distance(r, self.matrix, depot=d)
            for r, d in zip(routes, route_depots)
        )
        self.assertAlmostEqual(total_dist, computed_total)

    def test_case_ii_explicit_assignment_distant_depot(self):
        # (ii) o mesmo caso com assignment mandando um cliente para o depósito distante
        # -> ele sai numa rota daquele depósito
        assignment = {2: 1}  # Cliente 2 (perto do D0) forçado para o D1
        routes, total_dist, loads, route_depots = solve_multi_depot_cvrp(
            self.matrix, self.demands, self.capacity, depots=self.depots, assignment=assignment
        )
        visited = [c for r in routes for c in r]
        self.assertEqual(sorted(visited), [2, 3, 4, 5, 6, 7])

        client_2_depot = None
        for route, depot in zip(routes, route_depots):
            if 2 in route:
                client_2_depot = depot
                break
        self.assertEqual(client_2_depot, 1)

        # Depósito 0 atende apenas 3 e 4
        for route, depot in zip(routes, route_depots):
            if depot == 0:
                for c in route:
                    self.assertIn(c, {3, 4})
            elif depot == 1:
                for c in route:
                    self.assertIn(c, {2, 5, 6, 7})

    def test_case_iii_single_depot_identical_to_solve_cvrp(self):
        # (iii) um só depósito -> rotas e distância idênticas às de solve_cvrp
        distance_matrix = [
            [0.0, 10.0, 10.0, 20.0],
            [10.0, 0.0, 5.0, 25.0],
            [10.0, 5.0, 0.0, 25.0],
            [20.0, 25.0, 25.0, 0.0],
        ]
        demands = [0.0, 5.0, 5.0, 8.0]
        capacity = 10.0

        routes_multi, dist_multi, loads_multi, depots_multi = solve_multi_depot_cvrp(
            distance_matrix, demands, capacity, depots=[0]
        )
        routes_single, dist_single, loads_single = solve_cvrp(
            distance_matrix, demands, capacity, depot=0
        )

        self.assertEqual(routes_multi, routes_single)
        self.assertAlmostEqual(dist_multi, dist_single)
        self.assertEqual(loads_multi, loads_single)
        self.assertEqual(depots_multi, [0] * len(routes_single))

    def test_case_iv_depot_without_clients_no_empty_route(self):
        # (iv) depósito sem cliente -> nenhuma rota vazia para ele
        # Manda todos os 6 clientes para o depósito 0
        assignment = {c: 0 for c in [2, 3, 4, 5, 6, 7]}
        routes, total_dist, loads, route_depots = solve_multi_depot_cvrp(
            self.matrix, self.demands, self.capacity, depots=self.depots, assignment=assignment
        )
        for r in routes:
            self.assertGreater(len(r), 0)
        self.assertNotIn(1, route_depots)
        self.assertTrue(all(d == 0 for d in route_depots))
        self.assertEqual(len(routes), len(route_depots))

    def test_case_v_unreachable_client_raises_value_error(self):
        # (v) cliente sem depósito alcançável -> ValueError
        matrix_unreach = [row[:] for row in self.matrix]
        matrix_unreach[0][7] = 1e18
        matrix_unreach[1][7] = 1e18

        with self.assertRaises(ValueError) as ctx:
            solve_multi_depot_cvrp(
                matrix_unreach, self.demands, self.capacity, depots=self.depots
            )
        self.assertIn("7", str(ctx.exception))

    def test_case_vi_capacity_respected_in_all_routes(self):
        # (vi) capacidade respeitada em todas as rotas
        cap = 2.0  # com demanda 1.0 cada, no máximo 2 clientes por rota
        routes, total_dist, loads, route_depots = solve_multi_depot_cvrp(
            self.matrix, self.demands, cap, depots=self.depots
        )
        self.assertTrue(len(routes) >= 4)
        for route, load, depot in zip(routes, loads, route_depots):
            self.assertGreater(len(route), 0)
            self.assertLessEqual(load, cap)
            self.assertEqual(load, sum(self.demands[c] for c in route))

    def test_validation_errors(self):
        # Depósitos vazios
        with self.assertRaises(ValueError):
            solve_multi_depot_cvrp(self.matrix, self.demands, self.capacity, depots=[])

        # Depósito inválido fora de alcance
        with self.assertRaises(ValueError):
            solve_multi_depot_cvrp(self.matrix, self.demands, self.capacity, depots=[99])

        # Depósitos duplicados
        with self.assertRaises(ValueError):
            solve_multi_depot_cvrp(self.matrix, self.demands, self.capacity, depots=[0, 0])

        # Demanda excede capacidade
        bad_demands = [0.0, 0.0, 15.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        with self.assertRaises(ValueError):
            solve_multi_depot_cvrp(self.matrix, bad_demands, 10.0, depots=[0, 1])

        # Cliente inexistente no assignment
        with self.assertRaises(ValueError):
            solve_multi_depot_cvrp(self.matrix, self.demands, self.capacity, depots=[0, 1], assignment={99: 0})

        # Cliente é depósito no assignment
        with self.assertRaises(ValueError):
            solve_multi_depot_cvrp(self.matrix, self.demands, self.capacity, depots=[0, 1], assignment={0: 1})

        # Depósito alvo não está em depots
        with self.assertRaises(ValueError):
            solve_multi_depot_cvrp(self.matrix, self.demands, self.capacity, depots=[0, 1], assignment={2: 5})

    def test_no_customers_returns_empty(self):
        matrix_depots_only = [[0.0, 10.0], [10.0, 0.0]]
        demands_depots_only = [0.0, 0.0]
        routes, dist, loads, depots = solve_multi_depot_cvrp(
            matrix_depots_only, demands_depots_only, 10.0, depots=[0, 1]
        )
        self.assertEqual(routes, [])
        self.assertAlmostEqual(dist, 0.0)
        self.assertEqual(loads, [])
        self.assertEqual(depots, [])


if __name__ == "__main__":
    unittest.main()


