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
        qm_path = os.path.join(os.path.dirname(__file__), "logis", "i18n", "logis_en.qm")
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

    def test_logis_pt_qm_does_not_exist(self):
        pt_qm_path = os.path.join(
            os.path.dirname(__file__), "logis", "i18n", "logis_pt.qm"
        )
        self.assertFalse(
            os.path.exists(pt_qm_path),
            "logis/i18n/logis_pt.qm não deve existir (fallback PT-BR de origem é suficiente).",
        )


if __name__ == "__main__":
    unittest.main()
