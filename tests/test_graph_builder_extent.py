# -*- coding: utf-8 -*-
import unittest
from logis.core.network.graph_builder import build_graph

try:
    from qgis.core import (QgsApplication, QgsVectorLayer, QgsField, QgsFeature,
                           QgsGeometry, QgsPointXY, QgsRectangle, QgsCsException)
    from qgis.PyQt.QtCore import QVariant
    _qgs = QgsApplication.instance()
    if not _qgs:
        _qgs = QgsApplication([], False)
        _qgs.initQgis()
    _HAS_QGIS = True
except ImportError:
    _HAS_QGIS = False

try:
    import processing  # noqa: F401  (só disponível dentro do QGIS ou com python/plugins no path)
    _HAS_PROCESSING = True
except ImportError:
    _HAS_PROCESSING = False

from logis.core.crs_transform import TransformCheckError
from logis.core import qgis_compat


@unittest.skipUnless(_HAS_QGIS, "QGIS não disponível")
class TestGraphBuilderExtent(unittest.TestCase):
    """
    Testes unitários para build_graph com e sem extent (core/network/graph_builder.py).
    """

    def setUp(self):
        layer = QgsVectorLayer("LineString?crs=EPSG:4326", "test_network", "memory")
        layer.dataProvider().addAttributes([
            QgsField("oneway", QVariant.String),
            QgsField("speed", QVariant.Double),
        ])
        layer.updateFields()

        geometries = [
            QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(1, 1)]),
            QgsGeometry.fromPolylineXY([QgsPointXY(1, 1), QgsPointXY(2, 2)]),
            QgsGeometry.fromPolylineXY([QgsPointXY(10, 10), QgsPointXY(11, 11)]),
        ]
        for geom in geometries:
            feat = QgsFeature(layer.fields())
            feat.setGeometry(geom)
            feat.setAttribute("oneway", "B")
            feat.setAttribute("speed", 40.0)
            layer.dataProvider().addFeature(feat)

        layer.updateExtents()
        self.layer = layer

    @unittest.skipUnless(_HAS_PROCESSING, "processing não disponível")
    def test_graph_builder_no_extent(self):
        res = build_graph(self.layer, target_crs="EPSG:4326")
        self.assertEqual(res["graph"].vertexCount(), 5)
        self.assertGreater(res["graph"].edgeCount(), 0)

    def test_graph_builder_with_extent(self):
        extent = QgsRectangle(-1, -1, 1.5, 1.5)
        res = build_graph(self.layer, target_crs="EPSG:4326", extent=extent)
        self.assertEqual(res["graph"].vertexCount(), 3)
        self.assertGreater(res["graph"].edgeCount(), 0)

    def test_graph_builder_extent_excludes_all(self):
        extent = QgsRectangle(20, 20, 21, 21)
        with self.assertRaises(RuntimeError) as ctx:
            build_graph(self.layer, target_crs="EPSG:4326", extent=extent)
        self.assertIn("No features found in the specified extent.", str(ctx.exception))

    def test_graph_builder_invalid_inverted_extent(self):
        inverted_extent = QgsRectangle()
        inverted_extent.setXMinimum(10)
        inverted_extent.setYMinimum(10)
        inverted_extent.setXMaximum(0)
        inverted_extent.setYMaximum(0)
        with self.assertRaises(ValueError) as ctx:
            build_graph(self.layer, target_crs="EPSG:4326", extent=inverted_extent)
        self.assertIn(str(inverted_extent), str(ctx.exception))

    def test_graph_builder_out_of_bounds_extent_transform(self):
        layer_4674 = QgsVectorLayer("LineString?crs=EPSG:4674", "test_network_4674", "memory")
        extent_5880 = QgsRectangle(-3046.67, -3023.63, 2953.40, 2976.51)
        with self.assertRaises(RuntimeError) as ctx:
            build_graph(layer_4674, target_crs="EPSG:5880", extent=extent_5880)
        self.assertIsInstance(ctx.exception, TransformCheckError)
        self.assertIn("EPSG:5880", str(ctx.exception))

    def test_graph_builder_extent_sao_paulo_5880(self):
        layer_sp = QgsVectorLayer("LineString?crs=EPSG:4674", "test_network_sp", "memory")
        layer_sp.dataProvider().addAttributes([
            QgsField("oneway", qgis_compat.field_type("string")),
            QgsField("speed", qgis_compat.field_type("double")),
        ])
        layer_sp.updateFields()

        geom1 = QgsGeometry.fromPolylineXY([QgsPointXY(-46.635, -23.555), QgsPointXY(-46.630, -23.550)])
        geom2 = QgsGeometry.fromPolylineXY([QgsPointXY(-46.630, -23.550), QgsPointXY(-46.625, -23.545)])
        for geom in [geom1, geom2]:
            feat = QgsFeature(layer_sp.fields())
            feat.setGeometry(geom)
            feat.setAttribute("oneway", "B")
            feat.setAttribute("speed", 40.0)
            layer_sp.dataProvider().addFeature(feat)
        layer_sp.updateExtents()

        extent_5880 = QgsRectangle(5750000, 7370000, 5760000, 7380000)
        res = build_graph(layer_sp, target_crs="EPSG:5880", extent=extent_5880)
        self.assertIsNotNone(res["graph"])
        self.assertGreater(res["graph"].vertexCount(), 0)
        self.assertGreater(res["graph"].edgeCount(), 0)
        self.assertEqual(res["crs"].authid(), "EPSG:5880")


if __name__ == "__main__":
    unittest.main()
