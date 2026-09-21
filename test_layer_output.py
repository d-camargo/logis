"""Testes unitários para logis.core.layer_output (sem dependência de QGIS)."""

import ast
import unittest
import logis.core.layer_output as layer_output


class TestLayerOutput(unittest.TestCase):
    def test_slugify(self):
        """Testa conversão de nomes para slugs em minúsculas e hífens."""
        self.assertEqual(layer_output.slugify("São Paulo"), "sao-paulo")
        self.assertEqual(layer_output.slugify("osm_links_3550308"), "osm-links-3550308")
        self.assertEqual(layer_output.slugify(""), "rede")
        self.assertEqual(layer_output.slugify(None), "rede")
        self.assertEqual(layer_output.slugify("   "), "rede")
        self.assertEqual(layer_output.slugify("___"), "rede")

    def test_output_names_d_l(self):
        """Testa os quatro pares de nomes padronizados da D-L (TSP/CVRP e rede/euclidiana)."""
        # 1. TSP em rede
        self.assertEqual(
            layer_output.output_names("TSP", "rede", "São Paulo"),
            ("TSP-rede_sao-paulo", "TSP-rede_sao-paulo_pontos")
        )
        # 2. TSP euclidiano
        self.assertEqual(
            layer_output.output_names("TSP", "euclidiana", "São Paulo"),
            ("TSP-euclidiana_sao-paulo", "TSP-euclidiana_sao-paulo_pontos")
        )
        # 3. CVRP em rede
        self.assertEqual(
            layer_output.output_names("CVRP", "rede", "São Paulo"),
            ("CVRP-rede_sao-paulo", "CVRP-rede_sao-paulo_pontos")
        )
        # 4. CVRP euclidiano
        self.assertEqual(
            layer_output.output_names("CVRP", "euclidiana", "São Paulo"),
            ("CVRP-euclidiana_sao-paulo", "CVRP-euclidiana_sao-paulo_pontos")
        )

    def test_gpkg_path_from_source(self):
        """Testa extração de caminho GeoPackage a partir do atributo source de camadas."""
        # com .gpkg em Linux/macOS
        self.assertEqual(
            layer_output.gpkg_path_from_source("/dados/rede.gpkg|layername=osm_links"),
            "/dados/rede.gpkg"
        )
        # com .gpkg em caixa alta
        self.assertEqual(
            layer_output.gpkg_path_from_source("/dados/rede.GPKG|layername=osm_links"),
            "/dados/rede.GPKG"
        )
        # com .shp (não é gpkg)
        self.assertIsNone(
            layer_output.gpkg_path_from_source("/dados/rede.shp|layername=osm_links")
        )
        # com caminho do Windows
        self.assertEqual(
            layer_output.gpkg_path_from_source(r"C:\dados\rede.gpkg|layername=osm_links"),
            r"C:\dados\rede.gpkg"
        )
        # com origem de camada de memória
        self.assertIsNone(
            layer_output.gpkg_path_from_source("memory:?geometry=Point&crs=EPSG:4326")
        )
        # com None e string vazia
        self.assertIsNone(layer_output.gpkg_path_from_source(None))
        self.assertIsNone(layer_output.gpkg_path_from_source(""))

    def test_no_qgis_import_at_top_level(self):
        """Garante que o módulo logis.core.layer_output não importa qgis no topo."""
        filepath = layer_output.__file__
        with open(filepath, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code, filename=filepath)
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertFalse(
                        alias.name.startswith("qgis"),
                        f"Importação no topo encontrada para '{alias.name}'"
                    )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                self.assertFalse(
                    module_name.startswith("qgis"),
                    f"Importação no topo encontrada de '{module_name}'"
                )


if __name__ == "__main__":
    unittest.main()
