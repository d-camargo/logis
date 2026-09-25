# -*- coding: utf-8 -*-
# Este teste estático proíbe uso de QgsCoordinateTransform cru em logis/algorithms/.
# Ele existe porque, nas versões 0.6.1->0.6.3, o TSP/CVRP transformavam coordenadas
# com QgsCoordinateTransform cru, e no Windows/QGIS 4 esse transform pode virar um
# no-op silencioso: as coordenadas de saida ficam identicas as de entrada, e graus
# passam a ser rotulados (e usados) como se fossem metros, corrompendo janelas e
# calculos de distancia sem lançar excecao (ver logis/core/crs_transform.py).
#
# A regra do GEMINI.md secao 2 manda ler a camada de entrada ja reprojetada dentro
# do algoritmo de Processing (source.getFeatures(QgsFeatureRequest()
# .setDestinationCrs(crs, context.transformContext())) ou native:reprojectlayer) ou,
# quando for preciso transformar pontos soltos (fora do fluxo de feicoes de uma
# camada), usar o helper conferido logis/core/crs_transform.py
# (checked_transform/transform_points/transform_bbox), que valida que o transform
# nao e um no-op e que as coordenadas resultantes sao plausiveis para o CRS alvo.
#
# LEGACY_ALLOWED é a lista de algoritmos que ainda usam QgsCoordinateTransform cru
# (débito técnico anterior a essa regra). A lista SÓ DIMINUI conforme cada algoritmo
# é migrado para o helper conferido ou para leitura já reprojetada; nenhum arquivo
# novo entra nela.

import ast
import pathlib
import re
import unittest

TRANSFORM_PATTERN = re.compile(r"\bQgsCoordinateTransform\(")

# Estado atual (conferido por grep em 2026-09-25): número de ocorrências de
# QgsCoordinateTransform( ainda toleradas, por arquivo, em logis/algorithms/.
LEGACY_ALLOWED = {}


def _algorithms_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "logis" / "algorithms"


def _count_occurrences_by_file():
    """Retorna {nome_arquivo: [(linha, texto), ...]} para cada ocorrência do padrão proibido."""
    occurrences = {}
    for py_path in sorted(_algorithms_dir().glob("*.py")):
        matches = []
        with open(py_path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                if TRANSFORM_PATTERN.search(line):
                    matches.append((line_idx, line.strip()))
        if matches:
            occurrences[py_path.name] = matches
    return occurrences


def _algorithm_classes_missing_create_instance():
    """Retorna {nome_arquivo: [nome_da_classe, ...]} para cada subclasse direta de
    QgsProcessingAlgorithm em logis/algorithms/*.py que não define createInstance().

    Sem createInstance(), QgsProcessingRegistry.createAlgorithmById() falha em runtime
    ("QgsProcessingAlgorithm.createInstance() is abstract") — o algoritmo não roda nem
    pela caixa de ferramentas nem via processing.run(), só chamando processAlgorithm()
    diretamente em Python.
    """
    missing = {}
    for py_path in sorted(_algorithms_dir().glob("*.py")):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = {
                base.id if isinstance(base, ast.Name) else getattr(base, "attr", None)
                for base in node.bases
            }
            if "QgsProcessingAlgorithm" not in base_names:
                continue
            method_names = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }
            if "createInstance" not in method_names:
                missing.setdefault(py_path.name, []).append(node.name)
    return missing


class TestAlgorithmsDefineCreateInstance(unittest.TestCase):
    """Toda subclasse de QgsProcessingAlgorithm em logis/algorithms/ precisa de createInstance()."""

    def test_all_algorithms_define_create_instance(self):
        missing = _algorithm_classes_missing_create_instance()
        if missing:
            details = "\n".join(
                f"{name}: {', '.join(classes)}" for name, classes in sorted(missing.items())
            )
            self.fail(
                "QgsProcessingAlgorithm sem createInstance() (processing.run()/"
                "createAlgorithmById() falha em runtime pela caixa de ferramentas):\n"
                + details
            )


class TestNativeRules(unittest.TestCase):
    """Verifica que QgsCoordinateTransform cru não se espalha em logis/algorithms/."""

    def test_algorithms_dir_exists(self):
        algorithms_dir = _algorithms_dir()
        self.assertTrue(
            algorithms_dir.exists(), f"Diretório {algorithms_dir} não encontrado."
        )
        py_files = list(algorithms_dir.glob("*.py"))
        self.assertTrue(
            py_files, f"Nenhum arquivo .py encontrado em {algorithms_dir}."
        )

    def test_no_new_files_use_raw_transform(self):
        occurrences = _count_occurrences_by_file()
        offenders = {
            name: matches
            for name, matches in occurrences.items()
            if name not in LEGACY_ALLOWED
        }
        if offenders:
            details = []
            for name, matches in sorted(offenders.items()):
                for line_idx, text in matches:
                    details.append(f"{name}:{line_idx}: {text}")
            self.fail(
                "QgsCoordinateTransform cru fora da lista LEGACY_ALLOWED "
                "(use leitura já reprojetada ou logis/core/crs_transform.py):\n"
                + "\n".join(details)
            )

    def test_legacy_files_do_not_exceed_allowed_count(self):
        occurrences = _count_occurrences_by_file()
        excesses = []
        for name, allowed_count in LEGACY_ALLOWED.items():
            actual_matches = occurrences.get(name, [])
            if len(actual_matches) > allowed_count:
                excesses.append(
                    f"{name}: permitido {allowed_count}, encontrado {len(actual_matches)}"
                )
        if excesses:
            self.fail(
                "Contagem de QgsCoordinateTransform cru acima do permitido em "
                "LEGACY_ALLOWED:\n" + "\n".join(excesses)
            )

    def test_legacy_allowed_tracks_migrations(self):
        occurrences = _count_occurrences_by_file()
        stale = []
        for name, allowed_count in LEGACY_ALLOWED.items():
            file_path = _algorithms_dir() / name
            actual_count = len(occurrences.get(name, []))
            if not file_path.exists() or actual_count < allowed_count:
                stale.append(
                    f"reduza LEGACY_ALLOWED para {name}: {actual_count}"
                )
        if stale:
            self.fail(
                "LEGACY_ALLOWED desatualizada (arquivo migrado ou removido); "
                "atualize a lista para acompanhar as migrações:\n"
                + "\n".join(stale)
            )


if __name__ == "__main__":
    unittest.main()
