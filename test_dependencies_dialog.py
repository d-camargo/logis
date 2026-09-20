# -*- coding: utf-8 -*-
# Este teste estático verifica o diálogo de gerenciamento de dependências (dependencies_dialog.py)
# e o instalador do OR-Tools (ortools_installer.py).
# Ele lê o conteúdo fonte dos arquivos sem importar QGIS/PyQt.

import pathlib
import unittest


class TestDependenciesDialog(unittest.TestCase):
    """Teste estático de layout e segurança do diálogo de dependências do plugin logis."""

    def setUp(self):
        self.root_dir = pathlib.Path(__file__).parent
        self.dialog_path = self.root_dir / "logis/gui/dependencies_dialog.py"
        self.installer_path = self.root_dir / "logis/core/ortools_installer.py"

        self.assertTrue(
            self.dialog_path.exists(), f"Arquivo {self.dialog_path} não encontrado."
        )
        self.assertTrue(
            self.installer_path.exists(), f"Arquivo {self.installer_path} não encontrado."
        )

        self.dialog_content = self.dialog_path.read_text(encoding="utf-8")
        self.installer_content = self.installer_path.read_text(encoding="utf-8")

    def test_btn_install_connected(self):
        """Verifica se self.btn_install está ligado a self.install_ortools."""
        self.assertIn(
            "self.btn_install.clicked.connect(self.install_ortools)",
            self.dialog_content,
        )

    def test_required_widgets_exist(self):
        """Verifica se existem self.lbl_env, self.lbl_install_hint e self.txt_install_log."""
        self.assertIn("self.lbl_env", self.dialog_content)
        self.assertIn("self.lbl_install_hint", self.dialog_content)
        self.assertIn("self.txt_install_log", self.dialog_content)

    def test_ortools_installer_imports(self):
        """Verifica se o módulo importa detect_environment, install_ortools e refresh_import_path de ..core.ortools_installer."""
        self.assertIn("detect_environment", self.dialog_content)
        self.assertIn("install_ortools", self.dialog_content)
        self.assertIn("refresh_import_path", self.dialog_content)
        self.assertIn("ortools_installer", self.dialog_content)

    def test_qmessagebox_usage(self):
        """Verifica se aparecem QMessageBox.question e QMessageBox.StandardButton.Yes."""
        self.assertIn("QMessageBox.question", self.dialog_content)
        self.assertIn("QMessageBox.StandardButton.Yes", self.dialog_content)

    def test_cursor_override_handling(self):
        """Verifica se QApplication.setOverrideCursor e restoreOverrideCursor aparecem em número igual (1 cada) e Qt.CursorShape.WaitCursor."""
        set_cursor_count = self.dialog_content.count("QApplication.setOverrideCursor(")
        restore_cursor_count = self.dialog_content.count(
            "QApplication.restoreOverrideCursor()"
        )

        self.assertEqual(
            set_cursor_count,
            1,
            f"Esperado 1 chamada para QApplication.setOverrideCursor(, encontrado {set_cursor_count}.",
        )
        self.assertEqual(
            restore_cursor_count,
            1,
            f"Esperado 1 chamada para QApplication.restoreOverrideCursor(), encontrado {restore_cursor_count}.",
        )
        self.assertIn("Qt.CursorShape.WaitCursor", self.dialog_content)

    def test_prohibited_patterns(self):
        """Verifica se NÃO aparecem subprocess, os.system, QgsTask nem self.tr( (regras D-A, D-B, D-J)."""
        self.assertNotIn("subprocess", self.dialog_content)
        self.assertNotIn("os.system", self.dialog_content)
        self.assertNotIn("QgsTask", self.dialog_content)
        self.assertNotIn("self.tr(", self.dialog_content)

    def test_refresh_import_path_called(self):
        """Verifica se refresh_import_path() é chamado."""
        self.assertIn("refresh_import_path()", self.dialog_content)

    def test_sys_executable_not_in_raw_pip_command(self):
        """Verifica se [sys.executable, "-m", "pip" NÃO existe mais em ortools_installer.py (fora de python_executable())."""
        self.assertNotIn('[sys.executable, "-m", "pip"', self.installer_content)

    def test_btn_reset_guard_connected(self):
        """Verifica se o botão Reativar OR-Tools existe e está conectado a reactivate_ortools."""
        self.assertIn("self.btn_reset_guard", self.dialog_content)
        self.assertIn("Reativar OR-Tools", self.dialog_content)
        self.assertIn(
            "self.btn_reset_guard.clicked.connect(self.reactivate_ortools)",
            self.dialog_content,
        )

    def test_reset_ortools_guard_imports_and_calls(self):
        """Verifica se guard_state e reset_ortools_guard são importados e chamados no diálogo."""
        self.assertIn("guard_state", self.dialog_content)
        self.assertIn("reset_ortools_guard", self.dialog_content)
        self.assertIn("reset_ortools_guard()", self.dialog_content)
        self.assertIn("guard_state()", self.dialog_content)

    def test_blocked_status_text(self):
        """Verifica se a mensagem de bloqueio menciona que o QGIS fechou e a heurística Python."""
        self.assertIn("QGIS fechou durante o carregamento do OR-Tools", self.dialog_content)
        self.assertIn("heurística Python", self.dialog_content)

    def test_ortools_group_title_and_description(self):
        """Verifica se o título do grupo OR-Tools e sua descrição refletem escopo correto de rotas vs instalações."""
        self.assertIn("Google OR-Tools (Otimização de Rotas)", self.dialog_content)
        self.assertNotIn("Google OR-Tools (Otimização de Rotas e Instalações)", self.dialog_content)
        self.assertIn("TSP e CVRP", self.dialog_content)
        self.assertIn("p-mediana, MCLP e LSCP", self.dialog_content)


if __name__ == "__main__":
    unittest.main()
