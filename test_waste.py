# -*- coding: utf-8 -*-
import unittest
from core.indicators.waste import (
    sector_waste_generation,
    allocate_generation_by_street_length
)

try:
    from qgis.core import (
        QgsApplication, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
        QgsField, QgsProcessingContext, QgsProcessingFeedback
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

    def test_waste_cpp_route_algorithm_metadata(self):
        try:
            from algorithms.waste_cpp_route import WasteCppRoute
            alg = WasteCppRoute()
            self.assertEqual(alg.name(), "waste_cpp_route")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteCppRoute)
        except ImportError:
            # Em ambiente sem QGIS C++ bindings completos, ignora instanciação
            pass

    def test_waste_rpp_route_algorithm_metadata(self):
        try:
            from algorithms.waste_rpp_route import WasteRppRoute
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
        from algorithms.waste_rpp_route import WasteRppRoute

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
            from algorithms.waste_carp_route import WasteCarpRoute
            alg = WasteCarpRoute()
            self.assertEqual(alg.name(), "waste_carp_route")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteCarpRoute)
        except ImportError:
            pass

    @unittest.skipUnless(_HAS_QGIS, "requer bindings QGIS completos")
    def test_waste_carp_route_splits_by_capacity(self):
        # Depósito na origem, dois trechos obrigatórios de 6 kg cada e capacidade
        # de 10 kg: a soma (12 kg) excede a capacidade de uma única viagem, então
        # o algorithm deve gerar exatamente 2 rotas.
        from algorithms.waste_carp_route import WasteCarpRoute

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


if __name__ == "__main__":
    unittest.main()

