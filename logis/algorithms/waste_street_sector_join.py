# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para associar trechos de via a setores censitários.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink,
    QgsProcessingUtils,
    NULL,
)


class WasteStreetSectorJoin(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para associar espacialmente trechos de via (linhas)
    a setores censitários ou áreas de coleta (polígonos).

    Utiliza a operação nativa de sobreposição espacial do QGIS (`native:joinattributesbylocation`)
    configurada com método de maior sobreposição (METHOD=2, one-to-one largest overlap),
    garantindo que cada trecho de via seja associado exclusivamente ao setor onde possui
    maior extensão geográfica. Trechos que cruzam divisas não são duplicados, evitando
    dupla contagem de extensão ou de demanda, e trechos fora de qualquer setor recebem NULL
    sem serem descartados.

    Referência Bibliográfica da Técnica:
        Smith, M. J. de, Goodchild, M. F., & Longley, P. A. (2018). Geospatial Analysis:
        A Comprehensive Guide to Principles, Techniques and Software Tools (6th ed.).
        Winchelsea Press. (Seção sobre Point and Line in Polygon overlay e spatial join).
        Worboys, M., & Duckham, M. (2004). GIS: A Computing Perspective (2nd ed.).
        CRC Press.

    Limite de Complexidade:
        Complexidade de Tempo: O((V + S) log S) no pior caso, onde V é o número de
        trechos de via e S é o número de polígonos de setor, dominada pela indexação
        espacial R-Tree nativa do QGIS e pelo cálculo de interseção geométrica.
        Complexidade de Espaço: O(V) para a geração da camada resultante.
        Testado com camadas de até 100.000 trechos de via e centenas de setores
        censitários.
    """

    INPUT_STREETS = "INPUT_STREETS"
    INPUT_SECTORS = "INPUT_SECTORS"
    FIELD_SECTOR_ID = "FIELD_SECTOR_ID"
    OUTPUT = "OUTPUT"

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication

        return QCoreApplication.translate("WasteStreetSectorJoin", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_STREETS,
                self.tr("Camada de vias"),
                [QgsProcessing.SourceType.TypeVectorLine],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_SECTORS,
                self.tr("Camada de setores"),
                [QgsProcessing.SourceType.TypeVectorPolygon],
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_SECTOR_ID,
                self.tr("Campo de identificação do setor"),
                type=QgsProcessingParameterField.DataType.Any,
                parentLayerParameterName=self.INPUT_SECTORS,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Vias com setor associado"),
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        import processing

        streets_source = self.parameterAsSource(parameters, self.INPUT_STREETS, context)
        sectors_source = self.parameterAsSource(parameters, self.INPUT_SECTORS, context)
        sector_id_field = self.parameterAsString(parameters, self.FIELD_SECTOR_ID, context)

        if streets_source is None:
            raise QgsProcessingException(self.tr("Camada de vias inválida."))
        if sectors_source is None:
            raise QgsProcessingException(self.tr("Camada de setores inválida."))

        if sectors_source.fields().indexFromName(sector_id_field) < 0:
            raise QgsProcessingException(
                self.tr(
                    "Campo de identificação do setor '{field}' não encontrado na camada de setores."
                ).format(field=sector_id_field)
            )

        if streets_source.fields().indexFromName(sector_id_field) >= 0:
            raise QgsProcessingException(
                self.tr(
                    "A camada de vias já possui o campo '{field}'. "
                    "Utilize esse campo diretamente em vez de refazer a junção."
                ).format(field=sector_id_field)
            )

        streets_param = parameters[self.INPUT_STREETS]
        sectors_param = parameters[self.INPUT_SECTORS]
        output_dest = parameters.get(self.OUTPUT, "TEMPORARY_OUTPUT")

        child_params = {
            "INPUT": streets_param,
            "JOIN": sectors_param,
            "PREDICATE": [0],
            "JOIN_FIELDS": [sector_id_field],
            "METHOD": 2,
            "DISCARD_NONMATCHING": False,
            "PREFIX": "",
            "OUTPUT": output_dest,
        }

        if feedback is not None:
            feedback.pushInfo(self.tr("Executando junção espacial por maior sobreposição..."))

        res = processing.run(
            "native:joinattributesbylocation",
            child_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        dest_val = res.get("OUTPUT")
        if isinstance(dest_val, str):
            out_layer = QgsProcessingUtils.mapLayerFromString(dest_val, context)
            if out_layer is None and context is not None:
                out_layer = context.getMapLayer(dest_val)
        else:
            out_layer = dest_val

        if out_layer is not None:
            idx = out_layer.fields().indexFromName(sector_id_field)
            if idx >= 0:
                null_count = sum(
                    1
                    for feat in out_layer.getFeatures()
                    if feat.attribute(idx) is None or feat.attribute(idx) == NULL
                )
                if null_count > 0 and feedback is not None:
                    feedback.pushWarning(
                        self.tr(
                            "{count} trecho(s) de via ficaram sem setor associado (valor NULL)."
                        ).format(count=null_count)
                    )

        return {self.OUTPUT: dest_val}

    def name(self):
        return "waste_street_sector_join"

    def displayName(self):
        return self.tr("Associar Vias a Setores Censitários")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Associa espacialmente cada trecho de via ao setor censitário correspondente.\n\n"
            "A operação utiliza a sobreposição espacial com critério de maior sobreposição "
            "(um para um), garantindo que trechos que cruzam a divisa entre dois setores "
            "sejam atribuídos ao setor onde possuem maior extensão, sem duplicar feições "
            "nem distorcer o rateio de extensão.\n\n"
            "Trechos que estiverem fora de todos os setores recebem valor NULL no campo de "
            "setor, sem serem descartados da camada de saída.\n\n"
            "Parâmetros:\n"
            "- Camada de vias: linhas representando a malha viária a ser associada.\n"
            "- Camada de setores: polígonos representando os setores censitários ou áreas de coleta.\n"
            "- Campo de identificação do setor: campo da camada de setores que identifica unicamente cada setor.\n\n"
            "Retorno:\n"
            "- Camada de vias contendo todos os atributos originais mais o campo de identificação "
            "do setor preenchido conforme a sobreposição espacial."
        )

    def createInstance(self):
        return WasteStreetSectorJoin()
