# -*- coding: utf-8 -*-
import os
import unittest

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


class TestVrpCvrpAlgorithm(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(__file__)
        self.alg_path = os.path.join(self.base_dir, "logis", "algorithms", "vrp_cvrp.py")

        with open(self.alg_path, "r", encoding="utf-8") as f:
            self.alg_source = f.read()

    def test_vrp_cvrp_parameters_and_backend(self):
        # parameter definitions
        self.assertIn("BACKEND = 'BACKEND'", self.alg_source)
        self.assertIn("QgsProcessingParameterEnum", self.alg_source)
        self.assertIn("Automático (OR-Tools quando disponível)", self.alg_source)
        self.assertIn("Python puro (heurística)", self.alg_source)
        self.assertIn("OR-Tools", self.alg_source)
        self.assertIn("parameterAsEnum", self.alg_source)

        # pass to solve_cvrp
        self.assertIn("backend=req_backend", self.alg_source)

        # backend layer field
        self.assertIn('route_fields.append(QgsField("backend", qgis_compat.field_type("string")))', self.alg_source)

    def test_vrp_cvrp_crashlog_trace(self):
        self.assertIn("crashlog", self.alg_source)
        for stage in (
            "cvrp-inicio",
            "cvrp-transform",
            "cvrp-build-graph",
            "cvrp-grafo-pronto",
            "cvrp-od-matrix",
            "cvrp-ortools-import",
            "cvrp-solver-ok",
            "cvrp-sinks",
            "cvrp-fim",
        ):
            self.assertIn(f'crashlog.mark("{stage}"', self.alg_source)

    def test_vrp_cvrp_progress_phases_and_extent(self):
        self.assertIn("PhaseProgress", self.alg_source)
        self.assertIn("feedback.setProgressText", self.alg_source)
        self.assertIn("Lendo pontos de demanda", self.alg_source)
        self.assertIn("Construindo o grafo", self.alg_source)
        self.assertIn("Calculando a matriz OD", self.alg_source)
        self.assertIn("Otimizando (OR-Tools)", self.alg_source)
        self.assertIn("Otimizando (heurística Python)", self.alg_source)
        self.assertIn("Gravando as saídas", self.alg_source)

        # Repasse de feedback= sub-faixa para build_graph, compute_od_matrix e solve_cvrp
        self.assertIn("feedback=p_build", self.alg_source)
        self.assertIn("feedback=p_od", self.alg_source)
        self.assertIn("feedback=p_opt", self.alg_source)

        # Repasse de extent= em build_graph
        self.assertIn("extent=extent", self.alg_source)
        self.assertIn("QgsRectangle", self.alg_source)

    def test_vrp_cvrp_metric_crs_check(self):
        # (passo 6 do plano) Garantir CRS métrico no cálculo: mapUnits() comparado com EPSG:5880
        self.assertIn('demand_crs.mapUnits() == QgsCoordinateReferenceSystem("EPSG:5880").mapUnits()', self.alg_source)
        self.assertNotIn("source_crs.isGeographic()", self.alg_source)
        self.assertNotIn("demand_crs.isGeographic()", self.alg_source)

    def test_vrp_cvrp_crs_check_static(self):
        # (passo 4 do plano) CVRP chama classify_input_crs, context.transformContext() e loga "SRC de"
        self.assertIn("classify_input_crs", self.alg_source)
        self.assertIn("context.transformContext()", self.alg_source)
        self.assertIn('"SRC de', self.alg_source)
        self.assertIn("_resolve_source_crs", self.alg_source)


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
class TestVrpCvrpRealQgisRegression(unittest.TestCase):
    """
    Teste de regressão com QGIS real para VrpCvrp:
    - Rede em EPSG:4674 em torno de (-46.63, -23.55).
    - Pontos de depósito e demanda em graus com SRC inválido (layer.setCrs(QgsCoordinateReferenceSystem()))
      -> as rotas são calculadas, a janela de análise logada está em metros (|x| > 1e5) e o log contém o aviso de EPSG:4674 assumido.
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
        from logis.algorithms.vrp_cvrp import VrpCvrp

        depot_layer = QgsVectorLayer("Point?crs=EPSG:4674", "depot", "memory")
        f_depot = QgsFeature()
        f_depot.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.63, -23.55)))
        depot_layer.dataProvider().addFeature(f_depot)
        depot_layer.updateExtents()

        demand_layer = QgsVectorLayer("Point?crs=EPSG:4674", "demand", "memory")
        for pt in [QgsPointXY(-46.631, -23.551), QgsPointXY(-46.629, -23.549)]:
            f_pt = QgsFeature()
            f_pt.setGeometry(QgsGeometry.fromPointXY(pt))
            demand_layer.dataProvider().addFeature(f_pt)
        demand_layer.updateExtents()

        # 2. Pontos com SRC inválido
        depot_layer.setCrs(QgsCoordinateReferenceSystem())
        demand_layer.setCrs(QgsCoordinateReferenceSystem())

        alg = VrpCvrp()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        fb = LogFeedback()

        params = {
            "INPUT_DEPOT": depot_layer,
            "INPUT_DEMAND": demand_layer,
            "INPUT_NETWORK": self.net_layer,
            "BACKEND": 1,  # Python
            "OUTPUT_ROUTES": "memory:",
            "OUTPUT_STOPS": "memory:",
        }

        res = alg.processAlgorithm(params, context, fb)
        self.assertIn("OUTPUT_ROUTES", res)

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
        depot_layer_5880 = QgsVectorLayer("Point?crs=EPSG:5880", "depot_5880", "memory")
        depot_layer_5880.dataProvider().addFeature(f_depot)
        depot_layer_5880.updateExtents()

        demand_layer_5880 = QgsVectorLayer("Point?crs=EPSG:5880", "demand_5880", "memory")
        for pt in [QgsPointXY(-46.631, -23.551), QgsPointXY(-46.629, -23.549)]:
            f_pt = QgsFeature()
            f_pt.setGeometry(QgsGeometry.fromPointXY(pt))
            demand_layer_5880.dataProvider().addFeature(f_pt)
        demand_layer_5880.updateExtents()

        params_5880 = {
            "INPUT_DEPOT": depot_layer_5880,
            "INPUT_DEMAND": demand_layer_5880,
            "INPUT_NETWORK": self.net_layer,
            "BACKEND": 1,
            "OUTPUT_ROUTES": "memory:",
            "OUTPUT_STOPS": "memory:",
        }

        with self.assertRaises(QgsProcessingException) as ctx:
            alg.processAlgorithm(params_5880, context, fb)
        self.assertIn("EPSG:5880", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
