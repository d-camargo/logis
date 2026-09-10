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
Algoritmo de processamento para Caixeiro Viajante (TSP).
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
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
from qgis.analysis import QgsGraphAnalyzer
try:
    from ..core import qgis_compat
    from ..core.routing.tsp import solve_tsp, split_legs, summarize_legs
    from ..core.optim_backend import pick_backend
    from ..core.network.graph_builder import build_graph
    from ..core.network.od_matrix import compute_od_matrix
except ImportError:
    from core import qgis_compat
    from core.routing.tsp import solve_tsp, split_legs, summarize_legs
    from core.optim_backend import pick_backend
    from core.network.graph_builder import build_graph
    from core.network.od_matrix import compute_od_matrix


def _extract_point(geom):
    """Retorna um QgsPointXY representando a geometria (ponto ou centroide de polígono)."""
    if geom.type() == QgsWkbTypes.GeometryType.PointGeometry:
        return geom.asPoint()
    else:
        return geom.centroid().asPoint()


class VrpTsp(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para resolver o Problema do Caixeiro Viajante (TSP).

    Utiliza a heurística do Vizinho Mais Próximo (Flood, 1956) para construção da rota inicial,
    combinada com as heurísticas de busca local 2-opt (Lin, 1965) e Or-opt (Or, 1976) para otimização,
    ou o solver de programação por restrições do Google OR-Tools.

    Referência Bibliográfica da Técnica:
        - Flood, M. M. (1956). The traveling-salesman problem.
          Operations Research, 4(1), 61-75.
        - Lin, S. (1965). Computer solutions of the traveling salesman problem.
          Bell System Technical Journal, 44(10), 2245-2269.
        - Or, I. (1976). Traveling salesman-type combinatorial problems and their
          relation to the logistics of regional blood banking. PhD thesis, Northwestern University.
        - Perron, L., & Furnon, V. (2019). OR-Tools. Google.

    Limite de Complexidade:
        Complexidade de Tempo: O(N^2) para construção + O(N^2) para busca local 2-opt/Or-opt,
        onde N é o número de pontos.
        Complexidade de Espaço: O(N^2) para a matriz de distâncias.
        Testado com até 1.000 pontos.
    """

    INPUT_START = 'INPUT_START'
    INPUT_POINTS = 'INPUT_POINTS'
    INPUT_END = 'INPUT_END'
    INPUT_NETWORK = 'INPUT_NETWORK'
    IMPROVE = 'IMPROVE'
    OUTPUT_ORDER = 'OUTPUT_ORDER'
    OUTPUT_ROUTE = 'OUTPUT_ROUTE'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("VrpTsp", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_START,
                self.tr("Camada do ponto inicial"),
                [QgsProcessing.SourceType.TypeVectorPoint, QgsProcessing.SourceType.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINTS,
                self.tr("Camada de pontos a visitar"),
                [QgsProcessing.SourceType.TypeVectorPoint, QgsProcessing.SourceType.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_END,
                self.tr("Camada do ponto final (opcional; vazia = a rota fecha no ponto inicial)"),
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
            QgsProcessingParameterBoolean(
                self.IMPROVE,
                self.tr("Aplicar busca local (2-opt e Or-opt)"),
                defaultValue=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_ORDER,
                self.tr("Ordem de visita")
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_ROUTE,
                self.tr("Rota (trechos)"),
                optional=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        start_source = self.parameterAsSource(parameters, self.INPUT_START, context)
        points_source = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        end_source = self.parameterAsSource(parameters, self.INPUT_END, context)
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        improve = self.parameterAsBool(parameters, self.IMPROVE, context)

        if start_source is None:
            raise QgsProcessingException(self.tr("Camada do ponto inicial inválida."))
        if points_source is None:
            raise QgsProcessingException(self.tr("Camada de pontos a visitar inválida."))

        # 1) CRS de cálculo
        if network_layer and network_layer.isValid():
            target_crs = QgsCoordinateReferenceSystem("EPSG:5880")
        else:
            source_crs = points_source.sourceCrs()
            if source_crs.isGeographic():
                target_crs = QgsCoordinateReferenceSystem("EPSG:5880")
            else:
                target_crs = source_crs

        transform_start = QgsCoordinateTransform(start_source.sourceCrs(), target_crs, QgsProject.instance())
        transform_points = QgsCoordinateTransform(points_source.sourceCrs(), target_crs, QgsProject.instance())

        # 2) Leitura do ponto inicial (primeira feição válida)
        start_pt = None
        for feat in start_source.getFeatures():
            geom = feat.geometry()
            if geom and not geom.isEmpty():
                start_pt = transform_start.transform(_extract_point(geom))
                break

        if start_pt is None:
            raise QgsProcessingException(self.tr("Nenhum ponto inicial válido encontrado."))

        # 3) Leitura dos pontos a visitar na ordem de leitura
        visit_points = []
        visit_features = []
        feedback.pushInfo(self.tr("Lendo pontos a visitar..."))
        for feat in points_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            pt_transformed = transform_points.transform(_extract_point(geom))
            visit_points.append(pt_transformed)
            visit_features.append(feat)

        if not visit_points:
            raise QgsProcessingException(self.tr("A camada de pontos a visitar está vazia."))

        # 4) Leitura do ponto final (opcional; primeira feição válida se a camada foi fornecida)
        end_pt = None
        if end_source is not None:
            transform_end = QgsCoordinateTransform(end_source.sourceCrs(), target_crs, QgsProject.instance())
            for feat in end_source.getFeatures():
                geom = feat.geometry()
                if geom and not geom.isEmpty():
                    end_pt = transform_end.transform(_extract_point(geom))
                    break
            if end_pt is None:
                raise QgsProcessingException(self.tr("Nenhum ponto final válido encontrado na camada fornecida."))

        # Indexação dos nós: 0 = ponto inicial, 1..N = pontos a visitar, N+1 = ponto final quando houver
        all_points = [start_pt] + visit_points
        if end_pt is not None:
            all_points.append(end_pt)
            end_idx = len(visit_points) + 1
        else:
            end_idx = None
        start_idx = 0

        # 5) Matriz de distâncias
        graph = None
        vertices = None
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

        # 6) Otimização TSP sem passar backend (padrão "ortools" com fallback silencioso)
        used_backend = pick_backend("ortools")
        feedback.pushInfo(self.tr("Executando a otimização TSP..."))
        try:
            tour, total_distance = solve_tsp(
                distance_matrix=cost_matrix,
                start=start_idx,
                end=end_idx,
                improve=improve
            )
        except (ValueError, RuntimeError) as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("Otimização TSP concluída. Pontos: {count} | Backend: {backend} | Distância Total: {dist:.2f}").format(
                count=len(all_points), backend=used_backend, dist=total_distance
            )
        )

        # 7) Gravação dos resultados nas camadas de saída
        order_fields = QgsFields(points_source.fields())
        order_fields.append(QgsField("visit_seq", qgis_compat.field_type("int")))
        order_fields.append(QgsField("node_role", qgis_compat.field_type("string")))
        order_fields.append(QgsField("leg_role", qgis_compat.field_type("string")))
        order_fields.append(QgsField("leg_dist", qgis_compat.field_type("double")))
        order_fields.append(QgsField("cum_dist", qgis_compat.field_type("double")))

        (sink_order, dest_order) = self.parameterAsSink(
            parameters,
            self.OUTPUT_ORDER,
            context,
            order_fields,
            QgsWkbTypes.Type.Point,
            target_crs
        )

        if sink_order is not None:
            closed = (end_idx is None)
            legs = split_legs(tour, cost_matrix, closed=closed)
            num_input_fields = points_source.fields().count()
            cum_dist = 0.0

            for i, node in enumerate(tour):
                if feedback.isCanceled():
                    return {}

                visit_seq = i + 1

                if i == 0:
                    node_role = "inicio"
                    leg_role = ""
                    leg_dist = 0.0
                    orig_attrs = [None] * num_input_fields
                else:
                    _, _, leg_role, leg_dist = legs[i - 1]
                    cum_dist += leg_dist
                    if end_idx is not None and node == end_idx:
                        node_role = "fim"
                        orig_attrs = [None] * num_input_fields
                    else:
                        node_role = "parada"
                        orig_attrs = visit_features[node - 1].attributes()

                feat = QgsFeature(order_fields)
                feat.setGeometry(QgsGeometry.fromPointXY(all_points[node]))
                feat.setAttributes(list(orig_attrs) + [visit_seq, node_role, leg_role, leg_dist, cum_dist])
                sink_order.addFeature(feat, QgsFeatureSink.Flag.FastInsert)

        route_fields = QgsFields()
        route_fields.append(QgsField("leg_seq", qgis_compat.field_type("int")))
        route_fields.append(QgsField("from_seq", qgis_compat.field_type("int")))
        route_fields.append(QgsField("to_seq", qgis_compat.field_type("int")))
        route_fields.append(QgsField("leg_role", qgis_compat.field_type("string")))
        route_fields.append(QgsField("leg_dist", qgis_compat.field_type("double")))
        route_fields.append(QgsField("cum_dist", qgis_compat.field_type("double")))
        route_fields.append(QgsField("stop_count", qgis_compat.field_type("int")))
        route_fields.append(QgsField("tour_dist", qgis_compat.field_type("double")))
        route_fields.append(QgsField("access_dist", qgis_compat.field_type("double")))
        route_fields.append(QgsField("service_dist", qgis_compat.field_type("double")))
        route_fields.append(QgsField("return_dist", qgis_compat.field_type("double")))
        route_fields.append(QgsField("dead_ratio", qgis_compat.field_type("double")))
        route_fields.append(QgsField("closed", qgis_compat.field_type("int")))
        route_fields.append(QgsField("backend", qgis_compat.field_type("string")))

        (sink_route, dest_route) = self.parameterAsSink(
            parameters,
            self.OUTPUT_ROUTE,
            context,
            route_fields,
            QgsWkbTypes.Type.LineString,
            target_crs
        )

        if sink_route is not None:
            closed = (end_idx is None)
            closed_int = 1 if closed else 0
            stop_count = len(visit_points)
            legs = split_legs(tour, cost_matrix, closed=closed)
            summary = summarize_legs(legs)

            tour_dist = summary["tour_dist"]
            access_dist = summary["access_dist"]
            service_dist = summary["service_dist"]
            return_dist = summary["return_dist"]
            dead_ratio = summary["dead_ratio"]

            has_network = bool(network_layer and network_layer.isValid() and graph is not None and vertices is not None)

            cum_leg_dist = 0.0
            num_legs = len(legs)

            for k, (u, v, leg_role, leg_dist) in enumerate(legs):
                if feedback.isCanceled():
                    return {}

                leg_seq = k + 1
                from_seq = k + 1
                to_seq = 1 if (closed and k == num_legs - 1) else (k + 2)
                cum_leg_dist += leg_dist

                pts = []
                if has_network:
                    try:
                        u_vtx = vertices[u]
                        v_vtx = vertices[v]
                        tree, _ = QgsGraphAnalyzer.dijkstra(graph, u_vtx, 0)
                        curr = v_vtx
                        path_vtx = []
                        unreachable = False
                        while curr != u_vtx:
                            path_vtx.append(curr)
                            edge_idx = tree[curr]
                            if edge_idx < 0:
                                unreachable = True
                                break
                            edge = graph.edge(edge_idx)
                            prev = edge.fromVertex() if edge.toVertex() == curr else edge.toVertex()
                            if prev == curr:
                                unreachable = True
                                break
                            curr = prev
                        if not unreachable:
                            path_vtx.append(u_vtx)
                            path_vtx.reverse()
                            pts = [graph.vertex(vtx).point() for vtx in path_vtx]
                    except Exception:
                        pts = []

                if len(pts) < 2:
                    pts = [all_points[u], all_points[v]]

                geom = QgsGeometry.fromPolylineXY(pts)
                feat = QgsFeature(route_fields)
                feat.setGeometry(geom)
                feat.setAttributes([
                    leg_seq,
                    from_seq,
                    to_seq,
                    leg_role,
                    leg_dist,
                    cum_leg_dist,
                    stop_count,
                    tour_dist,
                    access_dist,
                    service_dist,
                    return_dist,
                    dead_ratio,
                    closed_int,
                    used_backend
                ])
                sink_route.addFeature(feat, QgsFeatureSink.Flag.FastInsert)

        results = {self.OUTPUT_ORDER: dest_order}
        if sink_route is not None:
            results[self.OUTPUT_ROUTE] = dest_route

        return results

    def name(self):
        return "vrp_tsp"

    def displayName(self):
        return self.tr("Caixeiro Viajante (TSP)")

    def group(self):
        return self.tr("Roteirização")

    def groupId(self):
        return "routing"

    def shortHelpString(self):
        return self.tr(
            "Resolve o Problema do Caixeiro Viajante (TSP) a partir de um ponto inicial, "
            "uma camada de pontos a visitar e, opcionalmente, um ponto final ou rede viária.\n\n"
            "Determina a sequência de visita de menor distância total utilizando as heurísticas "
            "do Vizinho Mais Próximo (Flood, 1956) com refinamento opcional por busca local "
            "2-opt (Lin, 1965) e Or-opt (Or, 1976), ou o solver de programação por restrições do Google OR-Tools.\n\n"
            "Parâmetros:\n"
            "- Camada do ponto inicial: feição de ponto/polígono do local de partida.\n"
            "- Camada de pontos a visitar: feições de pontos/polígonos a serem visitadas.\n"
            "- Camada do ponto final (opcional): feição do ponto de chegada (se omitida ou vazia, a rota fecha no ponto inicial).\n"
            "- Camada de rede viária: rede viária para distâncias reais (opcional, usa distância euclidiana se omitida).\n"
            "- Aplicar busca local: se verdadeiro, aplica 2-opt e Or-opt para otimização da rota.\n\n"
            "Saídas:\n"
            "- Ordem de visita: camada de pontos ordenada com a ordem de visita na tabela de atributos em 'visit_seq', nó ('node_role'), papel da perna ('leg_role'), distância da perna ('leg_dist') e distância acumulada ('cum_dist').\n"
            "- Rota (trechos): camada de linhas com a geometria das pernas da rota classificadas ('leg_role': 'acesso', 'rota', 'retorno'). Os trechos 'acesso' e 'retorno' da camada de rota são os deslocamentos improdutivos (do ponto inicial ao primeiro ponto a visitar e do último ao ponto final), somados em 'access_dist' e 'return_dist', com os totais de distância ('tour_dist', 'service_dist') e a taxa improdutiva ('dead_ratio') repetidos em todas as feições."
        )

    def createInstance(self):
        return VrpTsp()
