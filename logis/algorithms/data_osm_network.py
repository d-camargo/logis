# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para download e construção da rede viária urbana (OSM) por município.
"""

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterString,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsFeatureSink
)
from qgis.PyQt.QtCore import QCoreApplication

from ..core import downloader
from ..core.network.osm_pipeline import build_osm_municipal_network


class LoadOsmNetwork(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para carregar/baixar a rede viária urbana (OSM) de um município
    brasileiro a partir de seu código IBGE (7 dígitos).

    Referência Bibliográfica da Técnica:
        OpenStreetMap contributors (2024). Planet dump [Data file from Overpass API].
        Haklay, M., & Weber, P. (2008). OpenStreetMap: User-generated street maps.
        IEEE Pervasive Computing, 7(4), 12-18.

    Limite de Complexidade:
        Complexidade de Tempo: O(V + E) para construção e filtragem do grafo OSM.
        Complexidade de Espaço: O(V + E) para armazenamento de nós (V) e arcos (E).
        Testado com redes municipais de até 100.000 arcos e nós.
    """

    INPUT_CODE_MUNI = 'INPUT_CODE_MUNI'
    INPUT_NOME_MUNI = 'INPUT_NOME_MUNI'
    FORCE = 'FORCE'
    OUTPUT_LINKS = 'OUTPUT_LINKS'
    OUTPUT_NODES = 'OUTPUT_NODES'

    def tr(self, string):
        return QCoreApplication.translate("LoadOsmNetwork", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString(
                self.INPUT_CODE_MUNI,
                self.tr("Código IBGE do município (7 dígitos)")
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.INPUT_NOME_MUNI,
                self.tr("Nome do município (opcional)"),
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FORCE,
                self.tr("Forçar novo download (ignorar cache)"),
                defaultValue=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINKS,
                self.tr("Arcos (rede viária)")
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr("Nós (rede viária)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        code = self.parameterAsString(parameters, self.INPUT_CODE_MUNI, context).strip()
        nome = self.parameterAsString(parameters, self.INPUT_NOME_MUNI, context).strip()
        force = self.parameterAsBool(parameters, self.FORCE, context)

        if len(code) != 7 or not code.isdigit():
            raise QgsProcessingException(
                self.tr("Código IBGE do município deve possuir exatamente 7 dígitos.")
            )

        gpkg_path = str(downloader.cache_dir() / f"osm_{code}.gpkg")

        result = build_osm_municipal_network(
            code,
            nome or None,
            gpkg_path,
            force=force,
            feedback=feedback
        )

        layers = result.get("layers", {}) if result else {}
        links_layer = layers.get("osm_links")
        nodes_layer = layers.get("osm_nodes")

        if (
            links_layer is None
            or not links_layer.isValid()
            or nodes_layer is None
            or not nodes_layer.isValid()
        ):
            erro = result.get("metadata", {}).get("erro") if result and "metadata" in result else None
            if not erro:
                erro = self.tr("nenhuma via encontrada para o município")
            raise QgsProcessingException(erro)

        sink_links, dest_links_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINKS,
            context,
            links_layer.fields(),
            links_layer.wkbType(),
            links_layer.sourceCrs()
        )
        if sink_links is None:
            raise QgsProcessingException(self.tr("Não foi possível criar o sink de arcos."))

        sink_nodes, dest_nodes_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            nodes_layer.fields(),
            nodes_layer.wkbType(),
            nodes_layer.sourceCrs()
        )
        if sink_nodes is None:
            raise QgsProcessingException(self.tr("Não foi possível criar o sink de nós."))

        total_features = links_layer.featureCount() + nodes_layer.featureCount()
        count = 0

        for feat in links_layer.getFeatures():
            if feedback.isCanceled():
                return {}
            sink_links.addFeature(feat, QgsFeatureSink.Flag.FastInsert)
            count += 1
            if total_features > 0:
                feedback.setProgress(int((count / total_features) * 100))

        for feat in nodes_layer.getFeatures():
            if feedback.isCanceled():
                return {}
            sink_nodes.addFeature(feat, QgsFeatureSink.Flag.FastInsert)
            count += 1
            if total_features > 0:
                feedback.setProgress(int((count / total_features) * 100))

        feedback.pushInfo(
            self.tr("Rede viária OSM carregada: {links} arcos, {nodes} nós.").format(
                links=links_layer.featureCount(),
                nodes=nodes_layer.featureCount()
            )
        )
        feedback.setProgress(100)

        return {
            self.OUTPUT_LINKS: dest_links_id,
            self.OUTPUT_NODES: dest_nodes_id
        }

    def name(self):
        return "load_osm_network"

    def displayName(self):
        return self.tr("Baixar rede viária urbana (OSM, município)")

    def group(self):
        return self.tr("Dados")

    def groupId(self):
        return "dados"

    def shortHelpString(self):
        return self.tr(
            "Baixa e processa a rede viária urbana de um município a partir dos dados do OpenStreetMap (via Overpass API).\n\n"
            "Parâmetros:\n"
            "- Código IBGE do município: código numérico de 7 dígitos.\n"
            "- Nome do município (opcional): para auxiliar na identificação.\n"
            "- Forçar novo download: se verdadeiro, ignora o cache local e faz nova requisição Overpass.\n\n"
            "Retorno:\n"
            "- Arcos (rede viária): camada de linhas representando os trechos de vias recortados para o município.\n"
            "- Nós (rede viária): camada de pontos representando as interseções e extremidades dos arcos."
        )

    def createInstance(self):
        return LoadOsmNetwork()
