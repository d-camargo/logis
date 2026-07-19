# -*- coding: utf-8 -*-
import unittest
from core.indicators.urban import gravity_accessibility

class TestGravityAccessibility(unittest.TestCase):
    def test_normal_case(self):
        # origem unica, dois destinos: peso 100 a 10m, peso 50 a 20m (beta=2.0)
        distances = [[10.0, 20.0]]
        weights = [100.0, 50.0]
        result = gravity_accessibility(distances, weights)
        expected = 100.0 / 10.0 ** 2 + 50.0 / 20.0 ** 2
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0], expected)

    def test_uniform_weights_multiple_origins(self):
        # duas origens, dois destinos, pesos iguais (beta=2.0)
        distances = [[10.0, 10.0], [5.0, 20.0]]
        weights = [1.0, 1.0]
        result = gravity_accessibility(distances, weights)
        self.assertAlmostEqual(result[0], 2 * (1.0 / 10.0 ** 2))
        self.assertAlmostEqual(result[1], 1.0 / 5.0 ** 2 + 1.0 / 20.0 ** 2)

    def test_zero_distance_is_ignored(self):
        # distancia zero/invalida (ex.: origem coincide com o destino) e ignorada, nao lanca erro
        distances = [[0.0, 10.0]]
        weights = [100.0, 50.0]
        result = gravity_accessibility(distances, weights)
        self.assertAlmostEqual(result[0], 50.0 / 10.0 ** 2)

    def test_custom_beta(self):
        distances = [[10.0]]
        weights = [100.0]
        result = gravity_accessibility(distances, weights, beta=1.0)
        self.assertAlmostEqual(result[0], 10.0)

    def test_invalid_beta_raises(self):
        with self.assertRaises(ValueError):
            gravity_accessibility([[10.0]], [1.0], beta=0.0)

    def test_empty_weights_raises(self):
        with self.assertRaises(ValueError):
            gravity_accessibility([[10.0]], [])

if __name__ == '__main__':
    unittest.main()
