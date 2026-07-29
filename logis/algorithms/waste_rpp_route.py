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
Algoritmo de processamento para roteirização por arcos com subconjunto de vias obrigatórias
(Rural Postman Problem - RPP) na coleta de resíduos sólidos.
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
        build_eulerian_circuit,
        connect_required_components
    )
    from ..core import qgis_compat
except ImportError:
    from core.routing.arc_routing import (
        find_odd_degree_nodes,
        match_odd_degree_nodes,
        build_eulerian_circuit,
        connect_required_components
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


def _is_truthy(val):
    """Verifica se um valor indica via de coleta obrigatória."""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    val_str = str(val).strip().lower()
    return val_str in ("1", "true", "t", "yes", "y", "sim", "s")


class WasteRppRoute(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para roteirização de coleta por arcos com subconjunto
    de vias obrigatórias (Rural Postman Problem - RPP).

    Determina a sequência ótima de percurso para coleta em trechos de via obrigatórios
    (por setor de coleta ou na camada inteira), conectando os componentes do subgrafo
    obrigatório via MST sobre caminhos mínimos da rede total e adicionando travessias
    de deadhead para eulerianizar o grafo.

    Referência Bibliográfica da Técnica:
        - Frederickson, G. N. (1979). Approximation algorithms for some postman problems.
          Journal of the ACM, 26(3), 538-554.
        - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
          Mathematical Programming, 5(1), 88-124.
        - Hierholzer, C. (1873). Über die Möglichkeit, einen Linienzug ohne Wiederholung
          und ohne Unterbrechung zu umfahren. Mathematische Annalen, 6(1), 30-32.

    Limite de Complexidade:
        Complexidade de Tempo: O(C² log V) para conexão de componentes via MST +
        O(K² log V) para emparelhamento de nós ímpares + O(E) para circuito euleriano,
        onde C é o nº de componentes obrigatórios, K é o nº de nós ímpares, V é o nº de vértices
        e E é o nº de trechos de via. Testado com até ~5.000 trechos de via.
    """

    INPUT_STREETS = 'INPUT_STREETS'
    FIELD_REQUIRED = 'FIELD_REQUIRED'
    FIELD_COLLECTION_SECTOR = 'FIELD_COLLECTION_SECTOR'
    NODE_TOLERANCE = 'NODE_TOLERANCE'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteRppRoute", string)

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
                self.FIELD_REQUIRED,
                self.tr("Campo de via obrigatória para coleta (opcional)"),
                parentLayerParameterName=self.INPUT_STREETS,
                optional=True
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
                self.tr("Vias com rota de coleta (RPP)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        streets_source = self.parameterAsSource(parameters, self.INPUT_STREETS, context)
        required_field_name = self.parameterAsString(parameters, self.FIELD_REQUIRED, context)
        sector_field_name = self.parameterAsString(parameters, self.FIELD_COLLECTION_SECTOR, context)
        tolerance = self.parameterAsDouble(parameters, self.NODE_TOLERANCE, context)

        if streets_source is None:
            raise QgsProcessingException(self.tr("Camada de vias inválida."))

        required_field_idx = (
            streets_source.fields().indexFromName(required_field_name)
            if required_field_name
            else -1
        )
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

            if required_field_idx != -1:
                is_req = _is_truthy(feature.attribute(required_field_idx))
            else:
                is_req = True

            if sec_val not in sector_edges_map:
                sector_edges_map[sec_val] = []

            sector_edges_map[sec_val].append({
                "id": feature.id(),
                "from_node": from_node,
                "to_node": to_node,
                "length": geometry.length(),
                "required": is_req
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
        out_fields.append(QgsField("route_is_connector", qgis_compat.field_type("bool")))

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

            full_edges = edges
            req_edges = [e for e in full_edges if e["required"]]

            if not req_edges:
                feedback.pushWarning(
                    self.tr("Setor '{sec}': nenhum trecho de coleta obrigatória. Ignorando setor.").format(
                        sec=sec_val
                    )
                )
                completed_sectors += 1
                feedback.setProgress(int((completed_sectors / total_sectors) * 100))
                continue

            feedback.pushInfo(
                self.tr("Calculando rota RPP para o setor '{sec}' ({req_count} obrigatórios de {tot_count} trechos)...").format(
                    sec=sec_val, req_count=len(req_edges), tot_count=len(full_edges)
                )
            )

            try:
                # 1. Conecta componentes obrigatórios isolados
                connector_ids = connect_required_components(req_edges, full_edges)

                # Monta a base inicial do RPP com required + connectors
                req_id_set = {e["id"] for e in req_edges}
                original_req_ids = set(req_id_set)
                full_by_id = {e["id"]: e for e in full_edges}

                rpp_base_edges = list(req_edges)
                for cid in connector_ids:
                    if cid not in req_id_set:
                        rpp_base_edges.append(full_by_id[cid])
                        req_id_set.add(cid)

                # 2. Nós de grau ímpar sobre rpp_base_edges
                odd_nodes = find_odd_degree_nodes(rpp_base_edges)

                # 3. Matching sobre a rede completa
                matched_pairs = match_odd_degree_nodes(full_edges, odd_nodes) if odd_nodes else []
                dup_path_ids = [eid for _, _, path in matched_pairs for eid in path]

                # 4. Calcular multiplicidade total de cada edge no multigrafo
                multiplicity = {}
                for e in rpp_base_edges:
                    eid = e["id"]
                    multiplicity[eid] = multiplicity.get(eid, 0) + 1
                for eid in dup_path_ids:
                    multiplicity[eid] = multiplicity.get(eid, 0) + 1

                # 5. Montar circuit_base_edges (1 cópia cada) e circuit_dup_ids (resto)
                circuit_base_edges = [full_by_id[eid] for eid, mult in multiplicity.items() if mult >= 1]
                circuit_dup_ids = []
                for eid, mult in multiplicity.items():
                    if mult > 1:
                        circuit_dup_ids.extend([eid] * (mult - 1))

                circuit = build_eulerian_circuit(circuit_base_edges, circuit_dup_ids)
            except ValueError as exc:
                raise QgsProcessingException(
                    self.tr("Erro ao calcular rota RPP para o setor '{sec}': {err}").format(
                        sec=sec_val, err=str(exc)
                    )
                )

            req_m = sum(e["length"] for e in req_edges)
            tot_route_m = sum(full_by_id[eid]["length"] for eid in circuit)
            deadhead_m = tot_route_m - req_m
            deadhead_km = max(0.0, deadhead_m / 1000.0)

            feedback.pushInfo(
                self.tr("Setor '{sec}': RPP concluído com {steps} passo(s). {km:.2f} km de deadhead/deslocamento.").format(
                    sec=sec_val, steps=len(circuit), km=deadhead_km
                )
            )

            for visit_idx, edge_id in enumerate(circuit, start=1):
                if feedback.isCanceled():
                    return {}

                orig_feat = feature_map[edge_id]
                out_feat = QgsFeature(out_fields)
                out_feat.setGeometry(orig_feat.geometry())
                is_connector = edge_id not in original_req_ids
                out_feat.setAttributes(orig_feat.attributes() + [visit_idx, sec_val, is_connector])
                sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

            completed_sectors += 1
            feedback.setProgress(int((completed_sectors / total_sectors) * 100))

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_rpp_route"

    def displayName(self):
        return self.tr("Roteirização por Arcos (RPP)")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Calcula a sequência de percurso para coleta de lixo por arcos em um subconjunto de vias "
            "obrigatórias usando o Problema do Carteiro Rural (Rural Postman Problem - RPP).\n\n"
            "Parâmetros:\n"
            "- Camada de vias: feições de linha com a malha viária.\n"
            "- Campo de via obrigatória (opcional): campo booleano/inteiro indicando trechos de coleta obrigatória; "
            "se omitido, todas as vias são consideradas obrigatórias (equivalente ao CPP).\n"
            "- Campo de setor de coleta (opcional): se informado, o RPP é resolvido separadamente por setor.\n"
            "- Tolerância de nó: distância em metros para conectar vértices das vias.\n\n"
            "Retorno:\n"
            "- Camada de linha com feições duplicadas na sequência de travessia e três campos "
            "adicionais: 'route_visit_order' (posição sequencial no circuito), "
            "'route_sector_id' (setor de coleta) e 'route_is_connector' (booleano indicando via conetora)."
        )

    def createInstance(self):
        return WasteRppRoute()
