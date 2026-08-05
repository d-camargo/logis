# -*- coding: utf-8 -*-
"""
Módulo para instalação e verificação da biblioteca Google OR-Tools.

Licença: GPL-3.0
"""

import sys
import subprocess
from importlib import import_module

try:
    from qgis.core import QgsTask, QgsApplication
    from qgis.PyQt.QtCore import pyqtSignal
except ImportError:
    class QgsTask:
        class Flag:
            CanCancel = 1
        def __init__(self, *args, **kwargs):
            pass
        def isCanceled(self):
            return False
        def setProgress(self, progress):
            pass
    QgsApplication = None
    
    # Mock de pyqtSignal para testes/sintaxe fora do QGIS
    class pyqtSignal:
        def __init__(self, *args, **kwargs):
            pass
        def __get__(self, instance, owner):
            return self
        def emit(self, *args):
            pass
        def connect(self, slot):
            pass

from .optim_backend import has_ortools


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


class ORToolsInstallTask(QgsTask):
    """
    Task executada em segundo plano para instalar a biblioteca ortools via pip.
    """
    log_received = pyqtSignal(str)

    def __init__(self, on_finish=None):
        super().__init__('Instalando Google OR-Tools', QgsTask.Flag.CanCancel)
        self.on_finish = on_finish
        self.error = None
        self.output = []

    def build_command(self, break_system_packages=False, versions=None):
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
            break_system_packages (bool): acrescenta --break-system-packages.
            versions (dict|None): versões já detectadas; None consulta o
                ambiente via installed_versions().

        Returns:
            list[str]: comando pip pronto para subprocess.
        """
        if versions is None:
            versions = installed_versions()

        packages = ["ortools"]
        for name in ("numpy", "pandas", "typing_extensions"):
            version = versions.get(name)
            if version is not None:
                packages.append(f"{name}=={version}")

        cmd = [sys.executable, "-m", "pip", "install", "--user", "--only-binary=:all:"] + packages
        if break_system_packages:
            cmd.append("--break-system-packages")
        return cmd

    def _run_pip(self, cmd):
        """
        Executa o pip transmitindo a saída via log_received.

        Returns:
            int|None: código de retorno, ou None se a task foi cancelada.
        """
        # Inicia o subprocesso redirecionando stderr para stdout
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        while True:
            if self.isCanceled():
                process.terminate()
                return None

            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break

            if line:
                stripped = line.strip()
                self.output.append(stripped)
                self.log_received.emit(stripped)

        return process.poll()

    def run(self):
        try:
            returncode = self._run_pip(self.build_command())
            if returncode is None:
                self.error = "Instalação cancelada pelo usuário."
                return False

            # Distros com PEP 668 (Debian/Ubuntu) recusam o pip no Python do
            # sistema; repetir uma única vez com --break-system-packages.
            if returncode != 0 and any(
                "externally-managed-environment" in line for line in self.output
            ):
                msg = "Ambiente gerenciado pela distro; repetindo com --break-system-packages."
                self.output.append(msg)
                self.log_received.emit(msg)
                returncode = self._run_pip(self.build_command(break_system_packages=True))
                if returncode is None:
                    self.error = "Instalação cancelada pelo usuário."
                    return False

            if returncode != 0:
                output_str = "\n".join(self.output)
                if "No module named pip" in output_str:
                    self.error = (
                        "O módulo 'pip' não está disponível neste ambiente Python. "
                        "Por favor, instale o pip primeiro."
                    )
                elif any(err in output_str for err in ["ConnectionError", "Network is unreachable", "Temporary failure in name resolution"]):
                    self.error = (
                        "Falha de rede ao tentar baixar o OR-Tools. "
                        "Verifique sua conexão com a internet."
                    )
                elif any(err in output_str for err in ["PermissionError", "Permission denied", "Access is denied"]):
                    self.error = (
                        "Erro de permissão ao instalar o OR-Tools. "
                        "Tente executar o QGIS com privilégios administrativos."
                    )
                elif "ResolutionImpossible" in output_str or ("Could not find a version that satisfies" in output_str and "numpy" in output_str):
                    self.error = (
                        "A versão do NumPy já instalada no QGIS é incompatível com a "
                        "versão atual do OR-Tools. O plugin segue funcionando com a "
                        "heurística em Python puro. O OR-Tools é opcional."
                    )
                # Sem wheel para este Python o pip emite "Could not find a version"
                # junto de "No matching distribution found" — não é falha de rede.
                elif any(err in output_str for err in ["No matching distribution found", "Could not find a version", "Failed building wheel", "only-binary"]):
                    self.error = (
                        "Não há pacote binário do OR-Tools para este Python/plataforma "
                        "e a compilação não é possível neste ambiente (como no QGIS Flatpak "
                        "com Python 3.13). O plugin segue funcionando com a heurística em "
                        "Python puro. O OR-Tools é opcional."
                    )
                else:
                    self.error = f"Erro na instalação (código {returncode}):\n{output_str}"
                return False
            
            return True
            
        except FileNotFoundError:
            self.error = "Interpretador Python ou comando pip não pôde ser executado."
            return False
        except Exception as e:
            self.error = f"Erro inesperado: {str(e)}"
            return False

    def finished(self, result):
        if self.on_finish:
            self.on_finish(result, self.error)


def is_installed():
    """
    Verifica se a biblioteca OR-Tools está instalada e disponível no ambiente.

    Returns:
        bool: True se estiver instalada, False caso contrário.
    """
    return has_ortools()


def install(on_progress=None, on_finish=None):
    """
    Dispara a instalação do OR-Tools usando pip em uma QgsTask.

    Args:
        on_progress (callable): Callback chamado para cada linha de log (recebe str).
        on_finish (callable): Callback chamado ao terminar (recebe bool, str).

    Returns:
        QgsTask: A tarefa criada e adicionada ao gerenciador de tarefas do QGIS.
    """
    task = ORToolsInstallTask(on_finish=on_finish)
    if on_progress:
        task.log_received.connect(on_progress)
        
    if QgsApplication is not None and QgsApplication.taskManager() is not None:
        QgsApplication.taskManager().addTask(task)
    return task
