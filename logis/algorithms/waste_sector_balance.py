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
Algoritmo de processamento para análise de equilíbrio (balanço) entre setores/rotas de coleta de resíduos sólidos.
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
    from ..core.indicators.waste import compute_route_balance
    from ..core import qgis_compat
except ImportError:
    from core.indicators.waste import compute_route_balance
    from core import qgis_compat


class WasteSectorBalance(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para avaliar o equilíbrio (balanço) entre rotas/setores
    de coleta de resíduos sólidos, calculando desvios de carga (kg) e tempo de operação (h),
    além de estatísticas como média, desvio padrão e coeficiente de variação (CV).

    Referência Bibliográfica da Técnica:
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.
        Kim, B. I., Kim, S., & Sahoo, S. (2006). Waste collection vehicle routing with
        time windows. Computers & Operations Research, 33(12), 3624-3642.

    Limite de Complexidade:
        Complexidade de Tempo: O(N), onde N é o número de feições/trechos na camada de entrada.
        Complexidade de Espaço: O(R), onde R é o número de rotas agrupadas por setor.
    """

    INPUT_ROUTES = 'INPUT_ROUTES'
    FIELD_LOAD = 'FIELD_LOAD'
    FIELD_DISTANCE = 'FIELD_DISTANCE'
    FIELD_ROUTE_ID = 'FIELD_ROUTE_ID'
    FIELD_COLLECTION_SECTOR = 'FIELD_COLLECTION_SECTOR'
    AVG_SPEED = 'AVG_SPEED'
    UNLOAD_TIME = 'UNLOAD_TIME'
    TRAVEL_TIME = 'TRAVEL_TIME'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteSectorBalance", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_ROUTES,
                self.tr("Camada de rotas de coleta (ex.: saída de logis:waste_carp_route)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_LOAD,
                self.tr("Campo de carga da rota (kg)"),
                parentLayerParameterName=self.INPUT_ROUTES,
                type=QgsProcessingParameterField.Numeric,
                defaultValue='route_load_kg',
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_DISTANCE,
                self.tr("Campo de distância da rota em km (opcional)"),
                parentLayerParameterName=self.INPUT_ROUTES,
                type=QgsProcessingParameterField.Numeric,
                defaultValue='route_distance_km',
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_ROUTE_ID,
                self.tr("Campo de identificação da rota (opcional)"),
                parentLayerParameterName=self.INPUT_ROUTES,
                defaultValue='route_id',
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_COLLECTION_SECTOR,
                self.tr("Campo de setor de coleta (opcional)"),
                parentLayerParameterName=self.INPUT_ROUTES,
                defaultValue='route_sector_id',
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.AVG_SPEED,
                self.tr("Velocidade média de coleta (km/h)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=10.0,
                minValue=0.0001,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.UNLOAD_TIME,
                self.tr("Tempo fixo de descarga por rota (horas)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TRAVEL_TIME,
                self.tr("Tempo fixo de deslocamento ao destino por rota (horas)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Indicadores de equilíbrio entre rotas por setor")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        routes_source = self.parameterAsSource(parameters, self.INPUT_ROUTES, context)
        load_field_name = self.parameterAsString(parameters, self.FIELD_LOAD, context)
        dist_field_name = self.parameterAsString(parameters, self.FIELD_DISTANCE, context)
        route_id_field_name = self.parameterAsString(parameters, self.FIELD_ROUTE_ID, context)
        sector_field_name = self.parameterAsString(parameters, self.FIELD_COLLECTION_SECTOR, context)
        avg_speed = self.parameterAsDouble(parameters, self.AVG_SPEED, context)
        unload_time = self.parameterAsDouble(parameters, self.UNLOAD_TIME, context)
        travel_time = self.parameterAsDouble(parameters, self.TRAVEL_TIME, context)

        if routes_source is None:
            raise QgsProcessingException(self.tr("Camada de rotas de coleta inválida."))

        load_idx = routes_source.fields().indexFromName(load_field_name)
        if load_idx == -1:
            raise QgsProcessingException(
                self.tr("Campo de carga da rota '{field}' não encontrado.").format(field=load_field_name)
            )

        dist_idx = (
            routes_source.fields().indexFromName(dist_field_name)
            if dist_field_name
            else -1
        )

        route_id_idx = (
            routes_source.fields().indexFromName(route_id_field_name)
            if route_id_field_name
            else -1
        )

        sector_field_idx = (
            routes_source.fields().indexFromName(sector_field_name)
            if sector_field_name
            else -1
        )

        feedback.pushInfo(self.tr("Agrupando feições e calculando cargas e distâncias de rotas por setor..."))

        # sector_val -> { route_key -> {'load_vals': [], 'dist_vals': [], 'geom_len_m': 0.0} }
        sector_grouped = {}

        feat_counter = 0
        for feature in routes_source.getFeatures():
            if feedback.isCanceled():
                return {}

            sec_val = feature.attribute(sector_field_idx) if sector_field_idx != -1 else 0
            if sec_val is None:
                sec_val = 0

            feat_counter += 1
            if route_id_idx != -1:
                r_val = feature.attribute(route_id_idx)
                route_key = r_val if r_val is not None else feat_counter
            else:
                route_key = feat_counter

            geom = feature.geometry()
            length_m = geom.length() if (geom and not geom.isEmpty()) else 0.0

            sec_dict = sector_grouped.setdefault(sec_val, {})
            r_data = sec_dict.setdefault(route_key, {'load_vals': [], 'dist_vals': [], 'geom_len_m': 0.0})

            load_val = feature.attribute(load_idx)
            if load_val is not None:
                r_data['load_vals'].append(float(load_val))

            if dist_idx != -1:
                dist_val = feature.attribute(dist_idx)
                if dist_val is not None:
                    r_data['dist_vals'].append(float(dist_val))

            r_data['geom_len_m'] += length_m

        if not sector_grouped:
            raise QgsProcessingException(self.tr("Nenhuma rota válida encontrada na camada de entrada."))

        out_fields = QgsFields()
        if sector_field_idx != -1:
            sec_type = routes_source.fields().at(sector_field_idx).type()
            out_fields.append(QgsField("sector_id", sec_type))
        else:
            out_fields.append(QgsField("sector_id", qgis_compat.field_type("int")))

        out_fields.append(QgsField("num_routes", qgis_compat.field_type("int")))
        out_fields.append(QgsField("total_load_kg", qgis_compat.field_type("double")))
        out_fields.append(QgsField("mean_load_kg", qgis_compat.field_type("double")))
        out_fields.append(QgsField("std_dev_load_kg", qgis_compat.field_type("double")))
        out_fields.append(QgsField("min_load_kg", qgis_compat.field_type("double")))
        out_fields.append(QgsField("max_load_kg", qgis_compat.field_type("double")))
        out_fields.append(QgsField("cv_load", qgis_compat.field_type("double")))

        out_fields.append(QgsField("total_time_h", qgis_compat.field_type("double")))
        out_fields.append(QgsField("mean_time_h", qgis_compat.field_type("double")))
        out_fields.append(QgsField("std_dev_time_h", qgis_compat.field_type("double")))
        out_fields.append(QgsField("min_time_h", qgis_compat.field_type("double")))
        out_fields.append(QgsField("max_time_h", qgis_compat.field_type("double")))
        out_fields.append(QgsField("cv_time", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            QgsWkbTypes.Type.NoGeometry, routes_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        total_sectors = len(sector_grouped)
        completed_sectors = 0

        for sec_val, routes_map in sector_grouped.items():
            if feedback.isCanceled():
                return {}

            sector_loads = []
            sector_distances = []
            has_valid_distances = True

            for r_key, r_data in routes_map.items():
                l_vals = r_data['load_vals']
                if not l_vals:
                    continue

                if len(l_vals) > 1 and len(set(l_vals)) == 1:
                    r_load = l_vals[0]
                else:
                    r_load = sum(l_vals)
                sector_loads.append(r_load)

                d_vals = r_data['dist_vals']
                if d_vals:
                    if len(d_vals) > 1 and len(set(d_vals)) == 1:
                        r_dist = d_vals[0]
                    else:
                        r_dist = sum(d_vals)
                    sector_distances.append(r_dist)
                elif r_data['geom_len_m'] > 0:
                    sector_distances.append(r_data['geom_len_m'] / 1000.0)
                else:
                    has_valid_distances = False

            if not sector_loads:
                continue

            if not has_valid_distances or len(sector_distances) != len(sector_loads):
                sector_distances_param = None
            else:
                sector_distances_param = sector_distances

            try:
                bal_res = compute_route_balance(
                    route_loads_kg=sector_loads,
                    route_distances_km=sector_distances_param,
                    avg_collection_speed_kmh=avg_speed if sector_distances_param is not None else None,
                    unload_time_h=unload_time,
                    travel_time_to_destination_h=travel_time
                )
            except ValueError as exc:
                raise QgsProcessingException(
                    self.tr("Erro ao calcular equilíbrio do setor '{sec}': {err}").format(
                        sec=sec_val, err=str(exc)
                    )
                )

            load_st = bal_res["load"]
            time_st = bal_res["time"]

            feedback.pushInfo(
                self.tr(
                    "Setor '{sec}': {num} rota(s) | Carga média: {m_load:.2f} kg (σ={std_load:.2f}, CV={cv_load:.1f}%)"
                ).format(
                    sec=sec_val,
                    num=bal_res["num_routes"],
                    m_load=load_st["mean_kg"],
                    std_load=load_st["std_dev_kg"],
                    cv_load=load_st["cv"] * 100.0
                )
            )

            if load_st["cv"] > 0.2:
                feedback.pushInfo(
                    self.tr(
                        "Aviso: setor '{sec}' apresenta desbalanço de carga alto (CV={cv:.1f}% > 20%)."
                    ).format(sec=sec_val, cv=load_st["cv"] * 100.0)
                )

            if time_st is not None:
                feedback.pushInfo(
                    self.tr(
                        "Setor '{sec}': Tempo médio: {m_time:.2f} h (σ={std_time:.2f}, CV={cv_time:.1f}%)"
                    ).format(
                        sec=sec_val,
                        m_time=time_st["mean_h"],
                        std_time=time_st["std_dev_h"],
                        cv_time=time_st["cv"] * 100.0
                    )
                )

            out_feat = QgsFeature(out_fields)
            out_feat.setAttributes([
                sec_val,
                bal_res["num_routes"],
                load_st["total_kg"],
                load_st["mean_kg"],
                load_st["std_dev_kg"],
                load_st["min_kg"],
                load_st["max_kg"],
                load_st["cv"],
                time_st["total_h"] if time_st else None,
                time_st["mean_h"] if time_st else None,
                time_st["std_dev_h"] if time_st else None,
                time_st["min_h"] if time_st else None,
                time_st["max_h"] if time_st else None,
                time_st["cv"] if time_st else None,
            ])
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

            completed_sectors += 1
            feedback.setProgress(int((completed_sectors / total_sectors) * 100))

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_sector_balance"

    def displayName(self):
        return self.tr("Equilíbrio entre Setores/Rotas de Coleta")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Avalia o equilíbrio (balanço) de carga e tempo operacional entre rotas/setores "
            "de coleta de resíduos sólidos, calculando média, desvio padrão, mínimo, máximo "
            "e coeficiente de variação (CV).\n\n"
            "Parâmetros:\n"
            "- Camada de rotas de coleta: feições com rotas/vias (ex.: saída de "
            "logis:waste_carp_route, com campos 'route_load_kg' e 'route_distance_km').\n"
            "- Campo de carga da rota (obrigatório): campo numérico com a carga total da rota (kg).\n"
            "- Campo de distância da rota (opcional): campo numérico com a distância em km; "
            "se omitido, utiliza a extensão das geometrias das rotas.\n"
            "- Campo de identificação da rota (opcional): se informado, agrupa feições por rota.\n"
            "- Campo de setor de coleta (opcional): se informado, calcula o equilíbrio separadamente "
            "para cada setor.\n"
            "- Velocidade média de coleta: velocidade operacional em km/h (default: 10 km/h).\n"
            "- Tempo fixo de descarga: tempo gasto na descarga por rota em horas (default: 0.0 h).\n"
            "- Tempo fixo de deslocamento: tempo de viagem ao aterro/depósito em horas (default: 0.0 h).\n\n"
            "Retorno:\n"
            "- Tabela sem geometria com uma feição por setor: 'sector_id', 'num_routes', "
            "'total_load_kg', 'mean_load_kg', 'std_dev_load_kg', 'min_load_kg', 'max_load_kg', "
            "'cv_load', 'total_time_h', 'mean_time_h', 'std_dev_time_h', 'min_time_h', "
            "'max_time_h' e 'cv_time'."
        )

    def createInstance(self):
        return WasteSectorBalance()
