# -*- coding: utf-8 -*-
import os
import unittest

class TestVrpCvrpAlgorithm(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(__file__)
        self.alg_path = os.path.join(self.base_dir, "logis", "algorithms", "vrp_cvrp.py")

        with open(self.alg_path, "r", encoding="utf-8") as f:
            self.alg_source = f.read()

    def test_vrp_cvrp_parameters_and_backend(self):
        # parameter definitions
        self.assertIn("BACKEND = 'BACKEND'", self.alg_source)
        self.assertIn("QgsProcessingParameterEnum", self.alg_source)
        self.assertIn("Automático (OR-Tools quando disponível)", self.alg_source)
        self.assertIn("Python puro (heurística)", self.alg_source)
        self.assertIn("OR-Tools", self.alg_source)
        self.assertIn("parameterAsEnum", self.alg_source)

        # pass to solve_cvrp
        self.assertIn("backend=req_backend", self.alg_source)

        # backend layer field
        self.assertIn('route_fields.append(QgsField("backend", qgis_compat.field_type("string")))', self.alg_source)

    def test_vrp_cvrp_crashlog_trace(self):
        self.assertIn("crashlog", self.alg_source)
        for stage in (
            "cvrp-inicio",
            "cvrp-transform",
            "cvrp-build-graph",
            "cvrp-grafo-pronto",
            "cvrp-od-matrix",
            "cvrp-ortools-import",
            "cvrp-solver-ok",
            "cvrp-sinks",
            "cvrp-fim",
        ):
            self.assertIn(f'crashlog.mark("{stage}"', self.alg_source)

if __name__ == "__main__":
    unittest.main()
