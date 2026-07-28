# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo da distância/tempo de entrega ao depósito mais próximo.
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
    QgsFeatureSink
)

from ..core import qgis_compat
from ..core.network.graph_builder import build_graph
from ..core.network.od_matrix import compute_od_matrix
from ..core.indicators.urban import nearest_depot_cost


class UrbanDeliveryDistance(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a distância ou o tempo de entrega das zonas
    ao depósito mais próximo, usando caminhos mínimos na rede viária.

    Referência Bibliográfica da Técnica:
        Daskin, M. S. (1995). Network and Discrete Location: Models, Algorithms, and Applications.
        John Wiley & Sons.
        (O cálculo de custo ao depósito mais próximo é a operação fundamental em problemas de
        localização de instalações e roteirização baseada em zonas de atendimento de menor custo).

    Limite de Complexidade:
        Complexidade de Tempo: O(D * (E + V log V)) para o Dijkstra multi-origem a partir de D depósitos,
        mais O(D * Z) para encontrar o depósito mais próximo de cada uma das Z zonas.
        Complexidade de Espaço: O(V + E) para o grafo, mais O(D * Z) para a matriz OD.
        Testado com redes de até 50.000 arestas e 40.000 vértices, com até 1.000 depósitos e 50.000 zonas.
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    INPUT_DEPOTS = 'INPUT_DEPOTS'
    INPUT_ZONES = 'INPUT_ZONES'
    CRITERION = 'CRITERION'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("UrbanDeliveryDistance", string)

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
                self.INPUT_DEPOTS,
                self.tr("Camada de depósitos candidatos (Pontos)"),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_ZONES,
                self.tr("Camada de zonas/centroides (Pontos)"),
                [QgsProcessing.TypeVectorPoint]
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
                self.tr("Zonas com custo de entrega")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        depots_source = self.parameterAsSource(parameters, self.INPUT_DEPOTS, context)
        zones_source = self.parameterAsSource(parameters, self.INPUT_ZONES, context)
        criterion_num = self.parameterAsEnum(parameters, self.CRITERION, context)

        if network_layer is None or not network_layer.isValid():
            raise QgsProcessingException(self.tr("Camada de rede viária inválida."))
        if depots_source is None:
            raise QgsProcessingException(self.tr("Camada de depósitos inválida."))
        if zones_source is None:
            raise QgsProcessingException(self.tr("Camada de zonas inválida."))

        # 1) Reprojetar depósitos e zonas para o CRS métrico alvo (mesmo usado pelo grafo, EPSG:5880)
        target_crs_obj = QgsCoordinateReferenceSystem("EPSG:5880")
        transform_depot = QgsCoordinateTransform(depots_source.sourceCrs(), target_crs_obj, QgsProject.instance())
        transform_zone = QgsCoordinateTransform(zones_source.sourceCrs(), target_crs_obj, QgsProject.instance())

        # 2) Ler depósitos
        depot_points = []
        feedback.pushInfo(self.tr("Lendo depósitos..."))
        for feature in depots_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            depot_points.append(transform_depot.transform(geom.asPoint()))

        if not depot_points:
            raise QgsProcessingException(self.tr("Nenhum depósito válido encontrado na camada de depósitos."))

        # 3) Ler zonas, preservando a feição original para gravar o resultado nela
        zone_features = []
        zone_points = []
        feedback.pushInfo(self.tr("Lendo zonas..."))
        for feature in zones_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            zone_features.append(feature)
            zone_points.append(transform_zone.transform(geom.asPoint()))

        if not zone_points:
            raise QgsProcessingException(self.tr("Nenhuma zona válida encontrada na camada de zonas."))

        # 4) Construir o grafo, amarrando depósitos e zonas como vértices
        feedback.pushInfo(self.tr("Construindo o grafo a partir da rede viária..."))
        tie_points = depot_points + zone_points
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

        snapped_depots = snapped_points[:len(depot_points)]
        snapped_zones = snapped_points[len(depot_points):]

        depot_vertices = [graph.findVertex(pt) for pt in snapped_depots]
        zone_vertices = [graph.findVertex(pt) for pt in snapped_zones]

        if any(v == -1 for v in depot_vertices):
            raise QgsProcessingException(self.tr("Não foi possível amarrar um ou mais depósitos à rede viária."))
        if any(v == -1 for v in zone_vertices):
            raise QgsProcessingException(self.tr("Não foi possível amarrar uma ou mais zonas à rede viária."))

        # 5) Matriz OD (com cache em disco) entre depósitos (origens) e zonas (destinos)
        feedback.pushInfo(self.tr("Calculando matriz de distâncias/tempos de viagem depósito-zona..."))
        try:
            distances = compute_od_matrix(
                graph, depot_vertices, zone_vertices,
                criterion_num=criterion_num,
                cache_id="delivery_distance", feedback=feedback
            )
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao calcular a matriz OD: {}").format(str(exc)))

        # 6) Calcular o custo do depósito mais próximo para cada zona chamando a função core
        try:
            costs = nearest_depot_cost(distances)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        # 7) Gravar o resultado como novo campo numa cópia da camada de zonas
        out_fields = zones_source.fields()
        out_fields.append(QgsField("dist_entrega", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            zones_source.wkbType(), zones_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        for feature, cost in zip(zone_features, costs):
            out_feature = QgsFeature(out_fields)
            out_feature.setGeometry(feature.geometry())
            out_feature.setAttributes(feature.attributes() + [cost])
            sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

        feedback.pushInfo(
            self.tr("Custo de entrega ao depósito mais próximo calculado para {count} zona(s).").format(count=len(costs))
        )
        feedback.setProgress(100)

        return {self.OUTPUT: dest_id}

    def name(self):
        return "urban_delivery_distance"

    def displayName(self):
        return self.tr("Distância de Entrega Urbana")

    def group(self):
        return self.tr("Indicadores Urbanos")

    def groupId(self):
        return "urban"

    def shortHelpString(self):
        return self.tr(
            "Calcula a distância ou tempo de entrega ao depósito mais próximo para cada zona de demanda "
            "(centroide de setor) a partir de uma camada de depósitos candidatos, usando caminhos mínimos "
            "na rede viária.\n\n"
            "Parâmetros:\n"
            "- Camada de rede viária: feições de linha representando as vias.\n"
            "- Camada de depósitos candidatos: feições de ponto representando os depósitos/centros de distribuição.\n"
            "- Camada de zonas/centroides: feições de ponto representando as zonas de demanda/entregas.\n"
            "- Critério de custo: define se o cálculo de custo de caminho mínimo é baseado em Distância ou Tempo de viagem.\n\n"
            "Retorno:\n"
            "- Cópia da camada de zonas com a coluna 'dist_entrega' (contendo a menor distância ou tempo de viagem até o depósito mais próximo)."
        )

    def createInstance(self):
        return UrbanDeliveryDistance()
