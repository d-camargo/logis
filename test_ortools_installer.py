# -*- coding: utf-8 -*-
"""Testes de core/ortools_installer.py.

Guarda a construção do comando de instalação:
fixar os pacotes já instalados no QGIS (numpy, pandas, typing_extensions)
preserva o ambiente do usuário sem impor travas fixas incompatíveis com
Python 3.13 / QGIS 4.x.
"""

import sys
import unittest
from unittest import mock

from logis.core import ortools_installer
from logis.core.ortools_installer import (
    build_command,
    command_text,
    installed_versions,
    is_installed,
)
from logis.core.optim_backend import has_ortools


class TestInstallCommand(unittest.TestCase):
    def test_command_has_only_binary_flag(self):
        cmd = build_command()
        self.assertIn("--only-binary=:all:", cmd)

    def test_command_pins_installed_versions(self):
        versions = {
            "numpy": "1.26.4",
            "pandas": "2.0.3",
            "typing_extensions": "4.10.0",
        }
        cmd = build_command(versions=versions)
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
        cmd = build_command(versions=versions)
        self.assertIn("numpy==2.1.3", cmd)
        self.assertIn("pandas==2.2.3", cmd)
        self.assertFalse(any(arg.startswith("typing_extensions") for arg in cmd))

    def test_command_packages_only_ortools_when_environment_is_empty(self):
        versions = {
            "numpy": None,
            "pandas": None,
            "typing_extensions": None,
        }
        cmd = build_command(versions=versions)
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
            cmd = build_command(versions=versions)
            self.assertNotIn("numpy<2", cmd)
            self.assertNotIn("pandas<3", cmd)
            self.assertIn("--only-binary=:all:", cmd)

    def test_installed_versions_returns_dict_with_keys(self):
        res = installed_versions()
        self.assertIsInstance(res, dict)
        for key in ("numpy", "pandas", "typing_extensions"):
            self.assertIn(key, res)

    def test_break_system_packages_is_opt_in(self):
        self.assertNotIn("--break-system-packages", build_command())
        self.assertIn(
            "--break-system-packages",
            build_command(break_system_packages=True),
        )

    def test_command_pins_valid_pep440_versions(self):
        versions = {
            "numpy": "2.1.0",
            "pandas": "1.5.3.post1",
            "typing_extensions": "4.10.0",
        }
        cmd = build_command(versions=versions)
        self.assertIn("numpy==2.1.0", cmd)
        self.assertIn("pandas==1.5.3.post1", cmd)
        self.assertIn("typing_extensions==4.10.0", cmd)

    def test_command_pins_prerelease_and_local_version(self):
        cmd = build_command(versions={"numpy": "2.0.0rc1+local"})
        self.assertIn("numpy==2.0.0rc1+local", cmd)

    def test_command_rejects_unsafe_versions(self):
        versions = {
            "numpy": "-rmalicioso.txt",
            "pandas": "1.0; rm -rf /",
            "typing_extensions": "4.10.0",
        }
        cmd = build_command(versions=versions)
        self.assertFalse(any(arg.startswith("numpy") for arg in cmd))
        self.assertFalse(any(arg.startswith("pandas") for arg in cmd))
        self.assertIn("typing_extensions==4.10.0", cmd)
        self.assertIn("ortools", cmd)

    def test_command_rejects_empty_and_non_string_versions(self):
        cmd = build_command(
            versions={"numpy": "", "pandas": 2.0, "typing_extensions": ["4.10.0"]}
        )
        pacotes = [
            arg for arg in cmd[cmd.index("install") + 1:] if not arg.startswith("-")
        ]
        self.assertEqual(pacotes, ["ortools"])

    def test_build_command_matches_pip_prefix(self):
        cmd = build_command()
        self.assertEqual(cmd[:4], [sys.executable, "-m", "pip", "install"])

    def test_command_text_returns_formatted_string(self):
        versions = {"numpy": "1.26.4"}
        text = command_text(versions=versions, break_system_packages=True)
        self.assertIsInstance(text, str)
        self.assertIn("pip install", text)
        self.assertIn("numpy==1.26.4", text)
        self.assertIn("--break-system-packages", text)

    def test_command_text_quotes_args_with_spaces(self):
        versions = {"numpy": "1.26.4"}
        with mock.patch("sys.executable", "/path with space/python"):
            text = command_text(versions=versions)
            self.assertIn('"/path with space/python"', text)

    def test_is_installed_returns_bool(self):
        res = is_installed()
        self.assertIsInstance(res, bool)

    def test_module_has_no_subprocess_and_no_installer_api(self):
        """O módulo não roda processo externo: sem subprocess, sem install/Task."""
        self.assertFalse(hasattr(ortools_installer, "subprocess"))
        self.assertFalse(hasattr(ortools_installer, "install"))
        self.assertFalse(hasattr(ortools_installer, "ORToolsInstallTask"))


class TestHasORTools(unittest.TestCase):
    def test_clean_import_error_returns_false_without_raising(self):
        from unittest.mock import patch
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
