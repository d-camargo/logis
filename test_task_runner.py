# -*- coding: utf-8 -*-
import pathlib
import unittest


class TestTaskRunnerSource(unittest.TestCase):
    """Teste estático do AlgTaskRunner sem depender da inicialização do QGIS."""

    def setUp(self):
        self.source_path = pathlib.Path(__file__).parent / 'logis' / 'gui' / 'task_runner.py'
        self.assertTrue(self.source_path.exists(), "O arquivo task_runner.py não existe.")
        self.source_code = self.source_path.read_text(encoding='utf-8')

    def test_qgs_processing_alg_runner_task_present(self):
        self.assertIn("QgsProcessingAlgRunnerTask", self.source_code,
                      "QgsProcessingAlgRunnerTask não encontrado")

    def test_task_manager_add_task_present(self):
        self.assertIn("taskManager().addTask", self.source_code,
                      "taskManager().addTask não encontrado")

    def test_set_project_present(self):
        self.assertIn("setProject", self.source_code, "setProject não encontrado")
        self.assertIn("QgsProject.instance()", self.source_code, "QgsProject.instance() não encontrado")

    def test_take_result_layer_present(self):
        self.assertIn("takeResultLayer", self.source_code, "takeResultLayer não encontrado")

    def test_synchronous_fallback_present(self):
        self.assertIn("processing.run(", self.source_code, "Fallback síncrono processing.run não encontrado")
        self.assertIn("on_finished(True", self.source_code, "Chamada on_finished(True no fallback não encontrada")

    def test_references_kept_in_self(self):
        self.assertIn("self.context =", self.source_code, "Referência forte de context não encontrada")
        self.assertIn("self.feedback =", self.source_code, "Referência forte de feedback não encontrada")
        self.assertIn("self.task =", self.source_code, "Referência forte de task não encontrada")

    def test_no_unscoped_enums(self):
        """test_qt6_compat já cuida da validação ampla, mas checamos obviedades aqui"""
        self.assertNotIn("QVariant.", self.source_code, "Enum QVariant não deve ser usado")
        self.assertNotIn("exec_(", self.source_code, "exec_() é proibido")
