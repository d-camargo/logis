# -*- coding: utf-8 -*-
import os
import unittest
from PyQt5.QtCore import QCoreApplication, QTranslator


class TestI18n(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if QCoreApplication.instance() is None:
            cls._app = QCoreApplication([])
        else:
            cls._app = QCoreApplication.instance()

    def test_logis_en_qm_translation(self):
        qm_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logis", "i18n", "logis_en.qm"
        )
        self.assertTrue(
            os.path.exists(qm_path),
            f"Arquivo de tradução {qm_path} não foi encontrado.",
        )

        translator = QTranslator()
        loaded = translator.load(qm_path)
        self.assertTrue(loaded, f"Falha ao carregar {qm_path} com QTranslator.")

        translated = translator.translate("UrbanDock", "Calcular Indicadores")
        self.assertEqual(
            translated,
            "Calculate Indicators",
            "A tradução de 'Calcular Indicadores' não corresponde ao esperado.",
        )

        translated_docs = translator.translate(
            "LogisPlugin", "Documentação".encode("utf-8")
        )
        self.assertEqual(
            translated_docs,
            "Documentation",
            "A tradução de 'Documentação' não corresponde ao esperado.",
        )

        translated_osm = translator.translate(
            "NetworkDock", "Baixando rede viária OSM…".encode("utf-8")
        )
        self.assertEqual(
            translated_osm,
            "Downloading OSM road network…",
            "A tradução de 'Baixando rede viária OSM…' não corresponde ao esperado.",
        )

        translated_alg = translator.translate(
            "AlgTaskRunner", "Algoritmo {id} não encontrado no registro do Processing.".encode("utf-8")
        )
        self.assertEqual(
            translated_alg,
            "Algorithm {id} not found in the Processing registry.",
            "A tradução de 'Algoritmo...' em AlgTaskRunner não corresponde ao esperado.",
        )

        translated_err = translator.translate(
            "RoutingDock",
            "<span style='color: #fc8181;'>Erro ao iniciar o cálculo: {error}</span><br>".encode("utf-8"),
        )
        self.assertEqual(
            translated_err,
            "<span style='color: #fc8181;'>Error starting the calculation: {error}</span><br>",
            "A tradução de 'Erro ao iniciar o cálculo...' em RoutingDock não corresponde ao esperado.",
        )

        translated_cvrp_depot = translator.translate("VrpCvrp", "depósito".encode("utf-8"))
        self.assertEqual(
            translated_cvrp_depot,
            "depot",
            "A tradução de 'depósito' em VrpCvrp não corresponde ao esperado.",
        )

        translated_tsp_crs = translator.translate("VrpTsp", "SRC da rede: {}")
        self.assertEqual(
            translated_tsp_crs,
            "Network CRS: {}",
            "A tradução de 'SRC da rede: {}' em VrpTsp não corresponde ao esperado.",
        )

    def test_logis_pt_qm_does_not_exist(self):
        pt_qm_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logis", "i18n", "logis_pt.qm"
        )
        self.assertFalse(
            os.path.exists(pt_qm_path),
            "logis/i18n/logis_pt.qm não deve existir (fallback PT-BR de origem é suficiente).",
        )


if __name__ == "__main__":
    unittest.main()
