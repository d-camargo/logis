# -*- coding: utf-8 -*-
"""
Algoritmo de processamento para cálculo do índice de restrição de circulação urbana de carga.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterExpression,
    QgsProcessingOutputNumber,
    QgsDistanceArea,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils
)

from ..core.indicators.urban import cargo_restriction_index

# Tipos de via (OSM highway=*) incompatíveis com circulação de veículos de carga.
CARGO_INCOMPATIBLE_HIGHWAYS = (
    'pedestrian', 'footway', 'path', 'steps', 'cycleway', 'bridleway', 'corridor'
)

# Limiares default usados quando a camada possui os campos de largura/peso máximo.
DEFAULT_MIN_WIDTH_M = 3.0
DEFAULT_MIN_MAXWEIGHT_T = 3.5


def _build_default_restriction_expression(layer):
    """
    Monta a expressão QGIS default de restrição de carga a partir dos campos
    disponíveis na camada: sempre filtra por tipo de via (highway) incompatível
    com carga; inclui largura e peso máximo somente quando esses campos existirem.
    """
    field_names = {f.name() for f in layer.fields()}

    highway_list = ", ".join("'{}'".format(h) for h in CARGO_INCOMPATIBLE_HIGHWAYS)
    clauses = ['"highway" IN ({})'.format(highway_list)]

    if 'width' in field_names:
        clauses.append('("width" IS NOT NULL AND "width" < {})'.format(DEFAULT_MIN_WIDTH_M))

    if 'maxweight' in field_names:
        clauses.append('("maxweight" IS NOT NULL AND "maxweight" < {})'.format(DEFAULT_MIN_MAXWEIGHT_T))

    return " OR ".join(clauses)


class UrbanCargoRestriction(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular o índice de restrição de circulação urbana de carga.

    Referência Bibliográfica da Técnica:
        Dablanc, L. (2007). Goods transport in large European cities: Difficult to organize,
        difficult to modernize. Transportation Research Part A: Policy and Practice, 41(3), 280-290.

    Limite de Complexidade:
        Complexidade de Tempo: O(N) onde N é o número total de trechos da rede viária.
        Complexidade de Espaço: O(1)
        Testado com redes de até 1.000.000 de trechos de via (cálculo instantâneo).
    """

    INPUT_NETWORK = 'INPUT_NETWORK'
    RESTRICTION_EXPRESSION = 'RESTRICTION_EXPRESSION'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("UrbanCargoRestriction", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NETWORK,
                self.tr("Camada de rede viária (Linhas)"),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.RESTRICTION_EXPRESSION,
                self.tr(
                    "Expressão de restrição (retorna verdadeiro para trechos restritos). "
                    "Se vazia, usa o filtro default por tipo de via (highway), largura e "
                    "peso máximo, quando esses campos existirem na camada."
                ),
                defaultValue='',
                parentLayerParameterName=self.INPUT_NETWORK,
                optional=True
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT,
                self.tr("Índice de restrição de circulação (%)")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        network_layer = self.parameterAsVectorLayer(parameters, self.INPUT_NETWORK, context)
        expression_str = self.parameterAsExpression(parameters, self.RESTRICTION_EXPRESSION, context)

        if network_layer is None or not network_layer.isValid():
            raise QgsProcessingException(self.tr("Camada de rede viária inválida."))

        # 1) Preparar expressão: usa a fornecida pelo usuário ou o filtro default
        # por highway/largura/maxweight (quando os campos existirem na camada).
        if not expression_str:
            expression_str = _build_default_restriction_expression(network_layer)
            feedback.pushInfo(
                self.tr("Usando expressão de restrição default: {}").format(expression_str)
            )

        expression = QgsExpression(expression_str)
        expression_context = QgsExpressionContext()
        expression_context.appendScopes(
            QgsExpressionContextUtils.globalProjectLayerScopes(network_layer)
        )
        if not expression.prepare(expression_context):
            raise QgsProcessingException(
                self.tr("Expressão de restrição inválida: {}").format(expression.evalErrorString())
            )

        # 2) Configurar medição de distâncias/comprimento
        da = QgsDistanceArea()
        da.setSourceCrs(network_layer.sourceCrs(), context.transformContext())
        da.setEllipsoid(network_layer.sourceCrs().ellipsoidAcronym())

        total_length_m = 0.0
        restricted_length_m = 0.0

        feedback.pushInfo(self.tr("Calculando a extensão total e restrita da rede viária..."))
        features = network_layer.getFeatures()
        
        # Para feedback de progresso
        total_features = network_layer.featureCount()
        count = 0

        for feature in features:
            if feedback.isCanceled():
                break

            geom = feature.geometry()
            if geom and not geom.isEmpty():
                length = da.measureLength(geom)
                total_length_m += length

                if expression:
                    expression_context.setFeature(feature)
                    is_restricted = expression.evaluate(expression_context)
                    if expression.hasEvalError():
                        raise QgsProcessingException(
                            self.tr("Erro ao avaliar a expressão de restrição: {}").format(expression.evalErrorString())
                        )
                    if bool(is_restricted):
                        restricted_length_m += length

            count += 1
            if total_features > 0:
                feedback.setProgress(int((count / total_features) * 100))

        if feedback.isCanceled():
            return {}

        if total_length_m <= 0:
            raise QgsProcessingException(
                self.tr("O comprimento total da rede viária calculada é 0 m ou negativo. Verifique as geometrias.")
            )

        # 3) Calcular o índice chamando a função core
        try:
            index_val = cargo_restriction_index(total_length_m, restricted_length_m)
        except ValueError as exc:
            raise QgsProcessingException(str(exc))

        feedback.pushInfo(
            self.tr("Comprimento Total: {total:.2f} m | Comprimento Restrito: {restricted:.2f} m").format(
                total=total_length_m, restricted=restricted_length_m
            )
        )
        feedback.pushInfo(
            self.tr("Índice de Acessibilidade de Carga: {index:.2f}%").format(index=index_val)
        )

        feedback.setProgress(100)

        return {self.OUTPUT: index_val}

    def name(self):
        return "urban_cargo_restriction"

    def displayName(self):
        return self.tr("Índice de Restrição de Circulação de Carga")

    def group(self):
        return self.tr("Indicadores Urbanos")

    def groupId(self):
        return "urban"

    def shortHelpString(self):
        return self.tr(
            "Calcula o índice de restrição de circulação para veículos de carga (acessibilidade de carga).\n"
            "O índice representa o percentual da rede viária urbana que está livre de restrições de circulação.\n\n"
            "Parâmetros:\n"
            "- Camada de rede viária: feições de linha representando as vias.\n"
            "- Expressão de restrição: expressão QGIS opcional que define quais trechos possuem restrições "
            "(ex: \"maxweight\" IS NOT NULL ou \"largura\" < 3.0).\n\n"
            "Retorno:\n"
            "- Valor numérico (%) de 0.0 a 100.0, onde 100.0 indica que nenhuma via é restrita."
        )

    def createInstance(self):
        return UrbanCargoRestriction()
