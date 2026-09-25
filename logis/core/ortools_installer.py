# -*- coding: utf-8 -*-
"""
Instalação opcional do Google OR-Tools no Python do próprio QGIS.

O plugin nunca cria processo externo (achado B603 do scanner do
plugins.qgis.org): quando instala, roda o pip **em processo**, pela API
do pip, com o ponto de entrada resolvido em try/except; quando não pode
instalar, monta e exibe o comando manual (`build_command()` /
`command_text()`), executado pelo usuário no console do ambiente Python
do QGIS.

Licença: GPL-3.0
"""

import contextlib
import importlib
import importlib.util
import io
import logging
import os
import platform
import re
import site
import sys
import sysconfig
import traceback
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


def pip_args(versions=None, break_system_packages=False, user_site=None):
    """
    Monta a lista de argumentos do pip (após 'python -m pip').

    Args:
        versions (dict|None): versões já detectadas; None consulta o
            ambiente via installed_versions().
        break_system_packages (bool): acrescenta --break-system-packages.
        user_site (bool|None): se True inclui --user; se None consulta
            site.ENABLE_USER_SITE is not False.

    Returns:
        list[str]: lista de argumentos do pip começando por 'install'.
    """
    if user_site is None:
        user_site = site.ENABLE_USER_SITE is not False

    if versions is None:
        versions = installed_versions()

    packages = ["ortools"]
    for name in ("numpy", "pandas", "typing_extensions"):
        version = versions.get(name)
        if version is not None and _is_safe_version(version):
            packages.append(f"{name}=={version}")

    args = ["install"]
    if user_site:
        args.append("--user")
    args.extend(["--only-binary=:all:", "--disable-pip-version-check"])
    args.extend(packages)
    if break_system_packages:
        args.append("--break-system-packages")
    return args


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
    return [python_executable(), "-m", "pip"] + pip_args(
        versions=versions, break_system_packages=break_system_packages
    )


def python_executable():
    """
    Devolve o interpretador Python que deve receber o pacote.

    No Linux/macOS é o próprio `sys.executable`. No Windows o QGIS embarca
    o interpretador e `sys.executable` aponta para o `qgis-bin.exe`, que
    não roda `-m pip` — por isso o `python.exe` é resolvido a partir de
    `sys.prefix` (no OSGeo4W e no instalador autônomo é `...\\apps\\Python3xx`).

    Returns:
        str: caminho (ou nome) do executável Python; nunca levanta.
    """
    try:
        exe = sys.executable
        if exe and os.path.basename(exe).lower().startswith("python"):
            return exe

        bindir = sysconfig.get_config_var("BINDIR")
        if sys.platform == "win32":
            candidates = [
                os.path.join(sys.prefix, "python.exe"),
                os.path.join(sys.prefix, "python3.exe"),
                os.path.join(sys.base_prefix, "python.exe"),
            ]
            if bindir:
                candidates.append(os.path.join(bindir, "python.exe"))
            fallback = "python"
        else:
            candidates = [os.path.join(sys.prefix, "bin", "python3")]
            if bindir:
                candidates.append(os.path.join(bindir, "python3"))
            candidates.append(os.path.join(sys.base_prefix, "bin", "python3"))
            fallback = "python3"

        for cand in candidates:
            if os.path.basename(cand).lower().startswith("python") and os.path.isfile(cand):
                return cand

        return fallback
    except Exception:
        return sys.executable or "python3"


def _is_externally_managed():
    """
    Verifica se o ambiente Python possui a trava EXTERNALLY-MANAGED (PEP 668).

    Returns:
        bool: True se o arquivo EXTERNALLY-MANAGED existir no stdlib, False caso contrário.
    """
    try:
        stdlib = sysconfig.get_path("stdlib")
        if stdlib and os.path.exists(os.path.join(stdlib, "EXTERNALLY-MANAGED")):
            return True
        return False
    except Exception:
        return False


def _detect_sandbox():
    """
    Detecta se o ambiente está rodando dentro de um container Flatpak ou Snap.

    Returns:
        str | None: "flatpak", "snap", ou None.
    """
    try:
        if os.path.exists("/.flatpak-info"):
            return "flatpak"
        if os.environ.get("SNAP"):
            return "snap"
        return None
    except Exception:
        return None


def pip_available():
    """
    Verifica se o módulo pip está disponível no ambiente Python.

    Returns:
        bool: True se o pip estiver instalado, False caso contrário.
    """
    try:
        return importlib.util.find_spec("pip") is not None
    except Exception:
        return False


def detect_environment():
    """
    Coleta o ambiente Python/SO em que o QGIS está rodando.

    Returns:
        dict: `os_name` ("Windows"/"macOS"/"Linux"), `python_version`,
            `executable` (resolvido por python_executable()),
            `sys_executable` (cru, para diagnóstico), `pip_available`,
            `user_site`, `externally_managed` (PEP 668) e `sandbox`
            ("flatpak"/"snap"/None). Nunca levanta.
    """
    try:
        if sys.platform == "win32":
            os_name = "Windows"
        elif sys.platform == "darwin":
            os_name = "macOS"
        else:
            os_name = "Linux"

        return {
            "os_name": os_name,
            "python_version": platform.python_version(),
            "executable": python_executable(),
            "sys_executable": sys.executable or "",
            "pip_available": pip_available(),
            "user_site": site.ENABLE_USER_SITE is not False,
            "externally_managed": _is_externally_managed(),
            "sandbox": _detect_sandbox(),
        }
    except Exception:
        logging.debug("[logis] detect_environment: falhou, usando fallback")
        return {
            "os_name": "Linux",
            "python_version": "",
            "executable": sys.executable or "",
            "sys_executable": sys.executable or "",
            "pip_available": False,
            "user_site": False,
            "externally_managed": False,
            "sandbox": None,
        }


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


def _pip_main():
    """
    Resolve o ponto de entrada do pip como biblioteca. A API é privada,
    por isso três caminhos conhecidos são tentados, em ordem.

    Returns:
        callable | None: main(args) do pip, ou None se nenhum existir.
    """
    for module_name, attr in (
        ("pip._internal.cli.main", "main"),
        ("pip._internal", "main"),
        ("pip", "main"),
    ):
        try:
            func = getattr(import_module(module_name), attr, None)
            if callable(func):
                return func
        except Exception as e:
            logging.debug(f"[logis] _pip_main ({module_name}.{attr}): {e}")
            continue
    return None


def refresh_import_path():
    """
    Reprocessa o diretório user-site e invalida os caches de importação,
    para o `import ortools` passar a funcionar sem reiniciar o QGIS
    quando possível.

    Returns:
        bool: resultado de has_ortools() após o refresh.
    """
    try:
        site.addsitedir(site.getusersitepackages())
    except Exception as e:
        logging.debug(f"[logis] refresh_import_path (addsitedir): {e}")
    try:
        importlib.invalidate_caches()
    except Exception as e:
        logging.debug(f"[logis] refresh_import_path (invalidate_caches): {e}")
    return has_ortools()


def install_ortools(versions=None, env=None):
    """
    Instala o OR-Tools chamando o pip em processo (nunca um processo externo).

    Args:
        versions (dict|None): versões a fixar; None detecta do ambiente.
        env (dict|None): ambiente detectado; None chama detect_environment().

    Returns:
        tuple[bool, str]: (ok, log) — o log traz o comando efetivo na
            primeira linha, seguido da saída do pip.
    """
    env = env or detect_environment()
    pip_main = _pip_main()
    if pip_main is None:
        return False, "pip não está disponível neste ambiente Python do QGIS."

    if versions is None:
        versions = installed_versions()
    args = pip_args(
        versions=versions,
        break_system_packages=env.get("externally_managed", False),
        user_site=env.get("user_site"),
    )

    buffer = io.StringIO()
    code = 1
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            code = pip_main(args)
        except SystemExit as exc:
            code = exc.code
        except Exception:
            buffer.write(traceback.format_exc() + "\n")
            code = 1

    ok = code in (0, None)
    first_line = "$ " + command_text(
        versions=versions,
        break_system_packages=env.get("externally_managed", False),
    )
    return ok, first_line + "\n" + buffer.getvalue()

