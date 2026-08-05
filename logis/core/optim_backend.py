# -*- coding: utf-8 -*-
"""Módulo de detecção e seleção do backend de otimização (OR-Tools vs Python puro)."""

try:
    from qgis.core import QgsMessageLog, Qgis
except ImportError:
    QgsMessageLog = None
    Qgis = None

# Tag para log de mensagens do QGIS
LOG_TAG = "logis"


def has_ortools():
    """Verifica se a biblioteca OR-Tools (Google) está instalada e disponível.

    Realiza um import dinâmico (lazy) de ortools para evitar erros de importação
    quando a biblioteca não estiver presente no ambiente Python.

    Returns:
        bool: True se o OR-Tools estiver disponível para importação, False caso contrário.
    """
    try:
        import ortools
        return True
    except Exception as e:
        if not isinstance(e, ImportError):
            msg = f"Erro ao importar ortools: {e}"
            if QgsMessageLog is not None and Qgis is not None:
                QgsMessageLog.logMessage(msg, LOG_TAG, Qgis.MessageLevel.Warning)
            else:
                import logging
                logging.warning(f"[{LOG_TAG}] {msg}")
        return False


def pick_backend(preferred="ortools"):
    """Seleciona o backend de otimização a ser utilizado.

    Se o backend preferido for 'ortools', verifica se ele está disponível.
    Caso não esteja no ambiente, realiza o fallback silencioso para o
    backend heurístico padrão em Python puro ('python') e registra uma
    mensagem de aviso no painel de logs do QGIS.

    Args:
        preferred (str): O backend preferido. Geralmente 'ortools' ou 'python'.

    Returns:
        str: O nome do backend a ser utilizado ('ortools' or 'python').
    """
    if preferred == "ortools":
        if has_ortools():
            return "ortools"
        else:
            # Fallback para heurística em Python puro com log de aviso
            msg = "OR-Tools não está instalado ou disponível. Usando backend heurístico em Python puro."
            if QgsMessageLog is not None and Qgis is not None:
                QgsMessageLog.logMessage(msg, LOG_TAG, Qgis.MessageLevel.Warning)
            else:
                import logging
                logging.warning(f"[{LOG_TAG}] {msg}")
            return "python"

    return "python"
