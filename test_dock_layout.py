# -*- coding: utf-8 -*-
# Este teste estático verifica se os painéis (docks) de UI possuem suporte a rolagem (QScrollArea).
# Ele lê o conteúdo fonte dos arquivos de dock sem importar QGIS/PyQt.

import pathlib
import re
import unittest


class TestDockLayout(unittest.TestCase):
    """Teste estático de layout dos painéis (docks) do plugin logis."""

    DOCK_FILES = [
        "logis/gui/urban_dock.py",
        "logis/gui/regional_dock.py",
        "logis/gui/waste_dock.py",
    ]

    REQUIRED_PATTERNS = [
        (r"QScrollArea\(", "Instanciação de QScrollArea"),
        (r"setWidgetResizable\(True\)", "Habilitação de widget resizável no scroll"),
        (r"self\.setWidget\(scroll\)", "Definição de scroll como widget principal do dock"),
    ]

    def test_docks_have_scroll_area(self):
        root_dir = pathlib.Path(__file__).parent

        for rel_file in self.DOCK_FILES:
            file_path = root_dir / rel_file
            self.assertTrue(
                file_path.exists(), f"Arquivo {file_path} não encontrado."
            )

            content = file_path.read_text(encoding="utf-8")

            for pattern, desc in self.REQUIRED_PATTERNS:
                self.assertTrue(
                    re.search(pattern, content),
                    f"Padrão ausente em {rel_file}: {desc} ({pattern})"
                )

    def test_waste_dock_has_four_tabs(self):
        content = (pathlib.Path(__file__).parent / "logis/gui/waste_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("QTabWidget(", content)
        self.assertIn("def _new_tab", content)

        new_tab_calls = len(re.findall(r"self\._new_tab\(", content))
        self.assertEqual(
            new_tab_calls, 4,
            f"Esperado exatamente 4 chamadas de _new_tab, encontrado {new_tab_calls}."
        )

    def test_waste_dock_results_panel_outside_tabs(self):
        content = (pathlib.Path(__file__).parent / "logis/gui/waste_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertTrue(
            re.search(r"outer\.addWidget\(self\.txt_results\)", content),
            "self.txt_results deve ser adicionado ao layout externo (outer), "
            "fora de qualquer aba (painel de resultados compartilhado)."
        )

    def test_urban_dock_has_three_tabs(self):
        content = (pathlib.Path(__file__).parent / "logis/gui/urban_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("QTabWidget(", content)
        self.assertIn("def _new_tab", content)

        new_tab_calls = len(re.findall(r"self\._new_tab\(", content))
        self.assertEqual(
            new_tab_calls, 3,
            f"Esperado exatamente 3 chamadas de _new_tab, encontrado {new_tab_calls}."
        )

    def test_urban_dock_results_panel_outside_tabs(self):
        content = (pathlib.Path(__file__).parent / "logis/gui/urban_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertTrue(
            re.search(r"outer\.addWidget\(self\.txt_results\)", content),
            "self.txt_results deve ser adicionado ao layout externo (outer), "
            "fora de qualquer aba (painel de resultados compartilhado)."
        )

    def test_urban_dock_tabs_end_with_stretch(self):
        content = (pathlib.Path(__file__).parent / "logis/gui/urban_dock.py").read_text(
            encoding="utf-8"
        )

        add_stretch_calls = len(re.findall(r"layout\.addStretch\(", content))
        self.assertEqual(
            add_stretch_calls, 3,
            f"Esperado exatamente 3 chamadas de layout.addStretch() no painel Urbano (1 por aba), encontrado {add_stretch_calls}."
        )


if __name__ == "__main__":
    unittest.main()
