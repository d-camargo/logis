# -*- coding: utf-8 -*-
"""Script de verificação headless da migração para read_points_in_crs (passo 4 do plano).

Roda logis:facility_p_median (sem rede) e logis:urban_delivery_distance (com uma rede
mínima) chamando processAlgorithm() diretamente (mesmo padrão usado nos testes reais de
QGIS do repositório, ver test_waste.py), com entradas em EPSG:4326 ao redor de São Paulo,
e confere:
  - a saída mantém o SRC da entrada (EPSG:4326);
  - o custo calculado está em metros, em ordem de grandeza plausível para pontos a ~0,01°
    de distância (algo entre ~500 m e ~3000 m);
  - um ponto (500, 500) na camada de demanda levanta QgsProcessingException (e não um
    resultado silenciosamente com um ponto a menos).

Nota: não usa processing.run()/registry porque logis:facility_p_median (e os demais
facility_*) não implementam createInstance(), então createAlgorithmById() falha com
"QgsProcessingAlgorithm.createInstance() is abstract" — débito pré-existente, fora do
escopo deste plano (que trata só da leitura de SRC).
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from qgis.core import QgsApplication


def main():
    qgs = QgsApplication([], False)
    qgs.initQgis()
    try:
        sys.path.insert(0, str(Path(QgsApplication.pkgDataPath()) / "python" / "plugins"))
        from processing.core.Processing import Processing
        Processing.initialize()

        from qgis.core import (
            QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
            QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException
        )
        from logis.algorithms.facility_p_median import FacilityPMedian
        from logis.algorithms.urban_delivery_distance import UrbanDeliveryDistance

        ok = True

        # ------------------------------------------------------------------
        # Caso A: facility_p_median, sem rede, EPSG:4326 ao redor de São Paulo.
        # ------------------------------------------------------------------
        print("[A] facility_p_median sem rede, EPSG:4326...")
        demand_layer = QgsVectorLayer("Point?crs=EPSG:4326", "demand", "memory")
        demand_dp = demand_layer.dataProvider()
        demand_coords = [(-46.63, -23.55), (-46.62, -23.55), (-46.63, -23.54)]
        demand_feats = []
        for lon, lat in demand_coords:
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            demand_feats.append(f)
        demand_dp.addFeatures(demand_feats)
        demand_layer.updateExtents()

        alg_a = FacilityPMedian()
        alg_a.initAlgorithm()
        context_a = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        params_a = {
            alg_a.INPUT_DEMAND: demand_layer,
            alg_a.P_FACILITIES: 1,
            alg_a.MAX_ITER: 100,
            alg_a.OUTPUT_FACILITIES: "memory:fac_a",
            alg_a.OUTPUT_ASSIGNMENTS: "memory:ass_a",
        }
        result_a = alg_a.processAlgorithm(params_a, context_a, feedback)
        ass_layer_a = context_a.getMapLayer(result_a[alg_a.OUTPUT_ASSIGNMENTS])

        crs_in = demand_layer.sourceCrs().authid()
        crs_out = ass_layer_a.sourceCrs().authid()
        print(f"  SRC entrada={crs_in} SRC saída={crs_out}")
        if crs_out != crs_in:
            print("  FALHA: SRC de saída diferente do SRC de entrada.")
            ok = False

        idx_cost = ass_layer_a.fields().indexFromName("cost_to_facility")
        costs_a = [feat.attribute(idx_cost) for feat in ass_layer_a.getFeatures()]
        print(f"  custos (m): {costs_a}")
        # Pontos a 0.01 grau de distância nessa latitude ~ 1.0-1.1 km; folga generosa.
        if not all(0.0 <= c <= 3000.0 for c in costs_a):
            print("  FALHA: custo fora da ordem de grandeza plausível (0-3000 m).")
            ok = False

        # ------------------------------------------------------------------
        # Caso B: urban_delivery_distance, com uma rede mínima (linha reta),
        # EPSG:4326 ao redor de São Paulo.
        # ------------------------------------------------------------------
        print("[B] urban_delivery_distance com rede mínima, EPSG:4326...")
        network_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "network", "memory")
        network_dp = network_layer.dataProvider()
        f_line = QgsFeature()
        f_line.setGeometry(QgsGeometry.fromPolylineXY([
            QgsPointXY(-46.63, -23.55), QgsPointXY(-46.62, -23.55)
        ]))
        network_dp.addFeatures([f_line])
        network_layer.updateExtents()

        depot_layer = QgsVectorLayer("Point?crs=EPSG:4326", "depot", "memory")
        depot_dp = depot_layer.dataProvider()
        f_depot = QgsFeature()
        f_depot.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.63, -23.55)))
        depot_dp.addFeatures([f_depot])
        depot_layer.updateExtents()

        zone_layer = QgsVectorLayer("Point?crs=EPSG:4326", "zone", "memory")
        zone_dp = zone_layer.dataProvider()
        f_zone = QgsFeature()
        f_zone.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-46.62, -23.55)))
        zone_dp.addFeatures([f_zone])
        zone_layer.updateExtents()

        alg_b = UrbanDeliveryDistance()
        alg_b.initAlgorithm()
        context_b = QgsProcessingContext()
        params_b = {
            alg_b.INPUT_NETWORK: network_layer,
            alg_b.INPUT_DEPOTS: depot_layer,
            alg_b.INPUT_ZONES: zone_layer,
            alg_b.CRITERION: 0,
            alg_b.OUTPUT: "memory:out_b",
        }
        result_b = alg_b.processAlgorithm(params_b, context_b, feedback)
        out_layer_b = context_b.getMapLayer(result_b[alg_b.OUTPUT])

        crs_in_b = zone_layer.sourceCrs().authid()
        crs_out_b = out_layer_b.sourceCrs().authid()
        print(f"  SRC entrada={crs_in_b} SRC saída={crs_out_b}")
        if crs_out_b != crs_in_b:
            print("  FALHA: SRC de saída diferente do SRC de entrada.")
            ok = False

        idx_dist = out_layer_b.fields().indexFromName("dist_entrega")
        dists_b = [feat.attribute(idx_dist) for feat in out_layer_b.getFeatures()]
        print(f"  custos (m): {dists_b}")
        if not all(500.0 <= d <= 3000.0 for d in dists_b):
            print("  FALHA: custo fora da ordem de grandeza plausível (500-3000 m).")
            ok = False

        # ------------------------------------------------------------------
        # Caso C: ponto (500, 500) na demanda -> QgsProcessingException, não um
        # resultado silencioso com um ponto a menos.
        # ------------------------------------------------------------------
        print("[C] facility_p_median com ponto (500, 500) na demanda...")
        bad_demand_layer = QgsVectorLayer("Point?crs=EPSG:4326", "bad_demand", "memory")
        bad_dp = bad_demand_layer.dataProvider()
        bad_feats = []
        for lon, lat in demand_coords + [(500.0, 500.0)]:
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            bad_feats.append(f)
        bad_dp.addFeatures(bad_feats)
        bad_demand_layer.updateExtents()

        alg_c = FacilityPMedian()
        alg_c.initAlgorithm()
        context_c = QgsProcessingContext()
        params_c = {
            alg_c.INPUT_DEMAND: bad_demand_layer,
            alg_c.P_FACILITIES: 1,
            alg_c.MAX_ITER: 100,
            alg_c.OUTPUT_FACILITIES: "memory:fac_c",
            alg_c.OUTPUT_ASSIGNMENTS: "memory:ass_c",
        }
        try:
            alg_c.processAlgorithm(params_c, context_c, feedback)
            print("  FALHA: não levantou QgsProcessingException para o ponto (500, 500).")
            ok = False
        except QgsProcessingException as exc:
            print(f"  OK: QgsProcessingException levantada: {exc}")

        if ok:
            print("\nVERIFICAÇÃO OK - migração para read_points_in_crs validada headlessly!")
            return 0
        else:
            print("\nVERIFICAÇÃO FALHOU - ver mensagens acima.")
            return 1
    except Exception:
        print("\nVERIFICAÇÃO FALHOU com exceção:")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        qgs.exitQgis()


if __name__ == "__main__":
    sys.exit(main())
