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
Algoritmo de processamento para localização de instalações via p-Mediana (Teitz-Bart).
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
from qgis.PyQt.QtCore import QVariant

try:
    from ..core.location.facility import solve_p_median
    from ..core.network.graph_builder import build_graph
    from ..core.network.od_matrix import compute_od_matrix
except ImportError:
    from core.location.facility import solve_p_median
    from core.network.graph_builder import build_graph
    from core.network.od_matrix import compute_od_matrix


def _extract_point(geom):
    """Retorna um QgsPointXY representando a geometria (ponto ou centroide de polígono)."""
    if geom.type() == QgsWkbTypes.PointGeometry:
        return geom.asPoint()
    else:
        return geom.centroid().asPoint()


class FacilityPMedian(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para resolver o problema de localização p-mediana
    utilizando a heurística Teitz-Bart (1-interchange local search).

    Minimiza o custo total ponderado de transporte entre os pontos de demanda e
    a instalação selecionada mais próxima.

    Referência Bibliográfica da Técnica:
        Teitz, M. B., & Bart, P. (1968). Heuristic methods for estimating the
        generalized vertex median of a weighted graph. Operations Research, 16(5), 955-961.

    Limite de Complexidade:
        Complexidade de Tempo: O(p * N * M + max_iter * p * (M - p) * N)
        Complexidade de Espaço: O(N * M)
        Testado com até 1.000 pontos de demanda e 500 candidatos.
    """

    INPUT_DEMAND = 'INPUT_DEMAND'
    FIELD_WEIGHT = 'FIELD_WEIGHT'
    INPUT_CANDIDATES = 'INPUT_CANDIDATES'
    INPUT_NETWORK = 'INPUT_NETWORK'
    P_FACILITIES = 'P_FACILITIES'
    MAX_ITER = 'MAX_ITER'
    OUTPUT_FACILITIES = 'OUTPUT_FACILITIES'
    OUTPUT_ASSIGNMENTS = 'OUTPUT_ASSIGNMENTS'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("FacilityPMedian", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_DEMAND,
                self.tr("Camada de demanda (Pontos/Polígonos)"),
                [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorPolygon]
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
                [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorPolygon],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de rede viária (Linhas) (opcional)"),
                [QgsProcessing.TypeVectorLine],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_FACILITIES,
                self.tr("Número de instalações (p)"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1,
                minValue=1
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ITER,
                self.tr("Número máximo de iterações do Teitz-Bart"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=100,
                minValue=1
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
                self.tr("Atribuição de demandas")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        demand_source = self.parameterAsSource(parameters, self.INPUT_DEMAND, context)
        weight_field_name = self.parameterAsString(parameters, self.FIELD_WEIGHT, context)
        candidates_source = self.parameterAsSource(parameters, self.INPUT_CANDIDATES, context)
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        p = self.parameterAsInt(parameters, self.P_FACILITIES, context)
        max_iter = self.parameterAsInt(parameters, self.MAX_ITER, context)

        if demand_source is None:
            raise QgsProcessingException(self.tr("Camada de demanda inválida."))

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
                if val is not None and not QVariant(val).isNull():
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

        if p > len(candidate_points):
            raise QgsProcessingException(
                self.tr("O número de instalações p ({p}) excede o número de candidatos ({cand}).").format(
                    p=p, cand=len(candidate_points)
                )
            )

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

        # 5) Resolução da p-mediana
        feedback.pushInfo(self.tr("Executando a otimização p-Mediana (Teitz-Bart)..."))
        try:
            selected_indices, total_cost, assignments = solve_p_median(
                cost_matrix=cost_matrix,
                demand_weights=demand_weights,
                p=p,
                max_iter=max_iter
            )
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("Localização concluída. Instalações selecionadas: {sel} | Custo Total: {cost:.2f}").format(
                sel=selected_indices, cost=total_cost
            )
        )

        # 6) Gravação dos resultados de saída
        assigned_counts = {c: 0 for c in selected_indices}
        assigned_demands = {c: 0.0 for c in selected_indices}
        assigned_costs = {c: 0.0 for c in selected_indices}

        for i, cand_idx in enumerate(assignments):
            w = demand_weights[i]
            cost = cost_matrix[i][cand_idx]
            assigned_counts[cand_idx] += 1
            assigned_demands[cand_idx] += w
            assigned_costs[cand_idx] += w * cost

        fac_source = candidates_source if candidates_source is not None else demand_source
        fac_fields = fac_source.fields()
        fac_fields.append(QgsField("facility_id", QVariant.Int))
        fac_fields.append(QgsField("assigned_count", QVariant.Int))
        fac_fields.append(QgsField("assigned_demand_sum", QVariant.Double))
        fac_fields.append(QgsField("total_weighted_cost", QVariant.Double))

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
                    assigned_demands[cand_idx],
                    assigned_costs[cand_idx]
                ])
                new_feat.setAttributes(attrs)
                sink_fac.addFeature(new_feat, QgsFeatureSink.FastInsert)

        ass_fields = demand_source.fields()
        ass_fields.append(QgsField("assigned_facility_id", QVariant.Int))
        ass_fields.append(QgsField("cost_to_facility", QVariant.Double))
        ass_fields.append(QgsField("weighted_cost", QVariant.Double))

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
                cand_idx = assignments[i]
                cost = cost_matrix[i][cand_idx]
                w_cost = demand_weights[i] * cost
                new_feat = QgsFeature(feat)
                attrs = feat.attributes()
                attrs.extend([cand_idx, cost, w_cost])
                new_feat.setAttributes(attrs)
                sink_ass.addFeature(new_feat, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT_FACILITIES: dest_fac,
            self.OUTPUT_ASSIGNMENTS: dest_ass
        }

    def name(self):
        return "facility_p_median"

    def displayName(self):
        return self.tr("Localização p-Mediana (Teitz-Bart)")

    def group(self):
        return self.tr("Localização de Instalações")

    def groupId(self):
        return "location"

    def shortHelpString(self):
        return self.tr(
            "Resolve o problema de localização p-mediana selecionando p instalações candidatas "
            "que minimizem a soma total das distâncias/custos ponderadas da demanda até a instalação mais próxima.\n\n"
            "Parâmetros:\n"
            "- Camada de demanda: feições de pontos ou polígonos representando a demanda.\n"
            "- Campo de peso da demanda: campo numérico indicando a demanda de cada feição (opcional, default=1.0).\n"
            "- Camada de instalações candidatas: instalações elegíveis (opcional, usa a camada de demanda se omitida).\n"
            "- Camada de rede viária: rede viária para distâncias reais na rede (opcional, usa distância euclidiana se omitida).\n"
            "- Número de instalações (p): quantidade de instalações a selecionar.\n"
            "- Número máximo de iterações: limite de trocas locais no algoritmo Teitz-Bart.\n\n"
            "Saídas:\n"
            "- Instalações selecionadas: camada de candidatos escolhidos com totais de demanda e custo.\n"
            "- Atribuição de demandas: camada de demanda com o ID da instalação atribuída e o custo de atendimento."
        )
