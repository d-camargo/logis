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

from qgis.core import QgsVectorLayer

from .. import downloader
from ..ufs import codigo_uf


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
    url = f"https://www.ipea.gov.br/geobr/data_gpkg/municipality/2020/{cod}municipality_2020_simplified.gpkg"

    try:
        path = downloader.fetch(url, feedback=feedback)
        layer = QgsVectorLayer(str(path), f"municipios_{uf}", "ogr")
        if not layer.isValid():
            raise RuntimeError(f"Camada de municípios inválida: {path}")

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
            result.append((str(code_val), str(name_val)))

        result.sort(key=lambda t: t[1].lower())
        return result
    except Exception as exc:
        raise RuntimeError(f"Falha ao listar municípios de {uf}: {exc}") from exc
