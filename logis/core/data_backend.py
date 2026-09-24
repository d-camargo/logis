# -*- coding: utf-8 -*-
"""Módulo de detecção do backend de dados (GisBR)."""

try:
    from qgis.core import QgsApplication
except ImportError:
    QgsApplication = None


def has_gisbr(alg_id="gisbr:read_municipality"):
    """Verifica se o plugin GisBR está instalado e registrado no Processing do QGIS.

    Consulta o processingRegistry do QgsApplication para verificar se o
    algoritmo especificado por `alg_id` (padrão 'gisbr:read_municipality') está disponível.
    Nota: 'gisbr:osm_network' existe desde o GisBR 0.11.0.

    Args:
        alg_id (str, optional): ID do algoritmo a ser verificado.
            Padrão: "gisbr:read_municipality".

    Returns:
        bool: True se o algoritmo do GisBR estiver registrado, False caso contrário.
    """
    if QgsApplication is None:
        return False

    registry = getattr(QgsApplication, "processingRegistry", None)
    if registry is None:
        return False

    reg_instance = registry()
    if reg_instance is None:
        return False

    return reg_instance.algorithmById(alg_id) is not None
