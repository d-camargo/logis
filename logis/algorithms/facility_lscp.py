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
Algoritmo de processamento para localização de instalações via Cobertura de Conjuntos (LSCP).
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsField,
    QgsFeature,
    QgsFeatureSink,
    QgsWkbTypes
)
try:
    from ..core import qgis_compat
    from ..core.location.facility import solve_lscp
    from ..core.network.graph_builder import build_graph
    from ..core.network.od_matrix import compute_od_matrix
except ImportError:
    from core import qgis_compat
    from core.location.facility import solve_lscp
    from core.network.graph_builder import build_graph
    from core.network.od_matrix import compute_od_matrix


def _extract_point(geom):
    """Retorna um QgsPointXY representando a geometria (ponto ou centroide de polígono)."""
    if geom.type() == QgsWkbTypes.GeometryType.PointGeometry:
        return geom.asPoint()
    else:
        return geom.centroid().asPoint()


class FacilityLSCP(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para resolver o problema de localização de cobertura de conjuntos (LSCP)
    utilizando a heurística de Toregas et al. (1971).

    Encontra o número mínimo de instalações necessárias para cobrir todos os pontos de demanda
    dentro de uma distância/tempo máximo especificado (max_distance).

    Referência Bibliográfica da Técnica:
        Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). The location of
        emergency service facilities. Operations Research, 19(6), 1363-1373.

    Limite de Complexidade:
        Complexidade de Tempo: O(M * N * min(M, N)) onde N é demanda e M candidatos.
        Complexidade de Espaço: O(N * M)
        Testado com até 1.000 pontos de demanda e 500 candidatos.
    """

    INPUT_DEMAND = 'INPUT_DEMAND'
    FIELD_WEIGHT = 'FIELD_WEIGHT'
    INPUT_CANDIDATES = 'INPUT_CANDIDATES'
    INPUT_NETWORK = 'INPUT_NETWORK'
    MAX_DISTANCE = 'MAX_DISTANCE'
    OUTPUT_FACILITIES = 'OUTPUT_FACILITIES'
    OUTPUT_ASSIGNMENTS = 'OUTPUT_ASSIGNMENTS'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("FacilityLSCP", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_DEMAND,
                self.tr("Camada de demanda (Pontos/Polígonos)"),
                [QgsProcessing.SourceType.TypeVectorPoint, QgsProcessing.SourceType.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_WEIGHT,
                self.tr("Campo de peso da demanda (opcional, default=1.0)"),
                type=QgsProcessingParameterField.Numeric,
                parentLayerParameterName=self.INPUT_DEMAND,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_CANDIDATES,
                self.tr("Camada de instalações candidatas (Pontos/Polígonos) (opcional)"),
                [QgsProcessing.SourceType.TypeVectorPoint, QgsProcessing.SourceType.TypeVectorPolygon],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de rede viária (Linhas) (opcional)"),
                [QgsProcessing.SourceType.TypeVectorLine],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_DISTANCE,
                self.tr("Distância/Tempo máximo de cobertura (max_distance)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=1000.0,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_FACILITIES,
                self.tr("Instalações selecionadas")
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_ASSIGNMENTS,
                self.tr("Atribuição e cobertura de demandas")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        demand_source = self.parameterAsSource(parameters, self.INPUT_DEMAND, context)
        weight_field_name = self.parameterAsString(parameters, self.FIELD_WEIGHT, context)
        candidates_source = self.parameterAsSource(parameters, self.INPUT_CANDIDATES, context)
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        max_distance = self.parameterAsDouble(parameters, self.MAX_DISTANCE, context)

        if demand_source is None:
            raise QgsProcessingException(self.tr("Camada de demanda inválida."))

        if max_distance <= 0:
            raise QgsProcessingException(self.tr("A distância máxima deve ser estritamente maior que zero."))

        # 1) Definição do CRS de cálculo
        if network_layer and network_layer.isValid():
            target_crs = QgsCoordinateReferenceSystem("EPSG:5880")
        else:
            source_crs = demand_source.sourceCrs()
            if source_crs.isGeographic():
                target_crs = QgsCoordinateReferenceSystem("EPSG:5880")
            else:
                target_crs = source_crs

        transform_demand = QgsCoordinateTransform(demand_source.sourceCrs(), target_crs, QgsProject.instance())

        # 2) Leitura das demandas, pontos e pesos
        weight_field_idx = demand_source.fields().indexOf(weight_field_name) if weight_field_name else -1

        demand_features = []
        demand_points = []
        demand_weights = []

        feedback.pushInfo(self.tr("Lendo pontos de demanda..."))
        for feat in demand_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            pt_transformed = transform_demand.transform(_extract_point(geom))

            weight = 1.0
            if weight_field_idx != -1:
                val = feat.attribute(weight_field_idx)
                if not qgis_compat.is_null(val):
                    try:
                        weight = float(val)
                    except (ValueError, TypeError):
                        weight = 1.0
            if weight < 0:
                weight = 0.0

            demand_features.append(feat)
            demand_points.append(pt_transformed)
            demand_weights.append(weight)

        if not demand_points:
            raise QgsProcessingException(self.tr("Nenhum ponto de demanda válido encontrado."))

        # 3) Leitura dos candidatos a instalação
        if candidates_source is not None:
            transform_cand = QgsCoordinateTransform(candidates_source.sourceCrs(), target_crs, QgsProject.instance())
            candidate_features = []
            candidate_points = []
            feedback.pushInfo(self.tr("Lendo instalações candidatas..."))
            for feat in candidates_source.getFeatures():
                if feedback.isCanceled():
                    return {}
                geom = feat.geometry()
                if geom is None or geom.isEmpty():
                    continue
                pt_transformed = transform_cand.transform(_extract_point(geom))

                candidate_features.append(feat)
                candidate_points.append(pt_transformed)
        else:
            candidate_features = demand_features
            candidate_points = demand_points

        if not candidate_points:
            raise QgsProcessingException(self.tr("Nenhuma instalação candidata válida encontrada."))

        # 4) Cálculo da matriz de custos/distâncias
        num_demands = len(demand_points)
        num_candidates = len(candidate_points)

        if network_layer and network_layer.isValid():
            feedback.pushInfo(self.tr("Construindo o grafo e calculando a matriz OD na rede..."))
            tie_points = demand_points + candidate_points
            try:
                res = build_graph(network_layer, target_crs=target_crs, points=tie_points)
            except Exception as exc:
                raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))

            graph = res["graph"]
            snapped_points = res["snapped_points"]

            if graph is None or graph.vertexCount() < 2:
                raise QgsProcessingException(self.tr("O grafo construído possui menos de 2 vértices."))

            snapped_demands = snapped_points[:num_demands]
            snapped_candidates = snapped_points[num_demands:]

            demand_vertices = [graph.findVertex(pt) for pt in snapped_demands]
            candidate_vertices = [graph.findVertex(pt) for pt in snapped_candidates]

            try:
                cost_matrix = compute_od_matrix(
                    graph=graph,
                    origins=demand_vertices,
                    destinations=candidate_vertices,
                    criterion_num=0,
                    feedback=feedback
                )
            except Exception as exc:
                raise QgsProcessingException(self.tr("Erro ao calcular a matriz OD: {}").format(str(exc)))
        else:
            feedback.pushInfo(self.tr("Calculando matriz de distâncias euclidianas..."))
            cost_matrix = []
            for i, dp in enumerate(demand_points):
                if feedback.isCanceled():
                    return {}
                row = [dp.distance(cp) for cp in candidate_points]
                cost_matrix.append(row)

        # 5) Resolução da Cobertura de Conjuntos (LSCP)
        feedback.pushInfo(self.tr("Executando a otimização LSCP (Toregas et al.)..."))
        try:
            selected_indices, is_fully_covered, uncovered_indices = solve_lscp(
                cost_matrix=cost_matrix,
                max_distance=max_distance,
                demand_weights=demand_weights
            )
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("LSCP concluído. Instalações: {sel} | Totalmente Coberto: {cov} | Não cobertos: {unc}").format(
                sel=selected_indices, cov=is_fully_covered, unc=len(uncovered_indices)
            )
        )

        # 6) Gravação dos resultados de saída
        assigned_counts = {c: 0 for c in selected_indices}
        assigned_demands = {c: 0.0 for c in selected_indices}

        assigned_facility = []
        cost_to_facility = []

        uncovered_set = set(uncovered_indices)

        for i in range(num_demands):
            if i not in uncovered_set:
                covering_facs = [f for f in selected_indices if cost_matrix[i][f] <= max_distance]
                if covering_facs:
                    closest_f = min(covering_facs, key=lambda f: cost_matrix[i][f])
                else:
                    closest_f = min(selected_indices, key=lambda f: cost_matrix[i][f]) if selected_indices else -1

                if closest_f != -1:
                    c_dist = cost_matrix[i][closest_f]
                    assigned_facility.append(closest_f)
                    cost_to_facility.append(c_dist)

                    assigned_counts[closest_f] += 1
                    assigned_demands[closest_f] += demand_weights[i]
                else:
                    assigned_facility.append(-1)
                    cost_to_facility.append(-1.0)
            else:
                assigned_facility.append(-1)
                cost_to_facility.append(-1.0)

        fac_source = candidates_source if candidates_source is not None else demand_source
        fac_fields = fac_source.fields()
        fac_fields.append(QgsField("facility_id", qgis_compat.field_type("int")))
        fac_fields.append(QgsField("covered_count", qgis_compat.field_type("int")))
        fac_fields.append(QgsField("covered_demand_sum", qgis_compat.field_type("double")))

        (sink_fac, dest_fac) = self.parameterAsSink(
            parameters,
            self.OUTPUT_FACILITIES,
            context,
            fac_fields,
            fac_source.wkbType(),
            fac_source.sourceCrs()
        )

        if sink_fac is not None:
            for cand_idx in selected_indices:
                feat = candidate_features[cand_idx]
                new_feat = QgsFeature(feat)
                attrs = feat.attributes()
                attrs.extend([
                    cand_idx,
                    assigned_counts[cand_idx],
                    assigned_demands[cand_idx]
                ])
                new_feat.setAttributes(attrs)
                sink_fac.addFeature(new_feat, QgsFeatureSink.FastInsert)

        ass_fields = demand_source.fields()
        ass_fields.append(QgsField("is_covered", qgis_compat.field_type("int")))
        ass_fields.append(QgsField("assigned_facility_id", qgis_compat.field_type("int")))
        ass_fields.append(QgsField("cost_to_facility", qgis_compat.field_type("double")))
        ass_fields.append(QgsField("weighted_cost", qgis_compat.field_type("double")))

        (sink_ass, dest_ass) = self.parameterAsSink(
            parameters,
            self.OUTPUT_ASSIGNMENTS,
            context,
            ass_fields,
            demand_source.wkbType(),
            demand_source.sourceCrs()
        )

        if sink_ass is not None:
            for i, feat in enumerate(demand_features):
                is_cov = 1 if i not in uncovered_set else 0
                cand_idx = assigned_facility[i]
                cost = cost_to_facility[i]
                w_cost = demand_weights[i] * cost if is_cov and cost >= 0 else 0.0
                new_feat = QgsFeature(feat)
                attrs = feat.attributes()
                attrs.extend([is_cov, cand_idx, cost, w_cost])
                new_feat.setAttributes(attrs)
                sink_ass.addFeature(new_feat, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT_FACILITIES: dest_fac,
            self.OUTPUT_ASSIGNMENTS: dest_ass
        }

    def name(self):
        return "facility_lscp"

    def displayName(self):
        return self.tr("Localização de Cobertura de Conjuntos (LSCP)")

    def group(self):
        return self.tr("Localização de Instalações")

    def groupId(self):
        return "location"

    def shortHelpString(self):
        return self.tr(
            "Resolve o problema de localização de cobertura de conjuntos (LSCP) utilizando a heurística "
            "gulosa de Toregas et al. (1971).\n\n"
            "Seleciona o menor número possível de instalações para cobrir todos os pontos de demanda "
            "dentro da distância/tempo máximo especificado (max_distance).\n\n"
            "Parâmetros:\n"
            "- Camada de demanda: feições de pontos ou polígonos representando a demanda.\n"
            "- Campo de peso da demanda: campo numérico indicando a demanda de cada feição (opcional, default=1.0).\n"
            "- Camada de instalações candidatas: instalações elegíveis (opcional, usa a camada de demanda se omitida).\n"
            "- Camada de rede viária: rede viária para distâncias reais na rede (opcional, usa distância euclidiana se omitida).\n"
            "- Distância/Tempo máximo de cobertura: raio ou tempo limite para considerar uma demanda coberta.\n\n"
            "Saídas:\n"
            "- Instalações selecionadas: camada de candidatos escolhidos com total de demanda e pontos cobertos.\n"
            "- Atribuição e cobertura de demandas: camada de demanda com o status de cobertura (is_covered) e a instalação atribuída."
        )
