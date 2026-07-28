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
Algoritmo de processamento para Roteirização de Veículos Capacitados (CVRP).
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsFeatureSink,
    QgsWkbTypes,
    QgsGeometry
)
from qgis.PyQt.QtCore import QVariant

try:
    from ..core.routing.vrp import solve_cvrp, compute_route_distance
    from ..core.network.graph_builder import build_graph
    from ..core.network.od_matrix import compute_od_matrix
except ImportError:
    from core.routing.vrp import solve_cvrp, compute_route_distance
    from core.network.graph_builder import build_graph
    from core.network.od_matrix import compute_od_matrix


def _extract_point(geom):
    """Retorna um QgsPointXY representando a geometria (ponto ou centroide de polígono)."""
    if geom.type() == QgsWkbTypes.PointGeometry:
        return geom.asPoint()
    else:
        return geom.centroid().asPoint()


class VrpCvrp(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para resolver o Problema de Roteirização de Veículos Capacitados (CVRP).

    Utiliza o algoritmo de economias de Clarke & Wright (1964) para construção de rotas iniciais,
    combinado com as heurísticas de busca local 2-opt (Lin, 1965) e Or-opt (Or, 1976) para otimização.

    Referência Bibliográfica da Técnica:
        - Clarke, G., & Wright, J. W. (1964). Scheduling of vehicles from a central depot
          to a number of delivery points. Operations Research, 12(4), 568-581.
        - Lin, S. (1965). Computer solutions of the traveling salesman problem.
          Bell System Technical Journal, 44(10), 2245-2269.
        - Or, I. (1976). Traveling salesman-type combinatorial problems and their
          relation to the logistics of regional blood banking. PhD thesis, Northwestern University.

    Limite de Complexidade:
        Complexidade de Tempo: O(N^2 log N) para Clarke-Wright + O(R * k^2) para busca local 2-opt/Or-opt,
        onde N é o número de pontos, R é o número de rotas e k é o tamanho da maior rota.
        Complexidade de Espaço: O(N^2) para matriz de distâncias/economias.
        Testado com até 1.000 pontos de demanda.
    """

    INPUT_DEPOT = 'INPUT_DEPOT'
    INPUT_DEMAND = 'INPUT_DEMAND'
    FIELD_DEMAND = 'FIELD_DEMAND'
    CAPACITY = 'CAPACITY'
    INPUT_NETWORK = 'INPUT_NETWORK'
    IMPROVE = 'IMPROVE'
    OUTPUT_ROUTES = 'OUTPUT_ROUTES'
    OUTPUT_STOPS = 'OUTPUT_STOPS'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("VrpCvrp", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_DEPOT,
                self.tr("Camada de depósito (Pontos/Polígonos)"),
                [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_DEMAND,
                self.tr("Camada de demanda / clientes (Pontos/Polígonos)"),
                [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_DEMAND,
                self.tr("Campo de peso/demanda (opcional, default=1.0)"),
                type=QgsProcessingParameterField.Numeric,
                parentLayerParameterName=self.INPUT_DEMAND,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.CAPACITY,
                self.tr("Capacidade do veículo"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=100.0,
                minValue=0.0001
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
            QgsProcessingParameterBoolean(
                self.IMPROVE,
                self.tr("Aplicar busca local (2-opt e Or-opt)"),
                defaultValue=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_ROUTES,
                self.tr("Rotas geradas")
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_STOPS,
                self.tr("Paradas por rota (opcional)"),
                optional=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        depot_source = self.parameterAsSource(parameters, self.INPUT_DEPOT, context)
        demand_source = self.parameterAsSource(parameters, self.INPUT_DEMAND, context)
        demand_field_name = self.parameterAsString(parameters, self.FIELD_DEMAND, context)
        capacity = self.parameterAsDouble(parameters, self.CAPACITY, context)
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        improve = self.parameterAsBool(parameters, self.IMPROVE, context)

        if depot_source is None:
            raise QgsProcessingException(self.tr("Camada de depósito inválida."))
        if demand_source is None:
            raise QgsProcessingException(self.tr("Camada de demanda inválida."))
        if capacity <= 0:
            raise QgsProcessingException(self.tr("A capacidade do veículo deve ser estritamente maior que zero."))

        # 1) CRS de cálculo
        if network_layer and network_layer.isValid():
            target_crs = QgsCoordinateReferenceSystem("EPSG:5880")
        else:
            source_crs = demand_source.sourceCrs()
            if source_crs.isGeographic():
                target_crs = QgsCoordinateReferenceSystem("EPSG:5880")
            else:
                target_crs = source_crs

        transform_depot = QgsCoordinateTransform(depot_source.sourceCrs(), target_crs, QgsProject.instance())
        transform_demand = QgsCoordinateTransform(demand_source.sourceCrs(), target_crs, QgsProject.instance())

        # 2) Leitura do depósito (primeira feição válida)
        depot_pt = None
        for feat in depot_source.getFeatures():
            geom = feat.geometry()
            if geom and not geom.isEmpty():
                depot_pt = transform_depot.transform(_extract_point(geom))
                break

        if depot_pt is None:
            raise QgsProcessingException(self.tr("Nenhum ponto de depósito válido encontrado."))

        # 3) Leitura das demandas, pontos e pesos
        demand_field_idx = demand_source.fields().indexOf(demand_field_name) if demand_field_name else -1

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
            if demand_field_idx != -1:
                val = feat.attribute(demand_field_idx)
                if val is not None and not QVariant(val).isNull():
                    try:
                        weight = float(val)
                    except (ValueError, TypeError):
                        weight = 1.0
            if weight < 0:
                weight = 0.0

            if weight > capacity:
                raise QgsProcessingException(
                    self.tr("A demanda do nó excede a capacidade máxima do veículo ({weight} > {cap}).").format(
                        weight=weight, cap=capacity
                    )
                )

            demand_features.append(feat)
            demand_points.append(pt_transformed)
            demand_weights.append(weight)

        if not demand_points:
            raise QgsProcessingException(self.tr("Nenhum ponto de demanda válido encontrado."))

        # 4) Matriz de distâncias (Nó 0 = depósito, Nôs 1..N = demandas)
        all_points = [depot_pt] + demand_points
        all_demands = [0.0] + demand_weights

        if network_layer and network_layer.isValid():
            feedback.pushInfo(self.tr("Construindo o grafo e calculando a matriz OD na rede..."))
            try:
                res = build_graph(network_layer, target_crs=target_crs, points=all_points)
            except Exception as exc:
                raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))

            graph = res["graph"]
            snapped_points = res["snapped_points"]

            if graph is None or graph.vertexCount() < 2:
                raise QgsProcessingException(self.tr("O grafo construído possui menos de 2 vértices."))

            vertices = [graph.findVertex(pt) for pt in snapped_points]

            try:
                cost_matrix = compute_od_matrix(
                    graph=graph,
                    origins=vertices,
                    destinations=vertices,
                    criterion_num=0,
                    feedback=feedback
                )
            except Exception as exc:
                raise QgsProcessingException(self.tr("Erro ao calcular a matriz OD: {}").format(str(exc)))
        else:
            feedback.pushInfo(self.tr("Calculando matriz de distâncias euclidianas..."))
            cost_matrix = []
            for i, p1 in enumerate(all_points):
                if feedback.isCanceled():
                    return {}
                row = [p1.distance(p2) for p2 in all_points]
                cost_matrix.append(row)

        # 5) Resolução do CVRP
        feedback.pushInfo(self.tr("Executando a otimização CVRP (Clarke-Wright + 2-opt/Or-opt)..."))
        try:
            routes, total_distance, route_loads = solve_cvrp(
                distance_matrix=cost_matrix,
                demands=all_demands,
                capacity=capacity,
                depot=0,
                improve=improve
            )
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("Roteirização concluída. Rotas geradas: {count} | Distância Total: {dist:.2f}").format(
                count=len(routes), dist=total_distance
            )
        )

        # 6) Gravação dos resultados nas camadas de saída
        route_fields = QgsFields()
        route_fields.append(QgsField("route_id", QVariant.Int))
        route_fields.append(QgsField("stop_count", QVariant.Int))
        route_fields.append(QgsField("route_load", QVariant.Double))
        route_fields.append(QgsField("route_dist", QVariant.Double))

        (sink_routes, dest_routes) = self.parameterAsSink(
            parameters,
            self.OUTPUT_ROUTES,
            context,
            route_fields,
            QgsWkbTypes.LineString,
            target_crs
        )

        stop_fields = demand_source.fields()
        stop_fields.append(QgsField("route_id", QVariant.Int))
        stop_fields.append(QgsField("stop_seq", QVariant.Int))
        stop_fields.append(QgsField("cum_load", QVariant.Double))

        (sink_stops, dest_stops) = self.parameterAsSink(
            parameters,
            self.OUTPUT_STOPS,
            context,
            stop_fields,
            demand_source.wkbType(),
            demand_source.sourceCrs()
        )

        for route_idx, route_nodes in enumerate(routes, start=1):
            if not route_nodes:
                continue
            r_dist = compute_route_distance(route_nodes, cost_matrix, depot=0)
            r_load = sum(all_demands[node] for node in route_nodes)

            if sink_routes is not None:
                pts = [depot_pt] + [demand_points[node - 1] for node in route_nodes] + [depot_pt]
                geom = QgsGeometry.fromPolylineXY(pts)
                feat = QgsFeature(route_fields)
                feat.setGeometry(geom)
                feat.setAttributes([route_idx, len(route_nodes), r_load, r_dist])
                sink_routes.addFeature(feat, QgsFeatureSink.FastInsert)

            if sink_stops is not None:
                cum_load = 0.0
                for seq_idx, node in enumerate(route_nodes, start=1):
                    demand_feat = demand_features[node - 1]
                    cum_load += all_demands[node]
                    stop_feat = QgsFeature(demand_feat)
                    attrs = stop_feat.attributes()
                    attrs.extend([route_idx, seq_idx, cum_load])
                    stop_feat.setAttributes(attrs)
                    sink_stops.addFeature(stop_feat, QgsFeatureSink.FastInsert)

        results = {self.OUTPUT_ROUTES: dest_routes}
        if sink_stops is not None:
            results[self.OUTPUT_STOPS] = dest_stops

        return results

    def name(self):
        return "vrp_cvrp"

    def displayName(self):
        return self.tr("Roteirização de Veículos Capacitados (CVRP)")

    def group(self):
        return self.tr("Roteirização")

    def groupId(self):
        return "routing"

    def shortHelpString(self):
        return self.tr(
            "Resolve o Problema de Roteirização de Veículos Capacitados (CVRP) a partir de uma "
            "camada de depósito e uma camada de pontos de demanda (clientes).\n\n"
            "Constroi rotas que iniciam e terminam no depósito, respeitando a capacidade máxima do veículo, "
            "utilizando a heurística de economias de Clarke & Wright (1964) e refinamento opcional por "
            "busca local 2-opt (Lin, 1965) e Or-opt (Or, 1976).\n\n"
            "Parâmetros:\n"
            "- Camada de depósito: feição de ponto/polígono representando o depósito de partida/chegada.\n"
            "- Camada de demanda / clientes: feições de pontos ou polígonos com demandas a atender.\n"
            "- Campo de peso/demanda: campo numérico da demanda de cada cliente (opcional, default=1.0).\n"
            "- Capacidade do veículo: carga máxima transportada por cada veículo em uma rota.\n"
            "- Camada de rede viária: rede viária para distâncias reais (opcional, usa distância euclidiana se omitida).\n"
            "- Aplicar busca local: se verdadeiro, aplica 2-opt e Or-opt para otimização de cada rota.\n\n"
            "Saídas:\n"
            "- Rotas geradas: camada de linhas com a geometria das rotas e estatísticas de carga e distância.\n"
            "- Paradas por rota: camada de pontos ordenada com atribuição de rota e carga acumulada."
        )

    def createInstance(self):
        return VrpCvrp()
