# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo de percentual de pavimentação e duplicação regional.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingOutputNumber
)

from ..core.indicators.regional import paved_duplicated_share


class RegionalPavementPercentage(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular o percentual da malha rodoviária regional
    que é pavimentada e o percentual que é duplicada.

    Referência Bibliográfica da Técnica:
        Confederação Nacional do Transporte. (2024). Pesquisa CNT de Rodovias.

    Limite de Complexidade:
        Complexidade de Tempo: O(N) onde N é o número total de trechos da malha rodoviária.
        Complexidade de Espaço: O(1)
        Testado com redes de até 1.000.000 de trechos (cálculo instantâneo).
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    FIELD_SURFACE = 'FIELD_SURFACE'
    OUTPUT_PCT_PAVED = 'OUTPUT_PCT_PAVED'
    OUTPUT_PCT_DUP = 'OUTPUT_PCT_DUP'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("RegionalPavementPercentage", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de malha rodoviária (Linhas)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_SURFACE,
                self.tr("Campo que indica o tipo de superfície (ex: 'ds_superfi')"),
                defaultValue='ds_superfi',
                parentLayerParameterName=self.INPUT_NETWORK,
                type=QgsProcessingParameterField.Any,
                optional=True
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_PCT_PAVED,
                self.tr("Percentual de vias pavimentadas (%)")
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_PCT_DUP,
                self.tr("Percentual de vias duplicadas (%)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_source = self.parameterAsSource(parameters, self.INPUT_NETWORK, context)
        field_surface = self.parameterAsString(parameters, self.FIELD_SURFACE, context)

        if network_source is None:
            raise QgsProcessingException(self.tr("Camada de malha rodoviária inválida."))

        if not field_surface:
            field_surface = 'ds_superfi'

        fields_names = network_source.fields().names()
        if field_surface not in fields_names:
            raise QgsProcessingException(
                self.tr("O campo '{field}' não foi encontrado na camada de malha rodoviária. Campos disponíveis: {fields}").format(
                    field=field_surface, fields=", ".join(fields_names)
                )
            )
        if 'length' not in fields_names:
            raise QgsProcessingException(
                self.tr(
                    "O campo 'length' não foi encontrado na camada de malha rodoviária. "
                    "Utilize a camada snv_links_{uf} gerada por core.network.snv_pipeline."
                )
            )

        # 1) Somar as extensões total, pavimentada e duplicada (campo 'length',
        # em metros, já pré-calculado pelo snv_pipeline a partir de vl_extensa do DNIT)
        total_length_m = 0.0
        paved_length_m = 0.0
        duplicated_length_m = 0.0

        feedback.pushInfo(self.tr("Somando as extensões da malha rodoviária (campo 'length')..."))
        length_idx = network_source.fields().indexFromName('length')
        field_idx = network_source.fields().indexFromName(field_surface)

        for feature in network_source.getFeatures():
            if feedback.isCanceled():
                break
            value = feature.attribute(length_idx)
            length = float(value) if value is not None else 0.0
            total_length_m += length

            attr_val = feature.attribute(field_idx)
            val = str(attr_val).lower().strip() if attr_val is not None else ""

            if "duplicada" in val:
                paved_length_m += length
                duplicated_length_m += length
            elif "pavimentada" in val:
                paved_length_m += length

        if total_length_m <= 0:
            raise QgsProcessingException(
                self.tr("O comprimento total da malha é de 0 metros ou menor. Verifique as feições da camada de entrada.")
            )

        feedback.setProgress(80)

        # 2) Calcular os percentuais chamando a função core
        try:
            pct_paved, pct_dup = paved_duplicated_share(total_length_m, paved_length_m, duplicated_length_m)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("Extensão Total: {total:.2f} m | Pavimentada: {paved:.2f} m | Duplicada: {dup:.2f} m").format(
                total=total_length_m, paved=paved_length_m, dup=duplicated_length_m
            )
        )
        feedback.pushInfo(
            self.tr("Percentual Pavimentada: {p_paved:.2f}% | Percentual Duplicada: {p_dup:.2f}%").format(
                p_paved=pct_paved, p_dup=pct_dup
            )
        )

        feedback.setProgress(100)

        return {
            self.OUTPUT_PCT_PAVED: pct_paved,
            self.OUTPUT_PCT_DUP: pct_dup
        }

    def name(self):
        return "regional_pavement_percentage"

    def displayName(self):
        return self.tr("Percentual de Pavimentação e Duplicação")

    def group(self):
        return self.tr("Indicadores Regionais")

    def groupId(self):
        return "regional"

    def shortHelpString(self):
        return self.tr(
            "Calcula o percentual da malha rodoviária regional que é pavimentada e o "
            "percentual que é duplicada.\n\n"
            "Parâmetros:\n"
            "- Camada de malha rodoviária: feições de linha representando as rodovias.\n"
            "- Campo de superfície: o atributo que armazena a superfície física (ex: 'ds_superfi').\n\n"
            "Retornos:\n"
            "- Percentual da malha pavimentada (%).\n"
            "- Percentual da malha duplicada (%)."
        )

    def createInstance(self):
        return RegionalPavementPercentage()
