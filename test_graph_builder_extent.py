# -*- coding: utf-8 -*-
import unittest
from logis.core.network.graph_builder import build_graph

try:
    from qgis.core import (QgsApplication, QgsVectorLayer, QgsField, QgsFeature,
                           QgsGeometry, QgsPointXY, QgsRectangle)
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


if __name__ == "__main__":
    unittest.main()
