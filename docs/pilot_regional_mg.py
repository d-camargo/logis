# -*- coding: utf-8 -*-
"""Piloto regional ponta-a-ponta (F3): SNV -> grafo -> matriz OD.

Roda a fundação do módulo Regional fora do QGIS Desktop (headless), encadeando
core.network.snv_pipeline -> core.network.graph_builder -> core.network.od_matrix
para o estado de MG. Script de validação, não empacotado no plugin.

Estado: MG (Minas Gerais)

Uso:
    python3 docs/pilot_regional_mg.py [caminho_gpkg_saida]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qgis.core import QgsApplication

UF = "MG"


def main():
    qgs = QgsApplication([], False)
    qgs.initQgis()
    try:
        sys.path.insert(0, str(Path(QgsApplication.pkgDataPath()) / "python" / "plugins"))
        from processing.core.Processing import Processing
        Processing.initialize()

        from core.network.snv_pipeline import build_snv_state_network
        from core.network.graph_builder import build_graph
        from core.network.od_matrix import compute_od_matrix
        from core.downloader import cache_dir

        gpkg_path = sys.argv[1] if len(sys.argv) > 1 else str(
            cache_dir() / "pilot" / "pilot_regional_{}.gpkg".format(UF)
        )
        Path(gpkg_path).parent.mkdir(parents=True, exist_ok=True)

        print("[1/3] Rede SNV para {}...".format(UF))
        result = build_snv_state_network(UF, gpkg_path)
        print("  metadata:", result["metadata"])
        
        links = result["layers"].get("snv_links_{}".format(UF))
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
            criterion_num=1, cache_id="pilot_regional_{}".format(UF),
        )
        print("  tempos de viagem (s):", matrix[0])

        print("\nPILOTO OK - saida gravada em {}".format(gpkg_path))
        return 0
    finally:
        qgs.exitQgis()


if __name__ == "__main__":
    sys.exit(main())
