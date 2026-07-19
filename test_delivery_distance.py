# -*- coding: utf-8 -*-
import unittest
from core.indicators.urban import nearest_depot_cost

class TestNearestDepotCost(unittest.TestCase):
    def test_multiple_depots(self):
        # 3 depósitos (linhas), 4 zonas (colunas)
        # depósito 0: [10.0, 50.0, 30.0, 5.0]
        # depósito 1: [20.0,  5.0, 40.0, 15.0]
        # depósito 2: [ 5.0, 25.0, 10.0, 25.0]
        od_matrix = [
            [10.0, 50.0, 30.0, 5.0],
            [20.0,  5.0, 40.0, 15.0],
            [ 5.0, 25.0, 10.0, 25.0]
        ]
        result = nearest_depot_cost(od_matrix)
        expected = [5.0, 5.0, 10.0, 5.0]
        self.assertEqual(result, expected)

    def test_single_depot(self):
        # 1 depósito (linha), 3 zonas (colunas)
        od_matrix = [
            [10.0, 5.0, 20.0]
        ]
        result = nearest_depot_cost(od_matrix)
        expected = [10.0, 5.0, 20.0]
        self.assertEqual(result, expected)

    def test_empty_matrix_raises(self):
        with self.assertRaises(ValueError):
            nearest_depot_cost([])

    def test_none_matrix_raises(self):
        with self.assertRaises(TypeError):
            nearest_depot_cost(None)

    def test_non_list_matrix_raises(self):
        with self.assertRaises(TypeError):
            nearest_depot_cost("not a list")

    def test_empty_row_raises(self):
        with self.assertRaises(ValueError):
            nearest_depot_cost([[]])

    def test_non_list_row_raises(self):
        with self.assertRaises(TypeError):
            nearest_depot_cost([[10.0], "not a list"])

    def test_inconsistent_row_sizes_raises(self):
        od_matrix = [
            [10.0, 20.0],
            [15.0]
        ]
        with self.assertRaises(ValueError):
            nearest_depot_cost(od_matrix)

    def test_negative_values_raises(self):
        od_matrix = [
            [10.0, -5.0],
            [15.0, 20.0]
        ]
        with self.assertRaises(ValueError):
            nearest_depot_cost(od_matrix)

    def test_invalid_value_type_raises(self):
        od_matrix = [
            [10.0, "invalid"],
            [15.0, 20.0]
        ]
        with self.assertRaises(TypeError):
            nearest_depot_cost(od_matrix)

if __name__ == '__main__':
    unittest.main()
