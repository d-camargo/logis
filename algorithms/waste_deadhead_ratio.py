# -*- coding: utf-8 -*-
"""
/***************************************************************************
 logis
                                A QGIS plugin
 Complemento do QGIS para apoiar projetos de logística no Brasil
                                -------------------
        begin                : 2026-07-21
        copyright            : (C) 2026 by Diego Camargo
        license              : GPL-3.0
 ***************************************************************************/
"""
"""
Algoritmo de processamento para cálculo da razão de deadhead em rotas de coleta de resíduos.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsFeatureSink,
    QgsWkbTypes
)

try:
    from ..core.indicators.waste import compute_deadhead_ratio
    from ..core import qgis_compat
except ImportError:
    from core.indicators.waste import compute_deadhead_ratio
    from core import qgis_compat


class WasteDeadheadRatio(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular os indicadores de deslocamento produtivo (coleta),
    improdutivo (deadhead/conector) e a razão de deadhead (deadhead_km / productive_km)
    para rotas de coleta de resíduos sólidos.

    Referência Bibliográfica da Técnica:
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.
        Beltrami, E. J., & Bodin, L. D. (1974). Networks and vehicle routing for municipal
        waste collection. Networks, 4(1), 65-94.

    Limite de Complexidade:
        Complexidade de Tempo: O(N), onde N é o número de trechos da camada de entrada.
        Complexidade de Espaço: O(N) para agrupamento e cálculo dos indicadores.
    """

    INPUT_ROUTES = 'INPUT_ROUTES'
    FIELD_DEADHEAD = 'FIELD_DEADHEAD'
    FIELD_ROUTE_ID = 'FIELD_ROUTE_ID'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteDeadheadRatio", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_ROUTES,
                self.tr("Camada de rotas/vias de coleta"),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_DEADHEAD,
                self.tr("Campo indicador de deadhead/improdutivo"),
                parentLayerParameterName=self.INPUT_ROUTES,
                type=QgsProcessingParameterField.Boolean,
                defaultValue='route_is_deadhead',
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_ROUTE_ID,
                self.tr("Campo de identificação da rota/setor (opcional)"),
                parentLayerParameterName=self.INPUT_ROUTES,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Razão de deadhead por rota")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        routes_source = self.parameterAsSource(parameters, self.INPUT_ROUTES, context)
        deadhead_field_name = self.parameterAsString(parameters, self.FIELD_DEADHEAD, context)
        route_id_field_name = self.parameterAsString(parameters, self.FIELD_ROUTE_ID, context)

        if routes_source is None:
            raise QgsProcessingException(self.tr("Camada de rotas de coleta inválida."))

        deadhead_idx = routes_source.fields().indexFromName(deadhead_field_name)
        if deadhead_idx == -1:
            raise QgsProcessingException(self.tr("Campo indicador de deadhead inválido."))

        route_id_idx = (
            routes_source.fields().indexFromName(route_id_field_name)
            if route_id_field_name
            else -1
        )

        feedback.pushInfo(self.tr("Lendo feições da camada e calculando comprimentos..."))

        lengths_km = []
        deadhead_flags = []
        route_ids = []

        for feature in routes_source.getFeatures():
            if feedback.isCanceled():
                return {}

            geom = feature.geometry()
            length_m = geom.length() if (geom and not geom.isEmpty()) else 0.0
            length_km = length_m / 1000.0

            is_dh = bool(feature.attribute(deadhead_idx)) if feature.attribute(deadhead_idx) is not None else False

            lengths_km.append(length_km)
            deadhead_flags.append(is_dh)

            if route_id_idx != -1:
                rid_val = feature.attribute(route_id_idx)
                route_ids.append(rid_val if rid_val is not None else 0)

        if not lengths_km:
            raise QgsProcessingException(
                self.tr("Nenhum trecho válido encontrado na camada de entrada.")
            )

        try:
            res = compute_deadhead_ratio(
                lengths_km=lengths_km,
                deadhead_flags=deadhead_flags,
                route_ids=route_ids if route_id_idx != -1 else None
            )
        except ValueError as exc:
            raise QgsProcessingException(
                self.tr("Erro ao calcular a razão de deadhead: {err}").format(err=str(exc))
            )

        out_fields = QgsFields()
        if route_id_idx != -1:
            rid_type = routes_source.fields().at(route_id_idx).type()
            out_fields.append(QgsField("route_id", rid_type))
        else:
            out_fields.append(QgsField("route_id", qgis_compat.field_type("string")))

        out_fields.append(QgsField("productive_km", qgis_compat.field_type("double")))
        out_fields.append(QgsField("deadhead_km", qgis_compat.field_type("double")))
        out_fields.append(QgsField("deadhead_ratio", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            QgsWkbTypes.NoGeometry, routes_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        routes_data = res["routes"]
        total_routes = len(routes_data)
        completed = 0

        for rid, data in routes_data.items():
            if feedback.isCanceled():
                return {}

            rid_display = rid if rid is not None else "Total"
            prod_km = data["productive_km"]
            dh_km = data["deadhead_km"]
            ratio = data["deadhead_ratio"]

            feedback.pushInfo(
                self.tr(
                    "Rota '{rid}': {prod:.2f} km produtivos | {dh:.2f} km deadhead | Razão: {ratio}"
                ).format(
                    rid=rid_display,
                    prod=prod_km,
                    dh=dh_km,
                    ratio=f"{ratio * 100.0:.1f}%" if ratio is not None else "N/A"
                )
            )

            out_feat = QgsFeature(out_fields)
            out_feat.setAttributes([
                rid_display,
                prod_km,
                dh_km,
                ratio
            ])
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

            completed += 1
            feedback.setProgress(int((completed / total_routes) * 100))

        tot = res["total"]
        if route_id_idx != -1 and len(routes_data) > 1:
            feedback.pushInfo(
                self.tr(
                    "Total acumulado de todas as rotas: {prod:.2f} km produtivos | "
                    "{dh:.2f} km deadhead | Razão total: {ratio}"
                ).format(
                    prod=tot["productive_km"],
                    dh=tot["deadhead_km"],
                    ratio=f"{(tot['deadhead_ratio'] or 0.0) * 100.0:.1f}%" if tot["deadhead_ratio"] is not None else "N/A"
                )
            )

            total_feat = QgsFeature(out_fields)
            total_feat.setAttributes([
                None,
                tot["productive_km"],
                tot["deadhead_km"],
                tot["deadhead_ratio"]
            ])
            sink.addFeature(total_feat, QgsFeatureSink.FastInsert)

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_deadhead_ratio"

    def displayName(self):
        return self.tr("Razão de Deadhead por Rota")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Calcula a extensão de deslocamento produtivo (coleta), improdutivo (deadhead/conector) "
            "e a razão de deadhead (deadhead_km / productive_km) para cada rota de coleta e no total.\n\n"
            "Parâmetros:\n"
            "- Camada de rotas/vias de coleta: feições de linha (ex.: saídas de "
            "logis:waste_cpp_route, logis:waste_rpp_route ou logis:waste_carp_route).\n"
            "- Campo indicador de deadhead (obrigatório): campo booleano onde True indica "
            "trecho de deadhead/deslocamento improdutivo (default: 'route_is_deadhead').\n"
            "- Campo de identificação da rota/setor (opcional): se informado, calcula a razão "
            "separadamente para cada rota/setor; se omitido, calcula para a camada inteira.\n\n"
            "Retorno:\n"
            "- Tabela sem geometria com uma feição por rota: 'route_id', 'productive_km' "
            "(extensão de coleta), 'deadhead_km' (extensão improdutiva) e 'deadhead_ratio' "
            "(razão deadhead_km / productive_km). Quando há mais de uma rota, uma feição "
            "adicional com 'route_id' nulo traz o total agregado de todas as rotas."
        )

    def createInstance(self):
        return WasteDeadheadRatio()
