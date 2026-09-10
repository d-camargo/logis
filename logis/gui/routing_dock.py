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
        QCheckBox
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

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Título principal
        title_label = QLabel(self.tr("<b>Roteirização</b>"))
        title_label.setStyleSheet("font-size: 14px; color: #2b6cb0; margin-bottom: 2px;")
        layout.addWidget(title_label)

        desc_label = QLabel(
            self.tr(
                "Selecione as camadas de origem, pontos a visitar e rede viária para "
                "calcular a rota otimizada (Problema do Caixeiro Viajante - TSP)."
            )
        )
        desc_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

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

        # Seletor de Camada de Rede Viária (Linhas - opcional)
        layout.addWidget(QLabel(self.tr("Camada de rede viária (Linhas - opcional):")))
        self.cmb_network = QgsMapLayerComboBox()
        self.cmb_network.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        if hasattr(self.cmb_network, 'setAllowEmptyLayer'):
            self.cmb_network.setAllowEmptyLayer(True)
        layout.addWidget(self.cmb_network)

        # Checkbox para busca local (2-opt e Or-opt)
        self.chk_improve = QCheckBox(self.tr("Aplicar busca local (2-opt e Or-opt)"))
        self.chk_improve.setChecked(True)
        layout.addWidget(self.chk_improve)

        # Botão Calcular Rota (TSP)
        self.btn_run_tsp = QPushButton(self.tr("Calcular Rota (TSP)"))
        self.btn_run_tsp.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_tsp.clicked.connect(self.run_tsp)
        layout.addWidget(self.btn_run_tsp)

        # Painel de resultados
        layout.addWidget(QLabel(self.tr("Resultados da Roteirização:")))
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

                    def _get_val(name, default):
                        if fields is not None and hasattr(fields, 'indexOf'):
                            idx = fields.indexOf(name)
                            if idx >= 0 and hasattr(feat, 'attributes'):
                                attrs = feat.attributes()
                                if 0 <= idx < len(attrs) and attrs[idx] is not None:
                                    return attrs[idx]
                        return default

                    num_visited = _get_val('stop_count', 0)
                    tour_dist = _get_val('tour_dist', 0.0)
                    access_dist = _get_val('access_dist', 0.0)
                    return_dist = _get_val('return_dist', 0.0)
                    dead_ratio = _get_val('dead_ratio', 0.0)
                    closed_val = _get_val('closed', 1)
                    is_closed = bool(closed_val)
                    backend_str = str(_get_val('backend', 'N/A'))

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
