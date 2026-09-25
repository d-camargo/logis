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
        QgsPointXY,
        QgsRectangle,
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


if __name__ == "__main__":
    unittest.main()
