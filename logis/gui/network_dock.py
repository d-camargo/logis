# -*- coding: utf-8 -*-
"""
Painel (dock) para Rede Viária.

Licença: GPL-3.0
"""

try:
    from qgis.gui import QgsDockWidget
    from qgis.core import QgsProject, QgsProcessingFeedback
    from qgis.PyQt.QtCore import Qt, QCoreApplication
    from qgis.PyQt.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QMessageBox,
        QLineEdit,
        QComboBox,
        QScrollArea,
        QCheckBox,
        QTabWidget,
        QApplication,
        QProgressBar
    )
except ImportError:
    # Mocks para quando rodado fora do QGIS (ex: smoke tests ou CLI)
    class QgsDockWidget:
        def __init__(self, title, parent=None):
            pass
        def setWidget(self, widget):
            pass
    class QgsProject:
        @staticmethod
        def instance():
            return None
    class QgsProcessingFeedback:
        def __init__(self):
            pass
        def pushInfo(self, info):
            pass
        def pushWarning(self, warning):
            pass
        def setProgress(self, progress):
            pass
        def setProgressText(self, text):
            pass
    class QProgressBar:
        def __init__(self, parent=None):
            self._value = 0
            self._min = 0
            self._max = 100
            self._visible = False
            self._text_visible = True
            self._format = "%p%"
        def setRange(self, minimum, maximum):
            self._min = minimum
            self._max = maximum
        def setValue(self, value):
            self._value = value
        def setFormat(self, format_str):
            self._format = format_str
        def setVisible(self, visible):
            self._visible = visible
        def setTextVisible(self, visible):
            self._text_visible = visible
    class Qt:
        class CursorShape:
            WaitCursor = 0
    class QCoreApplication:
        @staticmethod
        def translate(context, text):
            return text
    class QWidget:
        def __init__(self, parent=None):
            pass
    class QVBoxLayout:
        def __init__(self, parent=None):
            pass
        def addWidget(self, widget, *args):
            pass
        def addLayout(self, layout, *args):
            pass
        def addStretch(self, *args):
            pass
        def setContentsMargins(self, *args):
            pass
        def setSpacing(self, *args):
            pass
    class QLabel:
        def __init__(self, text="", parent=None):
            pass
        def setStyleSheet(self, style):
            pass
        def setWordWrap(self, wrap):
            pass
    class QPushButton:
        def __init__(self, text="", parent=None):
            self.clicked = MockSignal()
        def setEnabled(self, enabled):
            pass
        def setStyleSheet(self, style):
            pass
    class QCheckBox:
        def __init__(self, text="", parent=None):
            self._checked = False
        def setChecked(self, checked):
            self._checked = checked
        def isChecked(self):
            return self._checked
    class MockSignal:
        def connect(self, slot):
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
        def setStyleSheet(self, style):
            pass
        def setMinimumHeight(self, height):
            pass
    class QMessageBox:
        @staticmethod
        def warning(parent, title, text):
            pass
        @staticmethod
        def critical(parent, title, text):
            pass
    class QLineEdit:
        def __init__(self, parent=None):
            pass
        def text(self):
            return ""
        def setText(self, text):
            pass
    class QComboBox:
        def __init__(self, parent=None):
            self.currentIndexChanged = MockSignal()
        def addItems(self, items):
            pass
        def addItem(self, text, data=None):
            pass
        def currentIndex(self):
            return 0
        def currentData(self):
            return None
        def currentText(self):
            return ""
        def clear(self):
            pass
    class QScrollArea:
        def __init__(self, parent=None):
            pass
        def setWidgetResizable(self, resizable):
            pass
        def setWidget(self, widget):
            pass
    class QTabWidget:
        def __init__(self, parent=None):
            self._tabs = []
        def addTab(self, widget, title):
            self._tabs.append(title)
            return len(self._tabs) - 1
        def count(self):
            return len(self._tabs)
        def tabText(self, index):
            return self._tabs[index]
    class QApplication:
        @staticmethod
        def setOverrideCursor(cursor):
            pass
        @staticmethod
        def restoreOverrideCursor():
            pass
        @staticmethod
        def processEvents():
            pass

from logis.core import ufs
from logis.core.data_backend import has_gisbr
from logis.core.network import municipios

class _DockFeedback(QgsProcessingFeedback):
    """
    Feedback customizado do Processing que redireciona mensagens e progresso
    para os componentes da UI do painel (dock).

    Origem: gisbr/gui/diagnostico_dock.py (_LogFeedback).
    """

    def __init__(self, log_fn, progress_bar=None):
        super().__init__()
        self.log_fn = log_fn
        self.progress_bar = progress_bar

    def pushInfo(self, info):
        super().pushInfo(info)
        if self.log_fn:
            self.log_fn(info)
        QApplication.processEvents()

    def pushWarning(self, warning):
        super().pushWarning(warning)
        if self.log_fn:
            self.log_fn(warning)
        QApplication.processEvents()

    def setProgress(self, progress):
        super().setProgress(progress)
        if self.progress_bar:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(progress))
        QApplication.processEvents()

    def setProgressText(self, text):
        super().setProgressText(text)
        if self.progress_bar:
            self.progress_bar.setFormat(f"{text} — %p%")
        QApplication.processEvents()


class NetworkDock(QgsDockWidget):
    """
    Painel lateral (Dock Widget) para Rede Viária.
    """

    def __init__(self, iface, parent=None):
        super().__init__(QCoreApplication.translate("NetworkDock", "logis — Rede Viária"), parent)
        self.iface = iface
        self._build_ui()

    def tr(self, string):
        return QCoreApplication.translate("NetworkDock", string)

    def _new_tab(self, title):
        """
        Cria uma aba com rolagem própria e devolve o layout onde as seções entram.
        """
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(10)

        tab_scroll = QScrollArea()
        tab_scroll.setWidgetResizable(True)
        tab_scroll.setWidget(page)

        self.tabs.addTab(tab_scroll, title)
        return page_layout

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(10)

        title_label = QLabel(self.tr("<b>Rede Viária</b>"))
        title_label.setStyleSheet("font-size: 14px; color: #2b6cb0; margin-bottom: 2px;")
        outer.addWidget(title_label)

        desc_label = QLabel(
            self.tr("O painel baixa arcos e nós direto para o projeto. O download roda em primeiro plano; acompanhe o andamento na barra de progresso.")
        )
        desc_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        desc_label.setWordWrap(True)
        outer.addWidget(desc_label)

        self.tabs = QTabWidget()
        
        # Aba Município (OSM)
        tab_muni = self._new_tab(self.tr("Município (OSM)"))
        
        tab_muni.addWidget(QLabel(self.tr("UF:")))
        self.cmb_uf_muni = QComboBox()
        self.cmb_uf_muni.addItems(ufs.siglas())
        tab_muni.addWidget(self.cmb_uf_muni)
        
        self.btn_list_munis = QPushButton(self.tr("Listar municípios da UF"))
        self.btn_list_munis.clicked.connect(self.list_municipalities)
        tab_muni.addWidget(self.btn_list_munis)
        
        tab_muni.addWidget(QLabel(self.tr("Município:")))
        self.cmb_muni = QComboBox()
        self.cmb_muni.currentIndexChanged.connect(self._on_muni_changed)
        tab_muni.addWidget(self.cmb_muni)
        
        tab_muni.addWidget(QLabel(self.tr("Código IBGE (7 dígitos):")))
        self.txt_code_muni = QLineEdit()
        tab_muni.addWidget(self.txt_code_muni)
        
        self.chk_force_osm = QCheckBox(self.tr("Forçar novo download (ignorar cache)"))
        tab_muni.addWidget(self.chk_force_osm)
        
        if has_gisbr("gisbr:osm_network"):
            src_txt = self.tr("Fonte: GisBR (gisbr:osm_network)")
        else:
            src_txt = self.tr("Fonte: pipeline interno do logis — instale o GisBR 0.11+ para usar o fluxo único")
        self.lbl_osm_source = QLabel(src_txt)
        tab_muni.addWidget(self.lbl_osm_source)

        self.btn_download_osm = QPushButton(self.tr("Baixar arcos e nós (OSM)"))
        self.btn_download_osm.clicked.connect(self.download_osm_network)
        tab_muni.addWidget(self.btn_download_osm)
        
        tab_muni.addStretch()
        
        # Aba Estado (SNV/DNIT)
        tab_snv = self._new_tab(self.tr("Estado (SNV/DNIT)"))
        
        tab_snv.addWidget(QLabel(self.tr("UF:")))
        self.cmb_uf_snv = QComboBox()
        self.cmb_uf_snv.addItems(ufs.siglas())
        tab_snv.addWidget(self.cmb_uf_snv)
        
        self.chk_force_snv = QCheckBox(self.tr("Forçar novo download (ignorar cache)"))
        tab_snv.addWidget(self.chk_force_snv)
        
        self.btn_download_snv = QPushButton(self.tr("Baixar arcos e nós (SNV)"))
        self.btn_download_snv.clicked.connect(self.download_snv_network)
        tab_snv.addWidget(self.btn_download_snv)
        
        tab_snv.addStretch()

        outer.addWidget(self.tabs)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        outer.addWidget(self.progress_bar)

        lbl_res = QLabel(self.tr("<b>Resultados:</b>"))
        outer.addWidget(lbl_res)

        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        self.txt_results.setMinimumHeight(150)
        outer.addWidget(self.txt_results)

        scroll.setWidget(central)
        self.setWidget(scroll)

    def _on_muni_changed(self):
        data = self.cmb_muni.currentData()
        if data:
            self.txt_code_muni.setText(municipios.normalize_code_muni(data))

    def _log(self, html):
        self.txt_results.append(html)

    def _error(self, msg):
        self.txt_results.append(f"<span style='color: #fc8181;'>{msg}</span>")

    def _set_busy(self, busy, texto=""):
        self.btn_list_munis.setEnabled(not busy)
        self.btn_download_osm.setEnabled(not busy)
        self.btn_download_snv.setEnabled(not busy)
        if busy:
            self.progress_bar.setRange(0, 0)
            if texto:
                self.progress_bar.setFormat(texto)
            self.progress_bar.setVisible(True)
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            QApplication.processEvents()
        else:
            self.progress_bar.setVisible(False)
            QApplication.restoreOverrideCursor()
            QApplication.processEvents()

    def list_municipalities(self):
        uf = self.cmb_uf_muni.currentText()
        if not uf:
            return
            
        self._set_busy(True, self.tr("Listando municípios…"))
        try:
            munis = municipios.list_municipios(uf)
            self.cmb_muni.clear()
            for code, nome in munis:
                self.cmb_muni.addItem(f"{nome} ({code})", code)
            self._log(self.tr(f"Municípios de {uf} carregados com sucesso."))
        except Exception as e:
            msg = self.tr(f"Erro ao listar municípios: {str(e)}")
            self._error(msg)
            QMessageBox.warning(self, self.tr("Erro"), msg)
        finally:
            self._set_busy(False)

    def download_osm_network(self):
        code_muni = municipios.normalize_code_muni(self.txt_code_muni.text().strip())
        if len(code_muni) != 7 or not code_muni.isdigit():
            msg = self.tr("Código IBGE do município deve possuir 7 dígitos.")
            self._error(msg)
            QMessageBox.warning(self, self.tr("Erro"), msg)
            return

        self._set_busy(True, self.tr("Baixando rede viária OSM…"))
        try:
            import processing
            from qgis.core import QgsProject

            fb = _DockFeedback(self._log, self.progress_bar)
            force = self.chk_force_osm.isChecked()
            nome_muni = ""
            selected = self.cmb_muni.currentData()
            if selected and municipios.normalize_code_muni(selected) == code_muni:
                nome_muni = self.cmb_muni.currentText().rsplit(" (", 1)[0].strip()
            params = {
                'INPUT_CODE_MUNI': code_muni,
                'INPUT_NOME_MUNI': nome_muni,
                'FORCE': force,
                'OUTPUT_LINKS': 'TEMPORARY_OUTPUT',
                'OUTPUT_NODES': 'TEMPORARY_OUTPUT'
            }
            res = processing.run("logis:load_osm_network", params, feedback=fb)

            place = nome_muni or code_muni
            links_layer = res.get('OUTPUT_LINKS') if res else None
            nodes_layer = res.get('OUTPUT_NODES') if res else None

            if links_layer is not None:
                if hasattr(links_layer, 'setName'):
                    links_layer.setName(f"Arcos OSM — {place}")
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(links_layer)

            if nodes_layer is not None:
                if hasattr(nodes_layer, 'setName'):
                    nodes_layer.setName(f"Nós OSM — {place}")
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(nodes_layer)

            n_links = links_layer.featureCount() if (links_layer and hasattr(links_layer, 'featureCount')) else 0
            n_nodes = nodes_layer.featureCount() if (nodes_layer and hasattr(nodes_layer, 'featureCount')) else 0
            source = "GisBR" if has_gisbr("gisbr:osm_network") else "logis"
            self._log(self.tr(f"Rede viária OSM ({code_muni}) carregada via {source}: {n_links} arcos, {n_nodes} nós."))
        except Exception as exc:
            self._error(str(exc))
        finally:
            self._set_busy(False)

    def download_snv_network(self):
        uf = self.cmb_uf_snv.currentText().strip()
        if not uf:
            msg = self.tr("Por favor, selecione uma UF.")
            self._error(msg)
            QMessageBox.warning(self, self.tr("Erro"), msg)
            return

        self._set_busy(True, self.tr("Baixando rede viária SNV…"))
        try:
            import processing
            from qgis.core import QgsProject

            fb = _DockFeedback(self._log, self.progress_bar)
            force = self.chk_force_snv.isChecked()
            params = {
                'INPUT_UF': uf,
                'FORCE': force,
                'OUTPUT_LINKS': 'TEMPORARY_OUTPUT',
                'OUTPUT_NODES': 'TEMPORARY_OUTPUT'
            }
            res = processing.run("logis:load_snv_network", params, feedback=fb)

            links_layer = res.get('OUTPUT_LINKS') if res else None
            nodes_layer = res.get('OUTPUT_NODES') if res else None

            if links_layer is not None:
                if hasattr(links_layer, 'setName'):
                    links_layer.setName(f"Arcos SNV — {uf}")
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(links_layer)

            if nodes_layer is not None:
                if hasattr(nodes_layer, 'setName'):
                    nodes_layer.setName(f"Nós SNV — {uf}")
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(nodes_layer)

            n_links = links_layer.featureCount() if (links_layer and hasattr(links_layer, 'featureCount')) else 0
            n_nodes = nodes_layer.featureCount() if (nodes_layer and hasattr(nodes_layer, 'featureCount')) else 0
            self._log(self.tr(f"Rede viária SNV ({uf}) carregada: {n_links} arcos, {n_nodes} nós."))
        except Exception as exc:
            self._error(str(exc))
        finally:
            self._set_busy(False)
