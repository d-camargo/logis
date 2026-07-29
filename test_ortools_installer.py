# -*- coding: utf-8 -*-
"""Testes de core/ortools_installer.py.

Guarda o comando de instalação: sem as três travas da seção 2.1 do CLAUDE.md
o pip sobrepõe o numpy do QGIS e quebra a instalação inteira do usuário.
"""

import unittest

from logis.core.ortools_installer import ORToolsInstallTask


class TestInstallCommand(unittest.TestCase):
    def setUp(self):
        self.task = ORToolsInstallTask()

    def test_command_has_the_three_pins(self):
        cmd = self.task.build_command()
        for pin in ("pandas<3", "numpy<2", "typing_extensions==4.10.0"):
            self.assertIn(pin, cmd)
        self.assertIn("ortools", cmd)
        self.assertIn("--user", cmd)

    def test_command_is_never_plain_pip_install_ortools(self):
        cmd = self.task.build_command()
        pacotes = [arg for arg in cmd[cmd.index("install") + 1:]
                   if not arg.startswith("-")]
        self.assertNotEqual(pacotes, ["ortools"])

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


if __name__ == "__main__":
    unittest.main()
