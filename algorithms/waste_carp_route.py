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
Algoritmo de processamento para roteirização por arcos capacitada
(Capacitated Arc Routing Problem - CARP) na coleta de resíduos sólidos.
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
    from ..core.routing.arc_routing import solve_carp_path_scanning
    from ..core import qgis_compat
except ImportError:
    from core.routing.arc_routing import solve_carp_path_scanning
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


def _extract_point(geom):
    """Retorna o ponto (x, y) de uma geometria de ponto."""
    pt = geom.asPoint()
    return pt.x(), pt.y()


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


class WasteCarpRoute(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para Roteirização por Arcos Capacitada (CARP).

    Determina rotas de veículos com limitação de capacidade a partir de um depósito/aterro,
    atendendo à demanda de resíduos sólidos em trechos de via usando a heurística Path-Scanning
    (Golden et al., 1983).

    Referência Bibliográfica da Técnica:
        - Golden, B. L., DeArmon, J. S., & Baker, E. K. (1983). Computational experiments
          with algorithms for a class of routing problems. Computers & Operations Research, 10(1), 47-59.
        - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
          Mathematical Programming, 5(1), 88-124.

    Limite de Complexidade:
        Complexidade de Tempo: O(R² · E log V), onde R é o número de trechos obrigatórios do
        setor, E é o número de trechos totais e V é o número de interseções.
        Testado com até ~500 trechos obrigatórios por setor.
    """

    INPUT_STREETS = 'INPUT_STREETS'
    FIELD_DEMAND = 'FIELD_DEMAND'
    FIELD_REQUIRED = 'FIELD_REQUIRED'
    FIELD_COLLECTION_SECTOR = 'FIELD_COLLECTION_SECTOR'
    CAPACITY = 'CAPACITY'
    INPUT_DEPOT = 'INPUT_DEPOT'
    NODE_TOLERANCE = 'NODE_TOLERANCE'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteCarpRoute", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_STREETS,
                self.tr("Camada de vias"),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_DEMAND,
                self.tr("Campo de geração/demanda de resíduos (kg)"),
                parentLayerParameterName=self.INPUT_STREETS,
                type=QgsProcessingParameterField.Numeric,
                optional=False
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
                self.CAPACITY,
                self.tr("Capacidade do veículo (em toneladas ou kg)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_DEPOT,
                self.tr("Camada de ponto do depósito/aterro (exatamente 1 feição)"),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_TOLERANCE,
                self.tr("Tolerância de nó em metros (requer CRS métrico)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.01,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Vias com rota de coleta (CARP)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        streets_source = self.parameterAsSource(parameters, self.INPUT_STREETS, context)
        demand_field_name = self.parameterAsString(parameters, self.FIELD_DEMAND, context)
        required_field_name = self.parameterAsString(parameters, self.FIELD_REQUIRED, context)
        sector_field_name = self.parameterAsString(parameters, self.FIELD_COLLECTION_SECTOR, context)
        capacity = self.parameterAsDouble(parameters, self.CAPACITY, context)
        depot_source = self.parameterAsSource(parameters, self.INPUT_DEPOT, context)
        tolerance = self.parameterAsDouble(parameters, self.NODE_TOLERANCE, context)

        if streets_source is None:
            raise QgsProcessingException(self.tr("Camada de vias inválida."))
        if capacity <= 0:
            raise QgsProcessingException(self.tr("A capacidade do veículo deve ser maior que zero."))

        demand_field_idx = (
            streets_source.fields().indexFromName(demand_field_name)
            if demand_field_name
            else -1
        )
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

        feedback.pushInfo(self.tr("Lendo trechos de via..."))

        sector_edges_map = {}
        feature_map = {}
        node_coords = {}
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
            node_coords[from_node] = (start_pt.x(), start_pt.y())
            node_coords[to_node] = (end_pt.x(), end_pt.y())

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

            attr_val = feature.attribute(demand_field_idx)
            try:
                demand_val = float(attr_val) if attr_val is not None else 0.0
            except (ValueError, TypeError):
                demand_val = 0.0

            if demand_val < 0:
                demand_val = 0.0

            if demand_val > capacity and is_req:
                raise QgsProcessingException(
                    self.tr("Demanda do trecho '{fid}' ({dem:.2f}) excede a capacidade do veículo ({cap:.2f}).").format(
                        fid=feature.id(), dem=demand_val, cap=capacity
                    )
                )

            if sec_val not in sector_edges_map:
                sector_edges_map[sec_val] = []

            sector_edges_map[sec_val].append({
                "id": feature.id(),
                "from_node": from_node,
                "to_node": to_node,
                "length": geometry.length(),
                "load": demand_val,
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

        # Determina o ponto do depósito (exatamente 1 feição, camada obrigatória)
        if depot_source is None:
            raise QgsProcessingException(self.tr("Camada de depósito inválida."))

        depot_points = []
        for feat in depot_source.getFeatures():
            geom = feat.geometry()
            if geom and not geom.isEmpty():
                pt = _extract_point(geom)
                if pt is not None:
                    depot_points.append(pt)
        if len(depot_points) != 1:
            raise QgsProcessingException(
                self.tr("A camada de ponto do depósito deve conter exatamente 1 feição (encontradas {count}).").format(
                    count=len(depot_points)
                )
            )
        depot_coords = depot_points[0]

        out_fields = streets_source.fields()
        out_fields.append(QgsField("route_id", qgis_compat.field_type("int")))
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

        for sec_val, full_edges in sector_edges_map.items():
            if feedback.isCanceled():
                return {}

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

            # Encontra o nó do depósito para o setor por distância euclidiana ao node_key mais próximo
            sec_nodes = list({e["from_node"] for e in full_edges} | {e["to_node"] for e in full_edges})
            dep_x, dep_y = depot_coords
            depot_node = min(
                sec_nodes,
                key=lambda n: (
                    (node_coords.get(n, (n[0] * tolerance, n[1] * tolerance))[0] - dep_x) ** 2 +
                    (node_coords.get(n, (n[0] * tolerance, n[1] * tolerance))[1] - dep_y) ** 2
                )
            )

            feedback.pushInfo(
                self.tr("Calculando rotas CARP para o setor '{sec}' ({req_count} trechos obrigatórios)...").format(
                    sec=sec_val, req_count=len(req_edges)
                )
            )

            try:
                routes = solve_carp_path_scanning(
                    required_edges=req_edges,
                    full_edges=full_edges,
                    depot_node=depot_node,
                    vehicle_capacity=capacity
                )
            except ValueError as exc:
                raise QgsProcessingException(
                    self.tr("Erro ao calcular rotas CARP para o setor '{sec}': {err}").format(
                        sec=sec_val, err=str(exc)
                    )
                )

            feedback.pushInfo(
                self.tr("Setor '{sec}': {count} rota(s)/viagem(ns) gerada(s).").format(
                    sec=sec_val, count=len(routes)
                )
            )

            req_id_set = {e["id"] for e in req_edges}
            full_edge_by_id = {e["id"]: e for e in full_edges}
            served_req_in_sector = set()

            for route_idx, route in enumerate(routes, start=1):
                route_edges = route["edges"]
                load_kg = route["load_kg"]
                req_m = sum(
                    full_edge_by_id[e_id]["length"]
                    for e_id in route_edges if e_id in req_id_set
                )
                deadhead_km = max(0.0, (route["distance_m"] - req_m) / 1000.0)

                feedback.pushInfo(
                    self.tr(
                        "Setor '{sec}', rota {idx}: carga {load:.2f} kg, {dh_km:.2f} km de deadhead."
                    ).format(sec=sec_val, idx=route_idx, load=load_kg, dh_km=deadhead_km)
                )
                if load_kg < 0.5 * capacity:
                    feedback.pushInfo(
                        self.tr(
                            "Aviso: rota {idx} do setor '{sec}' usa menos de 50% da capacidade "
                            "({load:.2f} kg de {cap:.2f} kg)."
                        ).format(idx=route_idx, sec=sec_val, load=load_kg, cap=capacity)
                    )

                for visit_idx, edge_id in enumerate(route_edges, start=1):
                    if feedback.isCanceled():
                        return {}

                    is_deadhead = (edge_id not in req_id_set) or (edge_id in served_req_in_sector)
                    if edge_id in req_id_set:
                        served_req_in_sector.add(edge_id)

                    orig_feat = feature_map[edge_id]

                    out_feat = QgsFeature(out_fields)
                    out_feat.setGeometry(orig_feat.geometry())
                    out_feat.setAttributes(
                        orig_feat.attributes() + [route_idx, visit_idx, sec_val, is_deadhead]
                    )
                    sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

            completed_sectors += 1
            feedback.setProgress(int((completed_sectors / total_sectors) * 100))

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_carp_route"

    def displayName(self):
        return self.tr("Roteirização por Arcos Capacitada (CARP)")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Calcula rotas de veículos capacitados para coleta de lixo por arcos usando o "
            "Problema de Roteirização por Arcos Capacitada (Capacitated Arc Routing Problem - CARP) "
            "com a heurística Path-Scanning (Golden et al., 1983).\n\n"
            "Parâmetros:\n"
            "- Camada de vias: feições de linha com a malha viária.\n"
            "- Campo de demanda de resíduos (obrigatório): campo numérico com a geração em cada trecho, em kg.\n"
            "- Campo de via obrigatória (opcional): campo indicando trechos com coleta obrigatória; "
            "se omitido, todos os trechos são obrigatórios.\n"
            "- Campo de setor de coleta (opcional): se informado, resolve o CARP separadamente por setor.\n"
            "- Capacidade do veículo: capacidade máxima de carga por veículo, em kg.\n"
            "- Camada de depósito/aterro: feição de ponto com a localização do aterro/depósito/garagem "
            "(exatamente 1 feição). O depósito é snapado ao vértice de via mais próximo por distância "
            "euclidiana — aproximação heurística, não uma projeção exata sobre a rede.\n"
            "- Tolerância de nó: distância em metros para conectar vértices das vias.\n\n"
            "Um trecho isolado com demanda maior que a capacidade do veículo gera erro explícito "
            "em vez de ser dividido entre mais de uma viagem (sem split-delivery).\n\n"
            "Retorno:\n"
            "- Camada de linha com feições de vias e campos adicionais: 'route_id' (identificador da "
            "rota/viagem dentro do setor), 'route_visit_order' (ordem de visita na rota), "
            "'route_sector_id' (setor de coleta) e 'route_is_deadhead' (booleano indicando passagem "
            "duplicada/deslocamento deadhead)."
        )

    def createInstance(self):
        return WasteCarpRoute()
