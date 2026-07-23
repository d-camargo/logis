# -*- coding: utf-8 -*-
"""
Painel (dock) para Coleta de Lixo / Logística Especializada.

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
            self.layerChanged = MockSignal()
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
            return 0.9
    class QSpinBox:
        def __init__(self, parent=None):
            pass
        def setRange(self, minimum, maximum):
            pass
        def setValue(self, value):
            pass
        def value(self):
            return 100
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


class WasteDock(QgsDockWidget):
    """
    Painel lateral (Dock Widget) para o módulo de Coleta de Lixo / Logística Especializada
    no plugin logis.
    """

    def __init__(self, iface, parent=None):
        super().__init__(QCoreApplication.translate("WasteDock", "logis — Coleta de Lixo"), parent)
        self.iface = iface
        self._build_ui()

    def tr(self, string):
        return QCoreApplication.translate("WasteDock", string)

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Título principal
        title_label = QLabel(self.tr("<b>Coleta de Lixo</b>"))
        title_label.setStyleSheet("font-size: 14px; color: #2b6cb0; margin-bottom: 2px;")
        layout.addWidget(title_label)

        desc_label = QLabel(
            self.tr(
                "Painel para gestão, estimativa de geração, setorização e "
                "roteirização por arcos (coleta de lixo urbana)."
            )
        )
        desc_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Seção: Estimativa de Geração
        gen_title = QLabel(self.tr("<b>Estimativa de Geração</b>"))
        gen_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 8px;")
        layout.addWidget(gen_title)

        # Camada de Setores (Polígonos)
        layout.addWidget(QLabel(self.tr("Camada de setores censitérios (Polígonos):")))
        self.cmb_sectors = QgsMapLayerComboBox()
        self.cmb_sectors.setFilters(QgsMapLayerProxyModel.Filter.PolygonLayer)
        layout.addWidget(self.cmb_sectors)

        # Campo ID do setor na camada de setores
        layout.addWidget(QLabel(self.tr("Campo ID do setor (Setores):")))
        self.cmb_sector_id = QgsFieldComboBox()
        self.cmb_sector_id.setLayer(self.cmb_sectors.currentLayer())
        self.cmb_sectors.layerChanged.connect(self.cmb_sector_id.setLayer)
        layout.addWidget(self.cmb_sector_id)

        # Campo População na camada de setores
        layout.addWidget(QLabel(self.tr("Campo de população (Setores):")))
        self.cmb_population = QgsFieldComboBox()
        self.cmb_population.setLayer(self.cmb_sectors.currentLayer())
        self.cmb_sectors.layerChanged.connect(self.cmb_population.setLayer)
        layout.addWidget(self.cmb_population)

        # Camada de Vias (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de trechos de via (Linhas):")))
        self.cmb_streets = QgsMapLayerComboBox()
        self.cmb_streets.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_streets)

        # Campo ID do setor na camada de vias
        layout.addWidget(QLabel(self.tr("Campo ID do setor (Vias):")))
        self.cmb_street_sector_id = QgsFieldComboBox()
        self.cmb_street_sector_id.setLayer(self.cmb_streets.currentLayer())
        self.cmb_streets.layerChanged.connect(self.cmb_street_sector_id.setLayer)
        layout.addWidget(self.cmb_street_sector_id)

        # Taxa Per Capita
        layout.addWidget(QLabel(self.tr("Taxa per capita (kg/hab/dia):")))
        self.spin_per_capita = QDoubleSpinBox()
        self.spin_per_capita.setRange(0.01, 100.0)
        self.spin_per_capita.setSingleStep(0.05)
        self.spin_per_capita.setValue(0.9)
        layout.addWidget(self.spin_per_capita)

        # Fração de Cobertura
        layout.addWidget(QLabel(self.tr("Fração de cobertura (0.0 a 1.0):")))
        self.spin_coverage = QDoubleSpinBox()
        self.spin_coverage.setRange(0.0, 1.0)
        self.spin_coverage.setSingleStep(0.05)
        self.spin_coverage.setValue(1.0)
        layout.addWidget(self.spin_coverage)

        # Botão Calcular
        self.btn_calculate_generation = QPushButton(self.tr("Calcular Estimativa de Geração"))
        self.btn_calculate_generation.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_calculate_generation.clicked.connect(self.calculate_waste_generation)
        layout.addWidget(self.btn_calculate_generation)

        # Seção: Roteirização CPP
        cpp_title = QLabel(self.tr("<b>Roteirização CPP</b>"))
        cpp_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 12px;")
        layout.addWidget(cpp_title)

        # Camada de Vias (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de trechos de via (Linhas):")))
        self.cmb_cpp_streets = QgsMapLayerComboBox()
        self.cmb_cpp_streets.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_cpp_streets)

        # Campo ID do setor na camada de vias (opcional)
        layout.addWidget(QLabel(self.tr("Campo de setor de coleta (opcional):")))
        self.cmb_cpp_sector_id = QgsFieldComboBox()
        if hasattr(self.cmb_cpp_sector_id, 'setAllowEmptyFieldName'):
            self.cmb_cpp_sector_id.setAllowEmptyFieldName(True)
        self.cmb_cpp_sector_id.setLayer(self.cmb_cpp_streets.currentLayer())
        self.cmb_cpp_streets.layerChanged.connect(self.cmb_cpp_sector_id.setLayer)
        layout.addWidget(self.cmb_cpp_sector_id)

        # Tolerância de nó (m)
        layout.addWidget(QLabel(self.tr("Tolerância de nó (m):")))
        self.spin_cpp_tolerance = QDoubleSpinBox()
        self.spin_cpp_tolerance.setRange(0.0001, 100.0)
        self.spin_cpp_tolerance.setSingleStep(0.01)
        self.spin_cpp_tolerance.setValue(0.01)
        layout.addWidget(self.spin_cpp_tolerance)

        # Botão Executar Roteirização CPP
        self.btn_run_cpp = QPushButton(self.tr("Executar Roteirização CPP"))
        self.btn_run_cpp.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_cpp.clicked.connect(self.run_cpp_route)
        layout.addWidget(self.btn_run_cpp)

        # Seção: Roteirização RPP
        rpp_title = QLabel(self.tr("<b>Roteirização RPP</b>"))
        rpp_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 12px;")
        layout.addWidget(rpp_title)

        # Camada de Vias (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de trechos de via (Linhas):")))
        self.cmb_rpp_streets = QgsMapLayerComboBox()
        self.cmb_rpp_streets.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_rpp_streets)

        # Campo de via obrigatória (opcional)
        layout.addWidget(QLabel(self.tr("Campo de via obrigatória (opcional):")))
        self.cmb_rpp_required_field = QgsFieldComboBox()
        if hasattr(self.cmb_rpp_required_field, 'setAllowEmptyFieldName'):
            self.cmb_rpp_required_field.setAllowEmptyFieldName(True)
        self.cmb_rpp_required_field.setLayer(self.cmb_rpp_streets.currentLayer())
        self.cmb_rpp_streets.layerChanged.connect(self.cmb_rpp_required_field.setLayer)
        layout.addWidget(self.cmb_rpp_required_field)

        # Campo ID do setor na camada de vias (opcional)
        layout.addWidget(QLabel(self.tr("Campo de setor de coleta (opcional):")))
        self.cmb_rpp_sector_id = QgsFieldComboBox()
        if hasattr(self.cmb_rpp_sector_id, 'setAllowEmptyFieldName'):
            self.cmb_rpp_sector_id.setAllowEmptyFieldName(True)
        self.cmb_rpp_sector_id.setLayer(self.cmb_rpp_streets.currentLayer())
        self.cmb_rpp_streets.layerChanged.connect(self.cmb_rpp_sector_id.setLayer)
        layout.addWidget(self.cmb_rpp_sector_id)

        # Tolerância de nó (m)
        layout.addWidget(QLabel(self.tr("Tolerância de nó (m):")))
        self.spin_rpp_tolerance = QDoubleSpinBox()
        self.spin_rpp_tolerance.setRange(0.0001, 100.0)
        self.spin_rpp_tolerance.setSingleStep(0.01)
        self.spin_rpp_tolerance.setValue(0.01)
        layout.addWidget(self.spin_rpp_tolerance)

        # Botão Executar Roteirização RPP
        self.btn_run_rpp = QPushButton(self.tr("Executar Roteirização RPP"))
        self.btn_run_rpp.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_rpp.clicked.connect(self.run_rpp_route)
        layout.addWidget(self.btn_run_rpp)

        # Seção: Roteirização CARP
        carp_title = QLabel(self.tr("<b>Roteirização CARP</b>"))
        carp_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 12px;")
        layout.addWidget(carp_title)

        # Camada de Vias (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de trechos de via (Linhas):")))
        self.cmb_carp_streets = QgsMapLayerComboBox()
        self.cmb_carp_streets.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_carp_streets)

        # Campo de via obrigatória (opcional)
        layout.addWidget(QLabel(self.tr("Campo de via obrigatória (opcional):")))
        self.cmb_carp_required_field = QgsFieldComboBox()
        if hasattr(self.cmb_carp_required_field, 'setAllowEmptyFieldName'):
            self.cmb_carp_required_field.setAllowEmptyFieldName(True)
        self.cmb_carp_required_field.setLayer(self.cmb_carp_streets.currentLayer())
        self.cmb_carp_streets.layerChanged.connect(self.cmb_carp_required_field.setLayer)
        layout.addWidget(self.cmb_carp_required_field)

        # Campo de demanda de resíduos (kg)
        layout.addWidget(QLabel(self.tr("Campo de demanda de resíduos (kg):")))
        self.cmb_carp_demand_field = QgsFieldComboBox()
        self.cmb_carp_demand_field.setLayer(self.cmb_carp_streets.currentLayer())
        self.cmb_carp_streets.layerChanged.connect(self.cmb_carp_demand_field.setLayer)
        layout.addWidget(self.cmb_carp_demand_field)

        # Camada de Ponto do Depósito (Pontos)
        layout.addWidget(QLabel(self.tr("Camada de ponto do depósito/aterro (Pontos):")))
        self.cmb_carp_depot = QgsMapLayerComboBox()
        self.cmb_carp_depot.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_carp_depot)

        # Capacidade do veículo
        layout.addWidget(QLabel(self.tr("Capacidade do veículo:")))
        self.spin_carp_capacity = QDoubleSpinBox()
        self.spin_carp_capacity.setRange(0.0001, 100000.0)
        self.spin_carp_capacity.setSingleStep(1.0)
        self.spin_carp_capacity.setValue(10.0)
        layout.addWidget(self.spin_carp_capacity)

        # Campo ID do setor na camada de vias (opcional)
        layout.addWidget(QLabel(self.tr("Campo de setor de coleta (opcional):")))
        self.cmb_carp_sector_id = QgsFieldComboBox()
        if hasattr(self.cmb_carp_sector_id, 'setAllowEmptyFieldName'):
            self.cmb_carp_sector_id.setAllowEmptyFieldName(True)
        self.cmb_carp_sector_id.setLayer(self.cmb_carp_streets.currentLayer())
        self.cmb_carp_streets.layerChanged.connect(self.cmb_carp_sector_id.setLayer)
        layout.addWidget(self.cmb_carp_sector_id)

        # Tolerância de nó (m)
        layout.addWidget(QLabel(self.tr("Tolerância de nó (m):")))
        self.spin_carp_tolerance = QDoubleSpinBox()
        self.spin_carp_tolerance.setRange(0.0001, 100.0)
        self.spin_carp_tolerance.setSingleStep(0.01)
        self.spin_carp_tolerance.setValue(0.01)
        layout.addWidget(self.spin_carp_tolerance)

        # Botão Executar Roteirização CARP
        self.btn_run_carp = QPushButton(self.tr("Executar Roteirização CARP"))
        self.btn_run_carp.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_carp.clicked.connect(self.run_carp_route)
        layout.addWidget(self.btn_run_carp)

        # Seção: Dimensionamento de Frota
        fleet_title = QLabel(self.tr("<b>Dimensionamento de Frota</b>"))
        fleet_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 12px;")
        layout.addWidget(fleet_title)

        # Camada de Rotas (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de rotas de coleta (Linhas):")))
        self.cmb_fleet_routes = QgsMapLayerComboBox()
        self.cmb_fleet_routes.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_fleet_routes)

        # Campo ID da rota
        layout.addWidget(QLabel(self.tr("Campo ID da rota:")))
        self.cmb_fleet_route_id = QgsFieldComboBox()
        self.cmb_fleet_route_id.setLayer(self.cmb_fleet_routes.currentLayer())
        self.cmb_fleet_routes.layerChanged.connect(self.cmb_fleet_route_id.setLayer)
        layout.addWidget(self.cmb_fleet_route_id)

        # Campo de setor de coleta (opcional)
        layout.addWidget(QLabel(self.tr("Campo de setor de coleta (opcional):")))
        self.cmb_fleet_sector_id = QgsFieldComboBox()
        if hasattr(self.cmb_fleet_sector_id, 'setAllowEmptyFieldName'):
            self.cmb_fleet_sector_id.setAllowEmptyFieldName(True)
        self.cmb_fleet_sector_id.setLayer(self.cmb_fleet_routes.currentLayer())
        self.cmb_fleet_routes.layerChanged.connect(self.cmb_fleet_sector_id.setLayer)
        layout.addWidget(self.cmb_fleet_sector_id)

        # Velocidade média de coleta (km/h)
        layout.addWidget(QLabel(self.tr("Velocidade média de coleta (km/h):")))
        self.spin_fleet_avg_speed = QDoubleSpinBox()
        self.spin_fleet_avg_speed.setRange(0.0001, 200.0)
        self.spin_fleet_avg_speed.setSingleStep(0.5)
        self.spin_fleet_avg_speed.setValue(10.0)
        layout.addWidget(self.spin_fleet_avg_speed)

        # Duração da jornada de trabalho (horas)
        layout.addWidget(QLabel(self.tr("Duração da jornada de trabalho (horas):")))
        self.spin_fleet_shift_duration = QDoubleSpinBox()
        self.spin_fleet_shift_duration.setRange(0.0001, 24.0)
        self.spin_fleet_shift_duration.setSingleStep(0.5)
        self.spin_fleet_shift_duration.setValue(8.0)
        layout.addWidget(self.spin_fleet_shift_duration)

        # Tempo de descarga por rota (horas)
        layout.addWidget(QLabel(self.tr("Tempo de descarga por rota (horas):")))
        self.spin_fleet_unload_time = QDoubleSpinBox()
        self.spin_fleet_unload_time.setRange(0.0, 24.0)
        self.spin_fleet_unload_time.setSingleStep(0.1)
        self.spin_fleet_unload_time.setValue(0.5)
        layout.addWidget(self.spin_fleet_unload_time)

        # Tempo de deslocamento ao destino por rota (horas)
        layout.addWidget(QLabel(self.tr("Tempo de deslocamento ao destino por rota (horas):")))
        self.spin_fleet_travel_time = QDoubleSpinBox()
        self.spin_fleet_travel_time.setRange(0.0, 24.0)
        self.spin_fleet_travel_time.setSingleStep(0.1)
        self.spin_fleet_travel_time.setValue(0.5)
        layout.addWidget(self.spin_fleet_travel_time)

        # Botão Executar Dimensionamento de Frota
        self.btn_run_fleet_sizing = QPushButton(self.tr("Executar Dimensionamento de Frota"))
        self.btn_run_fleet_sizing.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_fleet_sizing.clicked.connect(self.run_fleet_sizing)
        layout.addWidget(self.btn_run_fleet_sizing)

        # Seção: Equilíbrio entre Setores
        balance_title = QLabel(self.tr("<b>Equilíbrio entre Setores</b>"))
        balance_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 12px;")
        layout.addWidget(balance_title)

        # Camada de Rotas (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de rotas de coleta (Linhas):")))
        self.cmb_balance_routes = QgsMapLayerComboBox()
        self.cmb_balance_routes.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_balance_routes)

        # Campo de carga da rota (kg)
        layout.addWidget(QLabel(self.tr("Campo de carga da rota (kg):")))
        self.cmb_balance_load_field = QgsFieldComboBox()
        self.cmb_balance_load_field.setLayer(self.cmb_balance_routes.currentLayer())
        self.cmb_balance_routes.layerChanged.connect(self.cmb_balance_load_field.setLayer)
        layout.addWidget(self.cmb_balance_load_field)

        # Campo de distância da rota em km (opcional)
        layout.addWidget(QLabel(self.tr("Campo de distância da rota em km (opcional):")))
        self.cmb_balance_distance_field = QgsFieldComboBox()
        if hasattr(self.cmb_balance_distance_field, 'setAllowEmptyFieldName'):
            self.cmb_balance_distance_field.setAllowEmptyFieldName(True)
        self.cmb_balance_distance_field.setLayer(self.cmb_balance_routes.currentLayer())
        self.cmb_balance_routes.layerChanged.connect(self.cmb_balance_distance_field.setLayer)
        layout.addWidget(self.cmb_balance_distance_field)

        # Campo ID da rota (opcional)
        layout.addWidget(QLabel(self.tr("Campo ID da rota (opcional):")))
        self.cmb_balance_route_id = QgsFieldComboBox()
        if hasattr(self.cmb_balance_route_id, 'setAllowEmptyFieldName'):
            self.cmb_balance_route_id.setAllowEmptyFieldName(True)
        self.cmb_balance_route_id.setLayer(self.cmb_balance_routes.currentLayer())
        self.cmb_balance_routes.layerChanged.connect(self.cmb_balance_route_id.setLayer)
        layout.addWidget(self.cmb_balance_route_id)

        # Campo de setor de coleta (opcional)
        layout.addWidget(QLabel(self.tr("Campo de setor de coleta (opcional):")))
        self.cmb_balance_sector_id = QgsFieldComboBox()
        if hasattr(self.cmb_balance_sector_id, 'setAllowEmptyFieldName'):
            self.cmb_balance_sector_id.setAllowEmptyFieldName(True)
        self.cmb_balance_sector_id.setLayer(self.cmb_balance_routes.currentLayer())
        self.cmb_balance_routes.layerChanged.connect(self.cmb_balance_sector_id.setLayer)
        layout.addWidget(self.cmb_balance_sector_id)

        # Velocidade média de coleta (km/h)
        layout.addWidget(QLabel(self.tr("Velocidade média de coleta (km/h):")))
        self.spin_balance_avg_speed = QDoubleSpinBox()
        self.spin_balance_avg_speed.setRange(0.0001, 200.0)
        self.spin_balance_avg_speed.setSingleStep(0.5)
        self.spin_balance_avg_speed.setValue(10.0)
        layout.addWidget(self.spin_balance_avg_speed)

        # Tempo de descarga por rota (horas)
        layout.addWidget(QLabel(self.tr("Tempo de descarga por rota (horas):")))
        self.spin_balance_unload_time = QDoubleSpinBox()
        self.spin_balance_unload_time.setRange(0.0, 24.0)
        self.spin_balance_unload_time.setSingleStep(0.1)
        self.spin_balance_unload_time.setValue(0.0)
        layout.addWidget(self.spin_balance_unload_time)

        # Tempo de deslocamento ao destino por rota (horas)
        layout.addWidget(QLabel(self.tr("Tempo de deslocamento ao destino por rota (horas):")))
        self.spin_balance_travel_time = QDoubleSpinBox()
        self.spin_balance_travel_time.setRange(0.0, 24.0)
        self.spin_balance_travel_time.setSingleStep(0.1)
        self.spin_balance_travel_time.setValue(0.0)
        layout.addWidget(self.spin_balance_travel_time)

        # Botão Executar Equilíbrio entre Setores
        self.btn_run_sector_balance = QPushButton(self.tr("Executar Equilíbrio entre Setores"))
        self.btn_run_sector_balance.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_sector_balance.clicked.connect(self.run_sector_balance)
        layout.addWidget(self.btn_run_sector_balance)

        # Seção: Distância ao Destino
        dest_title = QLabel(self.tr("<b>Distância ao Destino</b>"))
        dest_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 12px;")
        layout.addWidget(dest_title)

        # Camada de Rede Viária (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de rede viária (Linhas):")))
        self.cmb_dest_network = QgsMapLayerComboBox()
        self.cmb_dest_network.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_dest_network)

        # Camada de Destinos de Resíduos (Pontos)
        layout.addWidget(QLabel(self.tr("Camada de destinos de resíduos (Pontos):")))
        self.cmb_dest_destinations = QgsMapLayerComboBox()
        self.cmb_dest_destinations.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_dest_destinations)

        # Camada de Setores/Origens de Coleta (Pontos ou Polígonos)
        layout.addWidget(QLabel(self.tr("Camada de setores/origens de coleta (Pontos ou Polígonos):")))
        self.cmb_dest_sectors = QgsMapLayerComboBox()
        self.cmb_dest_sectors.setFilters(QgsMapLayerProxyModel.Filter.PointLayer | QgsMapLayerProxyModel.Filter.PolygonLayer)
        layout.addWidget(self.cmb_dest_sectors)

        # Critério de Custo
        layout.addWidget(QLabel(self.tr("Critério de custo:")))
        self.cmb_dest_criterion = QComboBox()
        self.cmb_dest_criterion.addItems([self.tr("Distância"), self.tr("Tempo de viagem")])
        layout.addWidget(self.cmb_dest_criterion)

        # Botão Executar Distância ao Destino
        self.btn_run_destination_distance = QPushButton(self.tr("Executar Distância ao Destino"))
        self.btn_run_destination_distance.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_destination_distance.clicked.connect(self.run_destination_distance)
        layout.addWidget(self.btn_run_destination_distance)

        # Seção: Cobertura por Frequência
        coverage_title = QLabel(self.tr("<b>Cobertura por Frequência</b>"))
        coverage_title.setStyleSheet("font-size: 13px; color: #2b6cb0; margin-top: 12px;")
        layout.addWidget(coverage_title)

        # Camada de Vias Exigidas (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de vias exigidas (faixa de frequência) (Linhas):")))
        self.cmb_coverage_required_roads = QgsMapLayerComboBox()
        self.cmb_coverage_required_roads.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_coverage_required_roads)

        # Campo de setor da camada de vias exigidas (opcional)
        layout.addWidget(QLabel(self.tr("Campo de setor da camada de vias exigidas (opcional):")))
        self.cmb_coverage_required_sector = QgsFieldComboBox()
        if hasattr(self.cmb_coverage_required_sector, 'setAllowEmptyFieldName'):
            self.cmb_coverage_required_sector.setAllowEmptyFieldName(True)
        self.cmb_coverage_required_sector.setLayer(self.cmb_coverage_required_roads.currentLayer())
        self.cmb_coverage_required_roads.layerChanged.connect(self.cmb_coverage_required_sector.setLayer)
        layout.addWidget(self.cmb_coverage_required_sector)

        # Camada de Rota Coberta (Linhas)
        layout.addWidget(QLabel(self.tr("Camada de rota coberta (Linhas):")))
        self.cmb_coverage_routes = QgsMapLayerComboBox()
        self.cmb_coverage_routes.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        layout.addWidget(self.cmb_coverage_routes)

        # Campo indicador de deadhead/conector (opcional)
        layout.addWidget(QLabel(self.tr("Campo indicador de deadhead/conector (opcional):")))
        self.cmb_coverage_deadhead_field = QgsFieldComboBox()
        if hasattr(self.cmb_coverage_deadhead_field, 'setAllowEmptyFieldName'):
            self.cmb_coverage_deadhead_field.setAllowEmptyFieldName(True)
        self.cmb_coverage_deadhead_field.setLayer(self.cmb_coverage_routes.currentLayer())
        self.cmb_coverage_routes.layerChanged.connect(self.cmb_coverage_deadhead_field.setLayer)
        layout.addWidget(self.cmb_coverage_deadhead_field)

        # Campo de setor da camada de rota coberta (opcional)
        layout.addWidget(QLabel(self.tr("Campo de setor da camada de rota coberta (opcional):")))
        self.cmb_coverage_route_sector = QgsFieldComboBox()
        if hasattr(self.cmb_coverage_route_sector, 'setAllowEmptyFieldName'):
            self.cmb_coverage_route_sector.setAllowEmptyFieldName(True)
        self.cmb_coverage_route_sector.setLayer(self.cmb_coverage_routes.currentLayer())
        self.cmb_coverage_routes.layerChanged.connect(self.cmb_coverage_route_sector.setLayer)
        layout.addWidget(self.cmb_coverage_route_sector)

        # Rótulo de frequência de coleta
        layout.addWidget(QLabel(self.tr("Rótulo de frequência de coleta:")))
        self.txt_coverage_frequency_label = QLineEdit("Diária")
        layout.addWidget(self.txt_coverage_frequency_label)

        # Botão Executar Cobertura por Frequência
        self.btn_run_coverage = QPushButton(self.tr("Executar Cobertura por Frequência"))
        self.btn_run_coverage.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_coverage.clicked.connect(self.run_collection_coverage)
        layout.addWidget(self.btn_run_coverage)

        # Painel de Resultados
        layout.addWidget(QLabel(self.tr("Resultados:")))
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

    def calculate_waste_generation(self):
        """
        Executa o algoritmo logis:waste_generation_estimate com as entradas informadas na UI.
        """
        self.txt_results.clear()

        sectors_layer = self.cmb_sectors.currentLayer()
        field_sector_id = self.cmb_sector_id.currentField()
        field_population = self.cmb_population.currentField()
        streets_layer = self.cmb_streets.currentLayer()
        field_street_sector_id = self.cmb_street_sector_id.currentField()
        per_capita = self.spin_per_capita.value()
        coverage = self.spin_coverage.value()

        if not sectors_layer or not streets_layer or not field_sector_id or not field_population or not field_street_sector_id:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione todas as camadas e campos necessários para a estimativa de geração.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Parâmetros incompletos.</span>"))
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

        self.btn_calculate_generation.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== CALCULANDO ESTIMATIVA DE GERAÇÃO ===</b><br>"))

        try:
            res = processing.run("logis:waste_generation_estimate", {
                'INPUT_SECTORS': sectors_layer,
                'FIELD_SECTOR_ID': field_sector_id,
                'FIELD_POPULATION': field_population,
                'INPUT_STREETS': streets_layer,
                'FIELD_STREET_SECTOR_ID': field_street_sector_id,
                'PER_CAPITA_KG_DAY': per_capita,
                'COVERAGE_FRACTION': coverage,
                'OUTPUT': 'memory:'
            })

            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(out_layer)

                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else 'OK'
                self.txt_results.append(
                    self.tr("-> <b>Estimativa calculada com sucesso!</b> (Camada com {count} trechos viários)<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Resultado da estimativa retornou vazio.</b><br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao calcular estimativa: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_calculate_generation.setEnabled(True)

    def run_cpp_route(self):
        """
        Executa o algoritmo logis:waste_cpp_route com as entradas informadas na UI.
        """
        self.txt_results.clear()

        streets_layer = self.cmb_cpp_streets.currentLayer()
        field_sector_id = self.cmb_cpp_sector_id.currentField()
        tolerance = self.spin_cpp_tolerance.value()

        if not streets_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de vias para a roteirização CPP.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Parâmetros incompletos.</span>"))
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

        self.btn_run_cpp.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== EXECUTANDO ROTEIRIZAÇÃO CPP ===</b><br>"))

        try:
            params = {
                'INPUT_STREETS': streets_layer,
                'FIELD_COLLECTION_SECTOR': field_sector_id if field_sector_id else None,
                'NODE_TOLERANCE': tolerance,
                'OUTPUT': 'memory:'
            }
            res = processing.run("logis:waste_cpp_route", params)

            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(out_layer)

                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else 'OK'
                self.txt_results.append(
                    self.tr("-> <b>Roteirização CPP concluída com sucesso!</b> (Camada com {count} trechos viários)<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Resultado da roteirização retornou vazio.</b><br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar roteirização CPP: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== ROTEIRIZAÇÃO CONCLUÍDA ===</b>"))
        self.btn_run_cpp.setEnabled(True)

    def run_rpp_route(self):
        """
        Executa o algoritmo logis:waste_rpp_route com as entradas informadas na UI.
        """
        self.txt_results.clear()

        streets_layer = self.cmb_rpp_streets.currentLayer()
        field_required = self.cmb_rpp_required_field.currentField()
        field_sector_id = self.cmb_rpp_sector_id.currentField()
        tolerance = self.spin_rpp_tolerance.value()

        if not streets_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de vias para a roteirização RPP.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Parâmetros incompletos.</span>"))
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

        self.btn_run_rpp.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== EXECUTANDO ROTEIRIZAÇÃO RPP ===</b><br>"))

        try:
            params = {
                'INPUT_STREETS': streets_layer,
                'FIELD_REQUIRED': field_required if field_required else None,
                'FIELD_COLLECTION_SECTOR': field_sector_id if field_sector_id else None,
                'NODE_TOLERANCE': tolerance,
                'OUTPUT': 'memory:'
            }
            res = processing.run("logis:waste_rpp_route", params)

            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(out_layer)

                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else 'OK'
                self.txt_results.append(
                    self.tr("-> <b>Roteirização RPP concluída com sucesso!</b> (Camada com {count} trechos viários)<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Resultado da roteirização retornou vazio.</b><br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar roteirização RPP: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== ROTEIRIZAÇÃO CONCLUÍDA ===</b>"))
        self.btn_run_rpp.setEnabled(True)

    def run_carp_route(self):
        """
        Executa o algoritmo logis:waste_carp_route com as entradas informadas na UI.
        """
        self.txt_results.clear()

        streets_layer = self.cmb_carp_streets.currentLayer()
        field_required = self.cmb_carp_required_field.currentField()
        field_demand = self.cmb_carp_demand_field.currentField()
        depot_layer = self.cmb_carp_depot.currentLayer()
        capacity = self.spin_carp_capacity.value()
        field_sector_id = self.cmb_carp_sector_id.currentField()
        tolerance = self.spin_carp_tolerance.value()

        if not streets_layer or not field_demand or not depot_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de vias, o campo de demanda e a camada do depósito para a roteirização CARP.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Parâmetros incompletos.</span>"))
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

        self.btn_run_carp.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== EXECUTANDO ROTEIRIZAÇÃO CARP ===</b><br>"))

        try:
            params = {
                'INPUT_STREETS': streets_layer,
                'FIELD_DEMAND': field_demand,
                'FIELD_REQUIRED': field_required if field_required else None,
                'FIELD_COLLECTION_SECTOR': field_sector_id if field_sector_id else None,
                'CAPACITY': capacity,
                'INPUT_DEPOT': depot_layer,
                'NODE_TOLERANCE': tolerance,
                'OUTPUT': 'memory:'
            }
            res = processing.run("logis:waste_carp_route", params)

            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(out_layer)

                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else 'OK'
                self.txt_results.append(
                    self.tr("-> <b>Roteirização CARP concluída com sucesso!</b> (Camada com {count} trechos viários)<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Resultado da roteirização retornou vazio.</b><br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar roteirização CARP: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== ROTEIRIZAÇÃO CONCLUÍDA ===</b>"))
        self.btn_run_carp.setEnabled(True)

    def run_fleet_sizing(self):
        """
        Executa o algoritmo logis:waste_fleet_sizing com as entradas informadas na UI.
        """
        self.txt_results.clear()

        routes_layer = self.cmb_fleet_routes.currentLayer()
        field_route_id = self.cmb_fleet_route_id.currentField()
        field_sector_id = self.cmb_fleet_sector_id.currentField()
        avg_speed = self.spin_fleet_avg_speed.value()
        shift_duration = self.spin_fleet_shift_duration.value()
        unload_time = self.spin_fleet_unload_time.value()
        travel_time = self.spin_fleet_travel_time.value()

        if not routes_layer or not field_route_id:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de rotas e o campo ID da rota para o dimensionamento de frota.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Parâmetros incompletos.</span>"))
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

        self.btn_run_fleet_sizing.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== EXECUTANDO DIMENSIONAMENTO DE FROTA ===</b><br>"))

        try:
            params = {
                'INPUT_ROUTES': routes_layer,
                'FIELD_ROUTE_ID': field_route_id,
                'FIELD_COLLECTION_SECTOR': field_sector_id if field_sector_id else None,
                'AVG_SPEED': avg_speed,
                'SHIFT_DURATION': shift_duration,
                'UNLOAD_TIME': unload_time,
                'TRAVEL_TIME': travel_time,
                'OUTPUT': 'memory:'
            }
            res = processing.run("logis:waste_fleet_sizing", params)

            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(out_layer)

                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else 'OK'
                self.txt_results.append(
                    self.tr("-> <b>Dimensionamento de frota concluído com sucesso!</b> (Camada com {count} registros)<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Resultado do dimensionamento retornou vazio.</b><br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar dimensionamento de frota: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== DIMENSIONAMENTO CONCLUÍDO ===</b>"))
        self.btn_run_fleet_sizing.setEnabled(True)

    def run_sector_balance(self):
        """
        Executa o algoritmo logis:waste_sector_balance com as entradas informadas na UI.
        """
        self.txt_results.clear()

        routes_layer = self.cmb_balance_routes.currentLayer()
        field_load = self.cmb_balance_load_field.currentField()
        field_distance = self.cmb_balance_distance_field.currentField()
        field_route_id = self.cmb_balance_route_id.currentField()
        field_sector_id = self.cmb_balance_sector_id.currentField()
        avg_speed = self.spin_balance_avg_speed.value()
        unload_time = self.spin_balance_unload_time.value()
        travel_time = self.spin_balance_travel_time.value()

        if not routes_layer or not field_load:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de rotas e o campo de carga para a análise de equilíbrio.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Parâmetros incompletos.</span>"))
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

        self.btn_run_sector_balance.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== EXECUTANDO EQUILÍBRIO ENTRE SETORES ===</b><br>"))

        try:
            params = {
                'INPUT_ROUTES': routes_layer,
                'FIELD_LOAD': field_load,
                'FIELD_DISTANCE': field_distance if field_distance else None,
                'FIELD_ROUTE_ID': field_route_id if field_route_id else None,
                'FIELD_COLLECTION_SECTOR': field_sector_id if field_sector_id else None,
                'AVG_SPEED': avg_speed,
                'UNLOAD_TIME': unload_time,
                'TRAVEL_TIME': travel_time,
                'OUTPUT': 'memory:'
            }
            res = processing.run("logis:waste_sector_balance", params)

            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(out_layer)

                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else 'OK'
                self.txt_results.append(
                    self.tr("-> <b>Equilíbrio entre setores calculado com sucesso!</b> (Camada com {count} registros)<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Resultado do equilíbrio retornou vazio.</b><br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar equilíbrio entre setores: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== ANÁLISE CONCLUÍDA ===</b>"))
        self.btn_run_sector_balance.setEnabled(True)

    def run_destination_distance(self):
        """
        Executa o algoritmo logis:waste_destination_distance com as entradas informadas na UI.
        """
        self.txt_results.clear()

        network_layer = self.cmb_dest_network.currentLayer()
        destinations_layer = self.cmb_dest_destinations.currentLayer()
        sectors_layer = self.cmb_dest_sectors.currentLayer()
        criterion = self.cmb_dest_criterion.currentIndex()

        if not network_layer or not destinations_layer or not sectors_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a rede viária, a camada de destinos e a camada de setores para o cálculo de distância ao destino.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Parâmetros incompletos.</span>"))
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

        self.btn_run_destination_distance.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== EXECUTANDO DISTÂNCIA AO DESTINO ===</b><br>"))

        try:
            params = {
                'INPUT_NETWORK': network_layer,
                'INPUT_DESTINATIONS': destinations_layer,
                'INPUT_SECTORS': sectors_layer,
                'CRITERION': criterion,
                'OUTPUT': 'memory:'
            }
            res = processing.run("logis:waste_destination_distance", params)

            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(out_layer)

                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else 'OK'
                self.txt_results.append(
                    self.tr("-> <b>Distância ao destino calculada com sucesso!</b> (Camada com {count} registro(s))<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Resultado da distância ao destino retornou vazio.</b><br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar distância ao destino: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_run_destination_distance.setEnabled(True)

    def run_collection_coverage(self):
        """
        Executa o algoritmo logis:waste_collection_coverage com as entradas informadas na UI.
        """
        self.txt_results.clear()

        required_roads_layer = self.cmb_coverage_required_roads.currentLayer()
        field_required_sector = self.cmb_coverage_required_sector.currentField()
        routes_layer = self.cmb_coverage_routes.currentLayer()
        field_deadhead = self.cmb_coverage_deadhead_field.currentField()
        field_route_sector = self.cmb_coverage_route_sector.currentField()
        frequency_label = self.txt_coverage_frequency_label.text()

        if not required_roads_layer or not routes_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de vias exigidas e a camada de rota coberta para o cálculo de cobertura por frequência.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Parâmetros incompletos.</span>"))
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

        self.btn_run_coverage.setEnabled(False)
        self.txt_results.append(self.tr("<b>=== EXECUTANDO COBERTURA POR FREQUÊNCIA ===</b><br>"))

        try:
            params = {
                'INPUT_REQUIRED_ROADS': required_roads_layer,
                'FIELD_REQUIRED_SECTOR': field_required_sector if field_required_sector else None,
                'INPUT_COVERED_ROUTES': routes_layer,
                'FIELD_COVERED_DEADHEAD': field_deadhead if field_deadhead else None,
                'FIELD_COVERED_SECTOR': field_route_sector if field_route_sector else None,
                'FREQUENCY_LABEL': frequency_label,
                'OUTPUT': 'memory:'
            }
            res = processing.run("logis:waste_collection_coverage", params)

            out_layer = res.get('OUTPUT')
            if out_layer is not None:
                if QgsProject.instance():
                    QgsProject.instance().addMapLayer(out_layer)

                count = out_layer.featureCount() if hasattr(out_layer, 'featureCount') else 'OK'
                self.txt_results.append(
                    self.tr("-> <b>Cobertura por frequência calculada com sucesso!</b> (Camada com {count} registro(s))<br>").format(count=count)
                )
            else:
                self.txt_results.append(self.tr("-> <b>Resultado da cobertura por frequência retornou vazio.</b><br>"))

        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar cobertura por frequência: {error}</span><br>").format(error=str(e))
            )

        self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        self.btn_run_coverage.setEnabled(True)
