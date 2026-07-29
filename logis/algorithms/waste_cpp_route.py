# -*- coding: utf-8 -*-
"""
/***************************************************************************
 logis
                                 A QGIS plugin
 Complemento do QGIS para apoiar projetos de logística no Brasil
                                -------------------
        begin                : 2026-07-20
        copyright            : (C) 2026 by Diego Camargo
        license              : GPL-3.0
 ***************************************************************************/
"""
"""
Algoritmo de processamento para roteirização por arcos (Chinese Postman Problem - CPP)
na coleta de resíduos sólidos.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsField,
    QgsFeature,
    QgsFeatureSink
)

try:
    from ..core.routing.arc_routing import (
        find_odd_degree_nodes,
        match_odd_degree_nodes,
        build_eulerian_circuit
    )
    from ..core import qgis_compat
except ImportError:
    from core.routing.arc_routing import (
        find_odd_degree_nodes,
        match_odd_degree_nodes,
        build_eulerian_circuit
    )
    from core import qgis_compat


def _edge_endpoints(geometry):
    """Retorna os pontos (x, y) do primeiro e do último vértice da geometria de linha."""
    if geometry.isMultipart():
        parts = geometry.asMultiPolyline()
        vertices = parts[0] if parts else []
    else:
        vertices = geometry.asPolyline()

    if len(vertices) < 2:
        return None, None

    return vertices[0], vertices[-1]


class WasteCppRoute(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para roteirização de coleta por arcos (Chinese Postman Problem - CPP).

    Determina a sequência ótima de percurso para coleta em trechos de via (por setor de coleta
    ou na camada inteira) duplicando a menor extensão de trechos necessária para tornar o grafo
    euleriano e construindo um circuito euleriano completo.

    Referência Bibliográfica da Técnica:
        - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
          Mathematical Programming, 5(1), 88-124.
        - Hierholzer, C. (1873). Über die Möglichkeit, einen Linienzug ohne Wiederholung
          und ohne Unterbrechung zu umfahren. Mathematische Annalen, 6(1), 30-32.

    Limite de Complexidade:
        Complexidade de Tempo: O(E log V) para emparelhamento de nós ímpares + O(E) para
        construção do circuito euleriano de Hierholzer, onde E é o número de trechos de via
        e V é o número de interseções. Testado com até ~5.000 trechos de via.
    """

    INPUT_STREETS = 'INPUT_STREETS'
    FIELD_COLLECTION_SECTOR = 'FIELD_COLLECTION_SECTOR'
    NODE_TOLERANCE = 'NODE_TOLERANCE'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteCppRoute", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_STREETS,
                self.tr("Camada de vias"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_COLLECTION_SECTOR,
                self.tr("Campo de setor de coleta (opcional)"),
                parentLayerParameterName=self.INPUT_STREETS,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_TOLERANCE,
                self.tr("Tolerância de nó em metros (requer CRS métrico)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.01,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Vias com rota de coleta (CPP)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        streets_source = self.parameterAsSource(parameters, self.INPUT_STREETS, context)
        sector_field_name = self.parameterAsString(parameters, self.FIELD_COLLECTION_SECTOR, context)
        tolerance = self.parameterAsDouble(parameters, self.NODE_TOLERANCE, context)

        if streets_source is None:
            raise QgsProcessingException(self.tr("Camada de vias inválida."))

        sector_field_idx = (
            streets_source.fields().indexFromName(sector_field_name)
            if sector_field_name
            else -1
        )

        feedback.pushInfo(self.tr("Lendo trechos de via e agrupando por setor..."))

        sector_edges_map = {}
        feature_map = {}
        skipped_fids = []

        for feature in streets_source.getFeatures():
            if feedback.isCanceled():
                return {}

            feature_map[feature.id()] = feature
            geometry = feature.geometry()
            if geometry is None or geometry.isEmpty():
                skipped_fids.append(feature.id())
                continue

            start_pt, end_pt = _edge_endpoints(geometry)
            if start_pt is None:
                skipped_fids.append(feature.id())
                continue

            from_node = (
                round(start_pt.x() / tolerance),
                round(start_pt.y() / tolerance)
            )
            to_node = (
                round(end_pt.x() / tolerance),
                round(end_pt.y() / tolerance)
            )

            if sector_field_idx != -1:
                sec_val = feature.attribute(sector_field_idx)
                if sec_val is None:
                    sec_val = 0
            else:
                sec_val = 0

            if sec_val not in sector_edges_map:
                sector_edges_map[sec_val] = []

            sector_edges_map[sec_val].append({
                "id": feature.id(),
                "from_node": from_node,
                "to_node": to_node,
                "length": geometry.length()
            })

        if skipped_fids:
            feedback.pushWarning(
                self.tr("{count} trecho(s) com geometria inválida foram ignorados.").format(
                    count=len(skipped_fids)
                )
            )

        if not sector_edges_map:
            raise QgsProcessingException(
                self.tr("Nenhum trecho de via válido encontrado na camada de entrada.")
            )

        out_fields = streets_source.fields()
        out_fields.append(QgsField("route_visit_order", qgis_compat.field_type("int")))
        if sector_field_idx != -1:
            sec_type = streets_source.fields().at(sector_field_idx).type()
            out_fields.append(QgsField("route_sector_id", sec_type))
        else:
            out_fields.append(QgsField("route_sector_id", qgis_compat.field_type("int")))
        out_fields.append(QgsField("route_is_deadhead", qgis_compat.field_type("bool")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            streets_source.wkbType(), streets_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        total_sectors = len(sector_edges_map)
        completed_sectors = 0

        for sec_val, edges in sector_edges_map.items():
            if feedback.isCanceled():
                return {}

            feedback.pushInfo(
                self.tr("Calculando rota CPP para o setor '{sec}' com {count} trecho(s)...").format(
                    sec=sec_val, count=len(edges)
                )
            )

            try:
                odd_nodes = find_odd_degree_nodes(edges)
                matched_pairs = match_odd_degree_nodes(edges, odd_nodes) if odd_nodes else []
                dup_ids = [eid for _, _, path in matched_pairs for eid in path]
                circuit = build_eulerian_circuit(edges, dup_ids)
            except ValueError as exc:
                raise QgsProcessingException(
                    self.tr("Erro ao calcular rota CPP para o setor '{sec}': {err}").format(
                        sec=sec_val, err=str(exc)
                    )
                )

            edge_by_id = {e["id"]: e for e in edges}
            deadhead_m = sum(edge_by_id[eid]["length"] for eid in dup_ids)
            deadhead_km = deadhead_m / 1000.0

            feedback.pushInfo(
                self.tr("Setor '{sec}': {dup} trecho(s) duplicado(s) (deadhead), {km:.2f} km improdutivos.").format(
                    sec=sec_val, dup=len(dup_ids), km=deadhead_km
                )
            )

            seen_in_sector = set()
            for visit_idx, edge_id in enumerate(circuit, start=1):
                if feedback.isCanceled():
                    return {}

                is_deadhead = edge_id in seen_in_sector
                seen_in_sector.add(edge_id)

                orig_feat = feature_map[edge_id]
                out_feat = QgsFeature(out_fields)
                out_feat.setGeometry(orig_feat.geometry())
                out_feat.setAttributes(orig_feat.attributes() + [visit_idx, sec_val, is_deadhead])
                sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

            completed_sectors += 1
            feedback.setProgress(int((completed_sectors / total_sectors) * 100))

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_cpp_route"

    def displayName(self):
        return self.tr("Roteirização por Arcos (CPP)")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Calcula a sequência de percurso para coleta de lixo por arcos usando o "
            "Problema do Carteiro Chinês (Chinese Postman Problem - CPP).\n\n"
            "Parâmetros:\n"
            "- Camada de vias: feições de linha a serem percorridas.\n"
            "- Campo de setor de coleta (opcional): se informado, o CPP é resolvido "
            "separadamente para cada setor de coleta; se omitido, toda a camada é "
            "tratada como um único setor.\n"
            "- Tolerância de nó: distância em metros para conectar vértices das vias.\n\n"
            "Retorno:\n"
            "- Camada de linha com feições duplicadas nos trechos de deadhead e campos "
            "adicionais: 'route_visit_order' (posição sequencial no circuito), "
            "'route_sector_id' (setor de coleta) e 'route_is_deadhead' (booleano indicando passagem duplicada/deadhead)."
        )

    def createInstance(self):
        return WasteCppRoute()
