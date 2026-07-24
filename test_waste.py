# -*- coding: utf-8 -*-
import unittest
from logis.core.indicators.waste import (
    sector_waste_generation,
    allocate_generation_by_street_length,
    estimate_fleet_size,
    compute_deadhead_ratio
)

try:
    from qgis.core import (
        QgsApplication, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
        QgsField, QgsProcessingContext, QgsProcessingFeedback, NULL
    )
    from qgis.PyQt.QtCore import QVariant

    _qgs = QgsApplication.instance()
    if not _qgs:
        _qgs = QgsApplication([], False)
        _qgs.initQgis()
    _HAS_QGIS = True
except ImportError:
    _HAS_QGIS = False


class TestWaste(unittest.TestCase):
    """
    Testes unitários para as funções de indicadores de resíduos em core/indicators/waste.py.
    """

    def test_sector_waste_generation(self):
        # 10.000 hab * 0.9 kg/hab/dia * 1.0 cobertura = 9000 kg/dia
        self.assertAlmostEqual(sector_waste_generation(10000, 0.9, 1.0), 9000.0)
        # Cobertura parcial: 10.000 hab * 0.95 kg/hab/dia * 0.8 cobertura = 7600 kg/dia
        self.assertAlmostEqual(sector_waste_generation(10000, 0.95, 0.8), 7600.0)
        # População zero -> geração zero
        self.assertEqual(sector_waste_generation(0, 0.9, 1.0), 0.0)
        # Defaults: population=1000 -> 1000 * 0.9 * 1.0 = 900.0
        self.assertAlmostEqual(sector_waste_generation(1000), 900.0)

        with self.assertRaises(ValueError):
            sector_waste_generation(-100, 0.9, 1.0)
        with self.assertRaises(ValueError):
            sector_waste_generation(1000, 0.0, 1.0)
        with self.assertRaises(ValueError):
            sector_waste_generation(1000, 0.9, -0.1)
        with self.assertRaises(ValueError):
            sector_waste_generation(1000, 0.9, 1.1)

    def test_allocate_generation_by_street_length(self):
        # 900 kg/dia rateados por comprimento: [200m, 600m, 200m] -> [180, 540, 180]
        result = allocate_generation_by_street_length(900.0, [200.0, 600.0, 200.0])
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[0], 180.0)
        self.assertAlmostEqual(result[1], 540.0)
        self.assertAlmostEqual(result[2], 180.0)
        self.assertAlmostEqual(sum(result), 900.0)

        # Trecho único recebe toda a geração
        result_single = allocate_generation_by_street_length(500.0, [1000.0])
        self.assertAlmostEqual(result_single[0], 500.0)

        # Geração total zero -> todos os trechos recebem zero
        result_zero = allocate_generation_by_street_length(0.0, [100.0, 200.0])
        self.assertAlmostEqual(sum(result_zero), 0.0)

        with self.assertRaises(ValueError):
            allocate_generation_by_street_length(-10.0, [100.0])
        with self.assertRaises(ValueError):
            allocate_generation_by_street_length(900.0, [])
        with self.assertRaises(ValueError):
            allocate_generation_by_street_length(900.0, [100.0, 0.0])
        with self.assertRaises(ValueError):
            allocate_generation_by_street_length(900.0, [100.0, -50.0])

    def test_estimate_fleet_size(self):
        # Caso 1: Rota única cabendo em 1 veículo
        res = estimate_fleet_size([20.0], 10.0, 8.0, 0.5, 0.5)
        self.assertEqual(res["fleet_size"], 1)
        self.assertEqual(res["vehicle_assignments"], [[0]])
        self.assertAlmostEqual(res["total_route_time_h"], 3.0)
        self.assertAlmostEqual(res["avg_utilization"], 3.0 / 8.0)

        # Caso 2: Múltiplas rotas distribuídas em múltiplos veículos (FFD Bin Packing)
        res_multi = estimate_fleet_size([30.0, 30.0, 30.0], 10.0, 8.0, 0.5, 0.5)
        self.assertEqual(res_multi["fleet_size"], 2)
        self.assertEqual(len(res_multi["vehicle_assignments"]), 2)
        self.assertAlmostEqual(res_multi["total_route_time_h"], 12.0)
        self.assertAlmostEqual(res_multi["avg_utilization"], 12.0 / 16.0)

        # Caso 3: Rota isolada excedendo a jornada máxima (ValueError)
        with self.assertRaises(ValueError):
            estimate_fleet_size([100.0], 10.0, 8.0, 0.5, 0.5)

        # Caso 4: Parâmetros operacionais/temporais inválidos (ValueError)
        with self.assertRaises(ValueError):
            estimate_fleet_size([10.0], 0.0, 8.0, 0.5, 0.5)
        with self.assertRaises(ValueError):
            estimate_fleet_size([10.0], 10.0, -8.0, 0.5, 0.5)
        with self.assertRaises(ValueError):
            estimate_fleet_size([10.0], 10.0, 8.0, -0.5, 0.5)
        with self.assertRaises(ValueError):
            estimate_fleet_size([10.0], 10.0, 8.0, 0.5, -0.5)

        # Caso 5: Lista de rotas vazia ou com distâncias inválidas (ValueError)
        with self.assertRaises(ValueError):
            estimate_fleet_size([], 10.0, 8.0, 0.5, 0.5)
        with self.assertRaises(ValueError):
            estimate_fleet_size([-10.0], 10.0, 8.0, 0.5, 0.5)

    def test_compute_deadhead_ratio(self):
        # Caso 1: Rota única sem route_ids (chave None) com trechos produtivos e deadhead
        res1 = compute_deadhead_ratio([10.0, 5.0, 5.0], [False, True, False])
        self.assertAlmostEqual(res1["total"]["productive_km"], 15.0)
        self.assertAlmostEqual(res1["total"]["deadhead_km"], 5.0)
        self.assertAlmostEqual(res1["total"]["deadhead_ratio"], 5.0 / 15.0)
        self.assertAlmostEqual(res1["routes"][None]["productive_km"], 15.0)
        self.assertAlmostEqual(res1["routes"][None]["deadhead_km"], 5.0)

        # Caso 2: Múltiplas rotas com route_ids explicitados (agrupamento por rota e total)
        res2 = compute_deadhead_ratio(
            [10.0, 2.0, 8.0, 4.0],
            [False, True, False, True],
            route_ids=[1, 1, 2, 2]
        )
        self.assertAlmostEqual(res2["routes"][1]["productive_km"], 10.0)
        self.assertAlmostEqual(res2["routes"][1]["deadhead_km"], 2.0)
        self.assertAlmostEqual(res2["routes"][1]["deadhead_ratio"], 0.2)
        self.assertAlmostEqual(res2["routes"][2]["productive_km"], 8.0)
        self.assertAlmostEqual(res2["routes"][2]["deadhead_km"], 4.0)
        self.assertAlmostEqual(res2["routes"][2]["deadhead_ratio"], 0.5)
        self.assertAlmostEqual(res2["total"]["productive_km"], 18.0)
        self.assertAlmostEqual(res2["total"]["deadhead_km"], 6.0)
        self.assertAlmostEqual(res2["total"]["deadhead_ratio"], 6.0 / 18.0)

        # Caso 3: Rota sem nenhum trecho deadhead (deadhead_km = 0.0, ratio = 0.0)
        res3 = compute_deadhead_ratio([5.0, 10.0], [False, False])
        self.assertAlmostEqual(res3["total"]["productive_km"], 15.0)
        self.assertAlmostEqual(res3["total"]["deadhead_km"], 0.0)
        self.assertAlmostEqual(res3["total"]["deadhead_ratio"], 0.0)

        # Caso 4: Rota com apenas trechos deadhead (productive_km = 0.0, ratio = None)
        res4 = compute_deadhead_ratio([5.0, 5.0], [True, True])
        self.assertAlmostEqual(res4["total"]["productive_km"], 0.0)
        self.assertAlmostEqual(res4["total"]["deadhead_km"], 10.0)
        self.assertIsNone(res4["total"]["deadhead_ratio"])

        # Caso 5: Entradas com comprimentos inválidos/negativos ou lista vazia (ValueError)
        with self.assertRaises(ValueError):
            compute_deadhead_ratio([], [])
        with self.assertRaises(ValueError):
            compute_deadhead_ratio([-5.0], [False])
        with self.assertRaises(ValueError):
            compute_deadhead_ratio(["inválido"], [False])

        # Caso 6: Listas com tamanhos incompatíveis entre si (ValueError)
        with self.assertRaises(ValueError):
            compute_deadhead_ratio([10.0], [False, True])
        with self.assertRaises(ValueError):
            compute_deadhead_ratio([10.0, 5.0], [False])
        with self.assertRaises(ValueError):
            compute_deadhead_ratio([10.0, 5.0], [False, True], route_ids=[1])

    def test_waste_cpp_route_algorithm_metadata(self):
        try:
            from logis.algorithms.waste_cpp_route import WasteCppRoute
            alg = WasteCppRoute()
            self.assertEqual(alg.name(), "waste_cpp_route")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteCppRoute)
            self.assertIn("route_is_deadhead", alg.shortHelpString())
        except ImportError:
            # Em ambiente sem QGIS C++ bindings completos, ignora instanciação
            pass

    @unittest.skipUnless(_HAS_QGIS, "requer bindings QGIS completos")
    def test_waste_cpp_route_marks_deadhead_edges(self):
        # Grafo simples com 2 nós ímpares (A-B, B-C, C-D):
        # O CPP emparelha A e D duplicando o caminho A-B-C-D.
        # Assim, os 3 trechos serão percorridos 2 vezes (1ª passagem regular, 2ª passagem deadhead).
        from logis.algorithms.waste_cpp_route import WasteCppRoute

        layer = QgsVectorLayer("LineString?crs=EPSG:3857", "streets", "memory")
        provider = layer.dataProvider()
        layer.updateFields()

        def add_feature(coords):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(*c) for c in coords]))
            provider.addFeature(feat)

        add_feature([(0, 0), (10, 0)])   # A-B
        add_feature([(10, 0), (20, 0)])  # B-C
        add_feature([(20, 0), (30, 0)])  # C-D
        layer.updateExtents()

        alg = WasteCppRoute()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        params = {
            alg.INPUT_STREETS: layer,
            alg.NODE_TOLERANCE: 0.01,
            alg.OUTPUT: "memory:out",
        }
        result = alg.processAlgorithm(params, context, feedback)
        out_layer = context.getMapLayer(result[alg.OUTPUT])

        idx_deadhead = out_layer.fields().indexFromName("route_is_deadhead")
        self.assertNotEqual(idx_deadhead, -1)

        deadhead_values = [feat.attribute(idx_deadhead) for feat in out_layer.getFeatures()]
        self.assertIn(True, deadhead_values)
        self.assertIn(False, deadhead_values)

    def test_waste_rpp_route_algorithm_metadata(self):
        try:
            from logis.algorithms.waste_rpp_route import WasteRppRoute
            alg = WasteRppRoute()
            self.assertEqual(alg.name(), "waste_rpp_route")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteRppRoute)
            self.assertIn("route_is_connector", alg.shortHelpString())
        except ImportError:
            pass

    @unittest.skipUnless(_HAS_QGIS, "requer bindings QGIS completos")
    def test_waste_rpp_route_marks_connector_edges(self):
        # Dois componentes obrigatórios desconexos (A-B-C e D-E) ligados só por um
        # trecho opcional (C-D); reaproveita o mesmo cenário de componentes
        # desconexos usado nos testes de connect_required_components.
        from logis.algorithms.waste_rpp_route import WasteRppRoute

        layer = QgsVectorLayer("LineString?crs=EPSG:3857", "streets", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("required", QVariant.Bool)])
        layer.updateFields()

        def add_feature(coords, required):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(*c) for c in coords]))
            feat.setAttributes([required])
            provider.addFeature(feat)

        add_feature([(0, 0), (10, 0)], True)    # A-B, obrigatório
        add_feature([(10, 0), (20, 0)], True)   # B-C, obrigatório
        add_feature([(20, 0), (30, 0)], False)  # C-D, conector (opcional)
        add_feature([(30, 0), (40, 0)], True)   # D-E, obrigatório
        layer.updateExtents()

        alg = WasteRppRoute()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        params = {
            alg.INPUT_STREETS: layer,
            alg.FIELD_REQUIRED: "required",
            alg.NODE_TOLERANCE: 0.01,
            alg.OUTPUT: "memory:out",
        }
        result = alg.processAlgorithm(params, context, feedback)
        out_layer = context.getMapLayer(result[alg.OUTPUT])

        idx_required = out_layer.fields().indexFromName("required")
        idx_connector = out_layer.fields().indexFromName("route_is_connector")

        seen_connector = False
        for feat in out_layer.getFeatures():
            is_required = feat.attribute(idx_required)
            is_connector = feat.attribute(idx_connector)
            # Trecho obrigatório nunca é marcado como conetor; o único trecho
            # opcional (C-D) é sempre marcado como conetor.
            self.assertEqual(is_connector, not is_required)
            if is_connector:
                seen_connector = True
        self.assertTrue(seen_connector, "nenhum trecho conetor foi gravado na saída")

    def test_waste_carp_route_algorithm_metadata(self):
        try:
            from logis.algorithms.waste_carp_route import WasteCarpRoute
            alg = WasteCarpRoute()
            self.assertEqual(alg.name(), "waste_carp_route")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteCarpRoute)
            self.assertIn("route_is_deadhead", alg.shortHelpString())
        except ImportError:
            pass

    @unittest.skipUnless(_HAS_QGIS, "requer bindings QGIS completos")
    def test_waste_carp_route_splits_by_capacity(self):
        # Depósito na origem, dois trechos obrigatórios de 6 kg cada e capacidade
        # de 10 kg: a soma (12 kg) excede a capacidade de uma única viagem, então
        # o algorithm deve gerar exatamente 2 rotas.
        from logis.algorithms.waste_carp_route import WasteCarpRoute

        layer = QgsVectorLayer("LineString?crs=EPSG:3857", "streets", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("demand", QVariant.Double)])
        layer.updateFields()

        def add_feature(coords, demand):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(*c) for c in coords]))
            feat.setAttributes([demand])
            provider.addFeature(feat)

        add_feature([(0, 0), (10, 0)], 6.0)
        add_feature([(0, 0), (-10, 0)], 6.0)
        layer.updateExtents()

        depot_layer = QgsVectorLayer("Point?crs=EPSG:3857", "depot", "memory")
        depot_provider = depot_layer.dataProvider()
        depot_feat = QgsFeature()
        depot_feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(0, 0)))
        depot_provider.addFeature(depot_feat)
        depot_layer.updateExtents()

        alg = WasteCarpRoute()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        params = {
            alg.INPUT_STREETS: layer,
            alg.FIELD_DEMAND: "demand",
            alg.CAPACITY: 10.0,
            alg.INPUT_DEPOT: depot_layer,
            alg.NODE_TOLERANCE: 0.01,
            alg.OUTPUT: "memory:out",
        }
        result = alg.processAlgorithm(params, context, feedback)
        out_layer = context.getMapLayer(result[alg.OUTPUT])

        idx_route = out_layer.fields().indexFromName("route_id")
        route_ids = {feat.attribute(idx_route) for feat in out_layer.getFeatures()}
        self.assertEqual(len(route_ids), 2)

        idx_deadhead = out_layer.fields().indexFromName("route_is_deadhead")
        self.assertNotEqual(idx_deadhead, -1)
        deadhead_values = [feat.attribute(idx_deadhead) for feat in out_layer.getFeatures()]
        self.assertIn(True, deadhead_values)
        self.assertIn(False, deadhead_values)

        idx_load = out_layer.fields().indexFromName("route_load_kg")
        self.assertNotEqual(idx_load, -1)
        idx_dist = out_layer.fields().indexFromName("route_distance_km")
        self.assertNotEqual(idx_dist, -1)
        load_values = [feat.attribute(idx_load) for feat in out_layer.getFeatures()]
        self.assertTrue(all(v == 6.0 for v in load_values))
        dist_values = [feat.attribute(idx_dist) for feat in out_layer.getFeatures()]
        self.assertTrue(all(v > 0.0 for v in dist_values))


    def test_waste_fleet_sizing_algorithm_metadata(self):
        try:
            from logis.algorithms.waste_fleet_sizing import WasteFleetSizing
            alg = WasteFleetSizing()
            self.assertEqual(alg.name(), "waste_fleet_sizing")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteFleetSizing)
        except ImportError:
            pass

    @unittest.skipUnless(_HAS_QGIS, "requer bindings QGIS completos")
    def test_waste_fleet_sizing_assigns_vehicles(self):
        from logis.algorithms.waste_fleet_sizing import WasteFleetSizing

        layer = QgsVectorLayer("LineString?crs=EPSG:3857", "routes", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("route_id", QVariant.Int),
            QgsField("route_sector_id", QVariant.Int)
        ])
        layer.updateFields()

        # Rota 1: 30 km -> tempo = 30/10 + 0.5 + 0.5 = 4.0h
        # Rota 2: 30 km -> tempo = 4.0h
        # Rota 3: 30 km -> tempo = 4.0h
        # Jornada de 8h: 3 rotas de 4h exigem 2 veículos (FFD).
        def add_segment(route_id, sector_id, length_m):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(length_m, 0)]))
            feat.setAttributes([route_id, sector_id])
            provider.addFeature(feat)

        add_segment(1, 1, 30000.0)
        add_segment(2, 1, 30000.0)
        add_segment(3, 1, 30000.0)
        layer.updateExtents()

        alg = WasteFleetSizing()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        params = {
            alg.INPUT_ROUTES: layer,
            alg.FIELD_ROUTE_ID: "route_id",
            alg.FIELD_COLLECTION_SECTOR: "route_sector_id",
            alg.AVG_SPEED: 10.0,
            alg.SHIFT_DURATION: 8.0,
            alg.UNLOAD_TIME: 0.5,
            alg.TRAVEL_TIME: 0.5,
            alg.OUTPUT: "memory:out",
        }
        result = alg.processAlgorithm(params, context, feedback)
        out_layer = context.getMapLayer(result[alg.OUTPUT])

        self.assertEqual(out_layer.featureCount(), 1)
        feat = next(out_layer.getFeatures())
        idx_sector = out_layer.fields().indexFromName("sector_id")
        idx_fleet = out_layer.fields().indexFromName("fleet_size")
        idx_routes = out_layer.fields().indexFromName("num_routes")

        self.assertEqual(feat.attribute(idx_sector), 1)
        self.assertEqual(feat.attribute(idx_fleet), 2)
        self.assertEqual(feat.attribute(idx_routes), 3)

    def test_waste_deadhead_ratio_algorithm_metadata(self):
        try:
            from logis.algorithms.waste_deadhead_ratio import WasteDeadheadRatio
            alg = WasteDeadheadRatio()
            self.assertEqual(alg.name(), "waste_deadhead_ratio")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteDeadheadRatio)
        except ImportError:
            pass

    def test_waste_sector_balance_algorithm_metadata(self):
        try:
            from logis.algorithms.waste_sector_balance import WasteSectorBalance
            alg = WasteSectorBalance()
            self.assertEqual(alg.name(), "waste_sector_balance")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteSectorBalance)
        except ImportError:
            pass

    def test_waste_destination_distance_algorithm_metadata(self):
        try:
            from logis.algorithms.waste_destination_distance import WasteDestinationDistance
            alg = WasteDestinationDistance()
            self.assertEqual(alg.name(), "waste_destination_distance")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteDestinationDistance)
        except ImportError:
            pass

    def test_waste_collection_coverage_algorithm_metadata(self):
        try:
            from logis.algorithms.waste_collection_coverage import WasteCollectionCoverage
            alg = WasteCollectionCoverage()
            self.assertEqual(alg.name(), "waste_collection_coverage")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteCollectionCoverage)
        except ImportError:
            pass

    @unittest.skipUnless(_HAS_QGIS, "requer bindings QGIS completos")
    def test_waste_sector_balance_computes_stats_per_sector(self):
        # Um setor com duas rotas (100 kg / 10 km e 300 kg / 30 km, cada uma
        # com dois trechos repetindo o mesmo valor de rota, como o
        # waste_carp_route grava): confirma agrupamento por route_id,
        # deduplicação do valor repetido por rota e estatísticas de
        # carga/tempo calculadas à mão.
        from logis.algorithms.waste_sector_balance import WasteSectorBalance

        layer = QgsVectorLayer("LineString?crs=EPSG:3857", "routes", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("route_id", QVariant.Int),
            QgsField("route_sector_id", QVariant.Int),
            QgsField("route_load_kg", QVariant.Double),
            QgsField("route_distance_km", QVariant.Double),
        ])
        layer.updateFields()

        def add_feature(coords, route_id, sector_id, load_kg, distance_km):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(*c) for c in coords]))
            feat.setAttributes([route_id, sector_id, load_kg, distance_km])
            provider.addFeature(feat)

        add_feature([(0, 0), (1, 0)], 1, 1, 100.0, 10.0)
        add_feature([(1, 0), (2, 0)], 1, 1, 100.0, 10.0)
        add_feature([(0, 0), (0, 1)], 2, 1, 300.0, 30.0)
        add_feature([(0, 1), (0, 2)], 2, 1, 300.0, 30.0)
        layer.updateExtents()

        alg = WasteSectorBalance()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        params = {
            alg.INPUT_ROUTES: layer,
            alg.FIELD_LOAD: "route_load_kg",
            alg.FIELD_DISTANCE: "route_distance_km",
            alg.FIELD_ROUTE_ID: "route_id",
            alg.FIELD_COLLECTION_SECTOR: "route_sector_id",
            alg.AVG_SPEED: 10.0,
            alg.UNLOAD_TIME: 0.0,
            alg.TRAVEL_TIME: 0.0,
            alg.OUTPUT: "memory:out",
        }
        result = alg.processAlgorithm(params, context, feedback)
        out_layer = context.getMapLayer(result[alg.OUTPUT])

        out_feats = list(out_layer.getFeatures())
        self.assertEqual(len(out_feats), 1)
        feat = out_feats[0]

        idx = out_layer.fields().indexFromName
        self.assertEqual(feat.attribute(idx("num_routes")), 2)
        self.assertAlmostEqual(feat.attribute(idx("total_load_kg")), 400.0)
        self.assertAlmostEqual(feat.attribute(idx("mean_load_kg")), 200.0)
        self.assertAlmostEqual(feat.attribute(idx("min_load_kg")), 100.0)
        self.assertAlmostEqual(feat.attribute(idx("max_load_kg")), 300.0)
        self.assertAlmostEqual(feat.attribute(idx("std_dev_load_kg")), 100.0)
        self.assertAlmostEqual(feat.attribute(idx("cv_load")), 0.5)

        self.assertAlmostEqual(feat.attribute(idx("mean_time_h")), 2.0)
        self.assertAlmostEqual(feat.attribute(idx("std_dev_time_h")), 1.0)
        self.assertAlmostEqual(feat.attribute(idx("cv_time")), 0.5)

    @unittest.skipUnless(_HAS_QGIS, "requer bindings QGIS completos")
    def test_waste_deadhead_ratio_computes_ratios(self):
        from logis.algorithms.waste_deadhead_ratio import WasteDeadheadRatio

        layer = QgsVectorLayer("LineString?crs=EPSG:3857", "routes", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("route_id", QVariant.Int),
            QgsField("is_deadhead", QVariant.Bool)
        ])
        layer.updateFields()

        # Rota 1: 10 km produtivos, 5 km deadhead
        def add_segment(route_id, is_dh, length_m):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(length_m, 0)]))
            feat.setAttributes([route_id, is_dh])
            provider.addFeature(feat)

        add_segment(1, False, 10000.0)
        add_segment(1, True, 5000.0)
        layer.updateExtents()

        alg = WasteDeadheadRatio()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        params = {
            alg.INPUT_ROUTES: layer,
            alg.FIELD_DEADHEAD: "is_deadhead",
            alg.FIELD_ROUTE_ID: "route_id",
            alg.OUTPUT: "memory:out",
        }
        result = alg.processAlgorithm(params, context, feedback)
        out_layer = context.getMapLayer(result[alg.OUTPUT])

        self.assertEqual(out_layer.featureCount(), 1)
        feat = next(out_layer.getFeatures())
        idx_route = out_layer.fields().indexFromName("route_id")
        idx_prod = out_layer.fields().indexFromName("productive_km")
        idx_dh = out_layer.fields().indexFromName("deadhead_km")
        idx_ratio = out_layer.fields().indexFromName("deadhead_ratio")

        self.assertEqual(feat.attribute(idx_route), 1)
        self.assertAlmostEqual(feat.attribute(idx_prod), 10.0)
        self.assertAlmostEqual(feat.attribute(idx_dh), 5.0)
        self.assertAlmostEqual(feat.attribute(idx_ratio), 0.5)

    @unittest.skipUnless(_HAS_QGIS, "requer bindings QGIS completos")
    def test_waste_deadhead_ratio_adds_total_row_for_multiple_routes(self):
        from logis.algorithms.waste_deadhead_ratio import WasteDeadheadRatio

        layer = QgsVectorLayer("LineString?crs=EPSG:3857", "routes", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("route_id", QVariant.Int),
            QgsField("is_deadhead", QVariant.Bool)
        ])
        layer.updateFields()

        def add_segment(route_id, is_dh, length_m):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(length_m, 0)]))
            feat.setAttributes([route_id, is_dh])
            provider.addFeature(feat)

        # Rota 1: 10 km produtivos, 2 km deadhead. Rota 2: 8 km produtivos, 4 km deadhead.
        add_segment(1, False, 10000.0)
        add_segment(1, True, 2000.0)
        add_segment(2, False, 8000.0)
        add_segment(2, True, 4000.0)
        layer.updateExtents()

        alg = WasteDeadheadRatio()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        params = {
            alg.INPUT_ROUTES: layer,
            alg.FIELD_DEADHEAD: "is_deadhead",
            alg.FIELD_ROUTE_ID: "route_id",
            alg.OUTPUT: "memory:out",
        }
        result = alg.processAlgorithm(params, context, feedback)
        out_layer = context.getMapLayer(result[alg.OUTPUT])

        # 2 feições de rota + 1 feição de total agregado (route_id nulo).
        self.assertEqual(out_layer.featureCount(), 3)

        idx_route = out_layer.fields().indexFromName("route_id")
        idx_prod = out_layer.fields().indexFromName("productive_km")
        idx_dh = out_layer.fields().indexFromName("deadhead_km")

        total_feats = [
            feat for feat in out_layer.getFeatures()
            if feat.attribute(idx_route) == NULL
        ]
        self.assertEqual(len(total_feats), 1)
        total_feat = total_feats[0]
        self.assertAlmostEqual(total_feat.attribute(idx_prod), 18.0)
        self.assertAlmostEqual(total_feat.attribute(idx_dh), 6.0)

    def test_compute_route_balance_no_deviation_equal_routes(self):
        from logis.core.indicators.waste import compute_route_balance

        loads = [500.0, 500.0, 500.0]
        res = compute_route_balance(loads)

        self.assertEqual(res["num_routes"], 3)
        self.assertAlmostEqual(res["load"]["std_dev_kg"], 0.0)
        self.assertAlmostEqual(res["load"]["cv"], 0.0)
        for detail in res["route_details"]:
            self.assertAlmostEqual(detail["load_dev_kg"], 0.0)

    def test_compute_route_balance_known_deviation(self):
        from logis.core.indicators.waste import compute_route_balance

        loads = [100.0, 200.0, 300.0]
        res = compute_route_balance(loads)

        self.assertEqual(res["num_routes"], 3)
        self.assertAlmostEqual(res["load"]["total_kg"], 600.0)
        self.assertAlmostEqual(res["load"]["mean_kg"], 200.0)
        self.assertAlmostEqual(res["load"]["min_kg"], 100.0)
        self.assertAlmostEqual(res["load"]["max_kg"], 300.0)
        self.assertAlmostEqual(res["load"]["std_dev_kg"], (20000.0 / 3.0) ** 0.5)
        self.assertAlmostEqual(res["load"]["cv"], ((20000.0 / 3.0) ** 0.5) / 200.0)
        self.assertIsNone(res["time"])

        self.assertEqual(len(res["route_details"]), 3)
        self.assertAlmostEqual(res["route_details"][0]["load_dev_kg"], -100.0)
        self.assertAlmostEqual(res["route_details"][1]["load_dev_kg"], 0.0)
        self.assertAlmostEqual(res["route_details"][2]["load_dev_kg"], 100.0)

    def test_compute_route_balance_derived_time_deviation(self):
        from logis.core.indicators.waste import compute_route_balance

        loads = [500.0, 500.0]
        distances = [10.0, 20.0]
        res = compute_route_balance(
            route_loads_kg=loads,
            route_distances_km=distances,
            avg_collection_speed_kmh=10.0,
            unload_time_h=0.5,
            travel_time_to_destination_h=0.5
        )

        self.assertEqual(res["num_routes"], 2)
        self.assertIsNotNone(res["time"])
        self.assertAlmostEqual(res["time"]["total_h"], 5.0)
        self.assertAlmostEqual(res["time"]["mean_h"], 2.5)
        self.assertAlmostEqual(res["time"]["min_h"], 2.0)
        self.assertAlmostEqual(res["time"]["max_h"], 3.0)
        self.assertAlmostEqual(res["time"]["std_dev_h"], 0.5)
        self.assertAlmostEqual(res["time"]["cv"], 0.2)

        self.assertAlmostEqual(res["route_details"][0]["time_h"], 2.0)
        self.assertAlmostEqual(res["route_details"][0]["time_dev_h"], -0.5)
        self.assertAlmostEqual(res["route_details"][1]["time_h"], 3.0)
        self.assertAlmostEqual(res["route_details"][1]["time_dev_h"], 0.5)

    def test_compute_route_balance_single_route(self):
        from logis.core.indicators.waste import compute_route_balance

        loads = [250.0]
        res = compute_route_balance(loads)

        self.assertEqual(res["num_routes"], 1)
        self.assertAlmostEqual(res["load"]["total_kg"], 250.0)
        self.assertAlmostEqual(res["load"]["mean_kg"], 250.0)
        self.assertAlmostEqual(res["load"]["std_dev_kg"], 0.0)
        self.assertAlmostEqual(res["load"]["cv"], 0.0)
        self.assertEqual(len(res["route_details"]), 1)
        self.assertAlmostEqual(res["route_details"][0]["load_dev_kg"], 0.0)

    def test_compute_route_balance_incompatible_list_lengths(self):
        from logis.core.indicators.waste import compute_route_balance

        with self.assertRaises(ValueError):
            compute_route_balance([100.0], route_distances_km=[10.0, 20.0])

    def test_compute_route_balance_empty_input(self):
        from logis.core.indicators.waste import compute_route_balance

        with self.assertRaises(ValueError):
            compute_route_balance([])

    def test_compute_route_balance_invalid_inputs(self):
        from logis.core.indicators.waste import compute_route_balance

        with self.assertRaises(ValueError):
            compute_route_balance([100.0, -10.0])

        with self.assertRaises(ValueError):
            compute_route_balance([100.0], unload_time_h=-1.0)

        with self.assertRaises(ValueError):
            compute_route_balance([100.0], route_distances_km=[10.0])  # falta speed

        with self.assertRaises(ValueError):
            compute_route_balance([100.0], route_distances_km=[10.0], avg_collection_speed_kmh=0.0)

    def test_compute_collection_coverage_full_coverage(self):
        from logis.core.indicators.waste import compute_collection_coverage

        res = compute_collection_coverage([10.0], [10.0])
        self.assertAlmostEqual(res["total"]["required_km"], 10.0)
        self.assertAlmostEqual(res["total"]["covered_km"], 10.0)
        self.assertAlmostEqual(res["total"]["coverage_pct"], 1.0)
        self.assertIn(None, res["by_sector"])
        self.assertAlmostEqual(res["by_sector"][None]["coverage_pct"], 1.0)

    def test_compute_collection_coverage_partial_coverage(self):
        from logis.core.indicators.waste import compute_collection_coverage

        res = compute_collection_coverage([20.0], [15.0])
        self.assertAlmostEqual(res["total"]["required_km"], 20.0)
        self.assertAlmostEqual(res["total"]["covered_km"], 15.0)
        self.assertAlmostEqual(res["total"]["coverage_pct"], 0.75)
        self.assertAlmostEqual(res["by_sector"][None]["coverage_pct"], 0.75)

    def test_compute_collection_coverage_multiple_sectors(self):
        from logis.core.indicators.waste import compute_collection_coverage

        res = compute_collection_coverage(
            required_km=[10.0, 30.0],
            covered_km=[8.0, 15.0],
            sector_ids=[1, 2]
        )
        self.assertAlmostEqual(res["by_sector"][1]["required_km"], 10.0)
        self.assertAlmostEqual(res["by_sector"][1]["covered_km"], 8.0)
        self.assertAlmostEqual(res["by_sector"][1]["coverage_pct"], 0.8)

        self.assertAlmostEqual(res["by_sector"][2]["required_km"], 30.0)
        self.assertAlmostEqual(res["by_sector"][2]["covered_km"], 15.0)
        self.assertAlmostEqual(res["by_sector"][2]["coverage_pct"], 0.5)

        self.assertAlmostEqual(res["total"]["required_km"], 40.0)
        self.assertAlmostEqual(res["total"]["covered_km"], 23.0)
        self.assertAlmostEqual(res["total"]["coverage_pct"], 0.575)

    def test_compute_collection_coverage_zero_required(self):
        from logis.core.indicators.waste import compute_collection_coverage

        res = compute_collection_coverage([0.0], [0.0])
        self.assertAlmostEqual(res["total"]["required_km"], 0.0)
        self.assertAlmostEqual(res["total"]["covered_km"], 0.0)
        self.assertIsNone(res["total"]["coverage_pct"])
        self.assertIsNone(res["by_sector"][None]["coverage_pct"])

    def test_compute_collection_coverage_capped_above_100(self):
        from logis.core.indicators.waste import compute_collection_coverage

        res = compute_collection_coverage([10.0], [15.0])
        self.assertAlmostEqual(res["total"]["required_km"], 10.0)
        self.assertAlmostEqual(res["total"]["covered_km"], 15.0)
        self.assertAlmostEqual(res["total"]["coverage_pct"], 1.0)
        self.assertAlmostEqual(res["by_sector"][None]["coverage_pct"], 1.0)

    def test_compute_collection_coverage_incompatible_lengths(self):
        from logis.core.indicators.waste import compute_collection_coverage

        with self.assertRaises(ValueError):
            compute_collection_coverage([10.0, 20.0], [10.0])

        with self.assertRaises(ValueError):
            compute_collection_coverage([10.0], [10.0], sector_ids=[1, 2])

    def test_compute_collection_coverage_empty_input(self):
        from logis.core.indicators.waste import compute_collection_coverage

        with self.assertRaises(ValueError):
            compute_collection_coverage([], [])


if __name__ == "__main__":
    unittest.main()

