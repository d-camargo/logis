# -*- coding: utf-8 -*-
"""Guarda estática de empacotamento para o complemento logis (D-C e D-D).

Verifica a declaração do changelog em .qgis-plugin-ci, a presença da chave
changelog= em metadata.txt, o formato das seções em docs/changelog.md, a
correspondência da versão atual no changelog e o alinhamento da homepage com
DOCS_URL da UI.
"""

import configparser
import pathlib
import re
import unittest

# Regex copiado literalmente de qgispluginci/changelog.py para validar o Keep a Changelog
CHANGELOG_REGEXP = r"(?<=##)\s*\[*(v?0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\]?(\(.*\))?(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?\]*\s-\s*([\d\-/]{10})(.*?)(?=##|\Z)"


class TestPackaging(unittest.TestCase):
    """Guarda de empacotamento e histórico de versões do logis."""

    def setUp(self):
        self.root_dir = pathlib.Path(__file__).parent
        self.ci_config_path = self.root_dir / ".qgis-plugin-ci"
        self.metadata_path = self.root_dir / "logis" / "metadata.txt"

    def test_a_changelog_path_declared_and_exists(self):
        """(a) .qgis-plugin-ci declara changelog_path e o arquivo apontado existe."""
        self.assertTrue(
            self.ci_config_path.exists(),
            f"Arquivo {self.ci_config_path} não encontrado.",
        )
        content = self.ci_config_path.read_text(encoding="utf-8")
        match = re.search(r"^\s*changelog_path:\s*([^\s#]+)", content, re.MULTILINE)
        self.assertIsNotNone(
            match, ".qgis-plugin-ci não declara a chave 'changelog_path'."
        )

        changelog_rel_path = match.group(1)
        changelog_file = self.root_dir / changelog_rel_path
        self.assertTrue(
            changelog_file.exists(),
            f"Arquivo de changelog '{changelog_rel_path}' não existe.",
        )

    def test_b_metadata_has_changelog_key(self):
        """(b) logis/metadata.txt tem uma linha que casa ^changelog=."""
        self.assertTrue(
            self.metadata_path.exists(),
            f"Arquivo {self.metadata_path} não encontrado.",
        )
        content = self.metadata_path.read_text(encoding="utf-8")
        match = re.search(r"^changelog=", content, re.MULTILINE)
        self.assertIsNotNone(
            match,
            "logis/metadata.txt não possui a linha 'changelog=' para injeção pelo empacotador.",
        )

    def test_c_changelog_sections_format_and_regex(self):
        """(c) Toda seção ## do changelog tem data e o regex do Keep a Changelog encontra entradas."""
        content = self.ci_config_path.read_text(encoding="utf-8")
        match = re.search(r"^\s*changelog_path:\s*([^\s#]+)", content, re.MULTILINE)
        self.assertIsNotNone(match)
        changelog_file = self.root_dir / match.group(1)

        changelog_content = changelog_file.read_text(encoding="utf-8")

        # Verifica se todas as seções ## seguem a formatação ## <X.Y.Z> - <AAAA-MM-DD>
        section_headers = re.findall(r"^##\s+.*", changelog_content, re.MULTILINE)
        self.assertGreater(
            len(section_headers), 0, "Nenhuma seção '##' encontrada no changelog."
        )

        header_pattern = re.compile(r"^## \d+\.\d+\.\d+ - \d{4}-\d{2}-\d{2}$")
        for header in section_headers:
            self.assertTrue(
                header_pattern.match(header),
                f"Cabeçalho de seção '{header}' não está no formato '## X.Y.Z - AAAA-MM-DD'.",
            )

        # Copiado de qgispluginci/changelog.py
        parsed_entries = re.findall(
            CHANGELOG_REGEXP, changelog_content, flags=re.MULTILINE | re.DOTALL
        )
        self.assertGreater(
            len(parsed_entries),
            0,
            "O regex do Keep a Changelog (qgispluginci) não encontrou nenhuma entrada no changelog.",
        )

    def test_d_metadata_version_in_changelog(self):
        """(d) A versão de metadata.txt tem seção correspondente no changelog."""
        config = configparser.ConfigParser()
        config.read(self.metadata_path, encoding="utf-8")
        version = config.get("general", "version")

        content = self.ci_config_path.read_text(encoding="utf-8")
        match = re.search(r"^\s*changelog_path:\s*([^\s#]+)", content, re.MULTILINE)
        self.assertIsNotNone(match)
        changelog_file = self.root_dir / match.group(1)

        changelog_content = changelog_file.read_text(encoding="utf-8")

        expected_header_re = rf"^## {re.escape(version)} - \d{{4}}-\d{{2}}-\d{{2}}$"
        found = re.search(expected_header_re, changelog_content, re.MULTILINE)
        self.assertIsNotNone(
            found,
            f"A versão '{version}' do metadata.txt não possui seção correspondente '## {version} - AAAA-MM-DD' no changelog.",
        )

    def test_e_homepage_equals_docs_url(self):
        """(e) homepage= do metadata.txt é exatamente logis.logis_plugin.DOCS_URL."""
        from logis.logis_plugin import DOCS_URL

        config = configparser.ConfigParser()
        config.read(self.metadata_path, encoding="utf-8")
        homepage = config.get("general", "homepage")

        self.assertEqual(
            homepage,
            DOCS_URL,
            f"homepage='{homepage}' no metadata.txt diverge de DOCS_URL='{DOCS_URL}'.",
        )


if __name__ == "__main__":
    unittest.main()
