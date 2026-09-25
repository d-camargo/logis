# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from unittest.mock import patch

from qgis.core import QgsApplication, QgsVectorLayer, QgsFeature, QgsGeometry, QgsFields, QgsField
from qgis.PyQt.QtCore import QVariant

# Initialize QgsApplication
qgs = QgsApplication.instance()
if not qgs:
    qgs = QgsApplication([], False)
    qgs.initQgis()

from logis.core.network.snv_pipeline import _parse_snv_speed, build_snv_state_network


class TestSNVPipeline(unittest.TestCase):
    def test_parse_snv_speed(self):
        self.assertEqual(_parse_snv_speed("Pavimentada"), 80.0)
        self.assertEqual(_parse_snv_speed("Duplicada"), 110.0)
        self.assertEqual(_parse_snv_speed("Implantada"), 60.0)
        self.assertEqual(_parse_snv_speed("Terra"), 40.0)
        self.assertEqual(_parse_snv_speed("Leito Natural"), 30.0)
        self.assertEqual(_parse_snv_speed("Planejada"), 30.0)
        self.assertEqual(_parse_snv_speed("Outra"), 60.0)
        self.assertEqual(_parse_snv_speed(""), 60.0)
        self.assertEqual(_parse_snv_speed(None), 60.0)

    @patch('logis.core.connectors.wfs.fetch_layer')
    def test_build_snv_state_network(self, mock_fetch_layer):
        # Create a mock source layer in memory representing WFS output
        mock_layer = QgsVectorLayer(
            "MultiLineString?crs=EPSG:4674&field=id_trecho_:int&field=vl_codigo:string&"
            "field=vl_br:string&field=sg_uf:string&field=ds_superfi:string&"
            "field=ds_jurisdi:string&field=vl_extensa:double",
            "mock_snv",
            "memory"
        )
        self.assertTrue(mock_layer.isValid())
        mock_layer.startEditing()

        # Add a mock feature
        feat = QgsFeature(mock_layer.fields())
        geom = QgsGeometry.fromWkt("MULTILINESTRING((0 0, 1 1))")
        feat.setGeometry(geom)
        feat["id_trecho_"] = 12345
        feat["vl_codigo"] = "116BRMG0110"
        feat["vl_br"] = "116"
        feat["sg_uf"] = "MG"
        feat["ds_superfi"] = "Pavimentada"
        feat["ds_jurisdi"] = "Federal"
        feat["vl_extensa"] = 1.5
        mock_layer.addFeature(feat)
        mock_layer.commitChanges()

        mock_fetch_layer.return_value = mock_layer

        with tempfile.TemporaryDirectory() as tmpdir:
            gpkg_path = os.path.join(tmpdir, "test_regional.gpkg")

            # Execute build_snv_state_network
            result = build_snv_state_network("MG", gpkg_path, force=True)

            # Check results
            self.assertTrue(result["metadata"]["gpkg_ok"])
            self.assertEqual(result["metadata"]["uf"], "MG")
            self.assertEqual(result["metadata"]["links"], 1)
            self.assertEqual(result["metadata"]["nodes"], 2)

            # Verify GeoPackage files were created and are valid layers
            links_path = f"{gpkg_path}|layername=snv_links_MG"
            nodes_path = f"{gpkg_path}|layername=snv_nodes_MG"

            links_lyr = QgsVectorLayer(links_path, "links", "ogr")
            nodes_lyr = QgsVectorLayer(nodes_path, "nodes", "ogr")

            self.assertTrue(links_lyr.isValid())
            self.assertTrue(nodes_lyr.isValid())

            # Verify fields and values
            features = list(links_lyr.getFeatures())
            self.assertEqual(len(features), 1)
            f = features[0]
            self.assertEqual(f["id_trecho"], 12345)
            self.assertEqual(f["vl_codigo"], "116BRMG0110")
            self.assertEqual(f["vl_br"], "116")
            self.assertEqual(f["sg_uf"], "MG")
            self.assertEqual(f["ds_superfi"], "Pavimentada")
            self.assertEqual(f["ds_jurisdi"], "Federal")
            self.assertEqual(f["oneway"], "no")
            self.assertAlmostEqual(f["length"], 1500.0)
            self.assertEqual(f["speed"], 80.0)
            self.assertAlmostEqual(f["travel_time"], 1500.0 / (80.0 / 3.6))

            node_features = list(nodes_lyr.getFeatures())
            self.assertEqual(len(node_features), 2)


if __name__ == '__main__':
    unittest.main()
