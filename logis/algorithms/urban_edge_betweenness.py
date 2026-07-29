# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo da centralidade de intermediação (betweenness)
aproximada das arestas de uma rede viária urbana.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsWkbTypes
)
try:
    from ..core import qgis_compat
except ImportError:
    from core import qgis_compat

from ..core.network.graph_builder import build_graph
from ..core.network.betweenness import compute_edge_betweenness


class UrbanEdgeBetweenness(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a centralidade de intermediação (betweenness)
    aproximada das arestas de uma rede viária urbana, por amostragem de pares OD.

    Referência Bibliográfica da Técnica:
        Freeman, L. C. (1977). A set of measures of centrality based on betweenness.
        Sociometry, 40(1), 35-41.
        Brandes, U., & Pich, C. (2007). Centrality estimation in large networks.
        International Journal of Bifurcation and Chaos, 17(7), 2303-2318.

    Limite de Complexidade:
        Complexidade de Tempo: O(S * (E + V log V)) onde S é o número de origens distintas
        amostradas, V é o número de vértices e E é o número de arestas do grafo.
        Complexidade de Espaço: O(V + E).
        Testado com redes de até 50.000 arestas e 40.000 vértices (rede municipal grande típica).
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    NUM_SAMPLES = 'NUM_SAMPLES'
    SEED = 'SEED'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("UrbanEdgeBetweenness", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de rede viária (Linhas)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NUM_SAMPLES,
                self.tr("Número de amostras (pares OD)"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=1000,
                minValue=1
            )
        )
        seed_param = QgsProcessingParameterNumber(
            self.SEED,
            self.tr("Semente aleatória (opcional, para reprodutibilidade)"),
            type=QgsProcessingParameterNumber.Type.Integer,
            optional=True
        )
        self.addParameter(seed_param)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Arestas com centralidade de intermediação")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        num_samples = self.parameterAsInt(parameters, self.NUM_SAMPLES, context)

        seed = None
        if parameters.get(self.SEED) is not None:
            seed = self.parameterAsInt(parameters, self.SEED, context)

        if network_layer is None or not network_layer.isValid():
            raise QgsProcessingException(self.tr("Camada de rede viária inválida."))

        feedback.pushInfo(self.tr("Construindo o grafo a partir da rede viária..."))
        try:
            res = build_graph(network_layer)
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))

        graph = res["graph"]
        crs = res["crs"]

        if graph is None or graph.vertexCount() == 0 or graph.edgeCount() == 0:
            raise QgsProcessingException(self.tr("O grafo construído está vazio."))

        feedback.pushInfo(
            self.tr("Grafo construído: {v} vértices, {e} arestas.").format(
                v=graph.vertexCount(), e=graph.edgeCount()
            )
        )

        feedback.pushInfo(self.tr("Amostrando pares OD e calculando a centralidade de intermediação..."))
        try:
            scores = compute_edge_betweenness(graph, num_samples, criterion_num=0, seed=seed, feedback=feedback)
        except (ValueError, RuntimeError) as exc:
            raise QgsProcessingException(str(exc))

        if feedback.isCanceled():
            return {}

        fields = QgsFields()
        fields.append(QgsField("betweenness", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields, QgsWkbTypes.Type.LineString, crs
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        for edge_id in range(graph.edgeCount()):
            if feedback.isCanceled():
                break

            edge = graph.edge(edge_id)
            from_point = graph.vertex(edge.fromVertex()).point()
            to_point = graph.vertex(edge.toVertex()).point()

            feat = QgsFeature(fields)
            feat.setGeometry(QgsGeometry.fromPolylineXY([from_point, to_point]))
            feat.setAttributes([scores[edge_id]])
            sink.addFeature(feat)

        feedback.pushInfo(
            self.tr("Centralidade de intermediação máxima observada: {max_score:.4f}").format(
                max_score=max(scores) if scores else 0.0
            )
        )
        feedback.setProgress(100)

        return {self.OUTPUT: dest_id}

    def name(self):
        return "urban_edge_betweenness"

    def displayName(self):
        return self.tr("Centralidade de Intermediação de Arestas (Betweenness)")

    def group(self):
        return self.tr("Indicadores Urbanos")

    def groupId(self):
        return "urban"

    def shortHelpString(self):
        return self.tr(
            "Calcula a centralidade de intermediação (betweenness) aproximada de cada aresta "
            "de uma rede viária urbana, por amostragem de pares origem-destino e caminhos mínimos "
            "de Dijkstra.\n\n"
            "Parâmetros:\n"
            "- Camada de rede viária: feições de linha representando as vias.\n"
            "- Número de amostras (pares OD): número de pares a amostrar (default 1000).\n"
            "- Semente aleatória: opcional, para reprodutibilidade da amostragem.\n\n"
            "Retorno:\n"
            "- Camada de linhas com o campo 'betweenness' (0.0 a 1.0), uma feição por aresta do grafo."
        )

    def createInstance(self):
        return UrbanEdgeBetweenness()
