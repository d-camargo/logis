# -*- coding: utf-8 -*-
import math
import unittest

from logis.core.crs_check import (
    BRAZIL_LONLAT_BOUNDS,
    classify_input_crs,
    valid_extent,
)


class TestClassifyInputCRS(unittest.TestCase):
    """Testes unitários para classify_input_crs (API de booleanos pré-computados)."""

    def test_empty_list_returns_ok(self):
        """Lista vazia deve retornar 'ok' independentemente dos flags de SRC."""
        self.assertEqual(classify_input_crs(True, True, []), "ok")
        self.assertEqual(classify_input_crs(False, False, []), "ok")

    def test_valid_geographic_with_degrees_returns_ok(self):
        """SRC geográfico válido com coordenadas em graus deve retornar 'ok'."""
        pts = [(-43.9378, -19.9208), (-43.9400, -19.9300)]
        self.assertEqual(classify_input_crs(True, True, pts), "ok")

    def test_valid_projected_with_metric_returns_ok(self):
        """SRC projetado válido com coordenadas métricas deve retornar 'ok'."""
        self.assertEqual(classify_input_crs(True, False, [(5752163.0, 7375218.0)]), "ok")

    def test_invalid_crs_inside_brazil_returns_assume_4674(self):
        """SRC inválido com todos os pontos em graus dentro da caixa do Brasil deve retornar 'assume_4674'."""
        pts = [(-46.63, -23.55), (-46.631, -23.551)]
        self.assertEqual(classify_input_crs(False, False, pts), "assume_4674")

    def test_invalid_crs_outside_brazil_returns_missing(self):
        """SRC inválido com qualquer ponto fora da caixa do Brasil deve retornar 'missing'."""
        self.assertEqual(classify_input_crs(False, False, [(-75.5, -15.0)]), "missing")
        self.assertEqual(classify_input_crs(False, False, [(10.0, 50.0)]), "missing")

    def test_invalid_crs_metric_coords_returns_missing(self):
        """SRC inválido com coordenadas métricas (fora da caixa) deve retornar 'missing'."""
        self.assertEqual(classify_input_crs(False, False, [(5752163.0, 7375218.0)]), "missing")

    def test_invalid_crs_mixed_coords_returns_missing(self):
        """SRC inválido com um ponto no Brasil e outro fora deve retornar 'missing'."""
        pts = [(-46.63, -23.55), (10.0, 50.0)]
        self.assertEqual(classify_input_crs(False, False, pts), "missing")

    def test_valid_projected_with_degrees_returns_degrees_in_projected(self):
        """SRC projetado válido com coordenadas em graus deve retornar 'degrees_in_projected'."""
        self.assertEqual(classify_input_crs(True, False, [(-46.63, -23.55)]), "degrees_in_projected")


class TestBrazilBounds(unittest.TestCase):
    """Testes da constante BRAZIL_LONLAT_BOUNDS."""

    def test_bounds_value(self):
        """A caixa do Brasil deve ser exatamente (xmin, ymin, xmax, ymax) esperada."""
        self.assertEqual(BRAZIL_LONLAT_BOUNDS, (-75.0, -35.0, -28.0, 6.0))
        self.assertIsInstance(BRAZIL_LONLAT_BOUNDS, tuple)


class TestValidExtent(unittest.TestCase):
    """Testes unitários para valid_extent (quatro floats)."""

    def test_valid_box_returns_true(self):
        """Caixa bem formada deve retornar True."""
        self.assertTrue(valid_extent(0.0, 0.0, 10.0, 10.0))

    def test_inverted_box_returns_false(self):
        """Caixa invertida (xmin > xmax ou ymin > ymax) deve retornar False."""
        self.assertFalse(valid_extent(10.0, 0.0, 0.0, 10.0))
        self.assertFalse(valid_extent(0.0, 10.0, 10.0, 0.0))

    def test_degenerate_box_returns_false(self):
        """Caixa degenerada (xmin == xmax ou ymin == ymax) deve retornar False."""
        self.assertFalse(valid_extent(5.0, 0.0, 5.0, 10.0))
        self.assertFalse(valid_extent(0.0, 5.0, 10.0, 5.0))

    def test_non_finite_values_return_false(self):
        """Valores não finitos (nan, inf, -inf) em qualquer posição devem retornar False."""
        nan = float("nan")
        self.assertFalse(valid_extent(nan, 0.0, 10.0, 10.0))
        self.assertFalse(valid_extent(0.0, nan, 10.0, 10.0))
        self.assertFalse(valid_extent(0.0, 0.0, nan, 10.0))
        self.assertFalse(valid_extent(0.0, 0.0, 10.0, nan))
        self.assertFalse(valid_extent(float("inf"), 0.0, 10.0, 10.0))
        self.assertFalse(valid_extent(0.0, 0.0, 10.0, float("-inf")))


if __name__ == "__main__":
    unittest.main()
