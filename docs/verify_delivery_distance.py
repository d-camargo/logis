# -*- coding: utf-8 -*-
"""Script de verificação headless do algoritmo logis:urban_delivery_distance.

Carrega a rede piloto gerada pelo F1, cria camadas em memória de depósitos
e zonas a partir dos nós da rede, executa o algoritmo Processing registrado
e valida que os resultados de distância e tempo são gravados corretamente.
"""
import sys
from pathlib import Path

# Adiciona o diretório contendo a pasta logis (para importações absolutas) e a pasta docs ao path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root.parent))
sys.path.insert(0, str(project_root / "docs"))

from qgis.core import QgsApplication

CODE_MUNI = "3166600"
NOME_MUNI = "Serra da Saudade"

def main():
    # Inicializa QGIS de forma headless
    qgs = QgsApplication([], False)
    qgs.initQgis()
    try:
        # Inicializa o framework Processing
        sys.path.insert(0, str(Path(QgsApplication.pkgDataPath()) / "python" / "plugins"))
        from processing.core.Processing import Processing
        Processing.initialize()

        from qgis.core import QgsVectorLayer, QgsFeature
        import processing
        from logis.provider import LogisProvider
        from logis.core.downloader import cache_dir

        # Registrar o provider do Logis no processamento
        provider = LogisProvider()
        QgsApplication.processingRegistry().addProvider(provider)

        # Caminho do GPKG piloto
        gpkg_path = str(cache_dir() / "pilot" / "pilot_urbano_{}.gpkg".format(CODE_MUNI))
        if not Path(gpkg_path).exists():
            print("GPKG piloto não encontrado em {}. Rodando pilot_urbano_mg.py primeiro...".format(gpkg_path))
            from pilot_urbano_mg import main as run_pilot
            run_pilot()

        print("[1/4] Carregando camadas do GPKG piloto...")
        network_layer = QgsVectorLayer("{}|layername=osm_links_{}".format(gpkg_path, CODE_MUNI), "Rede", "ogr")
        nodes_layer = QgsVectorLayer("{}|layername=osm_nodes_{}".format(gpkg_path, CODE_MUNI), "Nós", "ogr")

        if not network_layer.isValid() or not nodes_layer.isValid():
            print("ERRO: Falha ao carregar camadas piloto do GPKG.")
            return 1

        print("  Rede viária: {} segmentos".format(network_layer.featureCount()))
        print("  Nós da rede: {} nós".format(nodes_layer.featureCount()))

        # Criar depósitos e zonas em memória a partir dos nós
        print("[2/4] Preparando dados de teste (depósitos e zonas em memória)...")
        features = list(nodes_layer.getFeatures())
        if len(features) < 10:
            print("ERRO: Menos de 10 nós na rede para o teste.")
            return 1

        # Depósito no nó 0
        depot_layer = QgsVectorLayer("Point?crs=EPSG:4674", "Depósito", "memory")
        depot_dp = depot_layer.dataProvider()
        f_depot = QgsFeature()
        f_depot.setGeometry(features[0].geometry())
        depot_dp.addFeatures([f_depot])

        # Zonas nos nós 1 a 6 (5 zonas de demanda)
        zones_layer = QgsVectorLayer("Point?crs=EPSG:4674", "Zonas", "memory")
        zones_dp = zones_layer.dataProvider()
        zones_dp.addAttributes(nodes_layer.fields())
        zones_layer.updateFields()

        zone_feats = []
        for i in range(1, 6):
            fz = QgsFeature(zones_layer.fields())
            fz.setGeometry(features[i].geometry())
            fz.setAttributes(features[i].attributes())
            zone_feats.append(fz)
        zones_dp.addFeatures(zone_feats)

        print("  Depósitos criados: {} ponto(s)".format(depot_layer.featureCount()))
        print("  Zonas de entrega criadas: {} pontos".format(zones_layer.featureCount()))

        # Executar no modo Distância (CRITERION = 0)
        print("[3/4] Executando logis:urban_delivery_distance (Critério: Distância)...")
        params_dist = {
            'INPUT_NETWORK': network_layer,
            'INPUT_DEPOTS': depot_layer,
            'INPUT_ZONES': zones_layer,
            'CRITERION': 0, # Distância
            'OUTPUT': 'memory:output_dist'
        }
        res_dist = processing.run("logis:urban_delivery_distance", params_dist)
        out_dist_layer = res_dist['OUTPUT']

        print("  Saída gerada: {} feições".format(out_dist_layer.featureCount()))
        dist_values = []
        for feat in out_dist_layer.getFeatures():
            val = feat['dist_entrega']
            dist_values.append(val)
            print("    Zona ID {}: dist_entrega (m) = {:.2f}".format(feat.id(), val))

        # Executar no modo Tempo de viagem (CRITERION = 1)
        print("[4/4] Executando logis:urban_delivery_distance (Critério: Tempo de viagem)...")
        params_time = {
            'INPUT_NETWORK': network_layer,
            'INPUT_DEPOTS': depot_layer,
            'INPUT_ZONES': zones_layer,
            'CRITERION': 1, # Tempo de viagem
            'OUTPUT': 'memory:output_time'
        }
        res_time = processing.run("logis:urban_delivery_distance", params_time)
        out_time_layer = res_time['OUTPUT']

        time_values = []
        for feat in out_time_layer.getFeatures():
            val = feat['dist_entrega']
            time_values.append(val)
            print("    Zona ID {}: tempo_entrega (s) = {:.2f}".format(feat.id(), val))

        # Verificações básicas de corretude
        assert len(dist_values) == 5, "Deveria ter exatamente 5 valores de saída"
        assert len(time_values) == 5, "Deveria ter exatamente 5 valores de saída"
        assert all(d > 0.0 for d in dist_values), "Todas as distâncias deveriam ser maiores que zero"
        assert all(t > 0.0 for t in time_values), "Todos os tempos de viagem deveriam ser maiores que zero"
        assert dist_values != time_values, "Os valores de distância e tempo de viagem não deveriam ser idênticos"

        print("\nVERIFICAÇÃO OK - Algoritmo executou e validou com sucesso headlessly!")
        return 0
    except Exception as e:
        print("\nVERIFICAÇÃO FALHOU com exceção:")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        qgs.exitQgis()

if __name__ == "__main__":
    sys.exit(main())
