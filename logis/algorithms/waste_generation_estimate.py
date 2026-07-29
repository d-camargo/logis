# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para estimativa de geração de resíduos sólidos por trecho de via.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsField,
    QgsFeature,
    QgsFeatureSink
)

from ..core import qgis_compat
from ..core.indicators.waste import sector_waste_generation, allocate_generation_by_street_length


class WasteGenerationEstimate(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para estimar a geração de resíduos sólidos (em kg/dia) por
    trecho de via de coleta, a partir da população de cada setor e do rateio proporcional
    ao comprimento dos trechos de via associados a esse setor.

    A camada de vias deve chegar com um campo de identificação do setor (`sector_id`) já
    preenchido, associando cada trecho ao setor a que pertence (ex.: via
    `native:joinbylocation`, executado previamente pelo usuário fora deste algorithm).

    Referência Bibliográfica da Técnica:
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.
        SNIS - Sistema Nacional de Informações sobre Saneamento (faixa nacional ~0,9-1,0 kg/hab/dia).
        Ghose, M. K., Dikshit, A. K., & Sharma, S. K. (2006). A GIS based transportation
        model for solid waste disposal – A case study on Asansol municipality.
        Waste Management, 26(11), 1287-1293.

    Limite de Complexidade:
        Complexidade de Tempo: O(S + V) onde S é o número de setores e V o número de trechos de via.
        Complexidade de Espaço: O(S + V) para o agrupamento de trechos por setor.
        Testado com camadas de até 100.000 trechos de via (cálculo instantâneo).
    """

    INPUT_SECTORS = 'INPUT_SECTORS'
    FIELD_SECTOR_ID = 'FIELD_SECTOR_ID'
    FIELD_POPULATION = 'FIELD_POPULATION'
    INPUT_STREETS = 'INPUT_STREETS'
    FIELD_STREET_SECTOR_ID = 'FIELD_STREET_SECTOR_ID'
    PER_CAPITA_KG_DAY = 'PER_CAPITA_KG_DAY'
    COVERAGE_FRACTION = 'COVERAGE_FRACTION'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteGenerationEstimate", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_SECTORS,
                self.tr("Camada de setores (população)"),
                [QgsProcessing.SourceType.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_SECTOR_ID,
                self.tr("Campo de identificação do setor"),
                type=QgsProcessingParameterField.Any,
                parentLayerParameterName=self.INPUT_SECTORS
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_POPULATION,
                self.tr("Campo de população (habitantes)"),
                type=QgsProcessingParameterField.Numeric,
                parentLayerParameterName=self.INPUT_SECTORS
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_STREETS,
                self.tr("Camada de vias (com setor já associado)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_STREET_SECTOR_ID,
                self.tr("Campo de identificação do setor na camada de vias"),
                type=QgsProcessingParameterField.Any,
                parentLayerParameterName=self.INPUT_STREETS
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PER_CAPITA_KG_DAY,
                self.tr("Geração per capita (kg/hab/dia)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.9,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.COVERAGE_FRACTION,
                self.tr("Fração de cobertura da coleta (0 a 1)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=1.0,
                minValue=0.0,
                maxValue=1.0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Vias com estimativa de geração de resíduos")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        sectors_source = self.parameterAsSource(parameters, self.INPUT_SECTORS, context)
        sector_id_field = self.parameterAsString(parameters, self.FIELD_SECTOR_ID, context)
        pop_field_name = self.parameterAsString(parameters, self.FIELD_POPULATION, context)
        streets_source = self.parameterAsSource(parameters, self.INPUT_STREETS, context)
        street_sector_id_field = self.parameterAsString(parameters, self.FIELD_STREET_SECTOR_ID, context)
        per_capita = self.parameterAsDouble(parameters, self.PER_CAPITA_KG_DAY, context)
        coverage_fraction = self.parameterAsDouble(parameters, self.COVERAGE_FRACTION, context)

        if sectors_source is None:
            raise QgsProcessingException(self.tr("Camada de setores inválida."))
        if streets_source is None:
            raise QgsProcessingException(self.tr("Camada de vias inválida."))

        sectors_pop_idx = sectors_source.fields().indexFromName(pop_field_name)
        if sectors_pop_idx < 0:
            raise QgsProcessingException(
                self.tr("Campo de população '{field}' não encontrado na camada de setores.").format(field=pop_field_name)
            )
        sectors_id_idx = sectors_source.fields().indexFromName(sector_id_field)
        if sectors_id_idx < 0:
            raise QgsProcessingException(
                self.tr("Campo de identificação do setor '{field}' não encontrado na camada de setores.").format(field=sector_id_field)
            )
        streets_sector_id_idx = streets_source.fields().indexFromName(street_sector_id_field)
        if streets_sector_id_idx < 0:
            raise QgsProcessingException(
                self.tr("Campo de identificação do setor '{field}' não encontrado na camada de vias.").format(field=street_sector_id_field)
            )

        # 1) Ler população por setor
        feedback.pushInfo(self.tr("Lendo população dos setores..."))
        population_by_sector = {}
        for feature in sectors_source.getFeatures():
            if feedback.isCanceled():
                return {}
            sector_key = feature.attribute(sectors_id_idx)
            pop_val = feature.attribute(sectors_pop_idx)
            if sector_key is None or pop_val is None:
                continue
            population_by_sector[str(sector_key)] = float(pop_val)

        # 2) Agrupar trechos de via por setor, preservando a feição original
        feedback.pushInfo(self.tr("Agrupando trechos de via por setor..."))
        streets_by_sector = {}
        for feature in streets_source.getFeatures():
            if feedback.isCanceled():
                return {}
            sector_key = feature.attribute(streets_sector_id_idx)
            if sector_key is None:
                feedback.pushWarning(
                    self.tr("Trecho {fid} sem setor associado — ignorado.").format(fid=feature.id())
                )
                continue
            streets_by_sector.setdefault(str(sector_key), []).append(feature)

        # 3) Calcular a geração por setor e ratear por comprimento de trecho
        waste_by_fid = {}
        for sector_key, street_features in streets_by_sector.items():
            if sector_key not in population_by_sector:
                feedback.pushWarning(
                    self.tr("Setor '{sector}' presente na camada de vias mas não encontrado na camada de setores — ignorado.").format(sector=sector_key)
                )
                continue

            total_generation_kg = sector_waste_generation(
                population_by_sector[sector_key], per_capita_kg_day=per_capita, coverage_fraction=coverage_fraction
            )
            lengths = [feature.geometry().length() for feature in street_features]
            allocations = allocate_generation_by_street_length(total_generation_kg, lengths)

            for feature, waste_kg in zip(street_features, allocations):
                waste_by_fid[feature.id()] = waste_kg

        # 4) Gravar a camada de vias de saída com o campo novo waste_kg_day
        out_fields = streets_source.fields()
        out_fields.append(QgsField("waste_kg_day", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            streets_source.wkbType(), streets_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        total_features = streets_source.featureCount()
        count = 0
        for feature in streets_source.getFeatures():
            if feedback.isCanceled():
                return {}

            waste_kg = waste_by_fid.get(feature.id(), 0.0)
            out_feature = QgsFeature(out_fields)
            out_feature.setGeometry(feature.geometry())
            out_feature.setAttributes(feature.attributes() + [waste_kg])
            sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

            count += 1
            if total_features > 0:
                feedback.setProgress(int((count / total_features) * 100))

        feedback.pushInfo(
            self.tr("Geração de resíduos estimada para {count} trecho(s) de via.").format(count=count)
        )
        feedback.setProgress(100)

        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_generation_estimate"

    def displayName(self):
        return self.tr("Estimativa de Geração de Resíduos Sólidos")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Estima a geração de resíduos sólidos (em kg/dia) por trecho de via, a partir da "
            "população de cada setor e do rateio proporcional ao comprimento dos trechos de via "
            "associados a esse setor.\n\n"
            "A camada de vias deve chegar com um campo de identificação do setor já preenchido "
            "(ex.: executando native:joinbylocation manualmente no QGIS antes deste algorithm, "
            "ou trazendo o campo de outra fonte) — este algorithm não faz nenhum spatial join.\n\n"
            "Parâmetros:\n"
            "- Camada de setores: feições de polígono representando os setores de coleta.\n"
            "- Campo de identificação do setor (setores): identifica cada setor.\n"
            "- Campo de população: população de cada setor.\n"
            "- Camada de vias: feições de linha representando os trechos de via a coletar.\n"
            "- Campo de identificação do setor (vias): associa cada trecho de via ao seu setor.\n"
            "- Geração per capita: taxa de geração diária por habitante em kg (default: 0.9 kg/hab/dia).\n"
            "- Fração de cobertura: fração da população do setor efetivamente coberta pela coleta (default: 1.0).\n\n"
            "Retorno:\n"
            "- Camada de vias com a nova coluna 'waste_kg_day', contendo a geração de resíduos "
            "rateada de cada trecho (kg/dia)."
        )

    def createInstance(self):
        return WasteGenerationEstimate()
