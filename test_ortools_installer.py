# -*- coding: utf-8 -*-
"""Testes de core/ortools_installer.py.

Guarda a construção do comando de instalação e os tratamentos de erro:
fixar os pacotes já instalados no QGIS (numpy, pandas, typing_extensions)
preserva o ambiente do usuário sem impor travas fixas incompatíveis com
Python 3.13 / QGIS 4.x.
"""

import unittest

from logis.core.ortools_installer import ORToolsInstallTask, installed_versions
from logis.core.optim_backend import has_ortools


class TestInstallCommand(unittest.TestCase):
    def setUp(self):
        self.task = ORToolsInstallTask()

    def test_command_has_only_binary_flag(self):
        cmd = self.task.build_command()
        self.assertIn("--only-binary=:all:", cmd)

    def test_command_pins_installed_versions(self):
        versions = {
            "numpy": "1.26.4",
            "pandas": "2.0.3",
            "typing_extensions": "4.10.0",
        }
        cmd = self.task.build_command(versions=versions)
        self.assertIn("numpy==1.26.4", cmd)
        self.assertIn("pandas==2.0.3", cmd)
        self.assertIn("typing_extensions==4.10.0", cmd)
        self.assertIn("ortools", cmd)
        self.assertIn("--user", cmd)
        self.assertIn("--only-binary=:all:", cmd)

    def test_command_omits_missing_versions(self):
        versions = {
            "numpy": "2.1.3",
            "pandas": "2.2.3",
            "typing_extensions": None,
        }
        cmd = self.task.build_command(versions=versions)
        self.assertIn("numpy==2.1.3", cmd)
        self.assertIn("pandas==2.2.3", cmd)
        self.assertFalse(any(arg.startswith("typing_extensions") for arg in cmd))

    def test_command_packages_only_ortools_when_environment_is_empty(self):
        versions = {
            "numpy": None,
            "pandas": None,
            "typing_extensions": None,
        }
        cmd = self.task.build_command(versions=versions)
        pacotes = [
            arg for arg in cmd[cmd.index("install") + 1:] if not arg.startswith("-")
        ]
        self.assertEqual(pacotes, ["ortools"])

    def test_command_invariants_in_all_cases(self):
        cases = [
            {"numpy": "1.26.4", "pandas": "2.0.3", "typing_extensions": "4.10.0"},
            {"numpy": "2.1.3", "pandas": "2.2.3", "typing_extensions": None},
            {"numpy": None, "pandas": None, "typing_extensions": None},
        ]
        for versions in cases:
            cmd = self.task.build_command(versions=versions)
            self.assertNotIn("numpy<2", cmd)
            self.assertNotIn("pandas<3", cmd)
            self.assertIn("--only-binary=:all:", cmd)

    def test_installed_versions_returns_dict_with_keys(self):
        res = installed_versions()
        self.assertIsInstance(res, dict)
        for key in ("numpy", "pandas", "typing_extensions"):
            self.assertIn(key, res)

    def test_break_system_packages_is_opt_in(self):
        self.assertNotIn("--break-system-packages", self.task.build_command())
        self.assertIn(
            "--break-system-packages",
            self.task.build_command(break_system_packages=True),
        )

    def test_retries_once_with_break_system_packages(self):
        chamadas = []

        def fake_run_pip(cmd):
            chamadas.append(cmd)
            if len(chamadas) == 1:
                self.task.output.append(
                    "error: externally-managed-environment"
                )
                return 1
            return 0

        self.task._run_pip = fake_run_pip
        self.assertTrue(self.task.run())
        self.assertEqual(len(chamadas), 2)
        self.assertNotIn("--break-system-packages", chamadas[0])
        self.assertIn("--break-system-packages", chamadas[1])

    def test_no_retry_when_error_is_unrelated(self):
        chamadas = []

        def fake_run_pip(cmd):
            chamadas.append(cmd)
            self.task.output.append("Network is unreachable")
            return 1

        self.task._run_pip = fake_run_pip
        self.assertFalse(self.task.run())
        self.assertEqual(len(chamadas), 1)
        self.assertIn("Falha de rede", self.task.error)

    def test_error_message_numpy_incompatibility(self):
        def fake_run_pip(cmd):
            self.task.output.append("ResolutionImpossible: numpy incompatibility")
            return 1

        self.task._run_pip = fake_run_pip
        self.assertFalse(self.task.run())
        self.assertIn("NumPy", self.task.error)
        self.assertIn("incompatível", self.task.error)
        self.assertTrue(self.task.error.endswith("O OR-Tools é opcional."))

    def test_error_message_no_binary_package(self):
        def fake_run_pip(cmd):
            self.task.output.append("No matching distribution found for ortools (only-binary)")
            return 1

        self.task._run_pip = fake_run_pip
        self.assertFalse(self.task.run())
        self.assertIn("pacote binário", self.task.error)
        self.assertTrue(self.task.error.endswith("O OR-Tools é opcional."))

    def test_no_wheel_for_this_python_is_not_reported_as_network_failure(self):
        """Saída real do pip no Flatpak/cp313: sem wheel, mas com rede."""
        def fake_run_pip(cmd):
            self.task.output.append(
                "ERROR: Could not find a version that satisfies the "
                "requirement ortools (from versions: none)"
            )
            self.task.output.append("ERROR: No matching distribution found for ortools")
            return 1

        self.task._run_pip = fake_run_pip
        self.assertFalse(self.task.run())
        self.assertNotIn("Falha de rede", self.task.error)
        self.assertIn("pacote binário", self.task.error)


class TestHasORTools(unittest.TestCase):
    def test_clean_import_error_returns_false_without_raising(self):
        from unittest.mock import patch
        import sys
        import builtins
        orig_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "ortools":
                raise ImportError("No module named ortools")
            return orig_import(name, *args, **kwargs)

        with patch.dict("sys.modules"):
            sys.modules.pop("ortools", None)
            with patch("builtins.__import__", side_effect=fake_import):
                self.assertFalse(has_ortools())

    def test_broken_installation_exception_returns_false_and_does_not_propagate(self):
        from unittest.mock import patch
        import sys
        import builtins
        orig_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "ortools":
                raise ValueError("Corrupted extension library")
            return orig_import(name, *args, **kwargs)

        with patch.dict("sys.modules"):
            sys.modules.pop("ortools", None)
            with patch("builtins.__import__", side_effect=fake_import):
                self.assertFalse(has_ortools())


if __name__ == "__main__":
    unittest.main()
