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

import math

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsFeatureSink,
    QgsWkbTypes,
    QgsGeometry,
    QgsRectangle,
    QgsCsException
)
try:
    from ..core import qgis_compat, crashlog
    from ..core.crs_check import classify_input_crs, valid_extent
    from ..core.progress import PhaseProgress
    from ..core.optim_backend import pick_backend
    from ..core.routing.vrp import solve_cvrp, compute_route_distance
    from ..core.network.graph_builder import build_graph
    from ..core.network.od_matrix import compute_od_matrix
except ImportError:
    from core import qgis_compat, crashlog
    from core.crs_check import classify_input_crs, valid_extent
    from core.progress import PhaseProgress
    from core.optim_backend import pick_backend
    from core.routing.vrp import solve_cvrp, compute_route_distance
    from core.network.graph_builder import build_graph
    from core.network.od_matrix import compute_od_matrix


def _extract_point(geom):
    """
    Returns a QgsPointXY representing the geometry.

    Handles single points, multipoints (using the first point), and polygons (using the centroid).
    Raises ValueError when the geometry is null, empty, or fails to produce a valid point.
    """
    if geom is None or geom.isEmpty():
        raise ValueError("Geometry is null or empty.")

    if geom.type() == QgsWkbTypes.GeometryType.PointGeometry:
        if QgsWkbTypes.isMultiType(geom.wkbType()):
            pts = geom.asMultiPoint()
            if pts and not pts[0].isEmpty():
                return pts[0]
            raise ValueError("MultiPoint geometry does not contain a valid point.")
        pt = geom.asPoint()
        if not pt.isEmpty():
            return pt
        raise ValueError("Point geometry does not produce a valid point.")
    else:
        centroid_geom = geom.centroid()
        if centroid_geom and not centroid_geom.isEmpty():
            pt = centroid_geom.asPoint()
            if not pt.isEmpty():
                return pt
        raise ValueError("Geometry does not produce a valid point or centroid.")


def _resolve_source_crs(source, raw_points, label, feedback):
    """
    Resolve o SRC efetivo da camada via classify_input_crs.

    - "assume_4674": SRC inválido e todas as coordenadas dentro do Brasil → aviso no
      feedback e retorna EPSG:4674 (SRC padrão do projeto).
    - "missing" e "degrees_in_projected": lança QgsProcessingException com o nome da
      camada, o SRC declarado e como corrigir.
    """
    from qgis.PyQt.QtCore import QCoreApplication

    def tr(string):
        return QCoreApplication.translate("VrpCvrp", string)

    crs = source.sourceCrs()
    status = classify_input_crs(
        crs.isValid(), crs.isGeographic(), [(p.x(), p.y()) for p in raw_points]
    )
    declared = crs.authid() if crs.authid() else "indefinido"

    if status == "assume_4674":
        if feedback:
            feedback.pushWarning(
                tr("SRC da camada de {label} não foi definido; coordenadas dentro do Brasil — assumindo EPSG:4674 (SIRGAS 2000).").format(label=label)
            )
        return QgsCoordinateReferenceSystem("EPSG:4674")

    if status == "missing":
        raise QgsProcessingException(
            tr("A camada de {label} está sem SRC válido (declarado: {crs}) e suas coordenadas não caem no Brasil. Defina o SRC da camada em Propriedades › Fonte e rode novamente.").format(
                label=label, crs=declared
            )
        )

    if status == "degrees_in_projected":
        raise QgsProcessingException(
            tr("A camada de {label} declara o SRC {crs}, mas as coordenadas estão em graus. Defina o SRC correto da camada em Propriedades › Fonte.").format(
                label=label, crs=declared
            )
        )

    return crs


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
    BACKEND = 'BACKEND'
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
                [QgsProcessing.SourceType.TypeVectorPoint, QgsProcessing.SourceType.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_DEMAND,
                self.tr("Camada de demanda / clientes (Pontos/Polígonos)"),
                [QgsProcessing.SourceType.TypeVectorPoint, QgsProcessing.SourceType.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_DEMAND,
                self.tr("Campo de peso/demanda (opcional, default=1.0)"),
                type=QgsProcessingParameterField.DataType.Numeric,
                parentLayerParameterName=self.INPUT_DEMAND,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.CAPACITY,
                self.tr("Capacidade do veículo"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=100.0,
                minValue=0.0001
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
            QgsProcessingParameterEnum(
                self.BACKEND,
                self.tr("Backend de otimização"),
                options=[
                    self.tr("Automático (OR-Tools quando disponível)"),
                    self.tr("Python puro (heurística)"),
                    self.tr("OR-Tools")
                ],
                defaultValue=0
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
        backend_idx = self.parameterAsEnum(parameters, self.BACKEND, context)

        if backend_idx == 1:
            req_backend = "python"
        elif backend_idx == 2:
            req_backend = "ortools"
        else:
            req_backend = pick_backend("ortools")

        if depot_source is None:
            raise QgsProcessingException(self.tr("Camada de depósito inválida."))
        if demand_source is None:
            raise QgsProcessingException(self.tr("Camada de demanda inválida."))
        if capacity <= 0:
            raise QgsProcessingException(self.tr("A capacidade do veículo deve ser estritamente maior que zero."))

        # 1) Leitura das geometrias cruas do depósito
        raw_depot_pt = None
        for feat in depot_source.getFeatures():
            geom = feat.geometry()
            if geom and not geom.isEmpty():
                raw_depot_pt = _extract_point(geom)
                break

        if raw_depot_pt is None:
            raise QgsProcessingException(self.tr("Nenhum ponto de depósito válido encontrado."))

        raw_depot_pts = [raw_depot_pt]

        # 2) Leitura das geometrias cruas da demanda e pesos
        p_read = PhaseProgress(feedback, 0.0, 8.0)
        feedback.setProgressText(self.tr("Lendo pontos de demanda…"))
        feedback.pushInfo(self.tr("Lendo pontos de demanda..."))

        demand_field_idx = demand_source.fields().indexOf(demand_field_name) if demand_field_name else -1

        demand_features = []
        raw_demand_pts = []
        demand_weights = []

        total_pts = demand_source.featureCount()
        for i, feat in enumerate(demand_source.getFeatures()):
            if p_read.isCanceled():
                return {}
            if total_pts > 0:
                p_read.setProgress(100.0 * (i + 1) / total_pts)
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            raw_pt = _extract_point(geom)

            weight = 1.0
            if demand_field_idx != -1:
                val = feat.attribute(demand_field_idx)
                if not qgis_compat.is_null(val):
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
            raw_demand_pts.append(raw_pt)
            demand_weights.append(weight)

        p_read.setProgress(100.0)

        if not raw_demand_pts:
            raise QgsProcessingException(self.tr("Nenhum ponto de demanda válido encontrado."))

        # 3) Resolver SRCs efetivos e target_crs
        depot_crs = _resolve_source_crs(depot_source, raw_depot_pts, self.tr("depósito"), feedback)
        demand_crs = _resolve_source_crs(demand_source, raw_demand_pts, self.tr("demanda"), feedback)

        dist_mode = "rede" if (network_layer and network_layer.isValid()) else "euclidiana"
        crashlog.mark("cvrp-inicio", f"modo={dist_mode} backend={req_backend}")

        if network_layer and network_layer.isValid():
            target_crs = QgsCoordinateReferenceSystem("EPSG:5880")
            if feedback:
                feedback.pushInfo(self.tr("SRC da rede: {}").format(network_layer.crs().authid()))
        else:
            if demand_crs.mapUnits() == QgsCoordinateReferenceSystem("EPSG:5880").mapUnits():
                target_crs = demand_crs
            else:
                target_crs = QgsCoordinateReferenceSystem("EPSG:5880")

        if feedback:
            feedback.pushInfo(self.tr("SRC de depósito: {} → {}").format(depot_crs.authid(), target_crs.authid()))
            feedback.pushInfo(self.tr("SRC de demanda: {} → {}").format(demand_crs.authid(), target_crs.authid()))

        # 4) Montar transforms com context.transformContext() e transformar pontos
        transform_depot = QgsCoordinateTransform(depot_crs, target_crs, context.transformContext())
        transform_demand = QgsCoordinateTransform(demand_crs, target_crs, context.transformContext())

        depot_pt = transform_depot.transform(raw_depot_pt)
        demand_points = [transform_demand.transform(pt) for pt in raw_demand_pts]

        crashlog.mark("cvrp-transform", f"1 deposito, {len(demand_points)} demandas -> CRS {target_crs.authid()}")

        # 4) Matriz de distâncias (Nó 0 = depósito, Nôs 1..N = demandas)
        all_points = [depot_pt] + demand_points
        all_demands = [0.0] + demand_weights

        graph = None
        vertices = None
        if network_layer and network_layer.isValid():
            feedback.pushInfo(self.tr("Construindo o grafo e calculando a matriz OD na rede..."))
            x_coords = [p.x() for p in all_points]
            y_coords = [p.y() for p in all_points]
            bbox = QgsRectangle(min(x_coords), min(y_coords), max(x_coords), max(y_coords))
            diag = math.sqrt(bbox.width() ** 2 + bbox.height() ** 2)
            margin = max(3000.0, diag)
            extent = QgsRectangle(
                bbox.xMinimum() - margin,
                bbox.yMinimum() - margin,
                bbox.xMaximum() + margin,
                bbox.yMaximum() + margin
            )
            if not valid_extent(extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()):
                raise QgsProcessingException(self.tr("Janela de análise calculada a partir dos pontos é inválida: {}").format(extent.toString()))

            net_crs = network_layer.crs()
            try:
                if net_crs.isValid() and net_crs != target_crs:
                    transform_net = QgsCoordinateTransform(net_crs, target_crs, context.transformContext())
                    net_extent = transform_net.transformBoundingBox(network_layer.extent())
                else:
                    net_extent = network_layer.extent()
            except QgsCsException:
                net_extent = None

            if net_extent is None or not valid_extent(
                net_extent.xMinimum(), net_extent.yMinimum(), net_extent.xMaximum(), net_extent.yMaximum()
            ) or not extent.intersects(net_extent):
                raise QgsProcessingException(
                    self.tr("Os pontos ({}) não caem na área da rede viária (rede em {}) — confira o SRC das camadas.").format(
                        target_crs.authid(), net_crs.authid() if net_crs.isValid() else "SRC desconhecido"
                    )
                )

            feedback.pushInfo(self.tr("Janela de análise: {}").format(extent.toString()))
            crashlog.mark("cvrp-build-graph", f"camada com {network_layer.featureCount()} feicoes")

            p_build = PhaseProgress(feedback, 8.0, 35.0)
            feedback.setProgressText(self.tr("Construindo o grafo…"))
            try:
                res = build_graph(network_layer, target_crs=target_crs, points=all_points, extent=extent, feedback=p_build)
            except Exception as exc:
                raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))
            p_build.setProgress(100.0)

            graph = res["graph"]
            snapped_points = res["snapped_points"]

            if graph is None or graph.vertexCount() < 2:
                raise QgsProcessingException(self.tr("O grafo construído possui menos de 2 vértices."))

            crashlog.mark("cvrp-grafo-pronto", f"{graph.vertexCount()} vertices, {graph.edgeCount()} arestas")

            vertices = [graph.findVertex(pt) for pt in snapped_points]

            p_od = PhaseProgress(feedback, 35.0, 70.0)
            feedback.setProgressText(self.tr("Calculando a matriz OD…"))
            try:
                crashlog.mark("cvrp-od-matrix", "Dijkstra multi-origem")
                cost_matrix = compute_od_matrix(
                    graph=graph,
                    origins=vertices,
                    destinations=vertices,
                    criterion_num=0,
                    cache_id="vrp_cvrp",
                    feedback=p_od
                )
            except Exception as exc:
                raise QgsProcessingException(self.tr("Erro ao calcular a matriz OD: {}").format(str(exc)))
            p_od.setProgress(100.0)
        else:
            p_euc = PhaseProgress(feedback, 8.0, 40.0)
            feedback.setProgressText(self.tr("Calculando matriz de distâncias euclidianas…"))
            feedback.pushInfo(self.tr("Calculando matriz de distâncias euclidianas..."))
            cost_matrix = []
            n_all = len(all_points)
            for i, p1 in enumerate(all_points):
                if p_euc.isCanceled():
                    return {}
                if n_all > 0:
                    p_euc.setProgress(100.0 * (i + 1) / n_all)
                row = [p1.distance(p2) for p2 in all_points]
                cost_matrix.append(row)
            p_euc.setProgress(100.0)

        # 5) Resolução do CVRP
        used_backend = pick_backend(req_backend)
        if used_backend == "ortools":
            opt_text = self.tr("Otimizando (OR-Tools)…")
        else:
            opt_text = self.tr("Otimizando (heurística Python)…")
        feedback.setProgressText(opt_text)

        if dist_mode == "rede":
            p_opt = PhaseProgress(feedback, 70.0, 90.0)
        else:
            p_opt = PhaseProgress(feedback, 40.0, 85.0)

        feedback.pushInfo(self.tr("Executando a otimização CVRP..."))
        crashlog.mark("cvrp-ortools-import", f"backend resolvido: {used_backend}")
        try:
            routes, total_distance, route_loads = solve_cvrp(
                distance_matrix=cost_matrix,
                demands=all_demands,
                capacity=capacity,
                depot=0,
                improve=improve,
                backend=req_backend,
                feedback=p_opt
            )
        except (ValueError, RuntimeError) as exc:
            raise QgsProcessingException(str(exc))
        p_opt.setProgress(100.0)

        crashlog.mark("cvrp-solver-ok", f"custo={total_distance:.1f}")

        feedback.pushInfo(
            self.tr("Roteirização concluída. Rotas geradas: {count} | Backend: {backend} | Distância Total: {dist:.2f}").format(
                count=len(routes), backend=used_backend, dist=total_distance
            )
        )

        # 6) Gravação dos resultados nas camadas de saída
        feedback.setProgressText(self.tr("Gravando as saídas…"))
        if dist_mode == "rede":
            p_out = PhaseProgress(feedback, 90.0, 100.0)
        else:
            p_out = PhaseProgress(feedback, 85.0, 100.0)

        crashlog.mark("cvrp-sinks", "gravando camadas de saida")
        route_fields = QgsFields()
        route_fields.append(QgsField("route_id", qgis_compat.field_type("int")))
        route_fields.append(QgsField("stop_count", qgis_compat.field_type("int")))
        route_fields.append(QgsField("route_load", qgis_compat.field_type("double")))
        route_fields.append(QgsField("route_dist", qgis_compat.field_type("double")))
        route_fields.append(QgsField("backend", qgis_compat.field_type("string")))

        (sink_routes, dest_routes) = self.parameterAsSink(
            parameters,
            self.OUTPUT_ROUTES,
            context,
            route_fields,
            QgsWkbTypes.Type.LineString,
            target_crs
        )

        stop_fields = demand_source.fields()
        stop_fields.append(QgsField("route_id", qgis_compat.field_type("int")))
        stop_fields.append(QgsField("stop_seq", qgis_compat.field_type("int")))
        stop_fields.append(QgsField("cum_load", qgis_compat.field_type("double")))

        (sink_stops, dest_stops) = self.parameterAsSink(
            parameters,
            self.OUTPUT_STOPS,
            context,
            stop_fields,
            demand_source.wkbType(),
            demand_crs
        )

        total_route_items = len(routes) if sink_routes is not None else 0
        total_stop_items = sum(len(r) for r in routes) if sink_stops is not None else 0
        total_out_items = total_route_items + total_stop_items
        written_items = 0

        for route_idx, route_nodes in enumerate(routes, start=1):
            if not route_nodes:
                continue
            r_dist = compute_route_distance(route_nodes, cost_matrix, depot=0)
            r_load = sum(all_demands[node] for node in route_nodes)

            if sink_routes is not None:
                if p_out.isCanceled():
                    return {}
                pts = [depot_pt] + [demand_points[node - 1] for node in route_nodes] + [depot_pt]
                geom = QgsGeometry.fromPolylineXY(pts)
                feat = QgsFeature(route_fields)
                feat.setGeometry(geom)
                feat.setAttributes([route_idx, len(route_nodes), r_load, r_dist, used_backend])
                sink_routes.addFeature(feat, QgsFeatureSink.Flag.FastInsert)
                written_items += 1
                if total_out_items > 0:
                    p_out.setProgress(100.0 * written_items / total_out_items)

            if sink_stops is not None:
                cum_load = 0.0
                for seq_idx, node in enumerate(route_nodes, start=1):
                    if p_out.isCanceled():
                        return {}
                    demand_feat = demand_features[node - 1]
                    cum_load += all_demands[node]
                    stop_feat = QgsFeature(demand_feat)
                    attrs = stop_feat.attributes()
                    attrs.extend([route_idx, seq_idx, cum_load])
                    stop_feat.setAttributes(attrs)
                    sink_stops.addFeature(stop_feat, QgsFeatureSink.Flag.FastInsert)
                    written_items += 1
                    if total_out_items > 0:
                        p_out.setProgress(100.0 * written_items / total_out_items)

        p_out.setProgress(100.0)

        crashlog.mark("cvrp-fim", "concluido")

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
            "- Aplicar busca local: se verdadeiro, aplica 2-opt e Or-opt para otimização de cada rota.\n"
            "- Backend de otimização: qual motor usar (Automático/Python/OR-Tools).\n\n"
            "Saídas:\n"
            "- Rotas geradas: camada de linhas com a geometria das rotas e estatísticas de carga e distância.\n"
            "- Paradas por rota: camada de pontos ordenada com atribuição de rota e carga acumulada."
        )

    def createInstance(self):
        return VrpCvrp()
