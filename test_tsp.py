# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch

try:
    from qgis.core import (
        QgsApplication,
        QgsVectorLayer,
        QgsField,
        QgsFeature,
        QgsGeometry,
        QgsPointXY,
        QgsCoordinateReferenceSystem,
        QgsProcessingContext,
        QgsProcessingFeedback,
        QgsProcessingException,
        QgsProject,
    )
    from qgis.PyQt.QtCore import QVariant

    _qgs = QgsApplication.instance()
    if not _qgs:
        _qgs = QgsApplication([], False)
        _qgs.initQgis()
    _HAS_QGIS = True
except ImportError:
    _HAS_QGIS = False

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

    def test_solve_tsp_ortools_load_solver_failure(self):
        # Quando load_routing_solver falha em solve_tsp_ortools, converte para RuntimeError com a indicação do diálogo
        with patch("logis.core.routing.tsp.load_routing_solver", side_effect=RuntimeError("OR-Tools import falhou")):
            with self.assertRaises(RuntimeError) as ctx:
                solve_tsp_ortools(self.distance_matrix, start=0)
            self.assertIn("Complementos → logis → Dependências…", str(ctx.exception))

    def test_solve_tsp_blocked_guard_uses_python_fallback(self):
        # (b) Com o selo bloqueado, solve_tsp devolve tour válido pela heurística Python sem tocar em ortools
        with patch("logis.core.optim_backend.guard_state", return_value="blocked"), \
             patch("logis.core.routing.tsp.load_routing_solver") as mock_load:
            tour, cost = solve_tsp(self.distance_matrix, start=0, backend="ortools")
            mock_load.assert_not_called()
            self.assertEqual(len(tour), 4)
            self.assertEqual(sorted(tour), [0, 1, 2, 3])
            tour_py, cost_py = solve_tsp(self.distance_matrix, start=0, backend="python")
            self.assertEqual(tour, tour_py)
            self.assertAlmostEqual(cost, cost_py)

    def test_solve_tsp_ortools_runtime_error_fallback(self):
        # (a) mock de solve_tsp_ortools levantando RuntimeError -> solve_tsp devolve tour válido pela heurística
        with patch("logis.core.routing.tsp.pick_backend", return_value="ortools"), \
             patch("logis.core.routing.tsp.solve_tsp_ortools", side_effect=RuntimeError("Erro OR-Tools")):
            tour, cost = solve_tsp(self.distance_matrix, start=0, backend="ortools")

        tour_py, cost_py = solve_tsp(self.distance_matrix, start=0, backend="python")
        self.assertEqual(tour, tour_py)
        self.assertAlmostEqual(cost, cost_py)

    def test_solve_tsp_ortools_happy_path_mock(self):
        # (c) caminho feliz OR-Tools intacto (mock devolvendo tour)
        expected_tour = [0, 1, 3, 2]
        expected_cost = 80.0
        with patch("logis.core.routing.tsp.pick_backend", return_value="ortools"), \
             patch("logis.core.routing.tsp.solve_tsp_ortools", return_value=(expected_tour, expected_cost)):
            tour, cost = solve_tsp(self.distance_matrix, start=0, backend="ortools")

        self.assertEqual(tour, expected_tour)
        self.assertEqual(cost, expected_cost)

    def test_solve_tsp_with_feedback(self):
        # (a) solve_tsp com feedback reporta progresso e termina
        fb = FakeFeedback()
        tour, cost = solve_tsp(self.distance_matrix, start=0, backend="python", improve=True, feedback=fb)
        self.assertEqual(sorted(tour), [0, 1, 2, 3])
        self.assertTrue(len(fb.progresses) > 0)
        self.assertTrue(len(fb.infos) > 0)

    def test_solve_tsp_canceled_feedback(self):
        # (b) feedback já cancelado devolve tour válido rapidamente, sem exceção
        fb = FakeFeedback(cancel_after_n_progress=0) # cancela imediatamente
        fb._canceled = True
        tour, cost = solve_tsp(self.distance_matrix, start=0, backend="python", improve=True, feedback=fb)
        self.assertEqual(len(tour), 4) # devolve tour valido
        self.assertEqual(sorted(tour), [0, 1, 2, 3])

        fb2 = FakeFeedback(cancel_after_n_progress=1)
        tour2, cost2 = solve_tsp(self.distance_matrix, start=0, backend="ortools", improve=True, feedback=fb2)
        self.assertEqual(len(tour2), 4)

    def test_solve_tsp_none_feedback(self):
        # (c) feedback=None (padrão) continua idêntico
        tour, cost = solve_tsp(self.distance_matrix, start=0, backend="python", improve=True)
        self.assertEqual(sorted(tour), [0, 1, 2, 3])

    def test_solve_tsp_fallback_with_feedback(self):
        # (d) o fallback RuntimeError -> heurística segue valendo com feedback
        fb = FakeFeedback()
        with patch("logis.core.routing.tsp.pick_backend", return_value="ortools"), \
             patch("logis.core.routing.tsp.solve_tsp_ortools", side_effect=RuntimeError("Erro")):
            tour, cost = solve_tsp(self.distance_matrix, start=0, backend="ortools", improve=True, feedback=fb)
        self.assertEqual(sorted(tour), [0, 1, 2, 3])
        self.assertTrue(len(fb.progresses) > 0)

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
        self.assertIn("Python puro", help_str)

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
            "BACKEND",
            "OUTPUT_ORDER",
            "OUTPUT_ROUTE",
        ]
        for param in params:
            self.assertTrue(hasattr(alg, param), f"VrpTsp deve declarar o atributo {param}")
            self.assertIn(f"{param} =", self.alg_source)

        # Verificar parâmetro BACKEND, enum, opções, parameterAsEnum e repasse de backend= para solve_tsp
        self.assertIn("QgsProcessingParameterEnum", self.alg_source)
        self.assertIn("Automático (OR-Tools quando disponível)", self.alg_source)
        self.assertIn("Python puro (heurística)", self.alg_source)
        self.assertIn("OR-Tools", self.alg_source)
        self.assertIn("parameterAsEnum", self.alg_source)
        self.assertIn("backend=", self.alg_source)

        # Verificar que INPUT_END é optional=True
        self.assertIn("INPUT_END", self.alg_source)
        self.assertIn("optional=True", self.alg_source)

        # Verificar que NÃO existe a string USE_ORTOOLS em vrp_tsp.py (D-D)
        self.assertNotIn("USE_ORTOOLS", self.alg_source)

        # Verificar 5 campos de OUTPUT_ORDER
        order_fields = ["visit_seq", "node_role", "leg_role", "leg_dist", "cum_dist"]
        for field in order_fields:
            self.assertIn(field, self.alg_source, f"Campo '{field}' de OUTPUT_ORDER deve estar no fonte")

        # Verificar 16 campos de OUTPUT_ROUTE
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
            "dist_mode",
            "leg_geom",
        ]
        for field in route_fields:
            self.assertIn(field, self.alg_source, f"Campo '{field}' de OUTPUT_ROUTE deve estar no fonte")

    def test_vrp_tsp_checked_transform_usage(self):
        # (a) teste estático de que o TSP importa de crs_transform e não chama mais .transform(raw_ direto
        self.assertIn("from ..core.crs_transform import", self.alg_source)
        self.assertIn("checked_transform", self.alg_source)
        self.assertIn("transform_points", self.alg_source)
        self.assertNotIn(".transform(raw_start_pt)", self.alg_source)
        self.assertNotIn(".transform(raw_end_pt)", self.alg_source)
        self.assertNotIn(".transform(pt) for pt in raw_visit_pts", self.alg_source)

    def test_vrp_tsp_network_guards(self):
        self.assertIn("_UNREACHABLE_COST", self.alg_source)
        self.assertIn("math.isinf", self.alg_source)
        self.assertIn("v == -1", self.alg_source)
        self.assertIn("amarrar", self.alg_source)
        self.assertIn('cache_id="vrp_tsp"', self.alg_source)

    def test_vrp_tsp_network_extent_and_dijkstra_cache(self):
        self.assertIn("extent=extent", self.alg_source)
        self.assertIn("3000.0", self.alg_source)
        self.assertIn("QgsRectangle", self.alg_source)
        self.assertIn("dijkstra_trees", self.alg_source)

    def test_vrp_tsp_crashlog_trace(self):
        # (passo 2 do plano) rastro de diagnóstico: crashlog importado e etapas marcadas
        self.assertIn("crashlog", self.alg_source)
        for stage in (
            "tsp-inicio",
            "tsp-transform",
            "tsp-build-graph",
            "tsp-grafo-pronto",
            "tsp-od-matrix",
            "tsp-ortools-import",
            "tsp-solver-ok",
            "tsp-sinks",
            "tsp-fim",
        ):
            self.assertIn(f'crashlog.mark("{stage}"', self.alg_source)

    def test_provider_imports_and_registers_vrptsp(self):
        self.assertIn("from .algorithms.vrp_tsp import VrpTsp", self.provider_source)
        self.assertIn("self.addAlgorithm(VrpTsp())", self.provider_source)

    def test_vrp_tsp_progress_phases(self):
        # (passo 4 do plano) Encadear as faixas de progresso no logis:vrp_tsp
        self.assertIn("PhaseProgress", self.alg_source)
        self.assertIn("feedback.setProgressText", self.alg_source)
        self.assertIn("Construindo o grafo", self.alg_source)
        self.assertIn("Calculando a matriz OD", self.alg_source)
        self.assertIn("Otimizando (OR-Tools)", self.alg_source)
        self.assertIn("Otimizando (heurística Python)", self.alg_source)
        self.assertIn("Gravando as saídas", self.alg_source)

        # Repasse de feedback= sub-faixa para build_graph, compute_od_matrix e solve_tsp
        self.assertIn("feedback=p_build", self.alg_source)
        self.assertIn("feedback=p_od", self.alg_source)
        self.assertIn("feedback=p_opt", self.alg_source)

    def test_vrp_tsp_metric_crs_check(self):
        # (passo 6 do plano) Garantir CRS métrico no cálculo: mapUnits() comparado com EPSG:5880
        self.assertIn('points_crs.mapUnits() == QgsCoordinateReferenceSystem("EPSG:5880").mapUnits()', self.alg_source)
        self.assertNotIn("points_crs.isGeographic()", self.alg_source)
        self.assertNotIn("source_crs.isGeographic()", self.alg_source)

    def test_extract_point(self):
        from qgis.core import QgsGeometry, QgsPointXY
        from logis.algorithms.vrp_tsp import _extract_point

        # Single point
        geom_pt = QgsGeometry.fromWkt("POINT(10 20)")
        pt = _extract_point(geom_pt)
        self.assertIsInstance(pt, QgsPointXY)
        self.assertAlmostEqual(pt.x(), 10.0)
        self.assertAlmostEqual(pt.y(), 20.0)

        # MultiPoint (uses first point)
        geom_mpt = QgsGeometry.fromWkt("MULTIPOINT((15 25), (35 45))")
        mpt = _extract_point(geom_mpt)
        self.assertIsInstance(mpt, QgsPointXY)
        self.assertAlmostEqual(mpt.x(), 15.0)
        self.assertAlmostEqual(mpt.y(), 25.0)

        # Polygon (uses centroid)
        geom_poly = QgsGeometry.fromWkt("POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))")
        poly_pt = _extract_point(geom_poly)
        self.assertIsInstance(poly_pt, QgsPointXY)
        self.assertAlmostEqual(poly_pt.x(), 5.0)
        self.assertAlmostEqual(poly_pt.y(), 5.0)

        # Invalid or empty geometries raise ValueError
        with self.assertRaises(ValueError):
            _extract_point(None)

        with self.assertRaises(ValueError):
            _extract_point(QgsGeometry())

        with self.assertRaises(ValueError):
            _extract_point(QgsGeometry.fromWkt("POINT EMPTY"))

        with self.assertRaises(ValueError):
            _extract_point(QgsGeometry.fromWkt("MULTIPOINT EMPTY"))


class LogFeedback(QgsProcessingFeedback if _HAS_QGIS else object):
    def __init__(self):
        if _HAS_QGIS:
            super().__init__()
        self.infos = []
        self.warnings = []

    def pushInfo(self, info):
        self.infos.append(info)

    def pushWarning(self, warning):
        self.warnings.append(warning)
        if _HAS_QGIS:
            super().pushWarning(warning)


@unittest.skipUnless(_HAS_QGIS, "QGIS não disponível")
class TestVrpTspRealQgisRegression(unittest.TestCase):
    """
    Teste de regressão com QGIS real para VrpTsp:
    - Rede em EPSG:4674 em torno de (-46.63, -23.55).
    - Pontos de início e visita em graus com SRC inválido (layer.setCrs(QgsCoordinateReferenceSystem()))
      -> a rota é calculada, a janela de análise logada está em metros (|x| > 1e5) e o log contém o aviso de EPSG:4674 assumido.
    - Pontos declarados em EPSG:5880 -> QgsProcessingException citando o SRC.
    """

    def setUp(self):
        net_layer = QgsVectorLayer("LineString?crs=EPSG:4674", "net", "memory")
        dp = net_layer.dataProvider()
        dp.addAttributes([QgsField("oneway", QVariant.String), QgsField("speed", QVariant.Double)])
        net_layer.updateFields()

        lines = [
            [QgsPointXY(-46.64, -23.56), QgsPointXY(-46.62, -23.56)],
            [QgsPointXY(-46.62, -23.56), QgsPointXY(-46.62, -23.54)],
            [QgsPointXY(-46.62, -23.54), QgsPointXY(-46.64, -23.54)],
            [QgsPointXY(-46.64, -23.54), QgsPointXY(-46.64, -23.56)],
            [QgsPointXY(-46.63, -23.56), QgsPointXY(-46.63, -23.54)],
            [QgsPointXY(-46.64, -23.55), QgsPointXY(-46.62, -23.55)],
        ]
        for pts in lines:
            f = QgsFeature(net_layer.fields())
            f.setGeometry(QgsGeometry.fromPolylineXY(pts))
            f.setAttribute("oneway", "B")
            f.setAttribute("speed", 40.0)
            dp.addFeature(f)
        net_layer.updateExtents()
        self.net_layer = net_layer

    def test_invalid_crs_fallback_and_degrees_in_projected_exception(self):
        from logis.algorithms.vrp_tsp import VrpTsp

        start_layer = QgsVectorLayer("Point?crs=EPSG:4674", "start", "memory")
        f_start = QgsFeature()
        f_start.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.63, -23.55)))
        start_layer.dataProvider().addFeature(f_start)
        start_layer.updateExtents()

        points_layer = QgsVectorLayer("Point?crs=EPSG:4674", "points", "memory")
        for pt in [QgsPointXY(-46.631, -23.551), QgsPointXY(-46.629, -23.549)]:
            f_pt = QgsFeature()
            f_pt.setGeometry(QgsGeometry.fromPointXY(pt))
            points_layer.dataProvider().addFeature(f_pt)
        points_layer.updateExtents()

        # 2. Pontos com SRC inválido
        start_layer.setCrs(QgsCoordinateReferenceSystem())
        points_layer.setCrs(QgsCoordinateReferenceSystem())

        alg = VrpTsp()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        fb = LogFeedback()

        params = {
            "INPUT_START": start_layer,
            "INPUT_POINTS": points_layer,
            "INPUT_NETWORK": self.net_layer,
            "BACKEND": 1,  # Python
            "OUTPUT_ORDER": "memory:",
            "OUTPUT_ROUTE": "memory:",
        }

        res = alg.processAlgorithm(params, context, fb)
        self.assertIn("OUTPUT_ORDER", res)
        self.assertIn("OUTPUT_ROUTE", res)

        # Log contém o aviso de EPSG:4674 assumido
        all_logs = " ".join(fb.infos)
        self.assertIn("EPSG:4674", all_logs)
        self.assertTrue(
            any("assumindo EPSG:4674" in w for w in fb.warnings),
            "O aviso de EPSG:4674 assumido deve chegar via pushWarning.",
        )

        # Janela de análise logada está em metros (|x| > 1e5)
        extent_log = [log for log in fb.infos if "Janela de análise:" in log]
        self.assertTrue(len(extent_log) > 0)
        ext_str = extent_log[0]
        coords = [float(val) for val in ext_str.replace("Janela de análise:", "").replace(":", ",").split(",") if val.strip()]
        self.assertTrue(any(abs(c) > 1e5 for c in coords))

        # 3. Pontos declarados em EPSG:5880 -> QgsProcessingException citando o SRC
        start_layer_5880 = QgsVectorLayer("Point?crs=EPSG:5880", "start_5880", "memory")
        start_layer_5880.dataProvider().addFeature(f_start)
        start_layer_5880.updateExtents()

        points_layer_5880 = QgsVectorLayer("Point?crs=EPSG:5880", "points_5880", "memory")
        for pt in [QgsPointXY(-46.631, -23.551), QgsPointXY(-46.629, -23.549)]:
            f_pt = QgsFeature()
            f_pt.setGeometry(QgsGeometry.fromPointXY(pt))
            points_layer_5880.dataProvider().addFeature(f_pt)
        points_layer_5880.updateExtents()

        params_5880 = {
            "INPUT_START": start_layer_5880,
            "INPUT_POINTS": points_layer_5880,
            "INPUT_NETWORK": self.net_layer,
            "BACKEND": 1,
            "OUTPUT_ORDER": "memory:",
            "OUTPUT_ROUTE": "memory:",
        }

        with self.assertRaises(QgsProcessingException) as ctx:
            alg.processAlgorithm(params_5880, context, fb)
        self.assertIn("EPSG:5880", str(ctx.exception))

    def test_regression_0_6_2_network_and_euclidean(self):
        from logis.algorithms.vrp_tsp import VrpTsp
        import math
        
        # Points in EPSG:4326 around (-46.63, -23.55)
        start_layer = QgsVectorLayer("Point?crs=EPSG:4326", "start", "memory")
        f_start = QgsFeature()
        f_start.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.63, -23.55)))
        start_layer.dataProvider().addFeature(f_start)
        start_layer.updateExtents()

        points_layer = QgsVectorLayer("Point?crs=EPSG:4326", "points", "memory")
        f_pt1 = QgsFeature()
        f_pt1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.631, -23.551)))
        f_pt2 = QgsFeature()
        f_pt2.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.629, -23.549)))
        points_layer.dataProvider().addFeatures([f_pt1, f_pt2])
        points_layer.updateExtents()

        alg = VrpTsp()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        fb = LogFeedback()

        # Network mode
        params = {
            "INPUT_START": start_layer,
            "INPUT_POINTS": points_layer,
            "INPUT_NETWORK": self.net_layer,
            "BACKEND": 1,
            "OUTPUT_ORDER": "memory:",
            "OUTPUT_ROUTE": "memory:",
        }

        res = alg.processAlgorithm(params, context, fb)

        # Check outputs
        out_order = res["OUTPUT_ORDER"]
        out_route = res["OUTPUT_ROUTE"]

        def _resolve_output(ctx, val, name):
            if isinstance(val, str):
                lay = ctx.getMapLayer(val)
                if lay is not None and lay.isValid():
                    return lay
                return QgsVectorLayer(val, name, "ogr")
            return val

        order_layer = _resolve_output(context, out_order, "order")
        route_layer = _resolve_output(context, out_route, "route")
        
        # Check CRS
        self.assertEqual(order_layer.crs().authid(), "EPSG:4674")
        self.assertEqual(route_layer.crs().authid(), "EPSG:4674")
        
        # Check Janela de análise
        extent_log = [log for log in fb.infos if "Janela de análise:" in log]
        self.assertTrue(len(extent_log) > 0)
        ext_str = extent_log[0]
        coords = [float(val) for val in ext_str.replace("Janela de análise:", "").replace(":", ",").split(",") if val.strip()]
        self.assertTrue(any(c > 5.7e6 for c in coords), "x da janela na casa de 5.7M")
        
        # Check distance between input start point and output start point
        feat = next(order_layer.getFeatures())
        geom = feat.geometry()
        out_pt = geom.asPoint()
        dist = math.hypot(out_pt.x() - (-46.63), out_pt.y() - (-23.55))
        self.assertTrue(dist < 1e-6)
        
        # Euclidean mode
        fb2 = LogFeedback()
        params_euc = {
            "INPUT_START": start_layer,
            "INPUT_POINTS": points_layer,
            "BACKEND": 1,
            "OUTPUT_ORDER": "memory:",
            "OUTPUT_ROUTE": "memory:",
        }
        res_euc = alg.processAlgorithm(params_euc, context, fb2)
        
        out_order_euc = res_euc["OUTPUT_ORDER"]
        out_route_euc = res_euc["OUTPUT_ROUTE"]
        order_layer_euc = _resolve_output(context, out_order_euc, "order_euc")
        route_layer_euc = _resolve_output(context, out_route_euc, "route_euc")
        
        self.assertEqual(order_layer_euc.crs().authid(), "EPSG:4674")
        self.assertEqual(route_layer_euc.crs().authid(), "EPSG:4674")
        
        feat_euc = next(route_layer_euc.getFeatures())
        leg_dist = feat_euc.attribute("leg_dist")
        self.assertTrue(leg_dist > 100) # distance in meters

    def test_utm_fallback_on_fake_transform(self):
        from logis.algorithms.vrp_tsp import VrpTsp
        
        start_layer = QgsVectorLayer("Point?crs=EPSG:4326", "start", "memory")
        f_start = QgsFeature()
        f_start.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.63, -23.55)))
        start_layer.dataProvider().addFeature(f_start)
        start_layer.updateExtents()

        points_layer = QgsVectorLayer("Point?crs=EPSG:4326", "points", "memory")
        f_pt1 = QgsFeature()
        f_pt1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.631, -23.551)))
        points_layer.dataProvider().addFeatures([f_pt1])
        points_layer.updateExtents()

        alg = VrpTsp()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        fb = LogFeedback()

        params = {
            "INPUT_START": start_layer,
            "INPUT_POINTS": points_layer,
            "BACKEND": 1,
            "OUTPUT_ORDER": "memory:",
            "OUTPUT_ROUTE": "memory:",
        }
        
        from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem
        orig_init = QgsCoordinateTransform.__init__
        orig_transform = QgsCoordinateTransform.transform
        orig_isvalid = QgsCoordinateTransform.isValid
        orig_isshort = QgsCoordinateTransform.isShortCircuited

        class FakeTransform:
            def __init__(self, src, dst, ctx=None):
                self.src = src
                self.dst = dst
                self._real = None
                if dst.authid() != "EPSG:5880":
                    self._real = QgsCoordinateTransform(src, dst, ctx)

            def transform(self, pt, *args):
                if self.dst.authid() == "EPSG:5880":
                    return pt
                return self._real.transform(pt, *args)
                
            def isValid(self):
                return True
                
            def isShortCircuited(self):
                return False

        with patch("logis.core.crs_transform.QgsCoordinateTransform", FakeTransform):
            res = alg.processAlgorithm(params, context, fb)
            
        all_logs = " ".join(fb.infos + fb.warnings)
        self.assertIn("EPSG:31983", all_logs)
        self.assertIn("adotando fallback para EPSG:31983", all_logs)


if __name__ == "__main__":
    unittest.main()
