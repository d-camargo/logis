# -*- coding: utf-8 -*-
import math
import unittest

from logis.core.crs_check import (
    BRAZIL_LONLAT_BOUNDS,
    PLAUSIBLE_BOUNDS,
    classify_input_crs,
    plausible_coords,
    point_moved,
    utm_sirgas_epsg,
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


class TestUtmSirgasEpsg(unittest.TestCase):
    """Testes unitários para utm_sirgas_epsg."""

    def test_utm_sirgas_epsg_samples(self):
        # utm_sirgas_epsg(-46.63, -23.55) == "EPSG:31983", (-60.0, 2.8) -> zona 20 norte "EPSG:31974"
        self.assertEqual(utm_sirgas_epsg(-46.63, -23.55), "EPSG:31983")
        self.assertEqual(utm_sirgas_epsg(-60.0, 2.8), "EPSG:31974")


class TestPlausibleCoords(unittest.TestCase):
    """Testes unitários para plausible_coords."""

    def test_plausible_coords_5880(self):
        # plausible_coords("EPSG:5880", [(5752163, 7375218)]) True e [(-46.6, -23.5)]/[(-3046.67, -3023.63)] False
        self.assertTrue(plausible_coords("EPSG:5880", [(5752163, 7375218)]))
        self.assertFalse(plausible_coords("EPSG:5880", [(-46.6, -23.5)]))
        self.assertFalse(plausible_coords("EPSG:5880", [(-3046.67, -3023.63)]))

    def test_plausible_coords_utm(self):
        # UTM (333000, 7395000) em EPSG:31983 True e (-46.6, -23.5) False
        self.assertTrue(plausible_coords("EPSG:31983", [(333000, 7395000)]))
        self.assertFalse(plausible_coords("EPSG:31983", [(-46.6, -23.5)]))

    def test_plausible_coords_unknown_authid(self):
        # authid desconhecido com valor finito True e com nan False
        self.assertTrue(plausible_coords("EPSG:99999", [(100.0, 200.0)]))
        self.assertFalse(plausible_coords("EPSG:99999", [(float("nan"), 200.0)]))

    def test_plausible_coords_empty_and_duck_typing(self):
        self.assertTrue(plausible_coords("EPSG:5880", []))

        class MockPoint:
            def __init__(self, x, y):
                self._x = x
                self._y = y

            def x(self):
                return self._x

            def y(self):
                return self._y

        self.assertTrue(plausible_coords("EPSG:5880", [MockPoint(5752163, 7375218)]))
        self.assertFalse(plausible_coords("EPSG:5880", [MockPoint(-46.6, -23.5)]))


class TestPointMoved(unittest.TestCase):
    """Testes unitários para point_moved."""

    def test_point_moved_equal(self):
        # point_moved com ponto igual False
        self.assertFalse(point_moved((-46.63, -23.55), (-46.63, -23.55)))

    def test_point_moved_different(self):
        self.assertTrue(point_moved((-46.63, -23.55), (5752163.0, 7375218.0)))

    def test_point_moved_tolerance(self):
        self.assertFalse(point_moved((-46.63, -23.55), (-46.63 + 1e-10, -23.55)))
        self.assertTrue(point_moved((-46.63, -23.55), (-46.63 + 1e-8, -23.55)))

    def test_point_moved_non_finite_and_invalid(self):
        self.assertFalse(point_moved((float("nan"), 0.0), (0.0, 0.0)))
        self.assertFalse(point_moved("invalid", (0.0, 0.0)))


class TestPlausibleBounds(unittest.TestCase):
    """Testes da constante PLAUSIBLE_BOUNDS."""

    def test_bounds_entries(self):
        self.assertIn("EPSG:5880", PLAUSIBLE_BOUNDS)
        self.assertIn("EPSG:4674", PLAUSIBLE_BOUNDS)
        self.assertIn("EPSG:4326", PLAUSIBLE_BOUNDS)
        self.assertEqual(PLAUSIBLE_BOUNDS["EPSG:4674"], BRAZIL_LONLAT_BOUNDS)
        self.assertEqual(PLAUSIBLE_BOUNDS["EPSG:4326"], BRAZIL_LONLAT_BOUNDS)
        self.assertEqual(
            PLAUSIBLE_BOUNDS["EPSG:5880"],
            (2_500_000, 5_600_000, 8_100_000, 10_900_000),
        )


if __name__ == "__main__":
    unittest.main()

