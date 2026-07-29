# -*- coding: utf-8 -*-
# Este teste estático verifica a compatibilidade com Qt6 / PyQt6 / QGIS 4.x nos arquivos Python sob logis/.
# Ele existe porque a suíte de testes roda em PyQt5 / QGIS 3.x, onde as sintaxes legadas do Qt5/QGIS 3.x
# não falham em runtime, mas quebram ao executar no Qt6 (onde enums como QVariant, QgsWkbTypes.*, etc.
# foram escopados ou alterados).

import pathlib
import re
import unittest


class TestQt6Compat(unittest.TestCase):
    """Teste estático de compatibilidade Qt6/QGIS 4.x para o pacote logis."""

    PROHIBITED_PATTERNS = [
        (
            r"\bQt\.(Right|Left|Top|Bottom)DockWidgetArea\b",
            "Uso desescopado de Qt.*DockWidgetArea",
        ),
        (
            r"\bQt\.Window[A-Za-z]*Hint\b",
            "Uso desescopado de Qt.Window*Hint",
        ),
        (
            r"\bQVariant\.",
            "Uso direto de QVariant",
        ),
        (
            r"\.exec_\(",
            "Uso de .exec_() incompatível com Qt6",
        ),
        (
            r"\bQgsProcessing\.TypeVector",
            "Uso desescopado de QgsProcessing.TypeVector",
        ),
        (
            r"\bQgsProcessingParameterNumber\.(Double|Integer)\b",
            "Uso desescopado de QgsProcessingParameterNumber.*",
        ),
        (
            r"\bQgsWkbTypes\.(LineString|NoGeometry|PointGeometry)\b",
            "Uso desescopado de QgsWkbTypes.*",
        ),
        (
            r"\bQgsTask\.CanCancel\b",
            "Uso desescopado de QgsTask.CanCancel",
        ),
    ]

    def test_no_qt6_incompatibilities(self):
        root_dir = pathlib.Path(__file__).parent
        logis_dir = root_dir / "logis"
        self.assertTrue(
            logis_dir.exists(), f"Diretório {logis_dir} não encontrado."
        )

        violations = []

        for py_path in sorted(logis_dir.rglob("*.py")):
            parts = [p.lower() for p in py_path.parts]
            if (
                "pycache" in str(py_path).lower()
                or "__pycache__" in parts
                or "i18n" in parts
            ):
                continue

            rel_path = py_path.relative_to(root_dir)
            is_qgis_compat = str(rel_path).replace("\\", "/").endswith(
                "core/qgis_compat.py"
            )

            with open(py_path, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, start=1):
                    for pattern, desc in self.PROHIBITED_PATTERNS:
                        if (
                            pattern == r"\bQVariant\."
                            and is_qgis_compat
                        ):
                            continue
                        if re.search(pattern, line):
                            violations.append(
                                f"{rel_path}:{line_idx}: {desc} -> {line.strip()}"
                            )

        if violations:
            msg = (
                f"Encontradas {len(violations)} incompatibilidades Qt6/QGIS 4.x:\n"
                + "\n".join(violations)
            )
            self.fail(msg)


if __name__ == "__main__":
    unittest.main()
