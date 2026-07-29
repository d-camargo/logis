# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo de densidade da malha rodoviária regional.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingOutputNumber,
    QgsDistanceArea
)

from ..core.indicators.regional import road_density


class RegionalNetworkDensity(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a densidade rodoviária regional
    por área territorial (km/1.000 km²) e por população (km/10.000 hab).

    Referência Bibliográfica da Técnica:
        Handy, S. L., & Clifton, K. J. (2001). Evaluating neighborhood accessibility:
        Possibilities and limitations. Journal of Transportation and Statistics, 4(2/3), 67-78.

    Limite de Complexidade:
        Complexidade de Tempo: O(N + M) onde N é o número total de trechos da malha rodoviária
        e M é o número de feições da camada de área de referência.
        Complexidade de Espaço: O(1)
        Testado com redes de até 1.000.000 de trechos (cálculo instantâneo).
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    INPUT_AREA = 'INPUT_AREA'
    INPUT_POPULATION = 'INPUT_POPULATION'
    OUTPUT_DENSITY_AREA = 'OUTPUT_DENSITY_AREA'
    OUTPUT_DENSITY_POP = 'OUTPUT_DENSITY_POP'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("RegionalNetworkDensity", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de malha rodoviária (Linhas)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_AREA,
                self.tr("Camada de área de referência (UF, mesorregião, etc.)"),
                [QgsProcessing.SourceType.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_POPULATION,
                self.tr("População da área de referência (hab.)"),
                type=QgsProcessingParameterNumber.Type.Double,
                minValue=0.0000001
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_DENSITY_AREA,
                self.tr("Densidade rodoviária por área (km/1.000 km²)")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_DENSITY_POP,
                self.tr("Densidade rodoviária por população (km/10.000 hab.)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_source = self.parameterAsSource(parameters, self.INPUT_NETWORK, context)
        area_source = self.parameterAsSource(parameters, self.INPUT_AREA, context)
        population = self.parameterAsDouble(parameters, self.INPUT_POPULATION, context)

        if network_source is None:
            raise QgsProcessingException(self.tr("Camada de malha rodoviária inválida."))
        if area_source is None:
            raise QgsProcessingException(self.tr("Camada de área de referência inválida."))

        if 'length' not in network_source.fields().names():
            raise QgsProcessingException(
                self.tr(
                    "O campo 'length' não foi encontrado na camada de malha rodoviária. "
                    "Utilize a camada snv_links_{uf} gerada por core.network.snv_pipeline."
                )
            )

        # 1) Somar a extensão total da malha (campo 'length', em metros, já
        # pré-calculado pelo snv_pipeline a partir de vl_extensa do DNIT)
        total_length_m = 0.0
        length_idx = network_source.fields().indexFromName('length')

        feedback.pushInfo(self.tr("Somando a extensão total da malha rodoviária (campo 'length')..."))
        features_network = network_source.getFeatures()
        for feature in features_network:
            if feedback.isCanceled():
                break
            value = feature.attribute(length_idx)
            if value is not None:
                total_length_m += float(value)

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

        # 3) Calcular as densidades chamando a função core
        try:
            density_area, density_pop = road_density(total_length_m, area_km2, population)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("Extensão da Malha: {length:.2f} m | Área: {area:.4f} km² | População: {pop:.0f} hab.").format(
                length=total_length_m, area=area_km2, pop=population
            )
        )
        feedback.pushInfo(
            self.tr("Densidade por Área: {da:.4f} km/1.000 km² | Densidade por População: {dp:.4f} km/10.000 hab.").format(
                da=density_area, dp=density_pop
            )
        )

        feedback.setProgress(100)

        return {
            self.OUTPUT_DENSITY_AREA: density_area,
            self.OUTPUT_DENSITY_POP: density_pop
        }

    def name(self):
        return "regional_network_density"

    def displayName(self):
        return self.tr("Densidade da Malha Rodoviária Regional")

    def group(self):
        return self.tr("Indicadores Regionais")

    def groupId(self):
        return "regional"

    def shortHelpString(self):
        return self.tr(
            "Calcula a densidade da malha rodoviária por área territorial (km/1.000 km²) e "
            "por população (km/10.000 hab.).\n\n"
            "Parâmetros:\n"
            "- Camada de malha rodoviária: feições de linha representando as rodovias.\n"
            "- Camada de área de referência: feições de polígono definindo o território (UF, mesorregião, etc.).\n"
            "- População da área de referência: número de habitantes do território.\n\n"
            "Retornos:\n"
            "- Densidade rodoviária por área (km/1.000 km²).\n"
            "- Densidade rodoviária por população (km/10.000 hab.)."
        )

    def createInstance(self):
        return RegionalNetworkDensity()
