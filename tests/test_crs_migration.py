# -*- coding: utf-8 -*-
"""Regressão com QGIS real para a migração da leitura de SRC (read_points_in_crs).

Roda logis:facility_p_median (sem rede) e logis:urban_delivery_distance (com uma rede
mínima) via processing.run(), com entradas em EPSG:4326 ao redor de São Paulo, e confere:
  - a saída mantém o SRC da entrada;
  - o custo calculado está em metros, na ordem de grandeza plausível para pontos a
    ~0,01 grau de distância (entre 900 m e 1200 m);
  - um ponto (500, 500) na demanda levanta QgsProcessingException citando o id da feição,
    em vez de sumir com um resultado silenciosamente com um ponto a menos.
"""
import sys
import unittest
from pathlib import Path

try:
    from qgis.core import (
        QgsApplication,
        QgsFeature,
        QgsGeometry,
        QgsPointXY,
        QgsProcessingException,
        QgsVectorLayer,
    )

    _qgs = QgsApplication.instance()
    if not _qgs:
        _qgs = QgsApplication([], False)
        _qgs.initQgis()
    _HAS_QGIS = True
except ImportError:
    _HAS_QGIS = False

# Registra o provider "logis" no Processing, para poder chamar processing.run("logis:...")
# como um usuário real faria (pela caixa de ferramentas ou pelo console). Guardado em
# try/except: se o ambiente não tiver o framework Processing completo, os testes abaixo
# são pulados via _HAS_PROCESSING_REGISTRY, no mesmo espírito do padrão _HAS_QGIS do resto
# da suíte.
_HAS_PROCESSING_REGISTRY = False
processing = None
# Referência global obrigatória: QgsProcessingRegistry.addProvider() transfere a posse do
# objeto para o C++, mas se o wrapper Python for coletado pelo GC (sem uma referência viva
# em algum lugar), o despacho virtual para os métodos Python (id()/name()/loadAlgorithms())
# passa a cair no padrão da classe base (id()/name() voltam vazios e a lista de algoritmos
# não é encontrada por processing.run()).
_logis_provider_instance = None
if _HAS_QGIS:
    try:
        sys.path.insert(0, str(Path(QgsApplication.pkgDataPath()) / "python" / "plugins"))
        from processing.core.Processing import Processing

        Processing.initialize()
        import processing

        from logis.provider import LogisProvider

        if not any(p.id() == "logis" for p in QgsApplication.processingRegistry().providers()):
            _logis_provider_instance = LogisProvider()
            QgsApplication.processingRegistry().addProvider(_logis_provider_instance)
        _HAS_PROCESSING_REGISTRY = True
    except Exception:
        _HAS_PROCESSING_REGISTRY = False


def _point_layer(coords, crs="EPSG:4326"):
    layer = QgsVectorLayer(f"Point?crs={crs}", "test", "memory")
    dp = layer.dataProvider()
    feats = []
    for lon, lat in coords:
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        feats.append(f)
    dp.addFeatures(feats)
    layer.updateExtents()
    return layer


def _line_layer(coords, crs="EPSG:4326"):
    layer = QgsVectorLayer(f"LineString?crs={crs}", "test", "memory")
    dp = layer.dataProvider()
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(lon, lat) for lon, lat in coords]))
    dp.addFeatures([f])
    layer.updateExtents()
    return layer


@unittest.skipUnless(
    _HAS_PROCESSING_REGISTRY, "requer QGIS + Processing com o provider logis registrado"
)
class TestCrsMigrationRegression(unittest.TestCase):
    """Regressão ponta a ponta (QGIS real, via processing.run) para read_points_in_crs."""

    # ~0,01 grau de longitude/latitude nessa latitude equivalem a ~1,0-1,1 km.
    DEMAND_COORDS = [(-46.63, -23.55), (-46.62, -23.55), (-46.63, -23.54)]

    def test_facility_p_median_sem_rede_preserva_src_e_custo_em_metros(self):
        """Caso A: facility_p_median sem rede, EPSG:4326 ao redor de São Paulo."""
        demand_layer = _point_layer(self.DEMAND_COORDS)

        result = processing.run(
            "logis:facility_p_median",
            {
                "INPUT_DEMAND": demand_layer,
                "P_FACILITIES": 1,
                "MAX_ITER": 100,
                "OUTPUT_FACILITIES": "memory:fac",
                "OUTPUT_ASSIGNMENTS": "memory:ass",
            },
        )
        ass_layer = result["OUTPUT_ASSIGNMENTS"]

        self.assertEqual(ass_layer.sourceCrs().authid(), demand_layer.sourceCrs().authid())

        idx_cost = ass_layer.fields().indexFromName("cost_to_facility")
        costs = [feat.attribute(idx_cost) for feat in ass_layer.getFeatures()]
        # Uma feição é a própria instalação selecionada (custo 0.0); as outras duas
        # formam pares a ~0,01 grau com ela.
        non_zero_costs = [c for c in costs if c > 0.0]
        self.assertEqual(len(non_zero_costs), 2)
        for cost in non_zero_costs:
            self.assertGreaterEqual(cost, 900.0)
            self.assertLessEqual(cost, 1200.0)

    def test_urban_delivery_distance_com_rede_minima_preserva_src_e_custo_em_metros(self):
        """Caso B: urban_delivery_distance com uma rede mínima, EPSG:4326 ao redor de São Paulo."""
        network_layer = _line_layer([(-46.63, -23.55), (-46.62, -23.55)])
        depot_layer = _point_layer([(-46.63, -23.55)])
        zone_layer = _point_layer([(-46.62, -23.55)])

        result = processing.run(
            "logis:urban_delivery_distance",
            {
                "INPUT_NETWORK": network_layer,
                "INPUT_DEPOTS": depot_layer,
                "INPUT_ZONES": zone_layer,
                "CRITERION": 0,
                "OUTPUT": "memory:out",
            },
        )
        out_layer = result["OUTPUT"]

        self.assertEqual(out_layer.sourceCrs().authid(), zone_layer.sourceCrs().authid())

        idx_dist = out_layer.fields().indexFromName("dist_entrega")
        dists = [feat.attribute(idx_dist) for feat in out_layer.getFeatures()]
        self.assertEqual(len(dists), 1)
        self.assertGreaterEqual(dists[0], 900.0)
        self.assertLessEqual(dists[0], 1200.0)

    def test_facility_p_median_ponto_500_500_levanta_excecao_citando_feature_id(self):
        """Caso C: ponto (500, 500) na demanda -> QgsProcessingException citando "feature id",
        e não um resultado silencioso com um ponto a menos."""
        bad_demand_layer = _point_layer(self.DEMAND_COORDS + [(500.0, 500.0)])

        with self.assertRaises(QgsProcessingException) as ctx:
            processing.run(
                "logis:facility_p_median",
                {
                    "INPUT_DEMAND": bad_demand_layer,
                    "P_FACILITIES": 1,
                    "MAX_ITER": 100,
                    "OUTPUT_FACILITIES": "memory:fac",
                    "OUTPUT_ASSIGNMENTS": "memory:ass",
                },
            )

        self.assertIn("feature id", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
