# -*- coding: utf-8 -*-
import unittest
import urllib.parse
from logis.core.connectors.wfs import build_url

class TestWFSConnector(unittest.TestCase):
    def test_build_url_simple(self):
        endpoint = "https://geoservicos.inde.gov.br/geoserver/DNIT/ows"
        type_name = "DNIT:snv_202507a"
        url = build_url(endpoint, type_name)
        
        self.assertTrue(url.startswith(endpoint))
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        
        self.assertEqual(params["service"], ["WFS"])
        self.assertEqual(params["version"], ["2.0.0"])
        self.assertEqual(params["request"], ["GetFeature"])
        self.assertEqual(params["typeNames"], [type_name])
        self.assertEqual(params["srsName"], ["EPSG:4674"])
        self.assertEqual(params["outputFormat"], ["application/json"])
        self.assertNotIn("CQL_FILTER", params)
        self.assertNotIn("bbox", params)

    def test_build_url_cql(self):
        endpoint = "https://geoservicos.inde.gov.br/geoserver/DNIT/ows"
        type_name = "DNIT:snv_202507a"
        cql = "sg_uf = 'MG'"
        url = build_url(endpoint, type_name, cql_filter=cql)
        
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(params["CQL_FILTER"], [cql])
        self.assertNotIn("bbox", params)

    def test_build_url_bbox(self):
        endpoint = "https://geoservicos.inde.gov.br/geoserver/DNIT/ows"
        type_name = "DNIT:snv_202507a"
        bbox = (-45.0, -20.0, -40.0, -15.0)
        url = build_url(endpoint, type_name, bbox=bbox)
        
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(params["bbox"], ["-45.0,-20.0,-40.0,-15.0,EPSG:4674"])
        self.assertNotIn("CQL_FILTER", params)

    def test_build_url_cql_priority(self):
        endpoint = "https://geoservicos.inde.gov.br/geoserver/DNIT/ows"
        type_name = "DNIT:snv_202507a"
        cql = "sg_uf = 'MG'"
        bbox = (-45.0, -20.0, -40.0, -15.0)
        url = build_url(endpoint, type_name, cql_filter=cql, bbox=bbox)
        
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(params["CQL_FILTER"], [cql])
        self.assertNotIn("bbox", params)

if __name__ == '__main__':
    unittest.main()
