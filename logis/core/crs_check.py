# -*- coding: utf-8 -*-
"""
Verificação de SRC de entrada para os algoritmos de roteirização.

Sintoma da 0.6.1: camada de pontos com SRC inválido → ``QgsCoordinateTransform``
curto-circuitado (não faz nada) → graus tratados como metros → janela de análise
em ±3000 "metros" → ``transformBoundingBox`` do grafo falha com "Invalid value
for an argument". Este módulo classifica a entrada antes de transformar, sem
importar ``qgis`` (funções puras, testáveis sem QGIS).

Sintoma da 0.6.2: mesmo com SRC declarado válido (EPSG:4326), a transformação
para EPSG:5880 no Windows/QGIS 4 virou no-op silencioso → coordenadas continuaram
em graus → margem de 3000 m somada a graus resultou no log da 0.6.2 com a
janela ±3000 = graus somados a metros ([-3046.67, -3023.63 : 2953.40, 2976.51]).
Este módulo fornece limites plausíveis (``PLAUSIBLE_BOUNDS``), determinação de fuso
UTM SIRGAS (``utm_sirgas_epsg``), verificação de plausibilidade de coordenadas
(``plausible_coords``) e teste de deslocamento de ponto (``point_moved``).
"""

import math
from typing import Any, List, Tuple

# Caixa lon/lat que contém o Brasil (xmin, ymin, xmax, ymax), com folga.
BRAZIL_LONLAT_BOUNDS = (-75.0, -35.0, -28.0, 6.0)

# Limites plausíveis de coordenadas para SRCs suportados (xmin, ymin, xmax, ymax).
PLAUSIBLE_BOUNDS = {
    "EPSG:5880": (2_500_000, 5_600_000, 8_100_000, 10_900_000),
    "EPSG:4674": BRAZIL_LONLAT_BOUNDS,
    "EPSG:4326": BRAZIL_LONLAT_BOUNDS,
}


def _extract_xy(pt: Any) -> Tuple[float, float]:
    """Extrai tupla (x, y) de float a partir de tupla/lista ou objeto com métodos x(), y()."""
    if hasattr(pt, "x") and callable(pt.x):
        return float(pt.x()), float(pt.y())
    if isinstance(pt, (tuple, list)) and len(pt) >= 2:
        return float(pt[0]), float(pt[1])
    raise TypeError(f"Coordenada inválida: {pt!r}")


def _is_utm_sirgas(authid: str) -> bool:
    """Verifica se authid corresponde a um fuso UTM SIRGAS 2000 (EPSG:3195x–3198x)."""
    if authid.startswith("EPSG:319"):
        suffix = authid[5:]
        if suffix.isdigit():
            code = int(suffix)
            return 31950 <= code <= 31990
    return False


def utm_sirgas_epsg(lon: float, lat: float) -> str:
    """
    Retorna o código EPSG do fuso UTM SIRGAS 2000 correspondente a (lon, lat).

    No hemisfério sul: EPSG:31960 + zona (ex.: São Paulo -> EPSG:31983).
    No hemisfério norte: EPSG:31954 + zona (ex.: (-60.0, 2.8) -> zona 20 norte EPSG:31974).
    Usado como fallback caso a transformação para EPSG:5880 falhe silenciosamente,
    conforme visto no log da 0.6.2 (janela ±3000 = graus somados a metros).
    """
    flon = float(lon)
    flat = float(lat)
    val = (flon + 180.0) / 6.0
    if val.is_integer() and val > 0:
        zone = int(val)
    else:
        zone = int(math.floor(val)) + 1
    zone = max(1, min(60, zone))

    if flat >= 0.0:
        base = 31954
    else:
        base = 31960
    return f"EPSG:{base + zone}"


def plausible_coords(authid: str, coords: Any) -> bool:
    """
    Verifica se todas as coordenadas em ``coords`` são finitas e plausíveis para o ``authid``.

    Detecta transformações no-op silenciosas onde coordenadas em graus foram mantidas
    e tratadas como métricas, conforme visto no log da 0.6.2 (janela ±3000 = graus somados a metros,
    resultando em caixas como [-3046.67, -3023.63]).

    :param authid: identificador do SRC (ex.: "EPSG:5880", "EPSG:4674", "EPSG:31983").
    :param coords: sequência ou iterável de tuplas (x, y) ou objetos com métodos x(), y().
    :return: True se todas as coordenadas forem finitas e plausíveis para o SRC.
    """
    pts = []
    for pt in coords:
        try:
            x, y = _extract_xy(pt)
        except (TypeError, ValueError, IndexError, AttributeError):
            return False
        if not (math.isfinite(x) and math.isfinite(y)):
            return False
        pts.append((x, y))

    if not pts:
        return True

    auth = str(authid).strip().upper() if authid else ""
    if auth in PLAUSIBLE_BOUNDS:
        xmin, ymin, xmax, ymax = PLAUSIBLE_BOUNDS[auth]
        return all(xmin <= x <= xmax and ymin <= y <= ymax for x, y in pts)

    if _is_utm_sirgas(auth):
        return all(100_000.0 <= x <= 900_000.0 and 0.0 <= y <= 10_000_000.0 for x, y in pts)

    return True


def point_moved(src: Any, dst: Any, tol: float = 1e-9) -> bool:
    """
    Verifica se o ponto transformado ``dst`` se moveu em relação a ``src`` além de ``tol``.

    Detecta transformações de coordenadas que devolvem o ponto intacto sem acusar erro,
    conforme o log da 0.6.2 (janela ±3000 = graus somados a metros).

    :param src: ponto original (x, y) ou objeto com métodos x(), y().
    :param dst: ponto transformado (x, y) ou objeto com métodos x(), y().
    :param tol: tolerância para considerar que o ponto se moveu (padrão 1e-9).
    :return: True se a distância entre src e dst for estritamente maior que tol.
    """
    try:
        x1, y1 = _extract_xy(src)
        x2, y2 = _extract_xy(dst)
    except (TypeError, ValueError, IndexError, AttributeError):
        return False
    if not (math.isfinite(x1) and math.isfinite(y1) and math.isfinite(x2) and math.isfinite(y2)):
        return False
    return math.hypot(x2 - x1, y2 - y1) > float(tol)


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
