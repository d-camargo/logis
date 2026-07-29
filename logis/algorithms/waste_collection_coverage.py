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
Algoritmo de processamento para cálculo da cobertura da coleta de resíduos por setor.
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsFeatureSink,
    QgsWkbTypes
)

try:
    from ..core.indicators.waste import compute_collection_coverage
    from ..core import qgis_compat
except ImportError:
    from core.indicators.waste import compute_collection_coverage
    from core import qgis_compat


class WasteCollectionCoverage(QgsProcessingAlgorithm):
    """
    Algoritmo QGIS Processing para calcular a extensão de via exigida (required_km),
    extensão efetivamente coberta por rotas de coleta (covered_km) e a taxa de cobertura
    (coverage_pct) por setor e no total acumulado.

    Referência Bibliográfica da Técnica:
        Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). The location of emergency
        service facilities. Operations Research, 19(6), 1363-1373.
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.

    Limite de Complexidade:
        Complexidade de Tempo: O(N), onde N é o número total de trechos nas camadas de entrada.
        Complexidade de Espaço: O(S), onde S é o número de setores de coleta.
    """

    INPUT_REQUIRED_ROADS = 'INPUT_REQUIRED_ROADS'
    FIELD_REQUIRED_SECTOR = 'FIELD_REQUIRED_SECTOR'
    INPUT_COVERED_ROUTES = 'INPUT_COVERED_ROUTES'
    FIELD_COVERED_DEADHEAD = 'FIELD_COVERED_DEADHEAD'
    FIELD_COVERED_SECTOR = 'FIELD_COVERED_SECTOR'
    FREQUENCY_LABEL = 'FREQUENCY_LABEL'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("WasteCollectionCoverage", string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_REQUIRED_ROADS,
                self.tr("Camada de vias exigidas (faixa de frequência)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_REQUIRED_SECTOR,
                self.tr("Campo de setor da camada de vias exigidas (opcional)"),
                parentLayerParameterName=self.INPUT_REQUIRED_ROADS,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_COVERED_ROUTES,
                self.tr("Camada de rota coberta (vias percorridas)"),
                [QgsProcessing.SourceType.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_COVERED_DEADHEAD,
                self.tr("Campo indicador de deadhead/conector (opcional)"),
                parentLayerParameterName=self.INPUT_COVERED_ROUTES,
                type=QgsProcessingParameterField.Boolean,
                defaultValue='route_is_deadhead',
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_COVERED_SECTOR,
                self.tr("Campo de setor da camada de rota coberta (opcional)"),
                parentLayerParameterName=self.INPUT_COVERED_ROUTES,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.FREQUENCY_LABEL,
                self.tr("Rótulo de frequência de coleta"),
                defaultValue="Diária",
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Tabela de cobertura por setor")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        req_source = self.parameterAsSource(parameters, self.INPUT_REQUIRED_ROADS, context)
        req_sector_field = self.parameterAsString(parameters, self.FIELD_REQUIRED_SECTOR, context)
        cov_source = self.parameterAsSource(parameters, self.INPUT_COVERED_ROUTES, context)
        cov_deadhead_field = self.parameterAsString(parameters, self.FIELD_COVERED_DEADHEAD, context)
        cov_sector_field = self.parameterAsString(parameters, self.FIELD_COVERED_SECTOR, context)
        freq_label = self.parameterAsString(parameters, self.FREQUENCY_LABEL, context)

        if req_source is None:
            raise QgsProcessingException(self.tr("Camada de vias exigidas inválida."))
        if cov_source is None:
            raise QgsProcessingException(self.tr("Camada de rota coberta inválida."))

        req_sector_idx = (
            req_source.fields().indexFromName(req_sector_field)
            if req_sector_field
            else -1
        )
        cov_deadhead_idx = (
            cov_source.fields().indexFromName(cov_deadhead_field)
            if cov_deadhead_field
            else -1
        )
        cov_sector_idx = (
            cov_source.fields().indexFromName(cov_sector_field)
            if cov_sector_field
            else -1
        )

        feedback.pushInfo(self.tr("Calculando extensão exigida por setor..."))

        required_by_sector = {}
        for feature in req_source.getFeatures():
            if feedback.isCanceled():
                return {}
            geom = feature.geometry()
            length_m = geom.length() if (geom and not geom.isEmpty()) else 0.0
            length_km = length_m / 1000.0

            sid = None
            if req_sector_idx != -1:
                val = feature.attribute(req_sector_idx)
                if val is not None:
                    sid = val

            if sid not in required_by_sector:
                required_by_sector[sid] = 0.0
            required_by_sector[sid] += length_km

        feedback.pushInfo(self.tr("Calculando extensão coberta por setor..."))

        covered_by_sector = {}
        for feature in cov_source.getFeatures():
            if feedback.isCanceled():
                return {}

            is_dh = False
            if cov_deadhead_idx != -1:
                val = feature.attribute(cov_deadhead_idx)
                if val is not None:
                    is_dh = bool(val)

            if is_dh:
                continue

            geom = feature.geometry()
            length_m = geom.length() if (geom and not geom.isEmpty()) else 0.0
            length_km = length_m / 1000.0

            sid = None
            if cov_sector_idx != -1:
                val = feature.attribute(cov_sector_idx)
                if val is not None:
                    sid = val

            if sid not in covered_by_sector:
                covered_by_sector[sid] = 0.0
            covered_by_sector[sid] += length_km

        all_sectors = list(set(required_by_sector.keys()) | set(covered_by_sector.keys()))
        if not all_sectors:
            raise QgsProcessingException(self.tr("Nenhum trecho válido encontrado nas camadas de entrada."))

        def sort_key(s):
            if s is None:
                return (0, "")
            return (1, str(s))

        all_sectors.sort(key=sort_key)

        req_list = [required_by_sector.get(sid, 0.0) for sid in all_sectors]
        cov_list = [covered_by_sector.get(sid, 0.0) for sid in all_sectors]
        sector_ids_param = all_sectors if (len(all_sectors) > 1 or all_sectors[0] is not None) else None

        try:
            res = compute_collection_coverage(
                required_km=req_list,
                covered_km=cov_list,
                sector_ids=sector_ids_param
            )
        except ValueError as exc:
            raise QgsProcessingException(
                self.tr("Erro ao calcular a cobertura da coleta: {err}").format(err=str(exc))
            )

        out_fields = QgsFields()
        if req_sector_idx != -1:
            sid_type = req_source.fields().at(req_sector_idx).type()
            out_fields.append(QgsField("sector_id", sid_type))
        elif cov_sector_idx != -1:
            sid_type = cov_source.fields().at(cov_sector_idx).type()
            out_fields.append(QgsField("sector_id", sid_type))
        else:
            out_fields.append(QgsField("sector_id", qgis_compat.field_type("string")))

        out_fields.append(QgsField("frequency_label", qgis_compat.field_type("string")))
        out_fields.append(QgsField("required_km", qgis_compat.field_type("double")))
        out_fields.append(QgsField("covered_km", qgis_compat.field_type("double")))
        out_fields.append(QgsField("coverage_pct", qgis_compat.field_type("double")))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            QgsWkbTypes.Type.NoGeometry, req_source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Não foi possível criar a camada de saída."))

        by_sector = res["by_sector"]
        completed = 0
        total_sectors = len(by_sector)

        for sid, data in by_sector.items():
            if feedback.isCanceled():
                return {}

            req_km = data["required_km"]
            cov_km = data["covered_km"]
            cov_pct = data["coverage_pct"]

            sid_display = sid if sid is not None else "Total"
            pct_str = f"{cov_pct * 100.0:.1f}%" if cov_pct is not None else "N/A"

            feedback.pushInfo(
                self.tr(
                    "Setor '{sid}': {req:.2f} km exigidos | {cov:.2f} km cobertos | Cobertura: {pct}"
                ).format(
                    sid=sid_display,
                    req=req_km,
                    cov=cov_km,
                    pct=pct_str
                )
            )

            if cov_pct is not None and cov_pct < 0.8:
                feedback.pushInfo(
                    self.tr(
                        "Aviso: Setor '{sid}' possui cobertura baixa ({pct:.1f}% < 80.0%)."
                    ).format(
                        sid=sid_display,
                        pct=cov_pct * 100.0
                    )
                )

            out_feat = QgsFeature(out_fields)
            out_feat.setAttributes([
                sid if sid is not None else None,
                freq_label,
                req_km,
                cov_km,
                cov_pct
            ])
            sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

            completed += 1
            feedback.setProgress(int((completed / total_sectors) * 100))

        tot = res["total"]
        tot_req = tot["required_km"]
        tot_cov = tot["covered_km"]
        tot_pct = tot["coverage_pct"]
        tot_pct_str = f"{(tot_pct or 0.0) * 100.0:.1f}%" if tot_pct is not None else "N/A"

        if len(by_sector) > 1:
            total_feat = QgsFeature(out_fields)
            total_feat.setAttributes([
                None,
                freq_label,
                tot_req,
                tot_cov,
                tot_pct
            ])
            sink.addFeature(total_feat, QgsFeatureSink.FastInsert)

        feedback.pushInfo(
            self.tr(
                "Total geral: {req:.2f} km exigidos | {cov:.2f} km cobertos | Cobertura total: {pct}"
            ).format(
                req=tot_req,
                cov=tot_cov,
                pct=tot_pct_str
            )
        )

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}

    def name(self):
        return "waste_collection_coverage"

    def displayName(self):
        return self.tr("Cobertura da Coleta de Resíduos por Setor")

    def group(self):
        return self.tr("Logística Especializada — Coleta de Lixo")

    def groupId(self):
        return "waste"

    def shortHelpString(self):
        return self.tr(
            "Calcula a extensão de via exigida (required_km), extensão efetivamente coberta por rotas "
            "de coleta (covered_km) e a taxa de cobertura (coverage_pct) por setor e no total acumulado.\n\n"
            "Parâmetros:\n"
            "- Camada de vias exigidas (faixa de frequência): feições de linha com as vias exigidas.\n"
            "- Campo de setor da camada de vias exigidas (opcional): campo com o identificador do setor.\n"
            "- Camada de rota coberta (vias percorridas): feições de linha (ex.: saídas de "
            "logis:waste_cpp_route, logis:waste_rpp_route ou logis:waste_carp_route).\n"
            "- Campo indicador de deadhead/conector (opcional): campo booleano onde True indica trecho improdutivo "
            "(default: 'route_is_deadhead'). Trechos improdutivos são desconsiderados da cobertura.\n"
            "- Campo de setor da camada de rota coberta (opcional): campo de setor na camada de rota.\n"
            "- Rótulo de frequência de coleta: rótulo textual de frequência (ex.: 'Diária', '3x/semana').\n\n"
            "Retorno:\n"
            "- Tabela sem geometria com uma feição por setor: 'sector_id', 'frequency_label', 'required_km', "
            "'covered_km' e 'coverage_pct'. Quando há mais de um setor, uma feição adicional com 'sector_id' "
            "nulo traz o total acumulado."
        )

    def createInstance(self):
        return WasteCollectionCoverage()
