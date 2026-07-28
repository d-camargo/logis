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
Algoritmo de processamento para dimensionamento da frota de coleta de resíduos sólidos.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsFeatureSink,
    QgsWkbTypes
)

try:
    from ..core.indicators.waste import estimate_fleet_size
    from ..core import qgis_compat
except ImportError:
    from core.indicators.waste import estimate_fleet_size
    from core import qgis_compat


class WasteFleetSizing(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para dimensionar a frota de veículos necessária para
    atender às rotas de coleta de resíduos sólidos durante uma jornada de trabalho,
    aplicando a heurística First-Fit Decreasing (FFD) para Bin Packing.

    Referência Bibliográfica da Técnica:
        Johnson, D. S. (1973). Near-optimal bin packing algorithms (Tese de Doutorado,
        Massachusetts Institute of Technology).

    Limite de Complexidade:
        Complexidade de Tempo: O(R log R), onde R é o número de rotas (ordenação FFD domina).
        Complexidade de Espaço: O(R) para armazenar as durações e as atribuições de veículos.
    """

    INPUT_ROUTES = 'INPUT_ROUTES'
    FIELD_ROUTE_ID = 'FIELD_ROUTE_ID'
    FIELD_COLLECTION_SECTOR = 'FIELD_COLLECTION_SECTOR'
    AVG_SPEED = 'AVG_SPEED'
    SHIFT_DURATION = 'SHIFT_DURATION'
    UNLOAD_TIME = 'UNLOAD_TIME'
    TRAVEL_TIME = 'TRAVEL_TIME'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteFleetSizing", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_ROUTES,
                self.tr("Camada de rotas de coleta (saída de logis:waste_carp_route)"),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_ROUTE_ID,
                self.tr("Campo de identificação da rota"),
                parentLayerParameterName=self.INPUT_ROUTES,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_COLLECTION_SECTOR,
                self.tr("Campo de setor de coleta (opcional)"),
                parentLayerParameterName=self.INPUT_ROUTES,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.AVG_SPEED,
                self.tr("Velocidade média de coleta (km/h)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SHIFT_DURATION,
                self.tr("Duração da jornada de trabalho diária (horas)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=8.0,
                minValue=0.0001
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.UNLOAD_TIME,
                self.tr("Tempo fixo de descarga por rota (horas)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.5,
                minValue=0.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TRAVEL_TIME,
                self.tr("Tempo fixo de deslocamento ao destino por rota (horas)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.5,
                minValue=0.0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Dimensionamento de frota por setor")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        routes_source = self.parameterAsSource(parameters, self.INPUT_ROUTES, context)
        route_id_field_name = self.parameterAsString(parameters, self.FIELD_ROUTE_ID, context)
        sector_field_name = self.parameterAsString(parameters, self.FIELD_COLLECTION_SECTOR, context)
        avg_speed = self.parameterAsDouble(parameters, self.AVG_SPEED, context)
        shift_duration = self.parameterAsDouble(parameters, self.SHIFT_DURATION, context)
        unload_time = self.parameterAsDouble(parameters, self.UNLOAD_TIME, context)
        travel_time = self.parameterAsDouble(parameters, self.TRAVEL_TIME, context)

        if routes_source is None:
            raise QgsProcessingException(self.tr("Camada de rotas de coleta inválida."))

        route_id_idx = routes_source.fields().indexFromName(route_id_field_name)
        if route_id_idx == -1:
            raise QgsProcessingException(self.tr("Campo de identificação da rota inválido."))

        sector_field_idx = (
            routes_source.fields().indexFromName(sector_field_name)
            if sector_field_name
            else -1
        )

        feedback.pushInfo(self.tr("Lendo rotas e somando distâncias por setor..."))

        # sector_key -> { route_key -> distância acumulada (m) }
        sector_routes_m = {}

        for feature in routes_source.getFeatures():
            if feedback.isCanceled():
                return {}

            sec_val = feature.attribute(sector_field_idx) if sector_field_idx != -1 else 0
            if sec_val is None:
                sec_val = 0

            route_val = feature.attribute(route_id_idx)

            geom = feature.geometry()
            length_m = geom.length() if (geom and not geom.isEmpty()) else 0.0

            routes_m = sector_routes_m.setdefault(sec_val, {})
            routes_m[route_val] = routes_m.get(route_val, 0.0) + length_m

        if not sector_routes_m:
            raise QgsProcessingException(
                self.tr("Nenhuma rota válida encontrada na camada de entrada.")
            )

        out_fields = QgsFields()
        if sector_field_idx != -1:
            sec_type = routes_source.fields().at(sector_field_idx).type()
            out_fields.append(QgsField("sector_id", sec_type))
        else:
            out_fields.append(QgsField("sector_id", qgis_compat.field_type("int")))
        out_fields.append(QgsField("fleet_size", qgis_compat.field_type("int")))
        out_fields.append(QgsField("num_routes", qgis_compat.field_type("int")))
        out_fields.append(QgsField("total_route_time_h", qgis_compat.field_type("double")))
        out_fields.append(QgsField("avg_utilization", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            QgsWkbTypes.NoGeometry, routes_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        total_sectors = len(sector_routes_m)
        completed_sectors = 0

        for sec_val, routes_m in sector_routes_m.items():
            if feedback.isCanceled():
                return {}

            route_distances_km = [dist_m / 1000.0 for dist_m in routes_m.values()]

            feedback.pushInfo(
                self.tr("Dimensionando frota do setor '{sec}' ({count} rota(s))...").format(
                    sec=sec_val, count=len(route_distances_km)
                )
            )

            try:
                fleet_res = estimate_fleet_size(
                    route_distances_km=route_distances_km,
                    avg_collection_speed_kmh=avg_speed,
                    shift_duration_h=shift_duration,
                    unload_time_h=unload_time,
                    travel_time_to_destination_h=travel_time
                )
            except ValueError as exc:
                raise QgsProcessingException(
                    self.tr("Erro ao dimensionar a frota do setor '{sec}': {err}").format(
                        sec=sec_val, err=str(exc)
                    )
                )

            feedback.pushInfo(
                self.tr(
                    "Setor '{sec}': {fleet} veículo(s) necessário(s) | "
                    "Utilização média: {util:.1f}% | Tempo total de rotas: {total:.2f} h"
                ).format(
                    sec=sec_val,
                    fleet=fleet_res["fleet_size"],
                    util=fleet_res["avg_utilization"] * 100.0,
                    total=fleet_res["total_route_time_h"]
                )
            )
            if fleet_res["avg_utilization"] < 0.5:
                feedback.pushInfo(
                    self.tr(
                        "Aviso: frota do setor '{sec}' com utilização média abaixo de 50% "
                        "({util:.1f}%) — possível sobredimensionamento."
                    ).format(sec=sec_val, util=fleet_res["avg_utilization"] * 100.0)
                )

            out_feat = QgsFeature(out_fields)
            out_feat.setAttributes([
                sec_val,
                fleet_res["fleet_size"],
                len(route_distances_km),
                fleet_res["total_route_time_h"],
                fleet_res["avg_utilization"]
            ])
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

            completed_sectors += 1
            feedback.setProgress(int((completed_sectors / total_sectors) * 100))

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_fleet_sizing"

    def displayName(self):
        return self.tr("Dimensionamento de Frota de Coleta")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Dimensiona a frota de veículos necessária para atender às rotas de coleta de "
            "resíduos sólidos durante a jornada de trabalho, aplicando o algoritmo First-Fit "
            "Decreasing (FFD) para o problema de empacotamento (Bin Packing).\n\n"
            "Parâmetros:\n"
            "- Camada de rotas de coleta: feições de linha, tipicamente a saída de "
            "logis:waste_carp_route.\n"
            "- Campo de identificação da rota (obrigatório): agrupa feições pela rota/viagem "
            "('route_id'); a distância de cada rota é a soma do comprimento das geometrias.\n"
            "- Campo de setor de coleta (opcional): se informado, dimensiona a frota "
            "separadamente por setor ('route_sector_id'); se omitido, trata a camada inteira "
            "como um único setor.\n"
            "- Velocidade média de coleta: velocidade operacional em km/h (default: 10 km/h).\n"
            "- Duração da jornada: tempo máximo de trabalho por veículo em horas (default: 8 h).\n"
            "- Tempo fixo de descarga: tempo gasto na descarga por rota em horas (default: 0.5 h).\n"
            "- Tempo fixo de deslocamento: tempo de viagem ao aterro/depósito por rota em horas (default: 0.5 h).\n\n"
            "Uma rota isolada cuja duração exceda a jornada de trabalho gera erro explícito "
            "em vez de ser dividida entre mais de um veículo (sem split).\n\n"
            "Retorno:\n"
            "- Tabela sem geometria com uma feição por setor: 'sector_id', 'fleet_size' "
            "(nº de veículos estimado), 'num_routes' (nº de rotas do setor), "
            "'total_route_time_h' (soma das durações das rotas) e 'avg_utilization' "
            "(utilização média da frota, entre 0 e 1)."
        )

    def createInstance(self):
        return WasteFleetSizing()
