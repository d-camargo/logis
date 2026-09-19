# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para download e construção da rede viária federal (SNV/DNIT) por UF.
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
from ..core.ufs import siglas
from ..core.network.snv_pipeline import build_snv_state_network


class LoadSnvNetwork(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para carregar/baixar a rede viária federal (SNV/DNIT) de uma UF.

    Referência Bibliográfica da Técnica:
        DNIT (Departamento Nacional de Infraestrutura de Transportes). (2025).
        Sistema Rodoviário Nacional (SRN/SNV) - Especificações Técnicas. Brasília: DNIT.

    Limite de Complexidade:
        Complexidade de Tempo: O(N) onde N é o número de trechos de rodovias na UF.
        Complexidade de Espaço: O(N) para armazenamento de links e nós.
        Testado com malhas regionais de UFs de grande porte.
    """

    INPUT_UF = 'INPUT_UF'
    FORCE = 'FORCE'
    OUTPUT_LINKS = 'OUTPUT_LINKS'
    OUTPUT_NODES = 'OUTPUT_NODES'

    def tr(self, string):
        return QCoreApplication.translate("LoadSnvNetwork", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString(
                self.INPUT_UF,
                self.tr("Sigla da UF (2 letras)")
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
        uf_raw = self.parameterAsString(parameters, self.INPUT_UF, context)
        uf = uf_raw.strip().upper()
        force = self.parameterAsBool(parameters, self.FORCE, context)

        if uf not in siglas():
            raise QgsProcessingException(
                self.tr(f"UF inválida: {uf}")
            )

        gpkg_path = str(downloader.cache_dir() / f"snv_{uf}.gpkg")

        try:
            result = build_snv_state_network(uf, gpkg_path, force=force, feedback=feedback)
        except Exception as exc:
            raise QgsProcessingException(str(exc))

        layers = result.get("layers", {}) if result else {}
        links_layer = layers.get(f"snv_links_{uf}")
        nodes_layer = layers.get(f"snv_nodes_{uf}")

        if (
            links_layer is None
            or not links_layer.isValid()
            or nodes_layer is None
            or not nodes_layer.isValid()
        ):
            erro = result.get("metadata", {}).get("erro") if result and "metadata" in result else None
            if not erro:
                erro = self.tr(f"O SNV não devolveu dados para a UF {uf}.")
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
            self.tr("Rede viária SNV carregada: {links} arcos, {nodes} nós.").format(
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
        return "load_snv_network"

    def displayName(self):
        return self.tr("Baixar rede viária federal (SNV/DNIT, UF)")

    def group(self):
        return self.tr("Dados")

    def groupId(self):
        return "dados"

    def shortHelpString(self):
        return self.tr(
            "Baixa e processa a rede viária federal de uma UF a partir dos dados do SNV/DNIT.\n\n"
            "Parâmetros:\n"
            "- Sigla da UF (2 letras): sigla do estado brasileiro (ex.: MG, SP, RJ).\n"
            "- Forçar novo download: se verdadeiro, ignora o cache local e faz nova requisição.\n\n"
            "Retorno:\n"
            "- Arcos (rede viária): camada de linhas representando os trechos de rodovias federais/estaduais no estado.\n"
            "- Nós (rede viária): camada de pontos representando as interseções e extremidades dos arcos."
        )

    def createInstance(self):
        return LoadSnvNetwork()
