# -*- coding: utf-8 -*-
"""Piloto urbano ponta-a-ponta (F1): OSM -> grafo -> matriz OD.

Roda a fundação do módulo Urbano fora do QGIS Desktop (headless), encadeando
core.network.osm_pipeline -> core.network.graph_builder -> core.network.od_matrix
para um município pequeno de MG. Script de validação, não empacotado no plugin.

Município: Serra da Saudade/MG (code_muni 3166600) — o menor município de MG por
população, malha viária pequena o suficiente para um piloto rápido.

Uso:
    python3 docs/pilot_urbano_mg.py [caminho_gpkg_saida]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qgis.core import QgsApplication

CODE_MUNI = "3166600"
NOME_MUNI = "Serra da Saudade"


def main():
    qgs = QgsApplication([], False)
    qgs.initQgis()
    try:
        sys.path.insert(0, str(Path(QgsApplication.pkgDataPath()) / "python" / "plugins"))
        from processing.core.Processing import Processing
        Processing.initialize()

        from core.network.osm_pipeline import build_osm_municipal_network
        from core.network.graph_builder import build_graph
        from core.network.od_matrix import compute_od_matrix
        from core.downloader import cache_dir

        gpkg_path = sys.argv[1] if len(sys.argv) > 1 else str(
            cache_dir() / "pilot" / "pilot_urbano_{}.gpkg".format(CODE_MUNI)
        )
        Path(gpkg_path).parent.mkdir(parents=True, exist_ok=True)

        print("[1/3] Rede OSM para {}/MG (code_muni={})...".format(NOME_MUNI, CODE_MUNI))
        result = build_osm_municipal_network(CODE_MUNI, NOME_MUNI, gpkg_path)
        print("  metadata:", result["metadata"])
        links = result["layers"]["osm_links"]
        if links is None or links.featureCount() == 0:
            print("PILOTO FALHOU: sem camada de links viarios.")
            return 1

        print("[2/3] Construindo grafo ({} segmentos)...".format(links.featureCount()))
        graph = build_graph(links)["graph"]
        print("  grafo: {} vertices, {} arestas".format(graph.vertexCount(), graph.edgeCount()))
        if graph.vertexCount() < 2 or graph.edgeCount() == 0:
            print("PILOTO FALHOU: grafo vazio ou desconexo.")
            return 1

        n_dest = min(5, graph.vertexCount())
        print("[3/3] Matriz OD (Dijkstra) de 1 origem para {} destinos...".format(n_dest))
        matrix = compute_od_matrix(
            graph, origins=[0], destinations=list(range(n_dest)),
            criterion_num=1, cache_id="pilot_mg",
        )
        print("  tempos de viagem (s):", matrix[0])

        print("\nPILOTO OK - saida gravada em {}".format(gpkg_path))
        return 0
    finally:
        qgs.exitQgis()


if __name__ == "__main__":
    sys.exit(main())
