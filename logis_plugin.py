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
        self.dialog = None
        self.dock_urban = None

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

    def show_dependencies(self):
        from .gui.dependencies_dialog import DependenciesDialog
        if self.dialog is None:
            self.dialog = DependenciesDialog(self.iface.mainWindow())
        self.dialog.refresh_status()
        self.dialog.exec_()

    def show_urban_dock(self):
        from qgis.PyQt.QtCore import Qt
        from .gui.urban_dock import UrbanDock
        if self.dock_urban is None:
            self.dock_urban = UrbanDock(self.iface, self.iface.mainWindow())
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_urban)
        self.dock_urban.show()

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

        # Libera referência ao diálogo
        if self.dialog is not None:
            self.dialog = None

        # Remove e libera o dock widget
        if self.dock_urban is not None:
            from qgis.PyQt import sip
            if not sip.isdeleted(self.dock_urban):
                self.iface.removeDockWidget(self.dock_urban)
            self.dock_urban = None
