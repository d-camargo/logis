# -*- coding: utf-8 -*-
# Este teste estático verifica a ausência de vulnerabilidades e maus padrões de segurança
# nos arquivos Python sob logis/ (guarda estática contra regressão).
# Não importa QGIS e não depende de ferramentas externas como bandit.

import pathlib
import re
import unittest


class TestSecurityScan(unittest.TestCase):
    """Guarda estática de segurança para o pacote logis."""

    def _get_logis_py_files(self):
        root_dir = pathlib.Path(__file__).parent
        logis_dir = root_dir / "logis"
        self.assertTrue(
            logis_dir.exists(), f"Diretório {logis_dir} não encontrado."
        )

        py_files = []
        for py_path in sorted(logis_dir.rglob("*.py")):
            parts = [p.lower() for p in py_path.parts]
            if (
                "pycache" in str(py_path).lower()
                or "__pycache__" in parts
                or "i18n" in parts
            ):
                continue
            py_files.append((py_path, py_path.relative_to(root_dir)))

        return root_dir, logis_dir, py_files

    def test_no_pickle(self):
        """(a) Nenhum arquivo sob logis/ contém import pickle ou pickle.load/pickle.dump."""
        root_dir, _, py_files = self._get_logis_py_files()
        pickle_patterns = [
            (r"\bimport\s+pickle\b", "Uso de 'import pickle'"),
            (r"\bpickle\.(load|dump)\b", "Uso de 'pickle.load' ou 'pickle.dump'"),
        ]
        violations = []

        for py_path, rel_path in py_files:
            with open(py_path, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, start=1):
                    for pattern, desc in pickle_patterns:
                        if re.search(pattern, line):
                            violations.append(
                                f"{rel_path}:{line_idx}: {desc} -> {line.strip()}"
                            )

        if violations:
            msg = (
                f"Encontradas {len(violations)} ocorrências de pickle em logis/:\n"
                + "\n".join(violations)
            )
            self.fail(msg)

    def test_no_except_exception_pass(self):
        """(b) Nenhum arquivo sob logis/ tem except Exception: ou except: seguido de pass."""
        root_dir, _, py_files = self._get_logis_py_files()
        broad_except_re = re.compile(
            r"^\s*except(?:\s+Exception(?:\s+as\s+\w+)?|\s*):"
        )
        violations = []

        for py_path, rel_path in py_files:
            with open(py_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_idx, line in enumerate(lines, start=1):
                if broad_except_re.search(line):
                    after_colon = line.split(":", 1)[1].strip()
                    if after_colon == "pass" or after_colon.startswith("pass ") or after_colon.startswith("pass#"):
                        violations.append(
                            f"{rel_path}:{line_idx}: 'except Exception: pass' na mesma linha -> {line.strip()}"
                        )
                    else:
                        for j in range(line_idx, len(lines)):
                            next_line = lines[j].strip()
                            if not next_line or next_line.startswith("#"):
                                continue
                            if next_line == "pass" or next_line.startswith("pass ") or next_line.startswith("pass#"):
                                violations.append(
                                    f"{rel_path}:{line_idx}: 'except Exception:' seguido de 'pass' (linha {j+1}) -> {line.strip()}"
                                )
                            break

        if violations:
            msg = (
                f"Encontrados {len(violations)} blocos de 'except Exception: pass' em logis/:\n"
                + "\n".join(violations)
            )
            self.fail(msg)

    def test_exec_has_nosec(self):
        """(c) A linha do .exec() em logis/logis_plugin.py carrega o marcador # nosec B102."""
        root_dir, logis_dir, _ = self._get_logis_py_files()
        target_plugin = logis_dir / "logis_plugin.py"
        self.assertTrue(
            target_plugin.exists(), f"Arquivo {target_plugin} não encontrado."
        )

        rel_path = target_plugin.relative_to(root_dir)
        violations = []

        with open(target_plugin, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if ".exec()" in line:
                    if "# nosec B102" not in line:
                        violations.append(
                            f"{rel_path}:{line_idx}: Chamada .exec() sem '# nosec B102' -> {line.strip()}"
                        )

        if violations:
            msg = (
                f"Encontradas {len(violations)} chamadas de .exec() sem marcador '# nosec B102':\n"
                + "\n".join(violations)
            )
            self.fail(msg)

    def test_no_peer_verify_none(self):
        """(d) Nenhum arquivo sob logis/ contém PeerVerifyMode acompanhado de VerifyNone."""
        root_dir, _, py_files = self._get_logis_py_files()
        violations = []

        for py_path, rel_path in py_files:
            with open(py_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "PeerVerifyMode" in content and "VerifyNone" in content:
                lines = content.splitlines()
                for line_idx, line in enumerate(lines, start=1):
                    if "PeerVerifyMode" in line or "VerifyNone" in line:
                        violations.append(
                            f"{rel_path}:{line_idx}: Uso de PeerVerifyMode + VerifyNone -> {line.strip()}"
                        )

        if violations:
            msg = (
                f"Encontradas {len(violations)} ocorrências de PeerVerifyMode + VerifyNone em logis/:\n"
                + "\n".join(violations)
            )
            self.fail(msg)


if __name__ == "__main__":
    unittest.main()
