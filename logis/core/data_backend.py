# -*- coding: utf-8 -*-
"""Módulo de detecção do backend de dados (GisBR)."""

try:
    from qgis.core import QgsApplication
except ImportError:
    QgsApplication = None


def has_gisbr():
    """Verifica se o plugin GisBR está instalado e registrado no Processing do QGIS.

    Consulta o processingRegistry do QgsApplication para verificar se o
    algoritmo 'gisbr:read_municipality' está disponível.

    Returns:
        bool: True se o plugin GisBR estiver registrado, False caso contrário.
    """
    if QgsApplication is None:
        return False

    registry = getattr(QgsApplication, "processingRegistry", None)
    if registry is None:
        return False

    reg_instance = registry()
    if reg_instance is None:
        return False

    return reg_instance.algorithmById("gisbr:read_municipality") is not None
