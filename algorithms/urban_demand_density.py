# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo de densidade de demanda urbana (população/km²)
por setor censitário.
"""

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink,
    QgsDistanceArea,
    QgsField,
    QgsFeature,
    QgsFeatureSink
)

from ..core import qgis_compat
from ..core.network.census_pipeline import fetch_census_tracts
from ..core.indicators.urban import demand_density


class UrbanDemandDensity(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a densidade de demanda (hab/km²) por setor
    censitário de um município, a partir dos setores + variáveis do censobr (via GisBR).

    Referência Bibliográfica da Técnica:
        Bertaud, A. (2004). The spatial organization of cities: Deliberate outcome or
        unforeseen consequence? Institute of Urban and Regional Development, UC Berkeley.

    Limite de Complexidade:
        Complexidade de Tempo: O(N) onde N é o número de setores censitários do município.
        Complexidade de Espaço: O(N) para o armazenamento das feições.
        Testado com municípios de até 10.000 setores censitários.
    """

    INPUT_CODE_MUNI = 'INPUT_CODE_MUNI'
    FIELD_POPULATION = 'FIELD_POPULATION'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("UrbanDemandDensity", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString(
                self.INPUT_CODE_MUNI,
                self.tr("Código IBGE do município (7 dígitos)")
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.FIELD_POPULATION,
                self.tr(
                    "Campo de população (ou domicílios/empregos) na camada do censobr "
                    "unida por gisbr:join_censo"
                )
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Setores censitários com densidade de demanda")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        code_muni = self.parameterAsString(parameters, self.INPUT_CODE_MUNI, context).strip()
        field_population = self.parameterAsString(parameters, self.FIELD_POPULATION, context).strip()

        if not code_muni:
            raise QgsProcessingException(self.tr("Código do município é obrigatório."))
        if not field_population:
            raise QgsProcessingException(self.tr("Campo de população é obrigatório."))

        feedback.pushInfo(self.tr("Obtendo setores censitários do município {}...").format(code_muni))
        try:
            tracts_layer = fetch_census_tracts(code_muni, feedback=feedback)
        except RuntimeError as exc:
            raise QgsProcessingException(str(exc))

        field_index = tracts_layer.fields().indexFromName(field_population)
        if field_index < 0:
            available = ", ".join(f.name() for f in tracts_layer.fields())
            raise QgsProcessingException(
                self.tr("Campo de população '{field}' não encontrado. Campos disponíveis: {available}").format(
                    field=field_population, available=available
                )
            )

        out_fields = tracts_layer.fields()
        out_fields.append(QgsField("dens_demanda_hab_km2", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            tracts_layer.wkbType(), tracts_layer.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        da_area = QgsDistanceArea()
        da_area.setSourceCrs(tracts_layer.sourceCrs(), context.transformContext())
        da_area.setEllipsoid(tracts_layer.sourceCrs().ellipsoidAcronym())

        feedback.pushInfo(self.tr("Calculando densidade de demanda por setor..."))
        total_features = tracts_layer.featureCount()
        count = 0
        for feature in tracts_layer.getFeatures():
            if feedback.isCanceled():
                return {}

            geom = feature.geometry()
            density = None
            if geom and not geom.isEmpty():
                area_km2 = da_area.measureArea(geom) / 1000000.0
                population = feature.attribute(field_index)
                if population is not None:
                    try:
                        density = demand_density(float(population), area_km2)
                    except ValueError as exc:
                        feedback.pushWarning(
                            self.tr("Setor {fid}: {error}").format(fid=feature.id(), error=str(exc))
                        )

            out_feature = QgsFeature(out_fields)
            out_feature.setGeometry(geom)
            out_feature.setAttributes(feature.attributes() + [density])
            sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

            count += 1
            if total_features > 0:
                feedback.setProgress(int((count / total_features) * 100))

        feedback.pushInfo(self.tr("Densidade de demanda calculada para {count} setor(es).").format(count=count))
        feedback.setProgress(100)

        return {self.OUTPUT: dest_id}

    def name(self):
        return "urban_demand_density"

    def displayName(self):
        return self.tr("Densidade de Demanda Urbana")

    def group(self):
        return self.tr("Indicadores Urbanos")

    def groupId(self):
        return "urban"

    def shortHelpString(self):
        return self.tr(
            "Calcula a densidade de demanda (população, domicílios ou empregos por km²) de cada "
            "setor censitário de um município, a partir dos setores + variáveis do censobr "
            "(gisbr:read_census_tract + gisbr:join_censo). Requer o plugin GisBR instalado.\n\n"
            "Parâmetros:\n"
            "- Código IBGE do município: código de 7 dígitos.\n"
            "- Campo de população: nome do campo de população/domicílios/empregos na camada "
            "unida pelo censobr (varia conforme o dataset do censobr).\n\n"
            "Retorno:\n"
            "- Cópia dos setores censitários com o campo 'dens_demanda_hab_km2'."
        )

    def createInstance(self):
        return UrbanDemandDensity()
