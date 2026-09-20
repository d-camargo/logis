# -*- coding: utf-8 -*-
"""Módulo de detecção e seleção do backend de otimização (OR-Tools vs Python puro)."""

import os
import json
import time

try:
    from qgis.core import QgsMessageLog, Qgis
except ImportError:
    QgsMessageLog = None
    Qgis = None

from logis.core import downloader

# Tag para log de mensagens do QGIS
LOG_TAG = "logis"

def log_warning(message):
    """Registra aviso no Log de Mensagens do QGIS (tag 'logis'); usa logging quando sem QGIS."""
    if QgsMessageLog is not None and Qgis is not None:
        QgsMessageLog.logMessage(message, LOG_TAG, Qgis.MessageLevel.Warning)
    else:
        import logging
        logging.warning(f"[{LOG_TAG}] {message}")

def _guard_path():
    return os.path.join(downloader.cache_dir(), "ortools_guard.json")

def guard_state():
    path = _guard_path()
    if not os.path.exists(path):
        return "unknown"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("stage") == "importing":
                return "blocked"
            if data.get("stage") == "ok":
                return "ok"
    except Exception:
        return "unknown"
    return "unknown"

def reset_ortools_guard():
    path = _guard_path()
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        import logging
        logging.warning("[%s] Erro ao apagar selo do OR-Tools (%s): %s", LOG_TAG, path, e)

def load_routing_solver():
    if guard_state() == "blocked":
        raise RuntimeError("OR-Tools import falhou ou esta bloqueado.")

    path = _guard_path()
    data_importing = {"stage": "importing", "pid": os.getpid(), "ts": time.time()}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data_importing, f)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        raise RuntimeError(f"OR-Tools import falhou ou esta bloqueado. (I/O error: {e})")

    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except Exception as e:
        # O import falhou com excecao Python: o processo sobreviveu, logo nao foi um
        # crash nativo — o selo volta a "unknown" para nao bloquear a proxima sessao.
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as remove_err:
            import logging
            logging.warning(
                "[%s] Erro ao apagar selo do OR-Tools apos falha de import: %s",
                LOG_TAG, remove_err
            )
        raise RuntimeError("OR-Tools import falhou ou esta bloqueado.") from e

    data_ok = {"stage": "ok", "pid": os.getpid(), "ts": time.time()}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data_ok, f)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        import logging
        logging.warning(f"[{LOG_TAG}] Erro ao atualizar selo guard ok: {e}")

    return pywrapcp, routing_enums_pb2


def has_ortools():
    """Verifica se a biblioteca OR-Tools (Google) está instalada e disponível.

    Realiza um import dinâmico (lazy) de ortools para evitar erros de importação
    quando a biblioteca não estiver presente no ambiente Python.

    Returns:
        bool: True se o OR-Tools estiver disponível para importação, False caso contrário.
    """
    if guard_state() == "blocked":
        return False
    try:
        import ortools
        return True
    except Exception as e:
        if not isinstance(e, ImportError):
            log_warning(f"Erro ao importar ortools: {e}")
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
        if guard_state() == "blocked":
            log_warning("OR-Tools foi desativado porque o QGIS fechou durante a última tentativa de carregá-lo.")
            return "python"

        if has_ortools():
            return "ortools"
        else:
            # Fallback para heurística em Python puro com log de aviso
            log_warning("OR-Tools não está instalado ou disponível. Usando backend heurístico em Python puro.")
            return "python"

    return "python"
