# -*- coding: utf-8 -*-
import unittest
from core.indicators.waste import (
    sector_waste_generation,
    allocate_generation_by_street_length
)


class TestWaste(unittest.TestCase):
    """
    Testes unitários para as funções de indicadores de resíduos em core/indicators/waste.py.
    """

    def test_sector_waste_generation(self):
        # 10.000 hab * 0.9 kg/hab/dia * 1.0 cobertura = 9000 kg/dia
        self.assertAlmostEqual(sector_waste_generation(10000, 0.9, 1.0), 9000.0)
        # Cobertura parcial: 10.000 hab * 0.95 kg/hab/dia * 0.8 cobertura = 7600 kg/dia
        self.assertAlmostEqual(sector_waste_generation(10000, 0.95, 0.8), 7600.0)
        # População zero -> geração zero
        self.assertEqual(sector_waste_generation(0, 0.9, 1.0), 0.0)
        # Defaults: population=1000 -> 1000 * 0.9 * 1.0 = 900.0
        self.assertAlmostEqual(sector_waste_generation(1000), 900.0)

        with self.assertRaises(ValueError):
            sector_waste_generation(-100, 0.9, 1.0)
        with self.assertRaises(ValueError):
            sector_waste_generation(1000, 0.0, 1.0)
        with self.assertRaises(ValueError):
            sector_waste_generation(1000, 0.9, -0.1)
        with self.assertRaises(ValueError):
            sector_waste_generation(1000, 0.9, 1.1)

    def test_allocate_generation_by_street_length(self):
        # 900 kg/dia rateados por comprimento: [200m, 600m, 200m] -> [180, 540, 180]
        result = allocate_generation_by_street_length(900.0, [200.0, 600.0, 200.0])
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[0], 180.0)
        self.assertAlmostEqual(result[1], 540.0)
        self.assertAlmostEqual(result[2], 180.0)
        self.assertAlmostEqual(sum(result), 900.0)

        # Trecho único recebe toda a geração
        result_single = allocate_generation_by_street_length(500.0, [1000.0])
        self.assertAlmostEqual(result_single[0], 500.0)

        # Geração total zero -> todos os trechos recebem zero
        result_zero = allocate_generation_by_street_length(0.0, [100.0, 200.0])
        self.assertAlmostEqual(sum(result_zero), 0.0)

        with self.assertRaises(ValueError):
            allocate_generation_by_street_length(-10.0, [100.0])
        with self.assertRaises(ValueError):
            allocate_generation_by_street_length(900.0, [])
        with self.assertRaises(ValueError):
            allocate_generation_by_street_length(900.0, [100.0, 0.0])
        with self.assertRaises(ValueError):
            allocate_generation_by_street_length(900.0, [100.0, -50.0])

    def test_waste_cpp_route_algorithm_metadata(self):
        try:
            from algorithms.waste_cpp_route import WasteCppRoute
            alg = WasteCppRoute()
            self.assertEqual(alg.name(), "waste_cpp_route")
            self.assertEqual(alg.groupId(), "waste")
            self.assertTrue(callable(alg.createInstance))
            self.assertIsInstance(alg.createInstance(), WasteCppRoute)
        except ImportError:
            # Em ambiente sem QGIS C++ bindings completos, ignora instanciação
            pass


if __name__ == "__main__":
    unittest.main()

