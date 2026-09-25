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

import math

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsProject,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsFeatureSink,
    QgsWkbTypes,
    QgsGeometry,
    QgsPointXY,
    QgsRectangle
)
from qgis.analysis import QgsGraphAnalyzer
try:
    from ..core import qgis_compat, crashlog
    from ..core.crs_check import classify_input_crs, valid_extent
    from ..core.progress import PhaseProgress
    from ..core.routing.tsp import solve_tsp, split_legs, summarize_legs
    from ..core.optim_backend import pick_backend
    from ..core.network.graph_builder import build_graph
    from ..core.network.od_matrix import compute_od_matrix
    from ..core.crs_transform import TransformCheckError, checked_transform, transform_points, transform_bbox
    from ..core.crs_check import utm_sirgas_epsg
except ImportError:
    from core import qgis_compat, crashlog
    from core.crs_check import classify_input_crs, valid_extent
    from core.progress import PhaseProgress
    from core.routing.tsp import solve_tsp, split_legs, summarize_legs
    from core.optim_backend import pick_backend
    from core.network.graph_builder import build_graph
    from core.network.od_matrix import compute_od_matrix
    from core.crs_transform import TransformCheckError, checked_transform, transform_points, transform_bbox
    from core.crs_check import utm_sirgas_epsg

# Custo limite para conexões inalcançáveis na rede (convenção de urban_mean_circuity.py)
_UNREACHABLE_COST = 1e18


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
        return QCoreApplication.translate("VrpTsp", string)

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
    BACKEND = 'BACKEND'
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
        backend_idx = self.parameterAsEnum(parameters, self.BACKEND, context)

        if backend_idx == 1:
            req_backend = "python"
        elif backend_idx == 2:
            req_backend = "ortools"
        else:
            req_backend = pick_backend("ortools")

        if start_source is None:
            raise QgsProcessingException(self.tr("Camada do ponto inicial inválida."))
        if points_source is None:
            raise QgsProcessingException(self.tr("Camada de pontos a visitar inválida."))

        # 1) Leitura das geometrias cruas
        raw_start_pt = None
        for feat in start_source.getFeatures():
            geom = feat.geometry()
            if geom and not geom.isEmpty():
                raw_start_pt = _extract_point(geom)
                break

        if raw_start_pt is None:
            raise QgsProcessingException(self.tr("Nenhum ponto inicial válido encontrado."))

        raw_start_pts = [raw_start_pt]

        p_read = PhaseProgress(feedback, 0.0, 8.0)
        feedback.setProgressText(self.tr("Lendo pontos a visitar…"))
        feedback.pushInfo(self.tr("Lendo pontos a visitar..."))
        raw_visit_pts = []
        visit_features = []
        total_pts = points_source.featureCount()
        for i, feat in enumerate(points_source.getFeatures()):
            if p_read.isCanceled():
                return {}
            if total_pts > 0:
                p_read.setProgress(100.0 * (i + 1) / total_pts)
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            raw_pt = _extract_point(geom)
            raw_visit_pts.append(raw_pt)
            visit_features.append(feat)
        p_read.setProgress(100.0)

        if not raw_visit_pts:
            raise QgsProcessingException(self.tr("A camada de pontos a visitar está vazia."))

        raw_end_pt = None
        raw_end_pts = []
        if end_source is not None:
            for feat in end_source.getFeatures():
                geom = feat.geometry()
                if geom and not geom.isEmpty():
                    raw_end_pt = _extract_point(geom)
                    raw_end_pts = [raw_end_pt]
                    break
            if raw_end_pt is None:
                raise QgsProcessingException(self.tr("Nenhum ponto final válido encontrado na camada fornecida."))

        # 2) Resolver SRCs efetivos e target_crs
        start_crs = _resolve_source_crs(start_source, raw_start_pts, self.tr("ponto inicial"), feedback)
        points_crs = _resolve_source_crs(points_source, raw_visit_pts, self.tr("pontos a visitar"), feedback)
        end_crs = None
        if end_source is not None:
            end_crs = _resolve_source_crs(end_source, raw_end_pts, self.tr("ponto final"), feedback)

        dist_mode = "rede" if (network_layer and network_layer.isValid()) else "euclidiana"
        crashlog.mark("tsp-inicio", f"modo={dist_mode} backend={req_backend}")

        if network_layer and network_layer.isValid():
            target_crs = QgsCoordinateReferenceSystem("EPSG:5880")
            if feedback:
                feedback.pushInfo(self.tr("SRC da rede: {}").format(network_layer.crs().authid()))
        else:
            if points_crs.mapUnits() == QgsCoordinateReferenceSystem("EPSG:5880").mapUnits():
                target_crs = points_crs
            else:
                target_crs = QgsCoordinateReferenceSystem("EPSG:5880")

        # 3) Montar transforms com os três contextos e checked_transform
        contexts = [
            context.transformContext(),
            QgsProject.instance().transformContext(),
            QgsCoordinateTransformContext()
        ]

        def _checked(src_crs, dest_crs, probe_pt):
            try:
                ct = checked_transform(src_crs, dest_crs, contexts, probe_pt)
            except TransformCheckError as exc:
                raise QgsProcessingException(self.tr("Transformação de coordenadas falhou: {exc}").format(exc=str(exc)))
            if ct is not None and feedback:
                t_pt = transform_points(ct, [probe_pt], dest_crs)[0]
                feedback.pushInfo(self.tr("Transformação {src} → {dst} ok (prova ({x1:.4f}, {y1:.4f}) → ({x2:.4f}, {y2:.4f}))").format(
                    src=src_crs.authid(), dst=dest_crs.authid(),
                    x1=probe_pt.x(), y1=probe_pt.y(),
                    x2=t_pt.x(), y2=t_pt.y()
                ))
            return ct

        def _utm_fallback_crs():
            cx = sum(p.x() for p in raw_visit_pts) / len(raw_visit_pts)
            cy = sum(p.y() for p in raw_visit_pts) / len(raw_visit_pts)
            centroid = QgsPointXY(cx, cy)
            if points_crs.mapUnits() == QgsCoordinateReferenceSystem("EPSG:4326").mapUnits():
                return QgsCoordinateReferenceSystem(utm_sirgas_epsg(cx, cy))
            ct = _checked(points_crs, QgsCoordinateReferenceSystem("EPSG:4674"), centroid)
            lonlat = transform_points(ct, [centroid], "EPSG:4674")[0]
            return QgsCoordinateReferenceSystem(utm_sirgas_epsg(lonlat.x(), lonlat.y()))

        # SRC métrico interno: EPSG:5880, com fallback para UTM SIRGAS da zona do
        # centroide dos pontos. A prova cobre todas as camadas de entrada e, no modo
        # Rede, a extensão da rede: se 5880 falhar em qualquer uma, refaz tudo em UTM.
        net_crs = network_layer.crs() if (network_layer and network_layer.isValid()) else None
        candidates = [target_crs]
        if target_crs.authid() == "EPSG:5880":
            candidates.append(_utm_fallback_crs())

        net_extent = None
        for cand_idx, cand_crs in enumerate(candidates):
            is_last = cand_idx == len(candidates) - 1
            try:
                transform_start = checked_transform(start_crs, cand_crs, contexts, raw_start_pt)
                transform_points_ct = checked_transform(points_crs, cand_crs, contexts, raw_visit_pts[0])
                transform_end = None
                if end_source is not None and end_crs is not None:
                    transform_end = checked_transform(end_crs, cand_crs, contexts, raw_end_pts[0])
                net_extent = None
                if net_crs is not None:
                    if net_crs.isValid() and net_crs != cand_crs:
                        transform_net = checked_transform(net_crs, cand_crs, contexts, network_layer.extent().center())
                        net_extent = transform_bbox(transform_net, network_layer.extent(), cand_crs)
                    else:
                        net_extent = QgsRectangle(network_layer.extent())
            except TransformCheckError as exc:
                if is_last:
                    if len(candidates) == 1:
                        raise QgsProcessingException(self.tr("Transformação de coordenadas falhou: {exc}").format(exc=str(exc)))
                    raise QgsProcessingException(self.tr("Transformação para UTM ({utm}) falhou: {exc}").format(utm=cand_crs.authid(), exc=str(exc)))
                if feedback:
                    feedback.pushWarning(self.tr("Transformação para EPSG:5880 falhou ({exc}) — adotando fallback para {utm_auth}").format(exc=str(exc), utm_auth=candidates[1].authid()))
                continue
            target_crs = cand_crs
            break

        if feedback:
            probes = [
                (start_crs, raw_start_pt, transform_start),
                (points_crs, raw_visit_pts[0], transform_points_ct),
            ]
            if transform_end is not None:
                probes.append((end_crs, raw_end_pts[0], transform_end))
            for src_crs, probe_pt, ct in probes:
                if ct is not None:
                    t_pt = transform_points(ct, [probe_pt], target_crs)[0]
                    feedback.pushInfo(self.tr("Transformação {src} → {dst} ok (prova ({x1:.4f}, {y1:.4f}) → ({x2:.4f}, {y2:.4f}))").format(
                        src=src_crs.authid(), dst=target_crs.authid(),
                        x1=probe_pt.x(), y1=probe_pt.y(),
                        x2=t_pt.x(), y2=t_pt.y()
                    ))

        if feedback:
            feedback.pushInfo(self.tr("SRC de ponto inicial: {} → {}").format(start_crs.authid(), target_crs.authid()))
            feedback.pushInfo(self.tr("SRC de pontos a visitar: {} → {}").format(points_crs.authid(), target_crs.authid()))
            if end_source is not None and end_crs is not None:
                feedback.pushInfo(self.tr("SRC de ponto final: {} → {}").format(end_crs.authid(), target_crs.authid()))

        start_pt = transform_points(transform_start, [raw_start_pt], target_crs)[0]
        visit_points = transform_points(transform_points_ct, raw_visit_pts, target_crs)

        end_pt = None
        if end_source is not None and end_crs is not None:
            end_pt = transform_points(transform_end, [raw_end_pt], target_crs)[0]

        # Indexação dos nós: 0 = ponto inicial, 1..N = pontos a visitar, N+1 = ponto final quando houver
        all_points = [start_pt] + visit_points
        if end_pt is not None:
            all_points.append(end_pt)
            end_idx = len(visit_points) + 1
        else:
            end_idx = None
        start_idx = 0
        crashlog.mark("tsp-transform", f"{len(all_points)} pontos -> CRS {target_crs.authid()}")

        # 5) Matriz de distâncias
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

            # A extensão da rede já foi provada no SRC interno (checked_transform +
            # transform_bbox) durante a resolução do SRC métrico; só resta a guarda.
            if net_extent is None or not valid_extent(
                net_extent.xMinimum(), net_extent.yMinimum(), net_extent.xMaximum(), net_extent.yMaximum()
            ) or not extent.intersects(net_extent):
                raise QgsProcessingException(
                    self.tr("Os pontos ({}) não caem na área da rede viária (rede em {}) — confira o SRC das camadas.").format(
                        target_crs.authid(), net_crs.authid() if net_crs.isValid() else "SRC desconhecido"
                    )
                )

            feedback.pushInfo(self.tr("Janela de análise: {}").format(extent.toString()))
            crashlog.mark("tsp-build-graph", f"camada com {network_layer.featureCount()} feicoes")

            p_build = PhaseProgress(feedback, 8.0, 35.0)
            feedback.setProgressText(self.tr("Construindo o grafo…"))
            try:
                res = build_graph(network_layer, target_crs=target_crs, points=all_points, extent=extent, feedback=p_build)
            except Exception as exc:
                raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))
            p_build.setProgress(100.0)

            graph = res["graph"]
            snapped_points = res["snapped_points"]
            crashlog.mark("tsp-grafo-pronto", f"{graph.vertexCount()} vertices, {graph.edgeCount()} arestas")

            if graph is None or graph.vertexCount() < 2:
                raise QgsProcessingException(self.tr("O grafo construído possui menos de 2 vértices."))

            vertices = [graph.findVertex(pt) for pt in snapped_points]

            if any(v == -1 for v in vertices):
                raise QgsProcessingException(
                    self.tr(
                        "Não foi possível amarrar um ou mais pontos à rede viária. "
                        "Verifique se os pontos estão próximos da malha e no mesmo território dela."
                    )
                )

            p_od = PhaseProgress(feedback, 35.0, 70.0)
            feedback.setProgressText(self.tr("Calculando a matriz OD…"))
            try:
                crashlog.mark("tsp-od-matrix", "Dijkstra multi-origem")
                cost_matrix = compute_od_matrix(
                    graph=graph,
                    origins=vertices,
                    destinations=vertices,
                    criterion_num=0,
                    cache_id="vrp_tsp",
                    feedback=p_od
                )
            except Exception as exc:
                raise QgsProcessingException(self.tr("Erro ao calcular a matriz OD: {}").format(str(exc)))
            p_od.setProgress(100.0)

            unreachable_count = 0
            for i, row in enumerate(cost_matrix):
                for j, c in enumerate(row):
                    if i != j and (math.isinf(c) or c > _UNREACHABLE_COST):
                        unreachable_count += 1

            if unreachable_count > 0:
                raise QgsProcessingException(
                    self.tr(
                        "A rede viária possui {} par(es) de pontos sem caminho entre si. "
                        "Verifique se a rede está desconectada."
                    ).format(unreachable_count)
                )
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

        # 6) Otimização TSP
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

        feedback.pushInfo(self.tr("Executando a otimização TSP..."))
        crashlog.mark("tsp-ortools-import", f"backend resolvido: {used_backend}")
        try:
            tour, total_distance = solve_tsp(
                distance_matrix=cost_matrix,
                start=start_idx,
                end=end_idx,
                improve=improve,
                backend=req_backend,
                feedback=p_opt
            )
        except (ValueError, RuntimeError) as exc:
            raise QgsProcessingException(str(exc))
        p_opt.setProgress(100.0)
        crashlog.mark("tsp-solver-ok", f"custo={total_distance:.1f}")

        feedback.pushInfo(
            self.tr("Otimização TSP concluída. Pontos: {count} | Modo: {dist_mode} | Backend: {backend} | Distância Total: {dist:.2f}").format(
                count=len(all_points), dist_mode=dist_mode, backend=used_backend, dist=total_distance
            )
        )

        # 7) Gravação dos resultados nas camadas de saída
        feedback.setProgressText(self.tr("Gravando as saídas…"))
        if dist_mode == "rede":
            p_out = PhaseProgress(feedback, 90.0, 100.0)
        else:
            p_out = PhaseProgress(feedback, 85.0, 100.0)

        out_crs = QgsCoordinateReferenceSystem("EPSG:4674")
        transform_out_start = _checked(start_crs, out_crs, raw_start_pt)
        start_pt_out = transform_points(transform_out_start, [raw_start_pt], out_crs)[0]

        transform_out_points = _checked(points_crs, out_crs, raw_visit_pts[0])
        visit_points_out = transform_points(transform_out_points, raw_visit_pts, out_crs)

        end_pt_out = None
        if end_source is not None and end_crs is not None:
            transform_out_end = _checked(end_crs, out_crs, raw_end_pts[0])
            end_pt_out = transform_points(transform_out_end, [raw_end_pt], out_crs)[0]

        all_points_out = [start_pt_out] + visit_points_out
        if end_pt_out is not None:
            all_points_out.append(end_pt_out)

        has_network = bool(network_layer and network_layer.isValid() and graph is not None and vertices is not None)
        transform_out_network = None
        if has_network:
            transform_out_network = _checked(target_crs, out_crs, all_points[0])

        crashlog.mark("tsp-sinks", "gravando camadas de saida")
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
            out_crs
        )

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
        route_fields.append(QgsField("dist_mode", qgis_compat.field_type("string")))
        route_fields.append(QgsField("leg_geom", qgis_compat.field_type("string")))

        (sink_route, dest_route) = self.parameterAsSink(
            parameters,
            self.OUTPUT_ROUTE,
            context,
            route_fields,
            QgsWkbTypes.Type.LineString,
            out_crs
        )

        closed = (end_idx is None)
        legs = split_legs(tour, cost_matrix, closed=closed)

        total_order_items = len(tour) if sink_order is not None else 0
        total_route_items = len(legs) if sink_route is not None else 0
        total_out_items = total_order_items + total_route_items
        written_items = 0

        if sink_order is not None:
            num_input_fields = points_source.fields().count()
            cum_dist = 0.0

            for i, node in enumerate(tour):
                if p_out.isCanceled():
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
                feat.setGeometry(QgsGeometry.fromPointXY(all_points_out[node]))
                feat.setAttributes(list(orig_attrs) + [visit_seq, node_role, leg_role, leg_dist, cum_dist])
                sink_order.addFeature(feat, QgsFeatureSink.Flag.FastInsert)

                written_items += 1
                if total_out_items > 0:
                    p_out.setProgress(100.0 * written_items / total_out_items)

        if sink_route is not None:
            closed_int = 1 if closed else 0
            stop_count = len(visit_points)
            summary = summarize_legs(legs)

            tour_dist = summary["tour_dist"]
            access_dist = summary["access_dist"]
            service_dist = summary["service_dist"]
            return_dist = summary["return_dist"]
            dead_ratio = summary["dead_ratio"]


            cum_leg_dist = 0.0
            num_legs = len(legs)
            dijkstra_trees = {}

            for k, (u, v, leg_role, leg_dist) in enumerate(legs):
                if p_out.isCanceled():
                    return {}

                leg_seq = k + 1
                from_seq = k + 1
                to_seq = 1 if (closed and k == num_legs - 1) else (k + 2)
                cum_leg_dist += leg_dist

                pts = []
                leg_geom = "reta"
                if has_network:
                    try:
                        u_vtx = vertices[u]
                        v_vtx = vertices[v]
                        if u_vtx in dijkstra_trees:
                            tree = dijkstra_trees[u_vtx]
                        else:
                            tree, _ = QgsGraphAnalyzer.dijkstra(graph, u_vtx, 0)
                            dijkstra_trees[u_vtx] = tree
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
                            if transform_out_network is not None:
                                pts = transform_points(transform_out_network, pts, out_crs)
                            if len(pts) >= 2:
                                leg_geom = "rede"
                    except Exception:
                        pts = []

                if leg_geom != "rede":
                    pts = [all_points_out[u], all_points_out[v]]
                    leg_geom = "reta"

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
                    used_backend,
                    dist_mode,
                    leg_geom
                ])
                sink_route.addFeature(feat, QgsFeatureSink.Flag.FastInsert)

                written_items += 1
                if total_out_items > 0:
                    p_out.setProgress(100.0 * written_items / total_out_items)

        p_out.setProgress(100.0)

        results = {self.OUTPUT_ORDER: dest_order}
        if sink_route is not None:
            results[self.OUTPUT_ROUTE] = dest_route

        crashlog.mark("tsp-fim", "concluido")
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
            "- Aplicar busca local: se verdadeiro, aplica 2-opt e Or-opt para otimização da rota.\n"
            "- Backend de otimização: escolha do solver ('Automático (OR-Tools quando disponível)', 'Python puro (heurística)' ou 'OR-Tools'). O modo 'Python puro' é o modo seguro quando o QGIS fecha ao rodar a rota.\n\n"
            "Saídas:\n"
            "- Ordem de visita: camada de pontos ordenada com a ordem de visita na tabela de atributos em 'visit_seq', nó ('node_role'), papel da perna ('leg_role'), distância da perna ('leg_dist') e distância acumulada ('cum_dist').\n"
            "- Rota (trechos): camada de linhas com a geometria das pernas da rota classificadas ('leg_role': 'acesso', 'rota', 'retorno'). Os trechos 'acesso' e 'retorno' da camada de rota são os deslocamentos improdutivos (do ponto inicial ao primeiro ponto a visitar e do último ao ponto final), somados em 'access_dist' e 'return_dist', com os totais de distância ('tour_dist', 'service_dist') e a taxa improdutiva ('dead_ratio') repetidos em todas as feições, além do modo de cálculo ('dist_mode') e da geometria do trecho ('leg_geom')."
        )

    def createInstance(self):
        return VrpTsp()
