# -*- coding: utf-8 -*-
"""
Diálogo de gerenciamento de dependências para o plugin logis.

Licença: GPL-3.0
"""

try:
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QProgressBar,
        QTextEdit,
        QGroupBox,
        QMessageBox,
    )
    from qgis.utils import iface
except ImportError:
    # Mocks para quando rodado fora do QGIS (ex: smoke tests ou CLI)
    class Qt:
        Window = 0

        class WindowType:
            WindowMinMaxButtonsHint = 0
            WindowCloseButtonHint = 0

    class QDialog:
        def __init__(self, parent=None, flags=0):
            pass
        def setWindowTitle(self, title):
            pass
        def resize(self, w, h):
            pass
        def setMinimumSize(self, w, h):
            pass
        def setLayout(self, layout):
            pass
        def close(self):
            pass

    class QVBoxLayout:
        def __init__(self, parent=None):
            pass
        def addWidget(self, widget, *args, **kwargs):
            pass
        def addLayout(self, layout, *args, **kwargs):
            pass
        def addStretch(self, *args, **kwargs):
            pass
        def setContentsMargins(self, *args, **kwargs):
            pass
        def setSpacing(self, *args, **kwargs):
            pass

    class QHBoxLayout:
        def __init__(self, parent=None):
            pass
        def addWidget(self, widget, *args, **kwargs):
            pass
        def addLayout(self, layout, *args, **kwargs):
            pass
        def addStretch(self, *args, **kwargs):
            pass
        def setContentsMargins(self, *args, **kwargs):
            pass
        def setSpacing(self, *args, **kwargs):
            pass

    class QLabel:
        def __init__(self, text="", parent=None):
            self._text = text
        def setText(self, text):
            self._text = text
        def setStyleSheet(self, style):
            pass
        def setWordWrap(self, wrap):
            pass
        def setVisible(self, visible):
            pass

    class MockSignal:
        def connect(self, slot):
            pass

    class QPushButton:
        def __init__(self, text="", parent=None):
            self._text = text
            self.clicked = MockSignal()
        def setEnabled(self, enabled):
            pass
        def setText(self, text):
            self._text = text
        def setStyleSheet(self, style):
            pass

    class QProgressBar:
        def __init__(self, parent=None):
            pass
        def setRange(self, min_val, max_val):
            pass
        def setValue(self, val):
            pass
        def setVisible(self, visible):
            pass

    class QTextEdit:
        def __init__(self, parent=None):
            pass
        def setReadOnly(self, read_only):
            pass
        def append(self, text):
            pass
        def clear(self):
            pass
        def setVisible(self, visible):
            pass
        def verticalScrollBar(self):
            class DummyScrollBar:
                def setValue(self, val): pass
                def maximum(self): return 0
            return DummyScrollBar()

    class QGroupBox:
        def __init__(self, title="", parent=None):
            pass
        def setLayout(self, layout):
            pass
        def setStyleSheet(self, style):
            pass

    class QMessageBox:
        @staticmethod
        def information(parent, title, text):
            pass
        @staticmethod
        def warning(parent, title, text):
            pass
        @staticmethod
        def critical(parent, title, text):
            pass
    iface = None

from ..core.data_backend import has_gisbr
from ..core.optim_backend import has_ortools
from ..core.ortools_installer import install


class DependenciesDialog(QDialog):
    """
    Diálogo para verificar e gerenciar as dependências do plugin logis.
    Permite visualizar o status do GisBR e do Google OR-Tools, além de
    instalar o OR-Tools em segundo plano.
    """

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint,
        )
        self.setWindowTitle("logis — Gerenciador de Dependências")
        self.resize(550, 420)
        self.setMinimumSize(500, 350)
        
        self.install_task = None
        
        self.init_ui()
        self.refresh_status()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Título principal
        title_label = QLabel("<b>Gerenciador de Dependências</b>")
        title_label.setStyleSheet("font-size: 16px; color: #2b6cb0; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Verifique e instale as dependências recomendadas para o funcionamento "
            "completo do plugin de logística."
        )
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # --- SEÇÃO 1: GisBR ---
        self.gisbr_group = QGroupBox("GisBR (Fonte de Dados Viários)")
        self.gisbr_group.setStyleSheet("font-weight: bold; padding: 10px;")
        gisbr_layout = QVBoxLayout()
        gisbr_layout.setSpacing(8)
        
        gisbr_status_layout = QHBoxLayout()
        gisbr_status_lbl_title = QLabel("Status:")
        gisbr_status_lbl_title.setStyleSheet("font-weight: normal; color: #333;")
        self.gisbr_status_val = QLabel("Verificando...")
        self.gisbr_status_val.setStyleSheet("font-weight: bold;")
        gisbr_status_layout.addWidget(gisbr_status_lbl_title)
        gisbr_status_layout.addWidget(self.gisbr_status_val)
        gisbr_status_layout.addStretch()
        
        gisbr_layout.addLayout(gisbr_status_layout)
        
        gisbr_desc = QLabel(
            "O GisBR é o plugin do QGIS utilizado como fonte primária de dados viários municipais e demografia. "
            "Se não estiver instalado, o logis usará uma cópia interna como fallback."
        )
            
        gisbr_desc.setStyleSheet("font-weight: normal; color: #555; font-size: 11px;")
        gisbr_desc.setWordWrap(True)
        gisbr_layout.addWidget(gisbr_desc)
        
        self.btn_gisbr = QPushButton("Abrir Gerenciador de Complementos")
        self.btn_gisbr.setStyleSheet("font-weight: normal;")
        self.btn_gisbr.clicked.connect(self.open_plugin_manager)
        gisbr_layout.addWidget(self.btn_gisbr)
        
        self.gisbr_group.setLayout(gisbr_layout)
        layout.addWidget(self.gisbr_group)
        
        # --- SEÇÃO 2: OR-Tools ---
        self.ortools_group = QGroupBox("Google OR-Tools (Otimização de Rotas e Instalações)")
        self.ortools_group.setStyleSheet("font-weight: bold; padding: 10px;")
        ortools_layout = QVBoxLayout()
        ortools_layout.setSpacing(8)
        
        ortools_status_layout = QHBoxLayout()
        ortools_status_lbl_title = QLabel("Status:")
        ortools_status_lbl_title.setStyleSheet("font-weight: normal; color: #333;")
        self.ortools_status_val = QLabel("Verificando...")
        self.ortools_status_val.setStyleSheet("font-weight: bold;")
        ortools_status_layout.addWidget(ortools_status_lbl_title)
        ortools_status_layout.addWidget(self.ortools_status_val)
        ortools_status_layout.addStretch()
        
        ortools_layout.addLayout(ortools_status_layout)
        
        ortools_desc = QLabel(
            "O OR-Tools é uma biblioteca do Google para resolver problemas complexos de otimização de rotas "
            "e localização de instalações. O logis possui heurísticas internas em Python puro, mas o "
            "OR-Tools é recomendado para maior velocidade e precisão. "
            "A instalação usa versões travadas de numpy e pandas (numpy<2, pandas<3) "
            "para não danificar a instalação do QGIS."
        )
        ortools_desc.setStyleSheet("font-weight: normal; color: #555; font-size: 11px;")
        ortools_desc.setWordWrap(True)
        ortools_layout.addWidget(ortools_desc)
        
        self.btn_ortools = QPushButton("Instalar OR-Tools")
        self.btn_ortools.setStyleSheet("font-weight: normal;")
        self.btn_ortools.clicked.connect(self.start_ortools_install)
        ortools_layout.addWidget(self.btn_ortools)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        ortools_layout.addWidget(self.progress_bar)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(100)
        self.log_area.setStyleSheet(
            "font-family: monospace; font-size: 10px; background-color: #2d3748; color: #edf2f7; font-weight: normal;"
        )
        self.log_area.setVisible(False)
        ortools_layout.addWidget(self.log_area)
        
        self.lbl_restart_warning = QLabel(
            "⚠️ <b>Nota:</b> Após a instalação ser concluída com sucesso, reinicie o QGIS "
            "para carregar a biblioteca."
        )
        self.lbl_restart_warning.setStyleSheet("color: #dd6b20; font-size: 11px; font-weight: normal;")
        self.lbl_restart_warning.setWordWrap(True)
        self.lbl_restart_warning.setVisible(False)
        ortools_layout.addWidget(self.lbl_restart_warning)
        
        self.ortools_group.setLayout(ortools_layout)
        layout.addWidget(self.ortools_group)
        
        # --- Botão Fechar no rodapé ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.btn_close = QPushButton("Fechar")
        self.btn_close.clicked.connect(self.close)
        button_layout.addWidget(self.btn_close)
        layout.addLayout(button_layout)

    def refresh_status(self):
        # 1. GisBR
        if has_gisbr():
            self.gisbr_status_val.setText("Instalado (Disponível)")
            self.gisbr_status_val.setStyleSheet("color: #2f855a; font-weight: bold;")
        else:
            self.gisbr_status_val.setText("Não instalado (Fallback ativado)")
            self.gisbr_status_val.setStyleSheet("color: #c53030; font-weight: bold;")
            
        # 2. OR-Tools
        if has_ortools():
            self.ortools_status_val.setText("Instalado (Disponível)")
            self.ortools_status_val.setStyleSheet("color: #2f855a; font-weight: bold;")
            self.btn_ortools.setEnabled(False)
            self.btn_ortools.setText("OR-Tools já instalado")
        else:
            self.ortools_status_val.setText("Não instalado (Heurística pura ativada)")
            self.ortools_status_val.setStyleSheet("color: #dd6b20; font-weight: bold;")
            self.btn_ortools.setEnabled(True)
            self.btn_ortools.setText("Instalar OR-Tools")

    def open_plugin_manager(self):
        if iface is not None:
            iface.showPluginManager()
        else:
            QMessageBox.warning(
                self,
                "Aviso",
                "O Gerenciador de Complementos só pode ser aberto dentro do QGIS."
            )
            
    def start_ortools_install(self):
        self.btn_ortools.setEnabled(False)
        self.btn_close.setEnabled(False)
        
        self.progress_bar.setVisible(True)
        self.log_area.setVisible(True)
        self.log_area.clear()
        self.log_area.append("Iniciando a instalação do Google OR-Tools...")
        
        try:
            self.install_task = install(
                on_progress=self.on_install_progress,
                on_finish=self.on_install_finish
            )
        except Exception as e:
            self.on_install_finish(False, f"Erro ao disparar tarefa: {str(e)}")
            
    def on_install_progress(self, message):
        self.log_area.append(message)
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def on_install_finish(self, success, error):
        self.progress_bar.setVisible(False)
        self.btn_close.setEnabled(True)
        
        if success:
            self.log_area.append("\nInstalação concluída com sucesso!")
            self.ortools_status_val.setText("Instalado (Pendente reiniciar)")
            self.ortools_status_val.setStyleSheet("color: #2f855a; font-weight: bold;")
            self.lbl_restart_warning.setVisible(True)
            
            QMessageBox.information(
                self,
                "Instalação Concluída",
                "Google OR-Tools foi instalado com sucesso!\n\n"
                "Por favor, reinicie o QGIS para carregar a biblioteca."
            )
        else:
            self.log_area.append(f"\nErro durante a instalação:\n{error}")
            self.btn_ortools.setEnabled(True)
            
            QMessageBox.critical(
                self,
                "Erro na Instalação",
                f"Falha ao instalar o Google OR-Tools:\n{error}"
            )
