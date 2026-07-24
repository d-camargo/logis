# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo da circuidade média da rede viária urbana.
"""

import random
import math

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingOutputNumber
)
from qgis.analysis import QgsGraphAnalyzer

from ..core.network.graph_builder import build_graph
from ..core.indicators.urban import mean_circuity


class UrbanMeanCircuity(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a circuidade média de uma rede viária urbana.

    Referência Bibliográfica da Técnica:
        Giacomin, C., & Levinson, D. (2015). Road network circuity in metro areas.
        Environment and Planning B: Planning and Design, 42(6), 1040-1053.

    Limite de Complexidade:
        Complexidade de Tempo: O(S * (E + V log V)) onde S é o número de origens Dijkstra executadas
        (S <= NUM_SAMPLES), V é o número de vértices e E é o número de arestas do grafo.
        Complexidade de Espaço: O(V + E) para armazenamento do grafo em memória.
        Testado com redes de até 50.000 arestas e 40.000 vértices (cálculo em poucos segundos).
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    NUM_SAMPLES = 'NUM_SAMPLES'
    MIN_DISTANCE = 'MIN_DISTANCE'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("UrbanMeanCircuity", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de rede viária (Linhas)"),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NUM_SAMPLES,
                self.tr("Número de amostras (pares OD)"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1000,
                minValue=1
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_DISTANCE,
                self.tr("Distância euclidiana mínima (metros)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=100.0,
                minValue=0.0
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT,
                self.tr("Circuidade média")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        num_samples = self.parameterAsInt(parameters, self.NUM_SAMPLES, context)
        min_distance = self.parameterAsDouble(parameters, self.MIN_DISTANCE, context)

        if network_layer is None or not network_layer.isValid():
            raise QgsProcessingException(self.tr("Camada de rede viária inválida."))

        feedback.pushInfo(self.tr("Construindo o grafo a partir da rede viária..."))
        try:
            res = build_graph(network_layer)
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))

        graph = res["graph"]
        num_vertices = graph.vertexCount()

        if graph is None or num_vertices < 2:
            raise QgsProcessingException(
                self.tr("O grafo construído possui menos de 2 vértices. Não é possível calcular a circuidade.")
            )

        feedback.pushInfo(
            self.tr("Grafo construído: {v} vértices, {e} arestas.").format(
                v=num_vertices, e=graph.edgeCount()
            )
        )

        feedback.pushInfo(self.tr("Amostrando pares de pontos para o cálculo da circuidade..."))

        # Determinar origens aleatórias
        all_vertices = list(range(num_vertices))
        random.shuffle(all_vertices)

        network_distances = []
        euclidean_distances = []

        for u in all_vertices:
            if feedback.isCanceled():
                break

            if len(network_distances) >= num_samples:
                break

            # Executa Dijkstra a partir da origem u usando a estratégia de distância (índice 0)
            tree, costs = QgsGraphAnalyzer.dijkstra(graph, u, 0)

            # Amostra destinos aleatórios para esta origem
            # Para evitar viés de correlação de uma única origem, limitamos o número de destinos
            # a partir da mesma origem, mas permitimos que complete se necessário.
            max_dest_per_origin = min(50, num_vertices - 1)
            dests = random.sample(all_vertices, max_dest_per_origin)

            pt_u = graph.vertex(u).point()

            for v in dests:
                if len(network_distances) >= num_samples:
                    break

                if v == u:
                    continue

                pt_v = graph.vertex(v).point()
                euc_dist = pt_u.distance(pt_v)

                if euc_dist < min_distance:
                    continue

                net_dist = costs[v]

                # QGIS dijkstra usa valores enormes (ex: 1e30 ou inf) para vértices inacessíveis
                if math.isinf(net_dist) or net_dist > 1e18:
                    continue

                network_distances.append(net_dist)
                euclidean_distances.append(euc_dist)

            # Atualizar progresso com base na quantidade de amostras coletadas
            progress = int((len(network_distances) / num_samples) * 100)
            feedback.setProgress(min(99, progress))

        if feedback.isCanceled():
            return {}

        if not network_distances:
            raise QgsProcessingException(
                self.tr(
                    "Não foi possível encontrar nenhum par de pontos válido que satisfaça "
                    "a distância mínima de {min_dist} metros."
                ).format(min_dist=min_distance)
            )

        feedback.pushInfo(
            self.tr("Calculando circuidade média com {count} amostras válidas...").format(
                count=len(network_distances)
            )
        )

        try:
            circuity = mean_circuity(network_distances, euclidean_distances)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(self.tr("Circuidade média calculada: {circuity:.4f}").format(circuity=circuity))
        feedback.setProgress(100)

        return {self.OUTPUT: circuity}

    def name(self):
        return "urban_mean_circuity"

    def displayName(self):
        return self.tr("Circuidade Média de Rede Viária Urbana")

    def group(self):
        return self.tr("Indicadores Urbanos")

    def groupId(self):
        return "urban"

    def shortHelpString(self):
        return self.tr(
            "Calcula a circuidade média de uma rede viária urbana a partir de amostras de caminhos mínimos.\n\n"
            "Parâmetros:\n"
            "- Camada de rede viária: feições de linha representando as vias.\n"
            "- Número de amostras (pares OD): número de caminhos a amostrar (default 1000).\n"
            "- Distância euclidiana mínima: distância mínima em metros entre origem e destino (default 100m).\n\n"
            "Retorno:\n"
            "- Valor numérico contendo a circuidade média (distância rede / distância euclidiana)."
        )

    def createInstance(self):
        return UrbanMeanCircuity()
