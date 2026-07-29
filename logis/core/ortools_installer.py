# -*- coding: utf-8 -*-
"""
Módulo para instalação e verificação da biblioteca Google OR-Tools.

Licença: GPL-3.0
"""

import sys
import subprocess

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

    def build_command(self, break_system_packages=False):
        """
        Monta o comando pip da seção 2.1 do CLAUDE.md.

        As travas de pandas/numpy/typing_extensions evitam que o pip danifique
        a instalação do QGIS do usuário (numpy 2.x sobrepondo o 1.26.4 do QGIS
        3.34, ou desinstalação órfã do typing_extensions da distro). Nunca usar
        `pip install ortools` puro.
        """
        cmd = [
            sys.executable, "-m", "pip", "install", "--user",
            "ortools", "pandas<3", "numpy<2", "typing_extensions==4.10.0",
        ]
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
                elif any(err in output_str for err in ["ConnectionError", "Could not find a version", "Network is unreachable", "Temporary failure in name resolution"]):
                    self.error = (
                        "Falha de rede ao tentar baixar o OR-Tools. "
                        "Verifique sua conexão com a internet."
                    )
                elif any(err in output_str for err in ["PermissionError", "Permission denied", "Access is denied"]):
                    self.error = (
                        "Erro de permissão ao instalar o OR-Tools. "
                        "Tente executar o QGIS com privilégios administrativos."
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
