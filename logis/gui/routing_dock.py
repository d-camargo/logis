# -*- coding: utf-8 -*-
"""
Painel (dock) para Roteirização (TSP/VRP).

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
        QScrollArea,
        QCheckBox,
        QTabWidget
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
            self.layerChanged = MockSignal()
        def setFilters(self, filters):
            pass
        def setAllowEmptyLayer(self, allow):
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
        def setAllowEmptyFieldName(self, allow):
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


class RoutingDock(QgsDockWidget):
    """
    Painel lateral (Dock Widget) para Roteirização (TSP/VRP)
    no plugin logis.
    """

    def __init__(self, iface, parent=None):
        super().__init__(QCoreApplication.translate("RoutingDock", "logis — Roteirização"), parent)
        self.iface = iface
        self._build_ui()

    def tr(self, string):
        return QCoreApplication.translate("RoutingDock", string)

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

        # Título principal
        title_label = QLabel(self.tr("<b>Roteirização</b>"))
        title_label.setStyleSheet("font-size: 14px; color: #2b6cb0; margin-bottom: 2px;")
        outer.addWidget(title_label)

        desc_label = QLabel(
            self.tr(
                "O painel reúne o Caixeiro Viajante e a Roteirização de Veículos "
                "Capacitados; a camada de rede viária escolhida abaixo vale para as duas abas."
            )
        )
        desc_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        desc_label.setWordWrap(True)
        outer.addWidget(desc_label)

        # Seletor de Camada de Rede Viária (Linhas - opcional)
        outer.addWidget(QLabel(self.tr("Camada de rede viária (Linhas - opcional):")))
        self.cmb_network = QgsMapLayerComboBox()
        self.cmb_network.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        if hasattr(self.cmb_network, 'setAllowEmptyLayer'):
            self.cmb_network.setAllowEmptyLayer(True)
        outer.addWidget(self.cmb_network)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)

        # Painel de resultados
        outer.addWidget(QLabel(self.tr("Resultados da Roteirização:")))
        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        self.txt_results.setMinimumHeight(150)
        self.txt_results.setStyleSheet(
            "font-family: monospace; font-size: 11px; background-color: #2d3748; color: #edf2f7; padding: 5px;"
        )
        outer.addWidget(self.txt_results)

        # Aba: TSP
        layout = self._new_tab(self.tr("TSP"))

        # Seletor de Camada do Ponto Inicial (Pontos)
        layout.addWidget(QLabel(self.tr("Camada do ponto inicial (Pontos):")))
        self.cmb_start = QgsMapLayerComboBox()
        self.cmb_start.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_start)

        # Seletor de Camada de Pontos a Visitar (Pontos)
        layout.addWidget(QLabel(self.tr("Camada de pontos a visitar (Pontos):")))
        self.cmb_points = QgsMapLayerComboBox()
        self.cmb_points.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_points)

        # Seletor de Camada do Ponto Final (Pontos - opcional, vazio fecha no ponto inicial)
        layout.addWidget(QLabel(self.tr("Camada do ponto final (Pontos - opcional, vazio fecha no ponto inicial):")))
        self.cmb_end = QgsMapLayerComboBox()
        self.cmb_end.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        if hasattr(self.cmb_end, 'setAllowEmptyLayer'):
            self.cmb_end.setAllowEmptyLayer(True)
        layout.addWidget(self.cmb_end)

        # Checkbox para busca local (2-opt e Or-opt)
        self.chk_improve = QCheckBox(self.tr("Aplicar busca local (2-opt e Or-opt)"))
        self.chk_improve.setChecked(True)
        layout.addWidget(self.chk_improve)

        # Botão Calcular Rota (TSP)
        self.btn_run_tsp = QPushButton(self.tr("Calcular Rota (TSP)"))
        self.btn_run_tsp.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_tsp.clicked.connect(self.run_tsp)
        layout.addWidget(self.btn_run_tsp)

        layout.addStretch()

        # Aba: CVRP
        layout = self._new_tab(self.tr("CVRP"))

        cvrp_desc = QLabel(
            self.tr("Resolve a roteirização de uma frota com capacidade a partir de um depósito.")
        )
        cvrp_desc.setStyleSheet("color: #666; font-size: 11px;")
        cvrp_desc.setWordWrap(True)
        layout.addWidget(cvrp_desc)

        cvrp_net_desc = QLabel(
            self.tr("Nota: A camada de rede viária utilizada é a selecionada no topo do painel.")
        )
        cvrp_net_desc.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        cvrp_net_desc.setWordWrap(True)
        layout.addWidget(cvrp_net_desc)

        # Seletor de Camada de Depósito (Pontos)
        layout.addWidget(QLabel(self.tr("Camada de depósito (Pontos):")))
        self.cmb_depot = QgsMapLayerComboBox()
        self.cmb_depot.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_depot)

        # Seletor de Camada de Demanda / Clientes (Pontos)
        layout.addWidget(QLabel(self.tr("Camada de demanda / clientes (Pontos):")))
        self.cmb_demand = QgsMapLayerComboBox()
        self.cmb_demand.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_demand)

        # Seletor de Campo de Peso/Demanda (opcional)
        layout.addWidget(QLabel(self.tr("Campo de peso/demanda (opcional, default = 1,0):")))
        self.cmb_demand_field = QgsFieldComboBox()
        if hasattr(self.cmb_demand_field, 'setAllowEmptyFieldName'):
            self.cmb_demand_field.setAllowEmptyFieldName(True)
        self.cmb_demand_field.setLayer(self.cmb_demand.currentLayer())
        self.cmb_demand.layerChanged.connect(self.cmb_demand_field.setLayer)
        layout.addWidget(self.cmb_demand_field)

        # Capacidade do Veículo
        layout.addWidget(QLabel(self.tr("Capacidade do veículo:")))
        self.spin_capacity = QDoubleSpinBox()
        self.spin_capacity.setRange(0.0001, 1e9)
        self.spin_capacity.setValue(100.0)
        self.spin_capacity.setSingleStep(10.0)
        layout.addWidget(self.spin_capacity)

        # Checkbox para busca local (2-opt e Or-opt)
        self.chk_cvrp_improve = QCheckBox(self.tr("Aplicar busca local (2-opt e Or-opt)"))
        self.chk_cvrp_improve.setChecked(True)
        layout.addWidget(self.chk_cvrp_improve)

        # Botão Executar Roteirização (CVRP)
        self.btn_run_cvrp = QPushButton(self.tr("Executar Roteirização (CVRP)"))
        self.btn_run_cvrp.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_cvrp.clicked.connect(self.run_cvrp)
        layout.addWidget(self.btn_run_cvrp)

        layout.addStretch()

        scroll.setWidget(central)
        self.setWidget(scroll)

    def _attr(self, feat, fields, name, default):
        """
        Helper para leitura de atributo de uma feição por nome de campo.
        """
        if fields is not None and hasattr(fields, 'indexOf'):
            idx = fields.indexOf(name)
            if idx >= 0 and hasattr(feat, 'attributes'):
                attrs = feat.attributes()
                if 0 <= idx < len(attrs) and attrs[idx] is not None:
                    return attrs[idx]
        return default

    def run_tsp(self):
        """
        Executa o algoritmo de Caixeiro Viajante (TSP) e exibe os resultados.
        """
        self.txt_results.clear()

        start_layer = self.cmb_start.currentLayer()
        points_layer = self.cmb_points.currentLayer()
        end_layer = self.cmb_end.currentLayer()
        network_layer = self.cmb_network.currentLayer()
        improve = self.chk_improve.isChecked()

        if not start_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada do ponto inicial.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Ponto inicial não selecionado.</span>"))
            return

        if not points_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de pontos a visitar.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Pontos a visitar não selecionados.</span>"))
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

        self.btn_run_tsp.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== CALCULANDO ROTA (TSP) ===</b><br>"))

        try:
            params = {
                'INPUT_START': start_layer,
                'INPUT_POINTS': points_layer,
                'INPUT_END': end_layer if end_layer else None,
                'INPUT_NETWORK': network_layer if network_layer else None,
                'IMPROVE': improve,
                'OUTPUT_ORDER': 'memory:',
                'OUTPUT_ROUTE': 'memory:'
            }
            res = processing.run("logis:vrp_tsp", params)

            order_layer = res.get('OUTPUT_ORDER')
            route_layer = res.get('OUTPUT_ROUTE')

            if order_layer is not None:
                QgsProject.instance().addMapLayer(order_layer)
            if route_layer is not None:
                QgsProject.instance().addMapLayer(route_layer)

            num_visited = 0
            tour_dist = 0.0
            access_dist = 0.0
            return_dist = 0.0
            dead_ratio = 0.0
            is_closed = True
            backend_str = "N/A"

            if route_layer is not None and hasattr(route_layer, 'getFeatures'):
                feats = list(route_layer.getFeatures())
                if feats:
                    feat = feats[0]
                    fields = route_layer.fields() if hasattr(route_layer, 'fields') else None

                    num_visited = self._attr(feat, fields, 'stop_count', 0)
                    tour_dist = self._attr(feat, fields, 'tour_dist', 0.0)
                    access_dist = self._attr(feat, fields, 'access_dist', 0.0)
                    return_dist = self._attr(feat, fields, 'return_dist', 0.0)
                    dead_ratio = self._attr(feat, fields, 'dead_ratio', 0.0)
                    closed_val = self._attr(feat, fields, 'closed', 1)
                    is_closed = bool(closed_val)
                    backend_str = str(self._attr(feat, fields, 'backend', 'N/A'))

            if num_visited == 0 and order_layer is not None and hasattr(order_layer, 'featureCount'):
                count = order_layer.featureCount()
                num_visited = count - (2 if (end_layer and count >= 2) else 1) if count > 0 else 0
                if num_visited < 0:
                    num_visited = 0

            self.txt_results.append(
                self.tr("-> <b>Pontos visitados:</b> {n}").format(n=num_visited)
            )
            self.txt_results.append(
                self.tr("-> <b>Distância total do tour:</b> {dist:.2f}").format(dist=tour_dist)
            )
            self.txt_results.append(
                self.tr("-> <b>Custo de acesso:</b> {acc:.2f}").format(acc=access_dist)
            )
            self.txt_results.append(
                self.tr("-> <b>Custo de retorno:</b> {ret:.2f}").format(ret=return_dist)
            )
            self.txt_results.append(
                self.tr("-> <b>Razão de deadhead (dead_ratio):</b> {dr:.4f}").format(dr=dead_ratio)
            )
            closing_str = self.tr("Sim (fecha no ponto inicial)") if is_closed else self.tr("Não (termina no ponto final)")
            self.txt_results.append(
                self.tr("-> <b>Fechamento:</b> {closed}").format(closed=closing_str)
            )
            self.txt_results.append(
                self.tr("-> <b>Backend de otimização:</b> {backend}<br>").format(backend=backend_str)
            )

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao calcular rota: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_run_tsp.setEnabled(True)

    def run_cvrp(self):
        """
        Executa o algoritmo de Roteirização de Veículos Capacitados (CVRP) e exibe os resultados.
        """
        self.txt_results.clear()

        depot_layer = self.cmb_depot.currentLayer()
        demand_layer = self.cmb_demand.currentLayer()
        demand_field = self.cmb_demand_field.currentField()
        capacity = self.spin_capacity.value()
        network_layer = self.cmb_network.currentLayer()
        improve = self.chk_cvrp_improve.isChecked()

        if not depot_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de depósito.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Depósito não selecionado.</span>"))
            return

        if not demand_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de demanda / clientes.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Camada de demanda não selecionada.</span>"))
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

        self.btn_run_cvrp.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== EXECUTANDO ROTEIRIZAÇÃO (CVRP) ===</b><br>"))

        try:
            params = {
                'INPUT_DEPOT': depot_layer,
                'INPUT_DEMAND': demand_layer,
                'FIELD_DEMAND': demand_field or '',
                'CAPACITY': capacity,
                'INPUT_NETWORK': network_layer if network_layer else None,
                'IMPROVE': improve,
                'OUTPUT_ROUTES': 'memory:',
                'OUTPUT_STOPS': 'memory:'
            }
            res = processing.run("logis:vrp_cvrp", params)

            routes_layer = res.get('OUTPUT_ROUTES')
            stops_layer = res.get('OUTPUT_STOPS')

            if routes_layer is not None:
                QgsProject.instance().addMapLayer(routes_layer)
            if stops_layer is not None:
                QgsProject.instance().addMapLayer(stops_layer)

            total_routes = 0
            total_stops = 0
            total_load = 0.0
            total_dist = 0.0
            route_lines = []

            if routes_layer is not None and hasattr(routes_layer, 'getFeatures'):
                fields = routes_layer.fields() if hasattr(routes_layer, 'fields') else None
                for feat in routes_layer.getFeatures():
                    r_id = self._attr(feat, fields, 'route_id', 0)
                    s_count = self._attr(feat, fields, 'stop_count', 0)
                    r_load = float(self._attr(feat, fields, 'route_load', 0.0))
                    r_dist = float(self._attr(feat, fields, 'route_dist', 0.0))

                    total_routes += 1
                    total_stops += s_count
                    total_load += r_load
                    total_dist += r_dist

                    line_str = self.tr("Rota {id}: {n} paradas | carga {load:.2f} | distância {dist:.2f}").format(
                        id=r_id, n=s_count, load=r_load, dist=r_dist
                    )
                    route_lines.append(line_str)

            self.txt_results.append(
                self.tr("-> <b>Rotas geradas:</b> {n}").format(n=total_routes)
            )
            self.txt_results.append(
                self.tr("-> <b>Paradas atendidas:</b> {n}").format(n=total_stops)
            )
            self.txt_results.append(
                self.tr("-> <b>Carga total:</b> {load:.2f}").format(load=total_load)
            )
            self.txt_results.append(
                self.tr("-> <b>Distância total:</b> {dist:.2f}<br>").format(dist=total_dist)
            )

            for line in route_lines:
                self.txt_results.append(line)
            if route_lines:
                self.txt_results.append("")

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar CVRP: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_run_cvrp.setEnabled(True)

