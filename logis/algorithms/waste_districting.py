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
Algoritmo de processamento para setorização (districting) da coleta de resíduos sólidos.
"""

from qgis.core import (
    QgsCoordinateReferenceSystem,
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
    from ..core import qgis_compat
    from ..core.crs_transform import TransformCheckError, length_meter, read_lines_in_crs
except ImportError:
    from core import qgis_compat
    from core.crs_transform import TransformCheckError, length_meter, read_lines_in_crs

try:
    from ..core.routing.districting import (
        connected_components,
        select_seed_edges_farthest_first,
        grow_sectors_from_seeds,
        rebalance_boundary_edges,
        UNASSIGNED_SECTOR
    )
except ImportError:
    from core.routing.districting import (
        connected_components,
        select_seed_edges_farthest_first,
        grow_sectors_from_seeds,
        rebalance_boundary_edges,
        UNASSIGNED_SECTOR
    )


def _edge_endpoints(geometry):
    """Retorna os pontos (x, y) do primeiro e do último vértice da geometria de linha."""
    vertices = _all_vertices(geometry)

    if len(vertices) < 2:
        return None, None

    return vertices[0], vertices[-1]


def _all_vertices(geometry):
    """Retorna todos os pontos (x, y) de todas as partes da geometria de linha."""
    if geometry.isMultipart():
        parts = geometry.asMultiPolyline()
        return [pt for part in parts for pt in part]
    return geometry.asPolyline()


class WasteDistricting(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para setorização (districting) da coleta de resíduos sólidos.

    Particiona os trechos de via de uma camada de rede viária em k setores de coleta
    contíguos e balanceados por carga, usando heurística de sementes farthest-first
    (Gonzalez, 1985), crescimento de regiões a partir das sementes e refinamento local
    por troca de trechos de fronteira.

    Referência Bibliográfica da Técnica:
        - Hopcroft, J., & Tarjan, R. (1973). Efficient algorithms for graph manipulation.
          Communications of the ACM, 16(6), 372-378.
        - Gonzalez, T. F. (1985). Clustering to minimize the maximum intercluster
          distance. Theoretical Computer Science, 38, 293-306.
        - Kalcsics, J., Nickel, S., & Schröder, M. (2005). Towards a unified
          territorial design approach – Applications, algorithms and GIS integration.
          Top, 13(1), 1-56.

    Limite de Complexidade:
        Complexidade de Tempo: O(E + soma dos graus) para os componentes conexos +
        O(K*E) para seleção de sementes + O(E log E) para crescimento de regiões +
        O(I*E) para refinamento de fronteira, onde E é o número de trechos de via,
        K o número de setores e I o número de iterações.
        Testado com até ~5.000 trechos de via.
    """

    INPUT_STREETS = 'INPUT_STREETS'
    FIELD_LOAD = 'FIELD_LOAD'
    NUM_SECTORS = 'NUM_SECTORS'
    NODE_TOLERANCE = 'NODE_TOLERANCE'
    MAX_ITERATIONS = 'MAX_ITERATIONS'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteDistricting", string)

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
                self.FIELD_LOAD,
                self.tr("Campo de carga (opcional, default=comprimento do trecho)"),
                type=QgsProcessingParameterField.DataType.Numeric,
                parentLayerParameterName=self.INPUT_STREETS,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NUM_SECTORS,
                self.tr("Número de setores de coleta desejado"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=2,
                minValue=2
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_TOLERANCE,
                self.tr("Tolerância de nó (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.01,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ITERATIONS,
                self.tr("Máximo de iterações de rebalanceamento de fronteira"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=50,
                minValue=1
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Vias com setor de coleta atribuído")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        streets_source = self.parameterAsSource(parameters, self.INPUT_STREETS, context)
        load_field_name = self.parameterAsString(parameters, self.FIELD_LOAD, context)
        num_sectors = self.parameterAsInt(parameters, self.NUM_SECTORS, context)
        tolerance = self.parameterAsDouble(parameters, self.NODE_TOLERANCE, context)
        max_iterations = self.parameterAsInt(parameters, self.MAX_ITERATIONS, context)

        if streets_source is None:
            raise QgsProcessingException(self.tr("Camada de vias inválida."))

        load_field_idx = streets_source.fields().indexFromName(load_field_name) if load_field_name else -1

        # 1) Montar a lista de trechos (edges) a partir da geometria das vias
        feedback.pushInfo(self.tr("Lendo trechos de via e construindo adjacência..."))

        streets_crs = streets_source.sourceCrs()
        target_crs = (
            QgsCoordinateReferenceSystem("EPSG:5880") if streets_crs.isGeographic() else streets_crs
        )
        try:
            features, proj_geoms = read_lines_in_crs(
                streets_source, target_crs, context, self.tr("camada de vias")
            )
            length_fn = length_meter(streets_crs, context)
        except TransformCheckError as exc:
            raise QgsProcessingException(str(exc))

        edges = []
        skipped_fids = []
        for feature, geometry in zip(features, proj_geoms):
            if feedback.isCanceled():
                return {}

            start_pt, end_pt = _edge_endpoints(geometry)
            if start_pt is None:
                skipped_fids.append(feature.id())
                continue

            from_node = (round(start_pt.x() / tolerance), round(start_pt.y() / tolerance))
            to_node = (round(end_pt.x() / tolerance), round(end_pt.y() / tolerance))
            nodes = {
                (round(pt.x() / tolerance), round(pt.y() / tolerance))
                for pt in _all_vertices(geometry)
            }

            length_m = length_fn(feature.geometry())
            if load_field_idx != -1:
                raw_value = feature.attribute(load_field_idx)
                load = float(raw_value) if raw_value is not None else length_m
            else:
                load = length_m

            edges.append({
                "id": feature.id(),
                "from_node": from_node,
                "to_node": to_node,
                "nodes": nodes,
                "length": length_m,
                "load": load
            })

        if skipped_fids:
            feedback.pushWarning(
                self.tr("{count} trecho(s) com geometria inválida foram ignorados.").format(
                    count=len(skipped_fids)
                )
            )

        if not edges:
            raise QgsProcessingException(self.tr("Nenhum trecho de via válido encontrado na camada de entrada."))

        if num_sectors > len(edges):
            raise QgsProcessingException(
                self.tr(
                    "O número de setores ({k}) não pode exceder o número de trechos válidos ({n})."
                ).format(k=num_sectors, n=len(edges))
            )

        # 2) Componentes conexos: setorizar só a rede principal; o resto sai com -1
        feedback.pushInfo(self.tr("Verificando a conectividade da rede..."))
        try:
            components = connected_components(edges)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        main_ids = set(components[0])
        main_edges = [edge for edge in edges if edge["id"] in main_ids]
        edge_by_id = {edge["id"]: edge for edge in edges}

        outside_ids = [edge["id"] for edge in edges if edge["id"] not in main_ids]
        outside_count = len(outside_ids)
        outside_load = sum(edge_by_id[eid]["load"] for eid in outside_ids)
        total_load = sum(edge["load"] for edge in edges)
        outside_pct = (100.0 * outside_load / total_load) if total_load > 0 else 0.0

        if outside_count > 0 and outside_pct > 50.0:
            raise QgsProcessingException(
                self.tr(
                    "Rede fragmentada demais para setorizar: {pct:.1f}% da carga total está "
                    "fora da rede principal, em {n_comp} componente(s) isolado(s) com "
                    "{n_edges} trecho(s). Aumente a tolerância de nó ou trate os trechos "
                    "isolados à parte."
                ).format(
                    pct=outside_pct, n_comp=len(components) - 1, n_edges=outside_count
                )
            )

        if num_sectors > len(main_edges):
            raise QgsProcessingException(
                self.tr(
                    "O número de setores ({k}) não pode exceder o número de trechos da rede "
                    "principal ({n}; há {m} trecho(s) fora dela, que saem com "
                    "collection_sector_id = -1)."
                ).format(k=num_sectors, n=len(main_edges), m=outside_count)
            )

        if outside_count > 0:
            ids_text = ", ".join(str(eid) for eid in sorted(outside_ids)[:20])
            if outside_count > 20:
                ids_text += ", …"
            feedback.pushWarning(
                self.tr(
                    "{count} trecho(s) de via fora da rede principal, em {n_comp} "
                    "componente(s) isolado(s): {pct:.1f}% da carga total. Esses trechos saem "
                    "com collection_sector_id = -1 e não entram em nenhum setor. IDs: {ids}. "
                    "Confira a conexão dessas vias, aumente a tolerância de nó ou trate-as à parte."
                ).format(
                    count=outside_count, n_comp=len(components) - 1,
                    pct=outside_pct, ids=ids_text
                )
            )

        # 3) Setorização: sementes farthest-first -> crescimento de regiões -> rebalanceamento
        feedback.pushInfo(self.tr("Selecionando sementes (farthest-first)..."))
        try:
            seeds = select_seed_edges_farthest_first(main_edges, num_sectors)

            feedback.pushInfo(self.tr("Crescendo setores a partir das sementes..."))
            sector_of_edge = grow_sectors_from_seeds(main_edges, seeds)

            feedback.pushInfo(self.tr("Rebalanceando trechos de fronteira..."))
            sector_of_edge = rebalance_boundary_edges(main_edges, sector_of_edge, max_iterations=max_iterations)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        # 4) Reportar carga mín/máx/média por setor
        sector_loads = {}
        for edge in main_edges:
            sid = sector_of_edge[edge["id"]]
            sector_loads[sid] = sector_loads.get(sid, 0.0) + edge["load"]
        loads = list(sector_loads.values())
        summary = self.tr(
            "Setorização concluída. Setores: {k} | carga mín={min:.2f} | "
            "carga máx={max:.2f} | carga média={avg:.2f}"
        ).format(k=len(loads), min=min(loads), max=max(loads), avg=sum(loads) / len(loads))
        if outside_count > 0:
            summary += self.tr(" | trechos sem setor (-1): {n}").format(n=outside_count)
        feedback.pushInfo(summary)

        # 5) Gravar a camada de vias de saída com o campo novo collection_sector_id
        out_fields = streets_source.fields()
        out_fields.append(QgsField("collection_sector_id", qgis_compat.field_type("int")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            streets_source.wkbType(), streets_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        total_features = streets_source.featureCount()
        count = 0
        for feature in streets_source.getFeatures():
            if feedback.isCanceled():
                return {}

            sector_id = sector_of_edge.get(feature.id(), UNASSIGNED_SECTOR)
            out_feature = QgsFeature(out_fields)
            out_feature.setGeometry(feature.geometry())
            out_feature.setAttributes(feature.attributes() + [sector_id])
            sink.addFeature(out_feature, QgsFeatureSink.Flag.FastInsert)

            count += 1
            if total_features > 0:
                feedback.setProgress(int((count / total_features) * 100))

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_districting"

    def displayName(self):
        return self.tr("Setorização de Coleta de Resíduos (Districting)")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Particiona os trechos de uma camada de vias em k setores de coleta contíguos "
            "e balanceados por carga (resíduos gerados ou, na ausência do campo, comprimento "
            "do trecho).\n\n"
            "Usa a heurística de sementes farthest-first (Gonzalez, 1985), seguida de "
            "crescimento de regiões a partir das sementes e refinamento local por troca de "
            "trechos de fronteira para equilibrar a carga entre setores mantendo contiguidade. "
            "A solução é boa, não necessariamente ótima.\n\n"
            "A adjacência entre trechos considera qualquer vértice compartilhado (não só as "
            "pontas), e a setorização roda apenas sobre o componente principal da rede (o de "
            "maior carga). Trechos que não se ligam à rede principal — ilhas, fragmentos do "
            "recorte municipal, vias internas isoladas — saem com "
            "collection_sector_id = -1 e são reportados em um aviso (quantos são, quanto da "
            "carga representam e seus IDs), porque não é possível formar setores contíguos com "
            "eles. Se mais de 50% da carga ficar fora da rede principal, a execução aborta com "
            "erro, indicando aumentar a tolerância de nó.\n\n"
            "Parâmetros:\n"
            "- Camada de vias: trechos de via (linhas) a setorizar.\n"
            "- Campo de carga: campo numérico com a carga de cada trecho (opcional; se "
            "omitido, usa o comprimento do trecho como proxy de carga).\n"
            "- Número de setores: quantidade desejada de setores de coleta (k >= 2).\n"
            "- Tolerância de nó: distância, em metros, usada para considerar dois vértices de "
            "extremidade como o mesmo nó da rede. Funciona com qualquer SRC de entrada — a "
            "camada é lida já reprojetada para coordenadas métricas quando está em SRC "
            "geográfico, e o comprimento de cada trecho é medido de forma elipsoidal, em "
            "metros de verdade.\n"
            "- Máximo de iterações: limite de trocas locais de trechos de fronteira.\n\n"
            "Saída:\n"
            "- Camada de vias com o novo atributo 'collection_sector_id' (ID do setor de "
            "coleta; -1 = trecho fora da rede principal)."
        )

    def createInstance(self):
        return WasteDistricting()
