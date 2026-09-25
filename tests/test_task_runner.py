# -*- coding: utf-8 -*-
import pathlib
import sys
import unittest
from unittest.mock import MagicMock, patch

if "processing" not in sys.modules:
    sys.modules["processing"] = MagicMock()

try:
    from qgis.core import QgsApplication
    _qgs = QgsApplication.instance()
    if _qgs is None:
        _qgs = QgsApplication([], False)
        _qgs.initQgis()
except ImportError:
    pass

from logis.gui.task_runner import AlgTaskRunner, SignalFeedback


class TestTaskRunnerSource(unittest.TestCase):
    """Teste estático do AlgTaskRunner sem depender da inicialização do QGIS."""

    def setUp(self):
        self.source_path = pathlib.Path(__file__).resolve().parent.parent / 'logis' / 'gui' / 'task_runner.py'
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


class TestAlgTaskRunner(unittest.TestCase):
    """Testes unitários com mock do AlgTaskRunner e SignalFeedback."""

    @patch("logis.gui.task_runner.QgsProcessingAlgRunnerTask")
    @patch("logis.gui.task_runner.QgsApplication")
    def test_task_runner_uses_alg_object(self, mock_qgs_app, mock_task_cls):
        """(a) O primeiro argumento de QgsProcessingAlgRunnerTask é o objeto devolvido por algorithmById, não a string."""
        mock_registry = MagicMock()
        mock_alg = MagicMock()
        mock_registry.algorithmById.return_value = mock_alg
        mock_qgs_app.processingRegistry.return_value = mock_registry

        mock_tm = MagicMock()
        mock_qgs_app.taskManager.return_value = mock_tm

        mock_on_finished = MagicMock()
        runner = AlgTaskRunner("logis:test_alg", {"PARAM": 123}, mock_on_finished)

        runner.start()

        mock_registry.algorithmById.assert_called_once_with("logis:test_alg")
        mock_task_cls.assert_called_once_with(
            mock_alg, {"PARAM": 123}, runner.context, runner.feedback
        )
        mock_tm.addTask.assert_called_once()

    @patch("logis.gui.task_runner.QgsProcessingAlgRunnerTask")
    @patch("logis.gui.task_runner.QgsApplication")
    def test_algorithm_by_id_none(self, mock_qgs_app, mock_task_cls):
        """(b) algorithmById -> None gera UM on_finished(False, str) e não cria task."""
        mock_registry = MagicMock()
        mock_registry.algorithmById.return_value = None
        mock_qgs_app.processingRegistry.return_value = mock_registry

        mock_on_finished = MagicMock()
        runner = AlgTaskRunner("invalid:alg", {}, mock_on_finished)

        runner.start()

        mock_on_finished.assert_called_once()
        success, msg = mock_on_finished.call_args[0]
        self.assertFalse(success)
        self.assertIsInstance(msg, str)
        self.assertIn("invalid:alg", msg)
        mock_task_cls.assert_not_called()

    @patch("logis.gui.task_runner.QgsProcessingAlgRunnerTask")
    @patch("logis.gui.task_runner.QgsApplication")
    def test_task_constructor_raises(self, mock_qgs_app, mock_task_cls):
        """(c) Construtor da task levantando gera UM on_finished(False, mensagem)."""
        mock_registry = MagicMock()
        mock_alg = MagicMock()
        mock_registry.algorithmById.return_value = mock_alg
        mock_qgs_app.processingRegistry.return_value = mock_registry

        mock_tm = MagicMock()
        mock_qgs_app.taskManager.return_value = mock_tm
        mock_task_cls.side_effect = RuntimeError("Erro na construção da task")

        mock_on_finished = MagicMock()
        runner = AlgTaskRunner("logis:test_alg", {}, mock_on_finished)

        runner.start()

        mock_on_finished.assert_called_once_with(False, "Erro na construção da task")

    @patch("logis.gui.task_runner.processing.run")
    @patch("logis.gui.task_runner.QgsApplication")
    def test_synchronous_fallback_failure_and_success(
        self, mock_qgs_app, mock_processing_run
    ):
        """(d) Fallback síncrono com processing.run levantando gera UM on_finished(False, ...), e sucesso gera UM on_finished(True, results)."""
        mock_registry = MagicMock()
        mock_alg = MagicMock()
        mock_registry.algorithmById.return_value = mock_alg
        mock_qgs_app.processingRegistry.return_value = mock_registry
        mock_qgs_app.taskManager.return_value = None

        # d1: failure
        mock_processing_run.side_effect = RuntimeError("Erro no processamento síncrono")
        mock_on_finished_fail = MagicMock()
        runner_fail = AlgTaskRunner("logis:test_alg", {}, mock_on_finished_fail)
        runner_fail.start()

        mock_on_finished_fail.assert_called_once_with(False, "Erro no processamento síncrono")

        # d2: success
        mock_processing_run.side_effect = None
        mock_processing_run.return_value = {"OUTPUT": "layer_result"}
        mock_on_finished_success = MagicMock()
        runner_success = AlgTaskRunner("logis:test_alg", {}, mock_on_finished_success)
        runner_success.start()

        mock_on_finished_success.assert_called_once_with(
            True, {"OUTPUT": "layer_result"}
        )

    def test_cancel_cancels_feedback_and_task(self):
        """(e) cancel() chama cancel no feedback e na task."""
        mock_on_finished = MagicMock()
        runner = AlgTaskRunner("logis:test_alg", {}, mock_on_finished)
        mock_task = MagicMock()
        runner.task = mock_task

        with patch.object(runner.feedback, "cancel") as mock_fb_cancel:
            runner.cancel()
            mock_fb_cancel.assert_called_once()
            mock_task.cancel.assert_called_once()

    def test_report_error_emits_message(self):
        """(f) reportError emite message_emitted e atualiza last_error."""
        feedback = SignalFeedback()
        self.assertEqual(feedback.last_error, "")
        mock_slot = MagicMock()
        feedback.message_emitted.connect(mock_slot)

        feedback.reportError("Mensagem de erro", fatalError=False)
        mock_slot.assert_called_once_with("Mensagem de erro")
        self.assertEqual(feedback.last_error, "Mensagem de erro")


if __name__ == "__main__":
    unittest.main()
