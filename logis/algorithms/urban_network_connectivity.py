# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo de conectividade da rede viária urbana.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingOutputNumber
)

from ..core.network.graph_builder import build_graph
from ..core.indicators.urban import network_connectivity


class UrbanNetworkConnectivity(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a conectividade de rede viária urbana
    a partir de índices de teoria dos grafos (Alfa, Beta, Gama) e estrutura de nós.

    Referência Bibliográfica da Técnica:
        Rodrigue, J. P., Comtois, C., & Slack, B. (2013). The geography of transport systems. Routledge.

    Limite de Complexidade:
        Complexidade de Tempo: O(V + E) para construção do grafo e cálculo dos graus de nós,
        onde V é o número de vértices e E é o número de arestas do grafo.
        Complexidade de Espaço: O(V + E) para armazenar os graus e arestas únicas.
        Testado com redes de até 50.000 arestas e 40.000 vértices (cálculo instantâneo).
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    NUM_NODES = 'NUM_NODES'
    NUM_EDGES = 'NUM_EDGES'
    ALPHA = 'ALPHA'
    BETA = 'BETA'
    GAMMA = 'GAMMA'
    PCT_4_WAY = 'PCT_4_WAY'
    PCT_DEAD_ENDS = 'PCT_DEAD_ENDS'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("UrbanNetworkConnectivity", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de rede viária (Linhas)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.NUM_NODES,
                self.tr("Número de nós (v)")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.NUM_EDGES,
                self.tr("Número de arestas (e)")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.ALPHA,
                self.tr("Índice Alfa")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.BETA,
                self.tr("Índice Beta")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.GAMMA,
                self.tr("Índice Gama")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.PCT_4_WAY,
                self.tr("Percentual de interseções com grau 4 ou mais")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.PCT_DEAD_ENDS,
                self.tr("Percentual de becos sem saída")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)

        if network_layer is None or not network_layer.isValid():
            raise QgsProcessingException(self.tr("Camada de rede viária inválida."))

        feedback.pushInfo(self.tr("Construindo o grafo a partir da rede viária..."))
        
        try:
            res = build_graph(network_layer)
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))

        graph = res["graph"]

        if graph is None or graph.vertexCount() == 0:
            raise QgsProcessingException(self.tr("O grafo construído não possui vértices."))

        feedback.setProgress(40)
        feedback.pushInfo(self.tr("Calculando os graus dos nós..."))

        # Determinar os graus dos nós de forma não direcionada (grau físico)
        unique_edges = set()
        for i in range(graph.edgeCount()):
            if feedback.isCanceled():
                break
            edge = graph.edge(i)
            u = edge.fromVertex()
            v = edge.toVertex()
            unique_edges.add((min(u, v), max(u, v)))

        vertex_degrees = [0] * graph.vertexCount()
        for u, v in unique_edges:
            if feedback.isCanceled():
                break
            vertex_degrees[u] += 1
            vertex_degrees[v] += 1

        feedback.setProgress(70)

        if feedback.isCanceled():
            return {}

        feedback.pushInfo(self.tr("Calculando os indicadores de conectividade..."))

        try:
            v, e, alpha, beta, gamma, pct_4, pct_dead = network_connectivity(vertex_degrees)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("Nós (v): {v} | Arestas (e): {e}").format(v=v, e=e)
        )
        feedback.pushInfo(
            self.tr("Índices: Alfa={alpha:.4f} | Beta={beta:.4f} | Gama={gamma:.4f}").format(
                alpha=alpha, beta=beta, gamma=gamma
            )
        )
        feedback.pushInfo(
            self.tr("Interseções 4+ pernas: {pct_4:.2f}% | Becos sem saída: {pct_dead:.2f}%").format(
                pct_4=pct_4, pct_dead=pct_dead
            )
        )

        feedback.setProgress(100)

        return {
            self.NUM_NODES: v,
            self.NUM_EDGES: e,
            self.ALPHA: alpha,
            self.BETA: beta,
            self.GAMMA: gamma,
            self.PCT_4_WAY: pct_4,
            self.PCT_DEAD_ENDS: pct_dead
        }

    def name(self):
        return "urban_network_connectivity"

    def displayName(self):
        return self.tr("Conectividade de Rede Viária Urbana")

    def group(self):
        return self.tr("Indicadores Urbanos")

    def groupId(self):
        return "urban"

    def shortHelpString(self):
        return self.tr(
            "Calcula indicadores de conectividade para uma rede viária urbana a partir dos graus de seus nós.\n\n"
            "Parâmetros:\n"
            "- Camada de rede viária: feições de linha representando as vias.\n\n"
            "Retornos:\n"
            "- Número de nós (v)\n"
            "- Número de arestas (e)\n"
            "- Índice Alfa (0 a 1)\n"
            "- Índice Beta (links por nó)\n"
            "- Índice Gama (0 a 1)\n"
            "- Percentual de interseções com grau 4 ou mais (cruzamentos de 4 pernas)\n"
            "- Percentual de becos sem saída (grau 1)"
        )

    def createInstance(self):
        return UrbanNetworkConnectivity()
