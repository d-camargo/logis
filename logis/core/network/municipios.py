# -*- coding: utf-8 -*-
"""Módulo para listagem de municípios por Unidade da Federação (UF).

Utiliza a malha municipal simplificada do geobr (IBGE 2020).

Referência Bibliográfica da Técnica:
    geobr: Download Spatial Data Sets of Brazil.
    IBGE (Instituto Brasileiro de Geografia e Estatística). (2020).
    Malha Municipal Simplificada 2020.

Limite de Complexidade:
    Complexidade de Tempo: O(N) nos municípios da UF (UF maior ~850 municípios, ex.: MG).
    Complexidade de Espaço: O(N) para o armazenamento das feições dos municípios.
"""

from qgis.core import QgsProject, QgsVectorLayer

from .. import downloader
from ..data_backend import has_gisbr
from ..ufs import codigo_uf


def normalize_code_muni(value) -> str:
    """Normaliza o código do município do IBGE removendo sufixo decimal e espaços.

    Inspirado no tratamento do GisBR em (`gisbr/gui/diagnostico_dock.py`,
    `str(f["code_muni"]).split(".")[0]`).

    Args:
        value: Código do município (int, float, str ou None).

    Returns:
        str: Código normalizado (ex.: '3506904'), '' se None ou vazio, ou o valor
            não numérico como está (sem mascarar) para acusar na validação.

    Limite de Complexidade:
        Complexidade de Tempo: O(1).
        Complexidade de Espaço: O(1).
    """
    if value is None:
        return ""
    val_str = str(value).strip()
    if not val_str:
        return ""
    return val_str.split(".")[0]


def _resolve_layer(out, layer_name: str):
    if isinstance(out, str):
        return QgsProject.instance().mapLayer(out) or QgsVectorLayer(out, layer_name, "ogr")
    return out


def list_municipios(uf: str, feedback=None) -> list[tuple[str, str]]:
    """Lista os municípios de uma UF com seus códigos IBGE e nomes.

    Args:
        uf (str): Sigla da Unidade da Federação (ex.: 'MG', 'SP').
        feedback (QgsProcessingFeedback, optional): Canal de feedback de progresso.

    Returns:
        list[tuple[str, str]]: Lista de tuplas (code_muni, name_muni) ordenada
            por nome (sem diferenciação de caixa alta/baixa).

    Raises:
        ValueError: Se a sigla da UF for inválida (deixa a exceção de codigo_uf subir).
        RuntimeError: Se ocorrer erro no download ou no carregamento/processamento da camada.
    """
    cod = codigo_uf(uf)
    layer = None

    try:
        if has_gisbr():
            try:
                import processing

                out = processing.run(
                    "gisbr:read_municipality",
                    {"CODE": uf, "SIMPLIFIED": True, "OUTPUT": "TEMPORARY_OUTPUT"},
                )["OUTPUT"]
                resolved = _resolve_layer(out, f"municipios_{uf}")
                if resolved is not None and resolved.isValid():
                    layer = resolved
                else:
                    if feedback is not None:
                        feedback.pushInfo("Camada obtida do GisBR é inválida.")
            except Exception as exc:
                if feedback is not None:
                    feedback.pushInfo(f"Falha ao obter municípios via GisBR: {exc}")

        if layer is None:
            url = f"https://www.ipea.gov.br/geobr/data_gpkg/municipality/2020/{cod}municipality_2020_simplified.gpkg"
            path = downloader.fetch(url, feedback=feedback)
            layer = QgsVectorLayer(str(path), f"municipios_{uf}", "ogr")

        if not layer.isValid():
            raise RuntimeError("Camada de municípios inválida")

        field_names = [f.name() for f in layer.fields()]
        code_col = "code_muni" if "code_muni" in field_names else ("code" if "code" in field_names else None)
        name_col = "name_muni" if "name_muni" in field_names else ("name" if "name" in field_names else None)

        if not code_col or not name_col:
            raise RuntimeError(
                f"Campos de código ou nome não encontrados. Campos disponíveis: {field_names}"
            )

        result = []
        for feat in layer.getFeatures():
            code_val = feat[code_col]
            name_val = feat[name_col]
            result.append((normalize_code_muni(code_val), str(name_val)))

        result.sort(key=lambda t: t[1].lower())
        return result
    except Exception as exc:
        raise RuntimeError(f"Falha ao listar municípios de {uf}: {exc}") from exc
