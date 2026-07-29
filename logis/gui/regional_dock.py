# -*- coding: utf-8 -*-
"""
Painel (dock) para cálculo e exibição de Indicadores Regionais.

Licença: GPL-3.0
"""

try:
    from qgis.gui import QgsDockWidget, QgsMapLayerComboBox, QgsFieldComboBox
    from qgis.core import QgsMapLayerProxyModel, QgsProject
    from qgis.PyQt.QtCore import Qt, QCoreApplication
    from qgis.PyQt.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QMessageBox,
        QLineEdit,
        QDoubleSpinBox,
        QSpinBox,
        QComboBox,
        QScrollArea
    )
except ImportError:
    # Mocks para quando rodado fora do QGIS (ex: smoke tests ou CLI)
    class QgsDockWidget:
        def __init__(self, title, parent=None):
            pass
        def setWidget(self, widget):
            pass
    class QgsMapLayerComboBox:
        def __init__(self, parent=None):
            pass
        def setFilters(self, filters):
            pass
        def currentLayer(self):
            return None
    class QgsMapLayerProxyModel:
        class Filter:
            LineLayer = 1
            PolygonLayer = 2
            PointLayer = 3
    class QgsFieldComboBox:
        def __init__(self, parent=None):
            pass
        def setLayer(self, layer):
            pass
        def currentField(self):
            return None
    class QgsProject:
        @staticmethod
        def instance():
            return None
    class Qt:
        pass
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
    class QHBoxLayout:
        def __init__(self, parent=None):
            pass
        def addWidget(self, widget, *args):
            pass
        def addLayout(self, layout, *args):
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
    class QDoubleSpinBox:
        def __init__(self, parent=None):
            pass
        def setRange(self, minimum, maximum):
            pass
        def setValue(self, value):
            pass
        def setSingleStep(self, step):
            pass
        def value(self):
            return 2.0
    class QSpinBox:
        def __init__(self, parent=None):
            pass
        def setRange(self, minimum, maximum):
            pass
        def setValue(self, value):
            pass
        def value(self):
            return 1000
    class QComboBox:
        def __init__(self, parent=None):
            pass
        def addItems(self, items):
            pass
        def currentIndex(self):
            return 0
    class QScrollArea:
        def __init__(self, parent=None):
            pass
        def setWidgetResizable(self, resizable):
            pass
        def setWidget(self, widget):
            pass


class RegionalDock(QgsDockWidget):
    """
    Painel lateral (Dock Widget) para o cálculo e exibição de Indicadores Regionais
    no plugin logis.
    """

    def __init__(self, iface, parent=None):
        super().__init__(QCoreApplication.translate("RegionalDock", "logis — Indicadores Regionais"), parent)
        self.iface = iface
        self._build_ui()

    def tr(self, string):
        return QCoreApplication.translate("RegionalDock", string)

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Título principal
        title_label = QLabel(self.tr("<b>Indicadores Regionais</b>"))
        title_label.setStyleSheet("font-size: 14px; color: #2b6cb0; margin-bottom: 2px;")
        layout.addWidget(title_label)

        desc_label = QLabel(
            self.tr(
                "Selecione as camadas e parâmetros abaixo para calcular os indicadores "
                "de densidade rodoviária regional e percentual de pavimentação."
            )
        )
        desc_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Seletor de Camada de Rede (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de rede regional (Linhas):")))
        self.cmb_network = QgsMapLayerComboBox()
        self.cmb_network.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_network)

        # Seletor de Camada de Área (Polígonos)
        layout.addWidget(QLabel(self.tr("Camada de área de referência (Polígonos - para Densidade):")))
        self.cmb_area = QgsMapLayerComboBox()
        self.cmb_area.setFilters(QgsMapLayerProxyModel.Filter.PolygonLayer)
        layout.addWidget(self.cmb_area)

        # Campo numérico de população
        layout.addWidget(QLabel(self.tr("População da área de referência (habitantes):")))
        self.spin_population = QSpinBox()
        self.spin_population.setRange(1, 2000000000)
        self.spin_population.setValue(21000000)  # Valor padrão razoável (ex: população de MG ~21M)
        layout.addWidget(self.spin_population)

        # Botão Calcular Densidade Rodoviária
        self.btn_calculate_density = QPushButton(self.tr("Calcular Densidade Rodoviária"))
        self.btn_calculate_density.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_calculate_density.clicked.connect(self.calculate_road_density)
        layout.addWidget(self.btn_calculate_density)

        # Botão Calcular % Pavimentação
        self.btn_calculate_pavement = QPushButton(self.tr("Calcular % Pavimentação"))
        self.btn_calculate_pavement.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_calculate_pavement.clicked.connect(self.calculate_pavement_percentage)
        layout.addWidget(self.btn_calculate_pavement)

        # Botão Calcular Pontes/Arcos Críticos
        self.btn_calculate_critical_links = QPushButton(self.tr("Calcular Pontes/Arcos Críticos"))
        self.btn_calculate_critical_links.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_calculate_critical_links.clicked.connect(self.calculate_critical_links)
        layout.addWidget(self.btn_calculate_critical_links)

        # Painel de resultados
        layout.addWidget(QLabel(self.tr("Resultados dos Indicadores Regionais:")))
        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        self.txt_results.setMinimumHeight(150)
        self.txt_results.setStyleSheet(
            "font-family: monospace; font-size: 11px; background-color: #2d3748; color: #edf2f7; padding: 5px;"
        )
        layout.addWidget(self.txt_results)

        layout.addStretch()

        scroll.setWidget(central)
        self.setWidget(scroll)

    def calculate_road_density(self):
        """
        Executa o algoritmo de densidade de rede regional e exibe os resultados.
        """
        self.txt_results.clear()
        
        network_layer = self.cmb_network.currentLayer()
        area_layer = self.cmb_area.currentLayer()
        population = self.spin_population.value()

        if not network_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de rede regional.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Camada de rede regional não selecionada.</span>"))
            return

        if not area_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de área de referência.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Camada de área de referência não selecionada.</span>"))
            return

        try:
            import processing
        except ImportError:
            QMessageBox.critical(
                self,
                self.tr("Erro"),
                self.tr("QGIS Processing não está disponível no ambiente atual.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: QGIS Processing não disponível.</span>"))
            return

        self.btn_calculate_density.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== CALCULANDO DENSIDADE RODOVIÁRIA REGIONAL ===</b><br>"))

        try:
            res_density = processing.run("logis:regional_network_density", {
                'INPUT_NETWORK': network_layer,
                'INPUT_AREA': area_layer,
                'INPUT_POPULATION': population
            })
            density_area = res_density.get('OUTPUT_DENSITY_AREA')
            density_pop = res_density.get('OUTPUT_DENSITY_POP')
            
            if density_area is not None:
                self.txt_results.append(
                    self.tr("-> <b>Densidade por Área:</b> {value:.4f} km/1.000 km²").format(value=density_area)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Densidade por Área:</b> N/A"))

            if density_pop is not None:
                self.txt_results.append(
                    self.tr("-> <b>Densidade por População:</b> {value:.4f} km/10.000 hab.<br>").format(value=density_pop)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Densidade por População:</b> N/A<br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao calcular densidade: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_calculate_density.setEnabled(True)

    def calculate_pavement_percentage(self):
        """
        Executa o algoritmo de percentual de pavimentação regional e exibe os resultados.
        """
        self.txt_results.clear()
        
        network_layer = self.cmb_network.currentLayer()

        if not network_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de rede regional.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Camada de rede regional não selecionada.</span>"))
            return

        try:
            import processing
        except ImportError:
            QMessageBox.critical(
                self,
                self.tr("Erro"),
                self.tr("QGIS Processing não está disponível no ambiente atual.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: QGIS Processing não disponível.</span>"))
            return

        self.btn_calculate_pavement.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== CALCULANDO PERCENTUAL DE PAVIMENTAÇÃO ===</b><br>"))

        try:
            res_pavement = processing.run("logis:regional_pavement_percentage", {
                'INPUT_NETWORK': network_layer,
                'FIELD_SURFACE': 'ds_superfi'
            })
            pct_paved = res_pavement.get('OUTPUT_PCT_PAVED')
            pct_dup = res_pavement.get('OUTPUT_PCT_DUP')
            
            if pct_paved is not None:
                self.txt_results.append(
                    self.tr("-> <b>Percentual Pavimentada:</b> {value:.2f}%").format(value=pct_paved)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Percentual Pavimentada:</b> N/A"))

            if pct_dup is not None:
                self.txt_results.append(
                    self.tr("-> <b>Percentual Duplicada:</b> {value:.2f}%<br>").format(value=pct_dup)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Percentual Duplicada:</b> N/A<br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao calcular pavimentação: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_calculate_pavement.setEnabled(True)

    def calculate_critical_links(self):
        """
        Executa o algoritmo de identificação de pontes/arcos críticos da malha
        regional e exibe os resultados.
        """
        self.txt_results.clear()

        network_layer = self.cmb_network.currentLayer()

        if not network_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de rede regional.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Camada de rede regional não selecionada.</span>"))
            return

        try:
            import processing
        except ImportError:
            QMessageBox.critical(
                self,
                self.tr("Erro"),
                self.tr("QGIS Processing não está disponível no ambiente atual.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: QGIS Processing não disponível.</span>"))
            return

        self.btn_calculate_critical_links.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== CALCULANDO PONTES/ARCOS CRÍTICOS ===</b><br>"))

        try:
            res_critical = processing.run("logis:regional_critical_links", {
                'INPUT_NETWORK': network_layer,
                'OUTPUT': 'memory:'
            })
            output_layer = res_critical.get('OUTPUT')
            num_bridges = res_critical.get('OUTPUT_NUM_CRITICAL_LINKS')
            total = output_layer.featureCount() if output_layer is not None else 0

            if output_layer is not None:
                QgsProject.instance().addMapLayer(output_layer)

            self.txt_results.append(
                self.tr("-> <b>Pontes/Arcos Críticos:</b> {n} de {total} trechos.<br>").format(
                    n=num_bridges, total=total
                )
            )

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao calcular pontes/arcos críticos: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_calculate_critical_links.setEnabled(True)
