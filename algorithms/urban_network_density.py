# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo de densidade de rede viária urbana.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingOutputNumber,
    QgsDistanceArea
)

from ..core.indicators.urban import network_density


class UrbanNetworkDensity(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a densidade de rede viária (km/km²).

    Referência Bibliográfica da Técnica:
        Handy, S. L., & Clifton, K. J. (2001). Evaluating neighborhood accessibility:
        Possibilities and limitations. Journal of Transportation and Statistics, 4(2/3), 67-78.

    Limite de Complexidade:
        Complexidade de Tempo: O(N + M) onde N é o número total de trechos da rede viária
        e M é o número de feições da camada de polígono.
        Complexidade de Espaço: O(1)
        Testado com redes de até 1.000.000 de trechos de via (cálculo instantâneo).
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    INPUT_AREA = 'INPUT_AREA'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("UrbanNetworkDensity", string)

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
                self.INPUT_AREA,
                self.tr("Camada de área de referência (Polígonos)"),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT,
                self.tr("Densidade da rede viária (km/km²)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_source = self.parameterAsSource(parameters, self.INPUT_NETWORK, context)
        area_source = self.parameterAsSource(parameters, self.INPUT_AREA, context)

        if network_source is None:
            raise QgsProcessingException(self.tr("Camada de rede viária inválida."))
        if area_source is None:
            raise QgsProcessingException(self.tr("Camada de área de referência inválida."))

        # 1) Calcular a extensão total da rede em metros
        total_length_m = 0.0
        da_network = QgsDistanceArea()
        da_network.setSourceCrs(network_source.sourceCrs(), context.transformContext())
        da_network.setEllipsoid(network_source.sourceCrs().ellipsoidAcronym())

        # Feedback/Progress
        feedback.pushInfo(self.tr("Calculando a extensão total da rede viária..."))
        features_network = network_source.getFeatures()
        for feature in features_network:
            if feedback.isCanceled():
                break
            geom = feature.geometry()
            if geom and not geom.isEmpty():
                total_length_m += da_network.measureLength(geom)

        feedback.setProgress(50)

        # 2) Calcular a área total do polígono em metros quadrados
        total_area_m2 = 0.0
        da_area = QgsDistanceArea()
        da_area.setSourceCrs(area_source.sourceCrs(), context.transformContext())
        da_area.setEllipsoid(area_source.sourceCrs().ellipsoidAcronym())

        feedback.pushInfo(self.tr("Calculando a área total do polígono de referência..."))
        features_area = area_source.getFeatures()
        for feature in features_area:
            if feedback.isCanceled():
                break
            geom = feature.geometry()
            if geom and not geom.isEmpty():
                total_area_m2 += da_area.measureArea(geom)

        feedback.setProgress(80)

        # Converter a área para km²
        area_km2 = total_area_m2 / 1000000.0

        if area_km2 <= 0:
            raise QgsProcessingException(
                self.tr("A área calculada é de 0 km² ou negativa. Verifique a geometria de referência.")
            )

        # 3) Calcular a densidade chamando a função core
        try:
            density = network_density(total_length_m, area_km2)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("Comprimento da Rede: {length:.2f} m | Área: {area:.4f} km²").format(
                length=total_length_m, area=area_km2
            )
        )
        feedback.pushInfo(self.tr("Densidade Calculada: {density:.4f} km/km²").format(density=density))

        feedback.setProgress(100)

        return {self.OUTPUT: density}

    def name(self):
        return "urban_network_density"

    def displayName(self):
        return self.tr("Densidade de Rede Viária Urbana")

    def group(self):
        return self.tr("Indicadores Urbanos")

    def groupId(self):
        return "urban"

    def shortHelpString(self):
        return self.tr(
            "Calcula a densidade da rede viária em km de via por km² de área de referência.\n\n"
            "Parâmetros:\n"
            "- Camada de rede viária: feições de linha representando as vias.\n"
            "- Camada de área de referência: feições de polígono definindo a área territorial.\n\n"
            "Retorno:\n"
            "- Valor numérico contendo a densidade em km/km²."
        )

    def createInstance(self):
        return UrbanNetworkDensity()
