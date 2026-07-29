# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo de acessibilidade gravitacional urbana a POIs.
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
    QgsFeatureSink
)

from ..core import qgis_compat
from ..core.network.graph_builder import build_graph
from ..core.network.od_matrix import compute_od_matrix
from ..core.indicators.urban import gravity_accessibility


class UrbanGravityAccessibility(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a acessibilidade gravitacional de uma camada de
    origens (ex.: centroides de setor) a uma camada de destinos (POIs) ponderados, usando
    caminhos mínimos na rede viária.

    Referência Bibliográfica da Técnica:
        Hansen, W. G. (1959). How accessibility shapes land use.
        Journal of the American Institute of Planners, 25(2), 73-76.

    Limite de Complexidade:
        Complexidade de Tempo: O(O * (E + V log V)) para o Dijkstra multi-origem, mais O(O * D)
        para a agregação gravitacional, onde O é o número de origens e D o de destinos.
        Complexidade de Espaço: O(V + E) para o grafo, mais O(O * D) para a matriz OD.
        Testado com redes de até 50.000 arestas e 40.000 vértices, e até 1.000 origens x
        1.000 destinos (cálculo em poucos segundos, com cache de matriz OD em disco).
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    INPUT_ORIGINS = 'INPUT_ORIGINS'
    INPUT_DESTINATIONS = 'INPUT_DESTINATIONS'
    FIELD_WEIGHT = 'FIELD_WEIGHT'
    BETA = 'BETA'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("UrbanGravityAccessibility", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de rede viária (Linhas)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_ORIGINS,
                self.tr("Camada de origem (pontos/centroides)"),
                [QgsProcessing.SourceType.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_DESTINATIONS,
                self.tr("Camada de destinos (POIs)"),
                [QgsProcessing.SourceType.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_WEIGHT,
                self.tr("Campo de peso/atratividade do destino (opcional, default 1 para todos)"),
                type=QgsProcessingParameterField.Numeric,
                parentLayerParameterName=self.INPUT_DESTINATIONS,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BETA,
                self.tr("Parâmetro de decaimento por distância (beta)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=2.0,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Origem com acessibilidade gravitacional")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        origins_source = self.parameterAsSource(parameters, self.INPUT_ORIGINS, context)
        destinations_source = self.parameterAsSource(parameters, self.INPUT_DESTINATIONS, context)
        field_weight = self.parameterAsString(parameters, self.FIELD_WEIGHT, context)
        beta = self.parameterAsDouble(parameters, self.BETA, context)

        if network_layer is None or not network_layer.isValid():
            raise QgsProcessingException(self.tr("Camada de rede viária inválida."))
        if origins_source is None:
            raise QgsProcessingException(self.tr("Camada de origem inválida."))
        if destinations_source is None:
            raise QgsProcessingException(self.tr("Camada de destinos inválida."))

        weight_field_index = (
            destinations_source.fields().indexFromName(field_weight) if field_weight else -1
        )

        # 1) Reprojetar origens e destinos para o CRS métrico alvo (mesmo usado pelo grafo)
        target_crs_obj = QgsCoordinateReferenceSystem("EPSG:5880")
        transform_origin = QgsCoordinateTransform(origins_source.sourceCrs(), target_crs_obj, QgsProject.instance())
        transform_dest = QgsCoordinateTransform(destinations_source.sourceCrs(), target_crs_obj, QgsProject.instance())

        # 2) Ler origens, preservando a feição original para gravar o resultado nela
        origin_features = []
        origin_points = []
        feedback.pushInfo(self.tr("Lendo origens..."))
        for feature in origins_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            origin_features.append(feature)
            origin_points.append(transform_origin.transform(geom.asPoint()))

        if not origin_points:
            raise QgsProcessingException(self.tr("Nenhuma origem válida encontrada na camada de origem."))

        # 3) Ler destinos e pesos (peso default 1.0 quando o campo não é informado)
        dest_points = []
        dest_weights = []
        feedback.pushInfo(self.tr("Lendo destinos e pesos..."))
        for feature in destinations_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            weight = feature.attribute(weight_field_index) if weight_field_index >= 0 else 1.0
            if weight is None:
                weight = 1.0
            dest_points.append(transform_dest.transform(geom.asPoint()))
            dest_weights.append(float(weight))

        if not dest_points:
            raise QgsProcessingException(self.tr("Nenhum destino válido encontrado na camada de destinos."))

        # 4) Construir o grafo, amarrando origens e destinos como vértices
        feedback.pushInfo(self.tr("Construindo o grafo a partir da rede viária..."))
        tie_points = origin_points + dest_points
        try:
            res = build_graph(network_layer, target_crs=target_crs_obj, points=tie_points)
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))

        graph = res["graph"]
        snapped_points = res["snapped_points"]

        if graph is None or graph.vertexCount() < 2:
            raise QgsProcessingException(
                self.tr("O grafo construído possui menos de 2 vértices. Não é possível calcular a acessibilidade.")
            )

        snapped_origins = snapped_points[:len(origin_points)]
        snapped_dests = snapped_points[len(origin_points):]

        origin_vertices = [graph.findVertex(pt) for pt in snapped_origins]
        dest_vertices = [graph.findVertex(pt) for pt in snapped_dests]

        if any(v == -1 for v in origin_vertices):
            raise QgsProcessingException(self.tr("Não foi possível amarrar uma ou mais origens à rede viária."))
        if any(v == -1 for v in dest_vertices):
            raise QgsProcessingException(self.tr("Não foi possível amarrar um ou mais destinos à rede viária."))

        # 5) Matriz OD (com cache em disco) entre origens e destinos
        feedback.pushInfo(self.tr("Calculando matriz de distâncias origem-destino..."))
        try:
            distances = compute_od_matrix(
                graph, origin_vertices, dest_vertices,
                cache_id="gravity_accessibility", feedback=feedback
            )
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao calcular a matriz OD: {}").format(str(exc)))

        # 6) Calcular a acessibilidade gravitacional de cada origem chamando a função core
        try:
            scores = gravity_accessibility(distances, dest_weights, beta)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        # 7) Gravar o resultado como novo campo numa cópia da camada de origem
        out_fields = origins_source.fields()
        out_fields.append(QgsField("acess_gravit", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            origins_source.wkbType(), origins_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        for feature, score in zip(origin_features, scores):
            out_feature = QgsFeature(out_fields)
            out_feature.setGeometry(feature.geometry())
            out_feature.setAttributes(feature.attributes() + [score])
            sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

        feedback.pushInfo(
            self.tr("Acessibilidade gravitacional calculada para {count} origem(ns).").format(count=len(scores))
        )
        feedback.setProgress(100)

        return {self.OUTPUT: dest_id}

    def name(self):
        return "urban_gravity_accessibility"

    def displayName(self):
        return self.tr("Acessibilidade Gravitacional Urbana")

    def group(self):
        return self.tr("Indicadores Urbanos")

    def groupId(self):
        return "urban"

    def shortHelpString(self):
        return self.tr(
            "Calcula a acessibilidade gravitacional de cada origem (ex.: centroides de setor) a uma "
            "camada de destinos ponderados (ex.: POIs, comércio, empregos), usando caminhos mínimos "
            "sobre a rede viária urbana.\n\n"
            "Parâmetros:\n"
            "- Camada de rede viária: feições de linha representando as vias.\n"
            "- Camada de origem: feições de ponto (ex.: centroides de setor, saída do indicador de "
            "densidade de demanda).\n"
            "- Camada de destinos (POIs): feições de ponto com os destinos.\n"
            "- Campo de peso/atratividade do destino: campo numérico opcional (default 1 para todos os destinos).\n"
            "- Beta: parâmetro de decaimento por distância do modelo gravitacional (default 2.0).\n\n"
            "Retorno:\n"
            "- Cópia da camada de origem com o campo 'acess_gravit' (índice de acessibilidade gravitacional)."
        )

    def createInstance(self):
        return UrbanGravityAccessibility()
