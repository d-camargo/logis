# -*- coding: utf-8 -*-
"""
/***************************************************************************
 logis
                                A QGIS plugin
 Complemento do QGIS para apoiar projetos de logística no Brasil
                                -------------------
        begin                : 2026-07-21
        copyright            : (C) 2026 by Diego Camargo
        license              : GPL-3.0
 ***************************************************************************/
"""
"""
Algoritmo de processamento para cálculo da distância/tempo aos destinos de resíduos (aterro/transbordo/ecoponto).
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
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
    from ..core.indicators.waste import waste_destination_distance
    from ..core.network.graph_builder import build_graph
    from ..core.network.od_matrix import compute_od_matrix
    from ..core import qgis_compat
except ImportError:
    from core.indicators.waste import waste_destination_distance
    from core.network.graph_builder import build_graph
    from core.network.od_matrix import compute_od_matrix
    from core import qgis_compat


class WasteDestinationDistance(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a menor distância ou tempo de viagem aos destinos
    de resíduos sólidos (aterros sanitários, estações de transbordo, ecopontos) para cada setor
    ou origem de coleta, a partir dos caminhos mínimos na rede viária.

    Referência Bibliográfica da Técnica:
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.
        Daskin, M. S. (1995). Network and Discrete Location: Models, Algorithms, and Applications.
        John Wiley & Sons.

    Limite de Complexidade:
        Complexidade de Tempo: O(D * (E + V log V)) para o Dijkstra multi-origem a partir de D destinos,
        mais O(D * S) para encontrar o destino mais próximo de cada um dos S setores/origens.
        Complexidade de Espaço: O(V + E) para o grafo, mais O(D * S) para a matriz OD.
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    INPUT_DESTINATIONS = 'INPUT_DESTINATIONS'
    INPUT_SECTORS = 'INPUT_SECTORS'
    CRITERION = 'CRITERION'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteDestinationDistance", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de rede viária (Linhas)"),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_DESTINATIONS,
                self.tr("Camada de destinos de resíduos - aterro/transbordo/ecoponto (Pontos)"),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_SECTORS,
                self.tr("Camada de setores/origens de coleta (Pontos ou Polígonos)"),
                [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.CRITERION,
                self.tr("Critério de custo"),
                options=[self.tr("Distância"), self.tr("Tempo de viagem")],
                defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Setores de coleta com distância ao destino")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        destinations_source = self.parameterAsSource(parameters, self.INPUT_DESTINATIONS, context)
        sectors_source = self.parameterAsSource(parameters, self.INPUT_SECTORS, context)
        criterion_num = self.parameterAsEnum(parameters, self.CRITERION, context)

        if network_layer is None or not network_layer.isValid():
            raise QgsProcessingException(self.tr("Camada de rede viária inválida."))
        if destinations_source is None:
            raise QgsProcessingException(self.tr("Camada de destinos de resíduos inválida."))
        if sectors_source is None:
            raise QgsProcessingException(self.tr("Camada de setores/origens inválida."))

        # 1) Reprojetar pontos de destino e origens para o CRS métrico (EPSG:5880)
        target_crs_obj = QgsCoordinateReferenceSystem("EPSG:5880")
        transform_dest = QgsCoordinateTransform(destinations_source.sourceCrs(), target_crs_obj, QgsProject.instance())
        transform_sector = QgsCoordinateTransform(sectors_source.sourceCrs(), target_crs_obj, QgsProject.instance())

        # 2) Ler pontos de destino
        dest_points = []
        feedback.pushInfo(self.tr("Lendo pontos de destino (aterros/transbordos/ecopontos)..."))
        for feature in destinations_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            dest_points.append(transform_dest.transform(geom.asPoint()))

        if not dest_points:
            raise QgsProcessingException(self.tr("Nenhum ponto de destino válido encontrado."))

        # 3) Ler setores/origens de coleta
        sector_features = []
        sector_points = []
        feedback.pushInfo(self.tr("Lendo setores/origens de coleta..."))
        for feature in sectors_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            sector_features.append(feature)
            if geom.type() == QgsWkbTypes.PointGeometry:
                pt = geom.asPoint()
            else:
                pt = geom.centroid().asPoint()
            sector_points.append(transform_sector.transform(pt))

        if not sector_points:
            raise QgsProcessingException(self.tr("Nenhum setor/origem de coleta válido encontrado."))

        # 4) Construir o grafo na rede viária amarrando destinos e setores
        feedback.pushInfo(self.tr("Construindo o grafo a partir da rede viária..."))
        tie_points = dest_points + sector_points
        try:
            res = build_graph(network_layer, target_crs=target_crs_obj, points=tie_points)
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))

        graph = res["graph"]
        snapped_points = res["snapped_points"]

        if graph is None or graph.vertexCount() < 2:
            raise QgsProcessingException(
                self.tr("O grafo construído possui menos de 2 vértices. Não é possível calcular as distâncias.")
            )

        snapped_dests = snapped_points[:len(dest_points)]
        snapped_sectors = snapped_points[len(dest_points):]

        dest_vertices = [graph.findVertex(pt) for pt in snapped_dests]
        sector_vertices = [graph.findVertex(pt) for pt in snapped_sectors]

        if any(v == -1 for v in dest_vertices):
            raise QgsProcessingException(self.tr("Não foi possível amarrar um ou mais pontos de destino à rede viária."))
        if any(v == -1 for v in sector_vertices):
            raise QgsProcessingException(self.tr("Não foi possível amarrar um ou mais setores/origens à rede viária."))

        # 5) Matriz OD entre destinos (origens da matriz) e setores (destinos da matriz)
        feedback.pushInfo(self.tr("Calculando matriz de distâncias/tempos de viagem destino-setor..."))
        try:
            distances = compute_od_matrix(
                graph, dest_vertices, sector_vertices,
                criterion_num=criterion_num,
                cache_id="waste_destination_distance", feedback=feedback
            )
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao calcular a matriz OD: {}").format(str(exc)))

        # 6) Calcular a menor distância ao destino mais próximo por setor
        try:
            costs = waste_destination_distance(distances)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        # 7) Gravar o resultado como novo campo na cópia da camada de setores
        out_fields = sectors_source.fields()
        out_fields.append(QgsField("dist_destino", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            sectors_source.wkbType(), sectors_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        for feature, cost in zip(sector_features, costs):
            out_feature = QgsFeature(out_fields)
            out_feature.setGeometry(feature.geometry())
            out_feature.setAttributes(feature.attributes() + [cost])
            sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

        feedback.pushInfo(
            self.tr("Distância ao destino de resíduos mais próximo calculada para {count} setor(es).").format(count=len(costs))
        )
        feedback.setProgress(100)

        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_destination_distance"

    def displayName(self):
        return self.tr("Distância ao Destino de Resíduos")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Calcula a distância ou tempo de viagem ao ponto de destino de resíduos mais próximo "
            "(aterro sanitário, estação de transbordo, ecoponto) para cada setor ou centroide de coleta, "
            "utilizando caminhos mínimos na rede viária.\n\n"
            "Parâmetros:\n"
            "- Camada de rede viária: feições de linha representando as vias.\n"
            "- Camada de destinos de resíduos: feições de ponto representando aterros, estações de transbordo ou ecopontos.\n"
            "- Camada de setores/origens: feições de ponto ou polígono representando os setores de coleta.\n"
            "- Critério de custo: define se o cálculo de custo de caminho mínimo é baseado em Distância ou Tempo de viagem.\n\n"
            "Retorno:\n"
            "- Cópia da camada de origens com a coluna 'dist_destino' (menor distância em km ou tempo em min até o destino mais próximo)."
        )

    def createInstance(self):
        return WasteDestinationDistance()
