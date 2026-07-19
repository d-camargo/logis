# -*- coding: utf-8 -*-
"""
Painel (dock) para cálculo e exibição de Indicadores Urbanos.

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
        QSpinBox
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


class UrbanDock(QgsDockWidget):
    """
    Painel lateral (Dock Widget) para o cálculo e exibição de Indicadores Urbanos
    no plugin logis.
    """

    def __init__(self, iface, parent=None):
        super().__init__(QCoreApplication.translate("UrbanDock", "logis — Indicadores Urbanos"), parent)
        self.iface = iface
        self._build_ui()

    def tr(self, string):
        return QCoreApplication.translate("UrbanDock", string)

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Título principal
        title_label = QLabel(self.tr("<b>Indicadores Urbanos</b>"))
        title_label.setStyleSheet("font-size: 14px; color: #2b6cb0; margin-bottom: 2px;")
        layout.addWidget(title_label)

        desc_label = QLabel(
            self.tr(
                "Selecione as camadas e clique no botão abaixo para calcular os indicadores "
                "de densidade, conectividade, circuidade e restrição de circulação de carga."
            )
        )
        desc_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Seletor de Camada de Rede (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de rede viária (Linhas):")))
        self.cmb_network = QgsMapLayerComboBox()
        self.cmb_network.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_network)

        # Seletor de Camada de Área (Polígonos)
        layout.addWidget(QLabel(self.tr("Camada de área de referência (Polígonos - para Densidade):")))
        self.cmb_area = QgsMapLayerComboBox()
        self.cmb_area.setFilters(QgsMapLayerProxyModel.Filter.PolygonLayer)
        layout.addWidget(self.cmb_area)

        # Botão Calcular
        self.btn_calculate = QPushButton(self.tr("Calcular Indicadores"))
        self.btn_calculate.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_calculate.clicked.connect(self.calculate_indicators)
        layout.addWidget(self.btn_calculate)

        # Painel de resultados
        layout.addWidget(QLabel(self.tr("Resultados dos Indicadores:")))
        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        self.txt_results.setMinimumHeight(150)
        self.txt_results.setStyleSheet(
            "font-family: monospace; font-size: 11px; background-color: #2d3748; color: #edf2f7; padding: 5px;"
        )
        layout.addWidget(self.txt_results)

        # Seção adicional: Densidade de Demanda
        demand_title = QLabel(self.tr("<b>Densidade de Demanda</b>"))
        demand_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 8px;")
        layout.addWidget(demand_title)

        layout.addWidget(QLabel(self.tr("Código IBGE do município (7 dígitos):")))
        self.txt_code_muni = QLineEdit()
        layout.addWidget(self.txt_code_muni)

        layout.addWidget(QLabel(self.tr("Campo de população (setor + censobr, requer GisBR):")))
        self.txt_population_field = QLineEdit()
        layout.addWidget(self.txt_population_field)

        self.btn_calculate_demand = QPushButton(self.tr("Calcular Densidade de Demanda"))
        self.btn_calculate_demand.clicked.connect(self.calculate_demand_density)
        layout.addWidget(self.btn_calculate_demand)

        # Seção adicional: Acessibilidade Gravitacional
        gravity_title = QLabel(self.tr("<b>Acessibilidade Gravitacional</b>"))
        gravity_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 8px;")
        layout.addWidget(gravity_title)

        layout.addWidget(QLabel(self.tr("Camada de origem (pontos/centroides):")))
        self.cmb_gravity_origin = QgsMapLayerComboBox()
        self.cmb_gravity_origin.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_gravity_origin)

        layout.addWidget(QLabel(self.tr("Camada de destinos (POIs):")))
        self.cmb_gravity_dest = QgsMapLayerComboBox()
        self.cmb_gravity_dest.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_gravity_dest)

        layout.addWidget(QLabel(self.tr("Campo de peso do destino (opcional, default 1):")))
        self.cmb_gravity_weight_field = QgsFieldComboBox()
        self.cmb_gravity_weight_field.setLayer(self.cmb_gravity_dest.currentLayer())
        self.cmb_gravity_dest.layerChanged.connect(self.cmb_gravity_weight_field.setLayer)
        layout.addWidget(self.cmb_gravity_weight_field)

        layout.addWidget(QLabel(self.tr("Beta (decaimento por distância):")))
        self.spin_gravity_beta = QDoubleSpinBox()
        self.spin_gravity_beta.setRange(0.0001, 10.0)
        self.spin_gravity_beta.setSingleStep(0.1)
        self.spin_gravity_beta.setValue(2.0)
        layout.addWidget(self.spin_gravity_beta)

        self.btn_calculate_gravity = QPushButton(self.tr("Calcular Acessibilidade Gravitacional"))
        self.btn_calculate_gravity.clicked.connect(self.calculate_gravity_accessibility)
        layout.addWidget(self.btn_calculate_gravity)

        # Seção adicional: Centralidade de Intermediação (Betweenness)
        betweenness_title = QLabel(self.tr("<b>Centralidade de Intermediação (Betweenness)</b>"))
        betweenness_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 8px;")
        layout.addWidget(betweenness_title)

        layout.addWidget(QLabel(self.tr("Número de amostras (pares OD):")))
        self.spin_betweenness_samples = QSpinBox()
        self.spin_betweenness_samples.setRange(1, 1000000)
        self.spin_betweenness_samples.setValue(1000)
        layout.addWidget(self.spin_betweenness_samples)

        self.btn_calculate_betweenness = QPushButton(self.tr("Calcular Centralidade de Intermediação"))
        self.btn_calculate_betweenness.clicked.connect(self.calculate_edge_betweenness)
        layout.addWidget(self.btn_calculate_betweenness)

        self.setWidget(central)

    def calculate_indicators(self):
        """
        Executa os quatro algoritmos de indicadores urbanos em sequência e
        exibe os resultados no painel de texto.
        """
        self.txt_results.clear()
        
        network_layer = self.cmb_network.currentLayer()
        area_layer = self.cmb_area.currentLayer()

        if not network_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de rede viária.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Camada de rede viária não selecionada.</span>"))
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

        self.btn_calculate.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== INICIANDO CÁLCULO DOS INDICADORES ===</b><br>"))

        # 1) Densidade Viária
        if not area_layer:
            self.txt_results.append(self.tr("<i>1) Densidade viária: Pulado (camada de área não selecionada)</i><br>"))
        else:
            self.txt_results.append(self.tr("1) Calculando densidade viária..."))
            try:
                res_density = processing.run("logis:urban_network_density", {
                    'INPUT_NETWORK': network_layer,
                    'INPUT_AREA': area_layer
                })
                density_val = res_density.get('OUTPUT')
                if density_val is not None:
                    self.txt_results.append(
                        self.tr("   -> <b>Densidade viária:</b> {value:.4f} km/km²<br>").format(value=density_val)
                    )
                else:
                    self.txt_results.append(self.tr("   -> <b>Densidade viária:</b> N/A (resultado vazio)<br>"))
            except Exception as e:
                self.txt_results.append(
                    self.tr("   -> <span style='color: #fc8181;'>Erro ao calcular densidade: {error}</span><br>").format(error=str(e))
                )

        # 2) Conectividade da Rede
        self.txt_results.append(self.tr("2) Calculando conectividade da rede..."))
        try:
            res_conn = processing.run("logis:urban_network_connectivity", {
                'INPUT_NETWORK': network_layer
            })
            nodes = res_conn.get('NUM_NODES')
            edges = res_conn.get('NUM_EDGES')
            alpha = res_conn.get('ALPHA')
            beta = res_conn.get('BETA')
            gamma = res_conn.get('GAMMA')
            pct_4 = res_conn.get('PCT_4_WAY')
            pct_dead = res_conn.get('PCT_DEAD_ENDS')

            self.txt_results.append(self.tr("   -> <b>Número de nós (v):</b> {v}").format(v=nodes))
            self.txt_results.append(self.tr("   -> <b>Número de arestas (e):</b> {e}").format(e=edges))
            if alpha is not None:
                self.txt_results.append(self.tr("   -> <b>Índice Alfa:</b> {v:.4f}").format(v=alpha))
            if beta is not None:
                self.txt_results.append(self.tr("   -> <b>Índice Beta:</b> {v:.4f}").format(v=beta))
            if gamma is not None:
                self.txt_results.append(self.tr("   -> <b>Índice Gama:</b> {v:.4f}").format(v=gamma))
            if pct_4 is not None:
                self.txt_results.append(self.tr("   -> <b>Cruzamentos 4+ pernas:</b> {v:.2f}%").format(v=pct_4))
            if pct_dead is not None:
                self.txt_results.append(self.tr("   -> <b>Becos sem saída:</b> {v:.2f}%<br>").format(v=pct_dead))
        except Exception as e:
            self.txt_results.append(
                self.tr("   -> <span style='color: #fc8181;'>Erro ao calcular conectividade: {error}</span><br>").format(error=str(e))
            )

        # 3) Circuidade Média
        self.txt_results.append(self.tr("3) Calculando circuidade média (amostragem)..."))
        try:
            res_circ = processing.run("logis:urban_mean_circuity", {
                'INPUT_NETWORK': network_layer,
                'NUM_SAMPLES': 1000,
                'MIN_DISTANCE': 100.0
            })
            circ_val = res_circ.get('OUTPUT')
            if circ_val is not None:
                self.txt_results.append(
                    self.tr("   -> <b>Circuidade média:</b> {value:.4f}<br>").format(value=circ_val)
                )
            else:
                self.txt_results.append(self.tr("   -> <b>Circuidade média:</b> N/A (resultado vazio)<br>"))
        except Exception as e:
            self.txt_results.append(
                self.tr("   -> <span style='color: #fc8181;'>Erro ao calcular circuidade: {error}</span><br>").format(error=str(e))
            )

        # 4) Restrição de Carga
        self.txt_results.append(self.tr("4) Calculando acessibilidade/restrição de carga..."))
        try:
            res_rest = processing.run("logis:urban_cargo_restriction", {
                'INPUT_NETWORK': network_layer,
                'RESTRICTION_EXPRESSION': ''
            })
            rest_val = res_rest.get('OUTPUT')
            if rest_val is not None:
                self.txt_results.append(
                    self.tr("   -> <b>Acessibilidade de carga:</b> {value:.2f}%<br>").format(value=rest_val)
                )
            else:
                self.txt_results.append(self.tr("   -> <b>Acessibilidade de carga:</b> N/A (resultado vazio)<br>"))
        except Exception as e:
            self.txt_results.append(
                self.tr("   -> <span style='color: #fc8181;'>Erro ao calcular restrição: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_calculate.setEnabled(True)

    def calculate_demand_density(self):
        """
        Executa o algoritmo de densidade de demanda (população/km² por setor
        censitário) para o município e campo de população informados.
        """
        code_muni = self.txt_code_muni.text().strip()
        population_field = self.txt_population_field.text().strip()

        if not code_muni:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, informe o código IBGE do município.")
            )
            return
        if not population_field:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, informe o campo de população.")
            )
            return

        try:
            import processing
        except ImportError:
            QMessageBox.critical(
                self,
                self.tr("Erro"),
                self.tr("QGIS Processing não está disponível no ambiente atual.")
            )
            return

        self.txt_results.append(self.tr("<b>Calculando densidade de demanda...</b>"))
        try:
            res = processing.run("logis:urban_demand_density", {
                'INPUT_CODE_MUNI': code_muni,
                'FIELD_POPULATION': population_field,
                'OUTPUT': 'memory:'
            })
            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                QgsProject.instance().addMapLayer(out_layer)
                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else '?'
                self.txt_results.append(
                    self.tr("   -> <b>Densidade de demanda:</b> camada adicionada ao projeto com {count} setor(es).<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("   -> <b>Densidade de demanda:</b> N/A (resultado vazio)<br>"))
        except Exception as e:
            self.txt_results.append(
                self.tr("   -> <span style='color: #fc8181;'>Erro ao calcular densidade de demanda: {error}</span><br>").format(error=str(e))
            )

    def calculate_gravity_accessibility(self):
        """
        Executa o algoritmo de acessibilidade gravitacional sobre a rede viária,
        a camada de origem e a camada de destinos (POIs) selecionadas.
        """
        network_layer = self.cmb_network.currentLayer()
        origin_layer = self.cmb_gravity_origin.currentLayer()
        dest_layer = self.cmb_gravity_dest.currentLayer()
        weight_field = self.cmb_gravity_weight_field.currentField()
        beta = self.spin_gravity_beta.value()

        if not network_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de rede viária.")
            )
            return
        if not origin_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de origem.")
            )
            return
        if not dest_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de destinos.")
            )
            return

        try:
            import processing
        except ImportError:
            QMessageBox.critical(
                self,
                self.tr("Erro"),
                self.tr("QGIS Processing não está disponível no ambiente atual.")
            )
            return

        self.txt_results.append(self.tr("<b>Calculando acessibilidade gravitacional...</b>"))
        try:
            params = {
                'INPUT_NETWORK': network_layer,
                'INPUT_ORIGINS': origin_layer,
                'INPUT_DESTINATIONS': dest_layer,
                'BETA': beta,
                'OUTPUT': 'memory:'
            }
            if weight_field:
                params['FIELD_WEIGHT'] = weight_field
            res = processing.run("logis:urban_gravity_accessibility", params)
            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                QgsProject.instance().addMapLayer(out_layer)
                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else '?'
                self.txt_results.append(
                    self.tr("   -> <b>Acessibilidade gravitacional:</b> camada adicionada ao projeto com {count} origem(ns).<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("   -> <b>Acessibilidade gravitacional:</b> N/A (resultado vazio)<br>"))
        except Exception as e:
            self.txt_results.append(
                self.tr("   -> <span style='color: #fc8181;'>Erro ao calcular acessibilidade gravitacional: {error}</span><br>").format(error=str(e))
            )

    def calculate_edge_betweenness(self):
        """
        Executa o algoritmo de centralidade de intermediação (betweenness) aproximada
        das arestas da rede viária selecionada, por amostragem de pares OD.
        """
        network_layer = self.cmb_network.currentLayer()
        num_samples = self.spin_betweenness_samples.value()

        if not network_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione uma camada de rede viária.")
            )
            return

        try:
            import processing
        except ImportError:
            QMessageBox.critical(
                self,
                self.tr("Erro"),
                self.tr("QGIS Processing não está disponível no ambiente atual.")
            )
            return

        self.txt_results.append(self.tr("<b>Calculando centralidade de intermediação...</b>"))
        try:
            res = processing.run("logis:urban_edge_betweenness", {
                'INPUT_NETWORK': network_layer,
                'NUM_SAMPLES': num_samples,
                'OUTPUT': 'memory:'
            })
            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                QgsProject.instance().addMapLayer(out_layer)
                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else '?'
                self.txt_results.append(
                    self.tr("   -> <b>Centralidade de intermediação:</b> camada adicionada ao projeto com {count} aresta(s).<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("   -> <b>Centralidade de intermediação:</b> N/A (resultado vazio)<br>"))
        except Exception as e:
            self.txt_results.append(
                self.tr("   -> <span style='color: #fc8181;'>Erro ao calcular centralidade de intermediação: {error}</span><br>").format(error=str(e))
            )
