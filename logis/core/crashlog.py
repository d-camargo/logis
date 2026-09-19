# -*- coding: utf-8 -*-
"""Log de rastro e diagnostico de falhas (crashlog).

Permite registrar etapas da execucao com timestamp, pid e detalhes em
diagnostico.log no diretorio de cache do plugin.
"""

import datetime
import logging
import os
from pathlib import Path
import sys


def trace_path():
    """Retorna o Path para o arquivo diagnostico.log no diretorio de cache."""
    try:
        from logis.core.downloader import cache_dir

        c_dir = cache_dir()
    except Exception:
        c_dir = Path.home() / ".cache" / "logis"

    c_dir = Path(c_dir)
    c_dir.mkdir(parents=True, exist_ok=True)
    return c_dir / "diagnostico.log"


def mark(stage, detail=""):
    """Registra uma etapa no log de diagnostico com ISO8601, pid, stage e detail."""
    try:
        path = trace_path()
        now_iso = datetime.datetime.now().isoformat()
        pid = os.getpid()
        line = f"{now_iso} | {pid} | {stage} | {detail}\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        sys.stderr.write(f"[crashlog] Erro ao gravar marca '{stage}': {e}\n")
        logging.warning("[crashlog] Erro ao gravar marca '%s': %s", stage, e)


def read_tail(n=30):
    """Devolve as ultimas n linhas do log de diagnostico."""
    try:
        path = trace_path()
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-n:] if n > 0 else []
    except Exception as e:
        sys.stderr.write(f"[crashlog] Erro ao ler rastro: {e}\n")
        logging.warning("[crashlog] Erro ao ler rastro: %s", e)
        return []


def reset():
    """Trunca (limpa) o arquivo de log de diagnostico."""
    try:
        path = trace_path()
        if path.exists():
            with open(path, "w", encoding="utf-8") as f:
                f.truncate(0)
    except Exception as e:
        sys.stderr.write(f"[crashlog] Erro ao limpar rastro: {e}\n")
        logging.warning("[crashlog] Erro ao limpar rastro: %s", e)
