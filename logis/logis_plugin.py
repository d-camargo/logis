# -*- coding: utf-8 -*-
"""Ponto de entrada do plugin logis."""

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication

try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction

from .provider import LogisProvider


class LogisPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.action = None
        self.action_urban = None
        self.action_regional = None
        self.action_waste = None
        self.dialog = None
        self.dock_urban = None
        self.dock_regional = None
        self.dock_waste = None

    def tr(self, s):
        return QCoreApplication.translate("LogisPlugin", s)

    def initProcessing(self):
        self.provider = LogisProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        
        # Cria a ação do menu "Dependências..."
        self.action = QAction(self.tr("Dependências..."), self.iface.mainWindow())
        self.action.triggered.connect(self.show_dependencies)
        
        # Registra a entrada no menu "logis"
        self.iface.addPluginToMenu("logis", self.action)

        # Cria a ação do menu "Indicadores Urbanos"
        self.action_urban = QAction(self.tr("Indicadores Urbanos"), self.iface.mainWindow())
        self.action_urban.triggered.connect(self.show_urban_dock)
        
        # Registra a entrada no menu "logis"
        self.iface.addPluginToMenu("logis", self.action_urban)

        # Cria a ação do menu "Indicadores Regionais"
        self.action_regional = QAction(self.tr("Indicadores Regionais"), self.iface.mainWindow())
        self.action_regional.triggered.connect(self.show_regional_dock)
        
        # Registra a entrada no menu "logis"
        self.iface.addPluginToMenu("logis", self.action_regional)

        # Cria a ação do menu "Coleta de Lixo"
        self.action_waste = QAction(self.tr("Coleta de Lixo"), self.iface.mainWindow())
        self.action_waste.triggered.connect(self.show_waste_dock)
        
        # Registra a entrada no menu "logis"
        self.iface.addPluginToMenu("logis", self.action_waste)

    def show_dependencies(self):
        from .gui.dependencies_dialog import DependenciesDialog
        if self.dialog is None:
            self.dialog = DependenciesDialog(self.iface.mainWindow())
        self.dialog.refresh_status()
        self.dialog.exec()

    def show_urban_dock(self):
        from qgis.PyQt.QtCore import Qt
        from .gui.urban_dock import UrbanDock
        if self.dock_urban is None:
            self.dock_urban = UrbanDock(self.iface, self.iface.mainWindow())
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_urban)
        self.dock_urban.show()

    def show_regional_dock(self):
        from qgis.PyQt.QtCore import Qt
        from .gui.regional_dock import RegionalDock
        if self.dock_regional is None:
            self.dock_regional = RegionalDock(self.iface, self.iface.mainWindow())
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_regional)
        self.dock_regional.show()

    def show_waste_dock(self):
        from qgis.PyQt.QtCore import Qt
        from .gui.waste_dock import WasteDock
        if self.dock_waste is None:
            self.dock_waste = WasteDock(self.iface, self.iface.mainWindow())
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_waste)
        self.dock_waste.show()

    def unload(self):
        # Desregistra o Processing Provider
        if self.provider is not None:
            from qgis.PyQt import sip
            if not sip.isdeleted(self.provider):
                QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

        # Remove o item do menu
        if self.action is not None:
            self.iface.removePluginMenu("logis", self.action)
            self.action = None

        # Remove o item de Indicadores Urbanos do menu
        if self.action_urban is not None:
            self.iface.removePluginMenu("logis", self.action_urban)
            self.action_urban = None

        # Remove o item de Indicadores Regionais do menu
        if self.action_regional is not None:
            self.iface.removePluginMenu("logis", self.action_regional)
            self.action_regional = None

        # Remove o item de Coleta de Lixo do menu
        if self.action_waste is not None:
            self.iface.removePluginMenu("logis", self.action_waste)
            self.action_waste = None

        # Libera referência ao diálogo
        if self.dialog is not None:
            self.dialog = None

        # Remove e libera o dock widget
        if self.dock_urban is not None:
            from qgis.PyQt import sip
            if not sip.isdeleted(self.dock_urban):
                self.iface.removeDockWidget(self.dock_urban)
            self.dock_urban = None

        # Remove e libera o dock regional widget
        if self.dock_regional is not None:
            from qgis.PyQt import sip
            if not sip.isdeleted(self.dock_regional):
                self.iface.removeDockWidget(self.dock_regional)
            self.dock_regional = None

        # Remove e libera o dock de coleta de lixo widget
        if self.dock_waste is not None:
            from qgis.PyQt import sip
            if not sip.isdeleted(self.dock_waste):
                self.iface.removeDockWidget(self.dock_waste)
            self.dock_waste = None
