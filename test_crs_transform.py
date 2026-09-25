# -*- coding: utf-8 -*-
import unittest

try:
    from qgis.core import (
        Qgis,
        QgsApplication,
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsCoordinateTransformContext,
        QgsCsException,
        QgsFeature,
        QgsGeometry,
        QgsPointXY,
        QgsProcessingContext,
        QgsRectangle,
        QgsVectorLayer,
    )
    _qgs = QgsApplication.instance()
    if not _qgs:
        _qgs = QgsApplication([], False)
        _qgs.initQgis()
    _HAS_QGIS = True
except ImportError:
    _HAS_QGIS = False

from logis.core.crs_transform import (
    TransformCheckError,
    checked_transform,
    length_meter,
    read_lines_in_crs,
    read_points_in_crs,
    transform_bbox,
    transform_points,
)


@unittest.skipUnless(_HAS_QGIS, "QGIS não disponível")
class TestCrsTransform(unittest.TestCase):
    """Testes unitários para o módulo core/crs_transform.py."""

    def test_checked_transform_4326_to_5880_and_transform_points(self):
        """4326→5880 com probe (-46.63, -23.55) aceito e transform_points dá ~(5752163, 7375218)."""
        src = QgsCoordinateReferenceSystem("EPSG:4326")
        dst = QgsCoordinateReferenceSystem("EPSG:5880")
        contexts = [QgsCoordinateTransformContext()]
        probe = (-46.63, -23.55)

        ct = checked_transform(src, dst, contexts, probe)
        self.assertIsNotNone(ct)
        self.assertTrue(ct.isValid())
        self.assertFalse(ct.isShortCircuited())

        pts = [QgsPointXY(-46.63, -23.55)]
        transformed = transform_points(ct, pts, dst.authid())
        self.assertEqual(len(transformed), 1)

        x, y = transformed[0].x(), transformed[0].y()
        self.assertAlmostEqual(x, 5752163.0, delta=20.0)
        self.assertAlmostEqual(y, 7375218.0, delta=20.0)

    def test_same_src_returns_none_and_transform_points_copies(self):
        """Mesmo SRC → None e transform_points(None, …) devolve cópia."""
        src = QgsCoordinateReferenceSystem("EPSG:4326")
        dst = QgsCoordinateReferenceSystem("EPSG:4326")
        contexts = [QgsCoordinateTransformContext()]

        ct = checked_transform(src, dst, contexts, (-46.63, -23.55))
        self.assertIsNone(ct)

        orig_pts = [QgsPointXY(-46.63, -23.55), QgsPointXY(-43.20, -22.90)]
        copied_pts = transform_points(None, orig_pts, "EPSG:4326")

        self.assertEqual(len(copied_pts), len(orig_pts))
        self.assertIsNot(copied_pts, orig_pts)
        self.assertIsNot(copied_pts[0], orig_pts[0])
        self.assertEqual(copied_pts[0].x(), orig_pts[0].x())
        self.assertEqual(copied_pts[0].y(), orig_pts[0].y())

        # Teste com tuplas
        tuple_pts = [(-46.63, -23.55)]
        copied_tuples = transform_points(None, tuple_pts, "EPSG:4326")
        self.assertIsNot(copied_tuples, tuple_pts)
        self.assertEqual(copied_tuples[0], tuple_pts[0])

    def test_fake_factory_unmoved_point_raises_transform_check_error(self):
        """factory falso cujo transform devolve o ponto intacto → TransformCheckError com EPSG:4326, EPSG:5880 e versão do QGIS."""
        class FakeTransform:
            def isValid(self):
                return True

            def isShortCircuited(self):
                return False

            def transform(self, pt):
                return pt

        def fake_factory(src_crs, dst_crs, ctx):
            return FakeTransform()

        src = QgsCoordinateReferenceSystem("EPSG:4326")
        dst = QgsCoordinateReferenceSystem("EPSG:5880")
        contexts = [QgsCoordinateTransformContext()]

        with self.assertRaises(TransformCheckError) as ctx:
            checked_transform(src, dst, contexts, (-46.63, -23.55), factory=fake_factory)

        msg = str(ctx.exception)
        self.assertIn("EPSG:4326", msg)
        self.assertIn("EPSG:5880", msg)
        self.assertIn(Qgis.version(), msg)

    def test_invalid_destination_crs_raises_transform_check_error(self):
        """Destino inválido (QgsCoordinateReferenceSystem()) → TransformCheckError."""
        src = QgsCoordinateReferenceSystem("EPSG:4326")
        dst = QgsCoordinateReferenceSystem()
        contexts = [QgsCoordinateTransformContext()]

        with self.assertRaises(TransformCheckError):
            checked_transform(src, dst, contexts, (-46.63, -23.55))

    def test_transform_bbox_5880_to_4674_out_of_bounds_raises_transform_check_error(self):
        """transform_bbox 5880→4674 da caixa (-3046.67,-3023.63,2953.40,2976.51) → TransformCheckError."""
        src = QgsCoordinateReferenceSystem("EPSG:5880")
        dst = QgsCoordinateReferenceSystem("EPSG:4674")
        ct = QgsCoordinateTransform(src, dst, QgsCoordinateTransformContext())
        box_out_of_bounds = QgsRectangle(-3046.67, -3023.63, 2953.40, 2976.51)

        try:
            with self.assertRaises(TransformCheckError):
                transform_bbox(ct, box_out_of_bounds, "EPSG:4674")
        except QgsCsException:
            self.fail("QgsCsException não deve vazar de transform_bbox")

    def test_transform_bbox_valid_5880_to_4674(self):
        """transform_bbox com caixa válida em 5880 transforma corretamente para 4674."""
        src = QgsCoordinateReferenceSystem("EPSG:5880")
        dst = QgsCoordinateReferenceSystem("EPSG:4674")
        ct = QgsCoordinateTransform(src, dst, QgsCoordinateTransformContext())
        # Caixa plausível em torno de São Paulo em EPSG:5880
        valid_box = QgsRectangle(5750000, 7370000, 5760000, 7380000)

        res = transform_bbox(ct, valid_box, "EPSG:4674")
        self.assertIsInstance(res, QgsRectangle)
        self.assertTrue(res.xMinimum() < res.xMaximum())
        self.assertTrue(res.yMinimum() < res.yMaximum())
        self.assertGreater(res.xMinimum(), -47.0)
        self.assertLess(res.xMaximum(), -46.0)
        self.assertGreater(res.yMinimum(), -24.0)
        self.assertLess(res.yMaximum(), -23.0)

    def test_transform_bbox_identity(self):
        """transform_bbox com ct=None devolve cópia da caixa."""
        rect = QgsRectangle(10.0, 20.0, 30.0, 40.0)
        res = transform_bbox(None, rect, "EPSG:4326")
        self.assertIsNot(res, rect)
        self.assertEqual(res.xMinimum(), rect.xMinimum())
        self.assertEqual(res.yMaximum(), rect.yMaximum())

    def test_transform_points_implausible_point_raises_with_index(self):
        """transform_points com ponto que resulta em coordenadas implausíveis cita índice e valor."""
        src = QgsCoordinateReferenceSystem("EPSG:4326")
        dst = QgsCoordinateReferenceSystem("EPSG:5880")
        ct = QgsCoordinateTransform(src, dst, QgsCoordinateTransformContext())
        # (0, 0) no Golfo da Guiné não fica nos limites plausíveis do Brasil em 5880
        pts = [QgsPointXY(-46.63, -23.55), QgsPointXY(0.0, 0.0)]

        with self.assertRaises(TransformCheckError) as ctx:
            transform_points(ct, pts, "EPSG:5880")

        msg = str(ctx.exception)
        self.assertIn("index 1", msg)


@unittest.skipUnless(_HAS_QGIS, "QGIS não disponível")
class TestReadPointsInCrs(unittest.TestCase):
    """Testes para core/crs_transform.py: read_points_in_crs."""

    def _memory_layer(self, geom_type, crs, wkts):
        layer = QgsVectorLayer(f"{geom_type}?crs={crs}", "test", "memory")
        pr = layer.dataProvider()
        feats = []
        for wkt in wkts:
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(wkt))
            feats.append(f)
        pr.addFeatures(feats)
        layer.updateExtents()
        return layer

    def test_two_valid_points_to_5880_preserve_order(self):
        """2 pontos válidos (São Paulo, Rio) 4326 -> 5880, ~(5752164, 7375218) e ordem preservada."""
        layer = self._memory_layer(
            "Point", "EPSG:4326",
            ["POINT(-46.63 -23.55)", "POINT(-43.20 -22.90)"],
        )
        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:5880")

        features, points = read_points_in_crs(layer, dst, context, "camada de teste")

        self.assertEqual(len(features), 2)
        self.assertEqual(len(points), 2)
        self.assertAlmostEqual(points[0].x(), 5752164.0, delta=20.0)
        self.assertAlmostEqual(points[0].y(), 7375218.0, delta=20.0)
        # Rio está a leste de São Paulo: x maior, ordem preservada (posição 0 = São Paulo).
        self.assertGreater(points[1].x(), points[0].x())

    def test_point_500_500_raises_transform_check_error_citing_id(self):
        """Ponto (500, 500) não transforma (geometria vazia) -> TransformCheckError citando o id."""
        layer = self._memory_layer("Point", "EPSG:4326", ["POINT(500 500)"])
        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:5880")

        feat = next(layer.getFeatures())
        with self.assertRaises(TransformCheckError) as ctx:
            read_points_in_crs(layer, dst, context, "camada de teste")

        msg = str(ctx.exception)
        self.assertIn(f"id {feat.id()}", msg)
        self.assertIn("EPSG:4326", msg)
        self.assertIn("EPSG:5880", msg)

    def test_polygon_uses_centroid(self):
        """Polígono -> ponto no centroide, reprojetado corretamente."""
        layer = self._memory_layer(
            "Polygon", "EPSG:4326",
            ["POLYGON((-46.64 -23.56, -46.62 -23.56, -46.62 -23.54, -46.64 -23.54, -46.64 -23.56))"],
        )
        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:5880")

        features, points = read_points_in_crs(layer, dst, context, "camada de teste")

        self.assertEqual(len(points), 1)
        self.assertAlmostEqual(points[0].x(), 5752164.0, delta=200.0)
        self.assertAlmostEqual(points[0].y(), 7375218.0, delta=200.0)

    def test_same_crs_returns_untransformed_points(self):
        """Mesmo SRC de entrada e saída -> pontos idênticos aos originais, sem passada reprojetada."""
        layer = self._memory_layer("Point", "EPSG:4326", ["POINT(-46.63 -23.55)"])
        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:4326")

        features, points = read_points_in_crs(layer, dst, context, "camada de teste")

        self.assertEqual(len(points), 1)
        self.assertAlmostEqual(points[0].x(), -46.63)
        self.assertAlmostEqual(points[0].y(), -23.55)

    def test_feature_without_geometry_is_ignored_without_error(self):
        """Feição sem geometria é ignorada nas duas passadas, sem erro."""
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "test", "memory")
        pr = layer.dataProvider()
        f_no_geom = QgsFeature()
        f_with_geom = QgsFeature()
        f_with_geom.setGeometry(QgsGeometry.fromWkt("POINT(-46.63 -23.55)"))
        pr.addFeatures([f_no_geom, f_with_geom])
        layer.updateExtents()

        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:5880")

        features, points = read_points_in_crs(layer, dst, context, "camada de teste")

        self.assertEqual(len(features), 1)
        self.assertEqual(len(points), 1)


@unittest.skipUnless(_HAS_QGIS, "QGIS não disponível")
class TestLengthMeter(unittest.TestCase):
    """Testes para core/crs_transform.py: length_meter."""

    def test_line_4674_measures_about_1020_meters(self):
        """Linha de (-46.63,-23.55) a (-46.62,-23.55) em EPSG:4674 mede ~1020 m (±2%)."""
        context = QgsProcessingContext()
        crs = QgsCoordinateReferenceSystem("EPSG:4674")
        geom = QgsGeometry.fromWkt("LINESTRING(-46.63 -23.55, -46.62 -23.55)")

        measure = length_meter(crs, context)
        length_m = measure(geom)

        self.assertAlmostEqual(length_m, 1020.0, delta=1020.0 * 0.02)

    def test_same_line_in_5880_measures_same_value(self):
        """A mesma linha, já reprojetada para EPSG:5880, mede o mesmo valor (±1%)."""
        context = QgsProcessingContext()
        crs4674 = QgsCoordinateReferenceSystem("EPSG:4674")
        crs5880 = QgsCoordinateReferenceSystem("EPSG:5880")
        geom4674 = QgsGeometry.fromWkt("LINESTRING(-46.63 -23.55, -46.62 -23.55)")

        ct = QgsCoordinateTransform(crs4674, crs5880, QgsCoordinateTransformContext())
        geom5880 = QgsGeometry(geom4674)
        geom5880.transform(ct)

        length_4674 = length_meter(crs4674, context)(geom4674)
        length_5880 = length_meter(crs5880, context)(geom5880)

        self.assertAlmostEqual(length_5880, length_4674, delta=length_4674 * 0.01)

    def test_invalid_source_crs_raises_transform_check_error(self):
        """CRS de origem inválido -> TransformCheckError (não mede no escuro)."""
        context = QgsProcessingContext()
        with self.assertRaises(TransformCheckError):
            length_meter(QgsCoordinateReferenceSystem(), context)

    def test_empty_geometry_measures_zero(self):
        """Geometria vazia/None -> 0.0, sem erro."""
        context = QgsProcessingContext()
        crs = QgsCoordinateReferenceSystem("EPSG:4674")
        measure = length_meter(crs, context)

        self.assertEqual(measure(QgsGeometry()), 0.0)
        self.assertEqual(measure(None), 0.0)


@unittest.skipUnless(_HAS_QGIS, "QGIS não disponível")
class TestReadLinesInCrs(unittest.TestCase):
    """Testes para core/crs_transform.py: read_lines_in_crs."""

    def _line_layer(self, crs, wkts):
        layer = QgsVectorLayer(f"LineString?crs={crs}", "test", "memory")
        pr = layer.dataProvider()
        feats = []
        for wkt in wkts:
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(wkt))
            feats.append(f)
        pr.addFeatures(feats)
        layer.updateExtents()
        return layer

    def test_line_4674_to_5880_preserves_order(self):
        """Camada de linha em 4674 -> geometria em 5880 com x na casa de 5,75 M, ordem preservada."""
        layer = self._line_layer(
            "EPSG:4674",
            [
                "LINESTRING(-46.63 -23.55, -46.62 -23.55)",
                "LINESTRING(-43.20 -22.90, -43.19 -22.90)",
            ],
        )
        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:5880")

        features, geometries = read_lines_in_crs(layer, dst, context, "camada de teste")

        self.assertEqual(len(features), 2)
        self.assertEqual(len(geometries), 2)

        first_vertices = geometries[0].asPolyline()
        self.assertAlmostEqual(first_vertices[0].x(), 5752164.0, delta=2000.0)
        # Rio está a leste de São Paulo: x maior, ordem preservada (posição 0 = São Paulo).
        second_vertices = geometries[1].asPolyline()
        self.assertGreater(second_vertices[0].x(), first_vertices[0].x())

    def test_line_with_vertex_500_500_raises_transform_check_error_citing_id(self):
        """Linha com vértice (500, 500) não transforma (geometria vazia) -> TransformCheckError citando o id."""
        layer = self._line_layer("EPSG:4674", ["LINESTRING(500 500, 500.01 500.01)"])
        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:5880")

        feat = next(layer.getFeatures())
        with self.assertRaises(TransformCheckError) as ctx:
            read_lines_in_crs(layer, dst, context, "camada de teste")

        msg = str(ctx.exception)
        self.assertIn(f"id {feat.id()}", msg)
        self.assertIn("EPSG:4674", msg)
        self.assertIn("EPSG:5880", msg)

    def test_same_crs_skips_reprojection(self):
        """SRC de origem igual ao destino -> geometria original devolvida, sem 2ª passada."""
        layer = self._line_layer("EPSG:3857", ["LINESTRING(0 0, 10 0)"])
        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:3857")

        features, geometries = read_lines_in_crs(layer, dst, context, "camada de teste")

        self.assertEqual(len(geometries), 1)
        vertices = geometries[0].asPolyline()
        self.assertAlmostEqual(vertices[0].x(), 0.0)
        self.assertAlmostEqual(vertices[1].x(), 10.0)

    def test_feature_without_geometry_is_ignored_without_error(self):
        """Feição sem geometria é ignorada nas duas passadas, sem erro."""
        layer = QgsVectorLayer("LineString?crs=EPSG:4674", "test", "memory")
        pr = layer.dataProvider()
        f_no_geom = QgsFeature()
        f_with_geom = QgsFeature()
        f_with_geom.setGeometry(QgsGeometry.fromWkt("LINESTRING(-46.63 -23.55, -46.62 -23.55)"))
        pr.addFeatures([f_no_geom, f_with_geom])
        layer.updateExtents()

        context = QgsProcessingContext()
        dst = QgsCoordinateReferenceSystem("EPSG:5880")

        features, geometries = read_lines_in_crs(layer, dst, context, "camada de teste")

        self.assertEqual(len(features), 1)
        self.assertEqual(len(geometries), 1)


if __name__ == "__main__":
    unittest.main()
