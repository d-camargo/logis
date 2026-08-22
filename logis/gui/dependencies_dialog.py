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
        QTextEdit,
        QGroupBox,
        QMessageBox,
        QScrollArea,
        QWidget,
        QApplication,
    )
    from qgis.utils import iface
except ImportError:
    # Mocks para quando rodado fora do QGIS (ex: smoke tests ou CLI)
    class MockClipboard:
        def setText(self, text):
            pass

    class QApplication:
        @staticmethod
        def clipboard():
            return MockClipboard()
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
        def setVisible(self, visible):
            pass

    class QTextEdit:
        def __init__(self, parent=None):
            self._text = ""
        def setReadOnly(self, read_only):
            pass
        def append(self, text):
            self._text += str(text) + "\n"
        def setText(self, text):
            self._text = str(text)
        def toPlainText(self):
            return self._text
        def clear(self):
            self._text = ""
        def setVisible(self, visible):
            pass
        def setMaximumHeight(self, h):
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

    class QWidget:
        def __init__(self, parent=None):
            pass
        def setLayout(self, layout):
            pass

    class QScrollArea:
        def __init__(self, parent=None):
            pass
        def setWidgetResizable(self, resizable):
            pass
        def setWidget(self, widget):
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
from ..core.ortools_installer import command_text


class DependenciesDialog(QDialog):
    """
    Diálogo para verificar e orientar a instalação de dependências do plugin logis.
    Permite visualizar o status do GisBR e do Google OR-Tools, exibindo o comando
    recomendado para a instalação manual do OR-Tools no ambiente do QGIS.
    """

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint,
        )
        self.setWindowTitle("logis — Gerenciador de Dependências")
        self.resize(620, 560)
        self.setMinimumSize(520, 420)
        
        self.init_ui()
        self.refresh_status()

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título principal
        title_label = QLabel("<b>Gerenciador de Dependências</b>")
        title_label.setStyleSheet("font-size: 16px; color: #2b6cb0; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Verifique as dependências recomendadas para o funcionamento "
            "completo do plugin de logística."
        )
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # --- SEÇÃO 1: GisBR ---
        self.gisbr_group = QGroupBox("GisBR (Fonte de Dados Viários)")
        self.gisbr_group.setStyleSheet("QGroupBox::title { font-weight: bold; }")
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
        self.ortools_group.setStyleSheet("QGroupBox::title { font-weight: bold; }")
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
            "OR-Tools é recomendado para maior velocidade e precisão.\n\n"
            "Por segurança, o plugin não executa comandos externos: ele monta o comando "
            "correto para ESTE ambiente Python do QGIS e cabe a você executá-lo. O comando "
            "fixa numpy, pandas e typing_extensions nas versões já instaladas no QGIS, "
            "para não danificar a instalação existente.\n\n"
            "Em instalações isoladas (Flatpak/Snap) a instalação pode não ser possível por "
            "falta de pacote binário para o Python do QGIS; nesse caso o plugin continua "
            "funcionando normalmente com as heurísticas em Python puro."
        )
        ortools_desc.setStyleSheet("font-weight: normal; color: #555; font-size: 11px;")
        ortools_desc.setWordWrap(True)
        ortools_layout.addWidget(ortools_desc)
        
        self.txt_command = QTextEdit()
        self.txt_command.setReadOnly(True)
        self.txt_command.setMaximumHeight(65)
        self.txt_command.setStyleSheet(
            "font-family: monospace; font-size: 10px; background-color: #2d3748; color: #edf2f7;"
        )
        ortools_layout.addWidget(self.txt_command)
        
        btn_cmd_layout = QHBoxLayout()
        self.btn_copy_cmd = QPushButton("Copiar Comando")
        self.btn_copy_cmd.setStyleSheet("font-weight: normal;")
        self.btn_copy_cmd.clicked.connect(self.copy_command)
        btn_cmd_layout.addWidget(self.btn_copy_cmd)
        btn_cmd_layout.addStretch()
        ortools_layout.addLayout(btn_cmd_layout)

        self.lbl_instructions = QLabel(
            "<b>Instruções de Instalação:</b><br>"
            "1. Clique em <b>Copiar Comando</b> acima.<br>"
            "2. Abra o console do Python que o QGIS usa — no Windows, o "
            "<i>OSGeo4W Shell</i>; no macOS, o Python embarcado do QGIS; no Linux, "
            "o terminal.<br>"
            "3. Cole e execute o comando. No Debian/Ubuntu, se o pip recusar com "
            "<i>externally-managed-environment</i>, acrescente "
            "<code>--break-system-packages</code> ao final e repita.<br>"
            "4. Reinicie o QGIS para carregar a biblioteca."
        )
        self.lbl_instructions.setStyleSheet("font-weight: normal; color: #555; font-size: 11px;")
        self.lbl_instructions.setWordWrap(True)
        ortools_layout.addWidget(self.lbl_instructions)
        
        self.ortools_group.setLayout(ortools_layout)
        layout.addWidget(self.ortools_group)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        # --- Botão Fechar no rodapé ---
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(15, 10, 15, 15)
        button_layout.addStretch()
        self.btn_close = QPushButton("Fechar")
        self.btn_close.clicked.connect(self.close)
        button_layout.addWidget(self.btn_close)
        outer_layout.addLayout(button_layout)

    def refresh_status(self):
        # 1. GisBR
        if has_gisbr():
            self.gisbr_status_val.setText("Instalado (Disponível)")
            self.gisbr_status_val.setStyleSheet("color: #2f855a; font-weight: bold;")
        else:
            self.gisbr_status_val.setText("Não instalado (Fallback ativado)")
            self.gisbr_status_val.setStyleSheet("color: #c53030; font-weight: bold;")
            
        # 2. OR-Tools
        self.txt_command.setText(command_text())
        self.btn_copy_cmd.setText("Copiar Comando")
        instalado = has_ortools()
        # Com o OR-Tools presente, o comando só polui a tela.
        self.txt_command.setVisible(not instalado)
        self.btn_copy_cmd.setVisible(not instalado)
        self.lbl_instructions.setVisible(not instalado)
        if instalado:
            self.ortools_status_val.setText("Instalado (Disponível)")
            self.ortools_status_val.setStyleSheet("color: #2f855a; font-weight: bold;")
        else:
            self.ortools_status_val.setText("Não instalado (Heurística pura ativada)")
            self.ortools_status_val.setStyleSheet("color: #dd6b20; font-weight: bold;")

    def open_plugin_manager(self):
        if iface is not None:
            iface.showPluginManager()
        else:
            QMessageBox.warning(
                self,
                "Aviso",
                "O Gerenciador de Complementos só pode ser aberto dentro do QGIS."
            )

    def copy_command(self):
        cmd = self.txt_command.toPlainText()
        if cmd:
            QApplication.clipboard().setText(cmd)
            self.btn_copy_cmd.setText("Comando copiado!")
