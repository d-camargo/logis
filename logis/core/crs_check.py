# -*- coding: utf-8 -*-
"""
Verificação de SRC de entrada para os algoritmos de roteirização.

Sintoma da 0.6.1: camada de pontos com SRC inválido → ``QgsCoordinateTransform``
curto-circuitado (não faz nada) → graus tratados como metros → janela de análise
em ±3000 "metros" → ``transformBoundingBox`` do grafo falha com "Invalid value
for an argument". Este módulo classifica a entrada antes de transformar, sem
importar ``qgis`` (funções puras, testáveis sem QGIS).
"""

import math
from typing import List, Tuple

# Caixa lon/lat que contém o Brasil (xmin, ymin, xmax, ymax), com folga.
BRAZIL_LONLAT_BOUNDS = (-75.0, -35.0, -28.0, 6.0)


def classify_input_crs(crs_valid: bool, crs_geographic: bool, coords: List[Tuple[float, float]]) -> str:
    """
    Classifica o SRC declarado de uma camada de pontos frente às coordenadas cruas.

    :param crs_valid: resultado de ``QgsCoordinateReferenceSystem.isValid()``.
    :param crs_geographic: resultado de ``QgsCoordinateReferenceSystem.isGeographic()``.
    :param coords: lista de tuplas ``(x, y)`` cruas, no SRC declarado da camada.
    :return: ``"ok"`` | ``"assume_4674"`` | ``"missing"`` | ``"degrees_in_projected"``.
    """
    pts = [(float(x), float(y)) for x, y in coords]
    if not pts:
        return "ok"

    if not crs_valid:
        xmin, ymin, xmax, ymax = BRAZIL_LONLAT_BOUNDS
        if all(xmin <= x <= xmax and ymin <= y <= ymax for x, y in pts):
            return "assume_4674"
        return "missing"

    if not crs_geographic and all(abs(x) <= 180.0 and abs(y) <= 90.0 for x, y in pts):
        return "degrees_in_projected"

    return "ok"


def valid_extent(xmin: float, ymin: float, xmax: float, ymax: float) -> bool:
    """
    Retorna True quando a caixa (xmin, ymin, xmax, ymax) tem os quatro valores
    finitos e não degenerada (``xmin < xmax`` e ``ymin < ymax``).
    """
    values = (xmin, ymin, xmax, ymax)
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        if not math.isfinite(number):
            return False
    return float(xmin) < float(xmax) and float(ymin) < float(ymax)
