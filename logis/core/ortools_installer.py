# -*- coding: utf-8 -*-
"""
Módulo que monta e explica o comando de instalação do Google OR-Tools.

O plugin não roda processos externos (para evitar o achado B603 do scanner
do plugins.qgis.org). O usuário executa o comando no console do ambiente
Python do QGIS.

Licença: GPL-3.0
"""

import sys
import re
from importlib import import_module

from .optim_backend import has_ortools

# Versão vinda de metadados de distribuições de terceiros não entra crua na linha de
# comando do pip: uma que comece com "-" viraria flag em vez de nome de pacote.
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+!-]*$")


def _is_safe_version(val):
    """Verifica se a versão pode entrar com segurança na linha de comando do pip.

    Args:
        val: valor lido dos metadados da distribuição.

    Returns:
        bool: True se for str e casar com _VERSION_RE.
    """
    return isinstance(val, str) and bool(_VERSION_RE.match(val))


def installed_versions(modules=("numpy", "pandas", "typing_extensions")):
    """
    Detecta a versão instalada de cada módulo, sem nunca propagar exceção.

    Tenta primeiro os metadados da distribuição (importlib.metadata.version)
    e, se falhar por qualquer motivo, cai no atributo __version__ do módulo
    importado. Módulo ausente ou sem versão legível vira None.

    Args:
        modules (tuple[str]): nomes dos módulos a consultar.

    Returns:
        dict: {nome: versão (str) ou None}.
    """
    result = {}
    for name in modules:
        version = None
        try:
            from importlib.metadata import version as metadata_version
            version = metadata_version(name)
        except Exception:
            try:
                version = getattr(import_module(name), "__version__", None)
            except Exception:
                version = None
        result[name] = version
    return result


def build_command(versions=None, break_system_packages=False):
    """
    Monta o comando pip fixando cada dependência na versão já instalada.

    A regra da seção 2.1 do CLAUDE.md continua valendo — o pip não pode
    substituir o numpy/pandas/typing_extensions que o QGIS carrega —, mas
    as travas fixas (`numpy<2`, `pandas<3`) não servem em todo ambiente:
    no QGIS 4.2 Flatpak, com Python 3.13, não existe wheel de `numpy<2`
    em cp313 e a trava ainda contradiz o `ortools>=9.15`, que exige
    numpy 2.x. Fixar em `nome==versão_instalada` preserva o ambiente do
    QGIS em qualquer versão: o requisito já está satisfeito e o pip não
    toca no pacote. Módulos ausentes ficam de fora do comando, deixando o
    resolvedor do pip escolher.

    Args:
        versions (dict|None): versões já detectadas; None consulta o
            ambiente via installed_versions().
        break_system_packages (bool): acrescenta --break-system-packages.

    Returns:
        list[str]: comando pip pronto para ser exibido ao usuário.
    """
    if versions is None:
        versions = installed_versions()

    packages = ["ortools"]
    for name in ("numpy", "pandas", "typing_extensions"):
        version = versions.get(name)
        if version is not None and _is_safe_version(version):
            packages.append(f"{name}=={version}")

    cmd = [sys.executable, "-m", "pip", "install", "--user", "--only-binary=:all:"] + packages
    if break_system_packages:
        cmd.append("--break-system-packages")
    return cmd


def command_text(versions=None, break_system_packages=False):
    """
    Devolve o comando pip pronto para cópia, envolvendo em aspas
    os tokens que contenham espaço.

    Args:
        versions (dict|None): versões já detectadas.
        break_system_packages (bool): se inclui a flag para quebrar o bloqueio PEP 668.

    Returns:
        str: linha de comando completa.
    """
    cmd = build_command(versions=versions, break_system_packages=break_system_packages)
    return " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd)


def is_installed():
    """
    Verifica se a biblioteca OR-Tools está instalada e disponível no ambiente.

    Returns:
        bool: True se estiver instalada, False caso contrário.
    """
    return has_ortools()
