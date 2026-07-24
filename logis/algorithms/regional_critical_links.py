# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para identificação de pontes/arcos críticos (cut links)
da malha rodoviária regional — trechos cuja remoção desconecta a rede.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingOutputNumber,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant

from ..core.network.graph_builder import build_graph
from ..core.indicators.regional import find_critical_links


class RegionalCriticalLinks(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para identificar as pontes/arcos críticos (cut links)
    da malha rodoviária regional, indicando trechos sem rota alternativa.

    Referência Bibliográfica da Técnica:
        Tarjan, R. E. (1974). A note on finding the bridges of a graph.
        Information Processing Letters, 2(6), 160-161.

    Limite de Complexidade:
        Complexidade de Tempo: O(V + E) onde V é o número de vértices e E o número
        de arestas físicas (únicas) do grafo.
        Complexidade de Espaço: O(V + E).
        Testado com redes de até 1.000.000 de arestas e 500.000 vértices.
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    OUTPUT = 'OUTPUT'
    OUTPUT_NUM_CRITICAL_LINKS = 'OUTPUT_NUM_CRITICAL_LINKS'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("RegionalCriticalLinks", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de malha rodoviária (Linhas)"),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Trechos com indicação de ponte/arco crítico")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_NUM_CRITICAL_LINKS,
                self.tr("Número de pontes/arcos críticos identificados")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)

        if network_layer is None or not network_layer.isValid():
            raise QgsProcessingException(self.tr("Camada de malha rodoviária inválida."))

        feedback.pushInfo(self.tr("Construindo o grafo a partir da malha rodoviária..."))
        try:
            res = build_graph(network_layer)
        except Exception as exc:
            raise QgsProcessingException(self.tr("Erro ao construir o grafo: {}").format(str(exc)))

        graph = res["graph"]
        crs = res["crs"]

        if graph is None or graph.vertexCount() == 0 or graph.edgeCount() == 0:
            raise QgsProcessingException(self.tr("O grafo construído está vazio."))

        # O QgsGraph é dirigido: vias de mão dupla geram dois arcos (u->v e v->u)
        # para o mesmo trecho físico. Deduplica por par de vértices não ordenado,
        # mantendo o id do primeiro arco encontrado como representante geométrico.
        feedback.pushInfo(self.tr("Deduplicando arcos em arestas físicas únicas..."))
        seen_pairs = {}
        unique_edges = []
        representative_edge_ids = []
        for edge_id in range(graph.edgeCount()):
            if feedback.isCanceled():
                return {}
            edge = graph.edge(edge_id)
            u, v = edge.fromVertex(), edge.toVertex()
            key = (u, v) if u <= v else (v, u)
            if key in seen_pairs:
                continue
            seen_pairs[key] = edge_id
            unique_edges.append((u, v))
            representative_edge_ids.append(edge_id)

        feedback.setProgress(50)

        feedback.pushInfo(
            self.tr("Identificando pontes/arcos críticos ({n} arestas físicas)...").format(
                n=len(unique_edges)
            )
        )
        try:
            is_bridge = find_critical_links(unique_edges, graph.vertexCount())
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        fields = QgsFields()
        fields.append(QgsField("is_critical_link", QVariant.Bool))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields, QgsWkbTypes.LineString, crs
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        for idx, edge_id in enumerate(representative_edge_ids):
            if feedback.isCanceled():
                break

            edge = graph.edge(edge_id)
            from_point = graph.vertex(edge.fromVertex()).point()
            to_point = graph.vertex(edge.toVertex()).point()

            feat = QgsFeature(fields)
            feat.setGeometry(QgsGeometry.fromPolylineXY([from_point, to_point]))
            feat.setAttributes([bool(is_bridge[idx])])
            sink.addFeature(feat)

        num_bridges = sum(1 for b in is_bridge if b)
        feedback.pushInfo(
            self.tr("Pontes/arcos críticos identificados: {n} de {total} trechos.").format(
                n=num_bridges, total=len(unique_edges)
            )
        )
        feedback.setProgress(100)

        return {
            self.OUTPUT: dest_id,
            self.OUTPUT_NUM_CRITICAL_LINKS: num_bridges
        }

    def name(self):
        return "regional_critical_links"

    def displayName(self):
        return self.tr("Pontes/Arcos Críticos da Malha Regional")

    def group(self):
        return self.tr("Indicadores Regionais")

    def groupId(self):
        return "regional"

    def shortHelpString(self):
        return self.tr(
            "Identifica as pontes/arcos críticos (cut links) da malha rodoviária regional: "
            "trechos cuja remoção desconecta a rede, indicando ligações intermunicipais "
            "sem rota alternativa.\n\n"
            "Parâmetros:\n"
            "- Camada de malha rodoviária: feições de linha representando as rodovias.\n\n"
            "Retorno:\n"
            "- Camada de linhas com o campo 'is_critical_link' (booleano), uma feição por "
            "trecho físico único da malha.\n"
            "- Número de pontes/arcos críticos identificados."
        )

    def createInstance(self):
        return RegionalCriticalLinks()
