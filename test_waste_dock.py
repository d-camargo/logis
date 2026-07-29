# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    from qgis.PyQt.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        app = QApplication([])
except ImportError:
    pass

from logis.gui.waste_dock import WasteDock
from logis.logis_plugin import LogisPlugin


class DummyIface:
    def __init__(self):
        self._docks = []
        self._menu_items = []

    def mainWindow(self):
        return None

    def addDockWidget(self, area, dock):
        self._docks.append((area, dock))

    def removeDockWidget(self, dock):
        if dock in [d[1] for d in self._docks]:
            self._docks = [d for d in self._docks if d[1] != dock]

    def addPluginToMenu(self, name, action):
        self._menu_items.append((name, action))

    def removePluginMenu(self, name, action):
        self._menu_items = [item for item in self._menu_items if item != (name, action)]


class TestWasteDock(unittest.TestCase):
    """
    Testes unitários para o WasteDock e a seção 'Estimativa de Geração'.
    """

    def setUp(self):
        self.iface = DummyIface()
        self.dock = WasteDock(self.iface)

    def test_ui_components_exist(self):
        """Verifica se os componentes da seção Estimativa de Geração e Roteirização CPP foram criados no WasteDock."""
        self.assertTrue(hasattr(self.dock, 'cmb_sectors'))
        self.assertTrue(hasattr(self.dock, 'cmb_sector_id'))
        self.assertTrue(hasattr(self.dock, 'cmb_population'))
        self.assertTrue(hasattr(self.dock, 'cmb_streets'))
        self.assertTrue(hasattr(self.dock, 'cmb_street_sector_id'))
        self.assertTrue(hasattr(self.dock, 'spin_per_capita'))
        self.assertTrue(hasattr(self.dock, 'spin_coverage'))
        self.assertTrue(hasattr(self.dock, 'btn_calculate_generation'))
        self.assertTrue(hasattr(self.dock, 'txt_results'))
        self.assertTrue(hasattr(self.dock, 'tabs'))

        # Componentes da seção Setorização
        self.assertTrue(hasattr(self.dock, 'cmb_dist_streets'))
        self.assertTrue(hasattr(self.dock, 'cmb_dist_field_load'))
        self.assertTrue(hasattr(self.dock, 'spin_dist_num_sectors'))
        self.assertTrue(hasattr(self.dock, 'spin_dist_node_tolerance'))
        self.assertTrue(hasattr(self.dock, 'spin_dist_max_iterations'))
        self.assertTrue(hasattr(self.dock, 'btn_run_districting'))

        # Componentes da seção Roteirização CPP
        self.assertTrue(hasattr(self.dock, 'cmb_cpp_streets'))
        self.assertTrue(hasattr(self.dock, 'cmb_cpp_sector_id'))
        self.assertTrue(hasattr(self.dock, 'spin_cpp_tolerance'))
        self.assertTrue(hasattr(self.dock, 'btn_run_cpp'))

        # Componentes da seção Roteirização RPP
        self.assertTrue(hasattr(self.dock, 'cmb_rpp_streets'))
        self.assertTrue(hasattr(self.dock, 'cmb_rpp_required_field'))
        self.assertTrue(hasattr(self.dock, 'cmb_rpp_sector_id'))
        self.assertTrue(hasattr(self.dock, 'spin_rpp_tolerance'))
        self.assertTrue(hasattr(self.dock, 'btn_run_rpp'))

        # Componentes da seção Roteirização CARP
        self.assertTrue(hasattr(self.dock, 'cmb_carp_streets'))
        self.assertTrue(hasattr(self.dock, 'cmb_carp_required_field'))
        self.assertTrue(hasattr(self.dock, 'cmb_carp_demand_field'))
        self.assertTrue(hasattr(self.dock, 'cmb_carp_depot'))
        self.assertTrue(hasattr(self.dock, 'spin_carp_capacity'))
        self.assertTrue(hasattr(self.dock, 'cmb_carp_sector_id'))
        self.assertTrue(hasattr(self.dock, 'spin_carp_tolerance'))
        self.assertTrue(hasattr(self.dock, 'btn_run_carp'))

        # Componentes da seção Dimensionamento de Frota
        self.assertTrue(hasattr(self.dock, 'cmb_fleet_routes'))
        self.assertTrue(hasattr(self.dock, 'cmb_fleet_route_id'))
        self.assertTrue(hasattr(self.dock, 'cmb_fleet_sector_id'))
        self.assertTrue(hasattr(self.dock, 'spin_fleet_avg_speed'))
        self.assertTrue(hasattr(self.dock, 'spin_fleet_shift_duration'))
        self.assertTrue(hasattr(self.dock, 'spin_fleet_unload_time'))
        self.assertTrue(hasattr(self.dock, 'spin_fleet_travel_time'))
        self.assertTrue(hasattr(self.dock, 'btn_run_fleet_sizing'))

        # Componentes da seção Equilíbrio entre Setores
        self.assertTrue(hasattr(self.dock, 'cmb_balance_routes'))
        self.assertTrue(hasattr(self.dock, 'cmb_balance_load_field'))
        self.assertTrue(hasattr(self.dock, 'cmb_balance_distance_field'))
        self.assertTrue(hasattr(self.dock, 'cmb_balance_route_id'))
        self.assertTrue(hasattr(self.dock, 'cmb_balance_sector_id'))
        self.assertTrue(hasattr(self.dock, 'spin_balance_avg_speed'))
        self.assertTrue(hasattr(self.dock, 'spin_balance_unload_time'))
        self.assertTrue(hasattr(self.dock, 'spin_balance_travel_time'))
        self.assertTrue(hasattr(self.dock, 'btn_run_sector_balance'))

        # Componentes da seção Deadhead Ratio
        self.assertTrue(hasattr(self.dock, 'cmb_deadhead_routes'))
        self.assertTrue(hasattr(self.dock, 'cmb_deadhead_field'))
        self.assertTrue(hasattr(self.dock, 'cmb_deadhead_route_id'))
        self.assertTrue(hasattr(self.dock, 'btn_run_deadhead_ratio'))

        # Componentes da seção Distância ao Destino
        self.assertTrue(hasattr(self.dock, 'cmb_dest_network'))
        self.assertTrue(hasattr(self.dock, 'cmb_dest_destinations'))
        self.assertTrue(hasattr(self.dock, 'cmb_dest_sectors'))
        self.assertTrue(hasattr(self.dock, 'cmb_dest_criterion'))
        self.assertTrue(hasattr(self.dock, 'btn_run_destination_distance'))

        # Componentes da seção Cobertura por Frequência
        self.assertTrue(hasattr(self.dock, 'cmb_coverage_required_roads'))
        self.assertTrue(hasattr(self.dock, 'cmb_coverage_required_sector'))
        self.assertTrue(hasattr(self.dock, 'cmb_coverage_routes'))
        self.assertTrue(hasattr(self.dock, 'cmb_coverage_deadhead_field'))
        self.assertTrue(hasattr(self.dock, 'cmb_coverage_route_sector'))
        self.assertTrue(hasattr(self.dock, 'txt_coverage_frequency_label'))
        self.assertTrue(hasattr(self.dock, 'btn_run_coverage'))

        # Verifica valores padrão das spinboxes
        self.assertAlmostEqual(self.dock.spin_per_capita.value(), 0.9)
        self.assertAlmostEqual(self.dock.spin_coverage.value(), 1.0)
        self.assertAlmostEqual(self.dock.spin_cpp_tolerance.value(), 0.01)
        self.assertAlmostEqual(self.dock.spin_rpp_tolerance.value(), 0.01)
        self.assertAlmostEqual(self.dock.spin_carp_tolerance.value(), 0.01)
        self.assertAlmostEqual(self.dock.spin_carp_capacity.value(), 10.0)
        self.assertAlmostEqual(self.dock.spin_fleet_avg_speed.value(), 10.0)
        self.assertAlmostEqual(self.dock.spin_fleet_shift_duration.value(), 8.0)
        self.assertAlmostEqual(self.dock.spin_fleet_unload_time.value(), 0.5)
        self.assertAlmostEqual(self.dock.spin_fleet_travel_time.value(), 0.5)
        self.assertAlmostEqual(self.dock.spin_balance_avg_speed.value(), 10.0)
        self.assertAlmostEqual(self.dock.spin_balance_unload_time.value(), 0.0)
        self.assertAlmostEqual(self.dock.spin_balance_travel_time.value(), 0.0)

    def test_calculate_waste_generation_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em calcular."""
        # Sem selecionar camadas/campos, a execução deve falhar graciosamente com mensagem de aviso
        # (QMessageBox.warning é mockado para não abrir um diálogo modal real durante o teste)
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.calculate_waste_generation()
            mock_warning.assert_called_once()

    def test_run_cpp_route_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em executar roteirização CPP."""
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.run_cpp_route()
            mock_warning.assert_called_once()

    def test_run_rpp_route_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em executar roteirização RPP."""
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.run_rpp_route()
            mock_warning.assert_called_once()

    def test_run_carp_route_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em executar roteirização CARP."""
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.run_carp_route()
            mock_warning.assert_called_once()

    def test_run_fleet_sizing_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em executar dimensionamento de frota."""
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.run_fleet_sizing()
            mock_warning.assert_called_once()

    def test_run_sector_balance_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em executar equilíbrio entre setores."""
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.run_sector_balance()
            mock_warning.assert_called_once()

    def test_run_destination_distance_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em executar distância ao destino."""
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.run_destination_distance()
            mock_warning.assert_called_once()

    def test_run_collection_coverage_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em executar cobertura por frequência."""
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.run_collection_coverage()
            mock_warning.assert_called_once()

    def test_run_deadhead_ratio_missing_inputs(self):
        """Verifica a validação de parâmetros incompletos ao clicar em executar razão de deadhead."""
        with patch('logis.gui.waste_dock.QMessageBox.warning') as mock_warning:
            self.dock.run_deadhead_ratio()
            mock_warning.assert_called_once()




    def test_plugin_integration(self):
        """Verifica a integração da ação e dock no LogisPlugin."""
        plugin = LogisPlugin(self.iface)
        plugin.initGui()
        self.assertIsNotNone(plugin.action_waste)

        plugin.show_waste_dock()
        self.assertIsNotNone(plugin.dock_waste)

        plugin.unload()
        self.assertIsNone(plugin.action_waste)
        self.assertIsNone(plugin.dock_waste)


if __name__ == '__main__':
    unittest.main()
