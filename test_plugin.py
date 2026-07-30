# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock
import sys
import os

# Insert the parent directory of logis to sys.path to enable absolute imports of logis package
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Mock QGIS/PyQt classes
from qgis.PyQt.QtWidgets import QMainWindow, QApplication

# Initialize QApplication if it doesn't exist (needed for QWidget/QMainWindow creation)
app = QApplication.instance()
if not app:
    app = QApplication([])

from logis.logis_plugin import LogisPlugin

class TestLogisPlugin(unittest.TestCase):
    def setUp(self):
        # Create a mock iface
        self.mock_iface = MagicMock()
        self.main_window = QMainWindow()
        self.mock_iface.mainWindow.return_value = self.main_window
        
        # Instantiate the plugin
        self.plugin = LogisPlugin(self.mock_iface)

    def tearDown(self):
        # Clean up widget
        self.main_window.deleteLater()

    def test_init(self):
        self.assertEqual(self.plugin.iface, self.mock_iface)
        self.assertIsNone(self.plugin.provider)
        self.assertIsNone(self.plugin.action)
        self.assertIsNone(self.plugin.action_urban)
        self.assertIsNone(self.plugin.action_regional)
        self.assertIsNone(self.plugin.action_waste)
        self.assertIsNone(self.plugin.dialog)
        self.assertIsNone(self.plugin.dock_urban)
        self.assertIsNone(self.plugin.dock_regional)
        self.assertIsNone(self.plugin.dock_waste)

    def test_init_gui(self):
        try:
            from qgis.core import QgsApplication
            QgsApplication.processingRegistry = MagicMock()
        except Exception:
            pass

        # Call initGui
        self.plugin.initGui()

        # Check that action, action_urban, action_regional and action_waste were created
        self.assertIsNotNone(self.plugin.action)
        self.assertIsNotNone(self.plugin.action_urban)
        self.assertIsNotNone(self.plugin.action_regional)
        self.assertIsNotNone(self.plugin.action_waste)

        # Check that they were added to menu "logis"
        self.mock_iface.addPluginToMenu.assert_any_call("logis", self.plugin.action)
        self.mock_iface.addPluginToMenu.assert_any_call("logis", self.plugin.action_urban)
        self.mock_iface.addPluginToMenu.assert_any_call("logis", self.plugin.action_regional)
        self.mock_iface.addPluginToMenu.assert_any_call("logis", self.plugin.action_waste)

    def test_show_urban_dock(self):
        self.plugin.initGui()
        self.assertIsNone(self.plugin.dock_urban)

        # Trigger show_urban_dock
        self.plugin.show_urban_dock()

        # Check that dock_urban was created and show was called
        self.assertIsNotNone(self.plugin.dock_urban)
        self.mock_iface.addDockWidget.assert_called_once()
        
        # Call it again to make sure it is not recreated
        dock_first = self.plugin.dock_urban
        self.plugin.show_urban_dock()
        self.assertEqual(self.plugin.dock_urban, dock_first)

    def test_show_regional_dock(self):
        self.plugin.initGui()
        self.assertIsNone(self.plugin.dock_regional)

        # Trigger show_regional_dock
        self.plugin.show_regional_dock()

        # Check that dock_regional was created and show was called
        self.assertIsNotNone(self.plugin.dock_regional)
        self.mock_iface.addDockWidget.assert_called_once()
        
        # Call it again to make sure it is not recreated
        dock_first = self.plugin.dock_regional
        self.plugin.show_regional_dock()
        self.assertEqual(self.plugin.dock_regional, dock_first)

    def test_show_waste_dock(self):
        self.plugin.initGui()
        self.assertIsNone(self.plugin.dock_waste)

        # Trigger show_waste_dock
        self.plugin.show_waste_dock()

        # Check that dock_waste was created
        self.assertIsNotNone(self.plugin.dock_waste)
        
        # Call it again to make sure it is not recreated
        dock_first = self.plugin.dock_waste
        self.plugin.show_waste_dock()
        self.assertEqual(self.plugin.dock_waste, dock_first)

    def test_unload(self):
        # Setup GUI
        self.plugin.initGui()
        self.plugin.show_urban_dock()
        self.plugin.show_regional_dock()
        self.plugin.show_waste_dock()

        action = self.plugin.action
        action_urban = self.plugin.action_urban
        action_regional = self.plugin.action_regional
        action_waste = self.plugin.action_waste
        dock_urban = self.plugin.dock_urban
        dock_regional = self.plugin.dock_regional
        dock_waste = self.plugin.dock_waste

        # Unload plugin
        self.plugin.unload()

        # Check that actions are removed from menu
        self.mock_iface.removePluginMenu.assert_any_call("logis", action)
        self.mock_iface.removePluginMenu.assert_any_call("logis", action_urban)
        self.mock_iface.removePluginMenu.assert_any_call("logis", action_regional)
        self.mock_iface.removePluginMenu.assert_any_call("logis", action_waste)
        
        # Check that docks are removed
        self.mock_iface.removeDockWidget.assert_any_call(dock_urban)
        self.mock_iface.removeDockWidget.assert_any_call(dock_regional)
        self.mock_iface.removeDockWidget.assert_any_call(dock_waste)

        # Check references are cleaned
        self.assertIsNone(self.plugin.action)
        self.assertIsNone(self.plugin.action_urban)
        self.assertIsNone(self.plugin.action_regional)
        self.assertIsNone(self.plugin.action_waste)
        self.assertIsNone(self.plugin.dock_urban)
        self.assertIsNone(self.plugin.dock_regional)
        self.assertIsNone(self.plugin.dock_waste)

    def test_urban_dock_delivery_distance_controls(self):
        self.plugin.initGui()
        self.plugin.show_urban_dock()
        dock = self.plugin.dock_urban
        self.assertIsNotNone(dock)
        
        # Check that new controls exist
        self.assertTrue(hasattr(dock, 'tabs'))
        self.assertTrue(hasattr(dock, 'cmb_delivery_depots'))
        self.assertTrue(hasattr(dock, 'cmb_delivery_zones'))
        self.assertTrue(hasattr(dock, 'cmb_delivery_criterion'))
        self.assertTrue(hasattr(dock, 'btn_calculate_delivery'))
        self.assertTrue(hasattr(dock, 'calculate_delivery_distance'))
        self.assertTrue(hasattr(dock, 'txt_cargo_expression'))
        self.assertTrue(hasattr(dock, 'btn_calculate_cargo'))
        self.assertTrue(hasattr(dock, 'calculate_cargo_restriction'))


if __name__ == '__main__':
    unittest.main()
