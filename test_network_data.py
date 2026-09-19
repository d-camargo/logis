"""Testes para o módulo logis.core.ufs."""

import pytest
from logis.core.ufs import UFS, codigo_uf, nome_uf, siglas


class TestUfs:
    def test_27_entradas(self):
        assert len(UFS) == 27
        assert len(siglas()) == 27

    def test_siglas_unicas_e_em_ordem_alfabetica(self):
        lista_siglas = siglas()
        assert len(set(lista_siglas)) == 27
        assert lista_siglas == sorted(lista_siglas)

    def test_codigos_de_2_digitos_e_unicos(self):
        codigos = [item[1] for item in UFS]
        assert len(set(codigos)) == 27
        for codigo in codigos:
            assert len(codigo) == 2
            assert codigo.isdigit()

    def test_codigo_uf(self):
        assert codigo_uf("mg") == "31"
        assert codigo_uf("SP") == "35"

    def test_nome_uf(self):
        assert nome_uf("TO") == "Tocantins"

    def test_uf_invalida(self):
        with pytest.raises(ValueError, match="UF inválida: XX"):
            codigo_uf("XX")
        with pytest.raises(ValueError, match="UF inválida: XX"):
            nome_uf("XX")


class TestListMunicipios:
    def test_import_e_uf_invalida_sem_rede(self, monkeypatch):
        from logis.core.network.municipios import list_municipios

        def mock_fetch(*args, **kwargs):
            pytest.fail("downloader.fetch não deveria ter sido chamado para UF inválida")

        monkeypatch.setattr("logis.core.downloader.fetch", mock_fetch)

        with pytest.raises(ValueError, match="UF inválida: XX"):
            list_municipios("XX")

    def test_fonte_regras_seguranca_e_conectores(self):
        from pathlib import Path
        import logis.core.network.municipios as mod_muni

        source = Path(mod_muni.__file__).read_text(encoding="utf-8")

        assert "downloader.fetch" in source
        assert "codigo_uf" in source
        assert "https://www.ipea.gov.br/geobr/data_gpkg/municipality/2020/" in source

        for proibido in ("requests", "urllib", "subprocess", "QVariant."):
            assert proibido not in source, f"Arquivo não pode conter {proibido}"

    def test_list_municipios_sucesso_mock(self, monkeypatch, tmp_path):
        from logis.core.network.municipios import list_municipios
        from qgis.core import QgsVectorLayer, QgsFeature, QgsField
        from logis.core import qgis_compat

        layer = QgsVectorLayer("Polygon?crs=EPSG:4674", "test_muni", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("code_muni", qgis_compat.field_type("string")),
            QgsField("name_muni", qgis_compat.field_type("string")),
        ])
        layer.updateFields()

        f1 = QgsFeature(layer.fields())
        f1.setAttribute("code_muni", "3100104")
        f1.setAttribute("name_muni", "Abadia dos Dourados")
        f2 = QgsFeature(layer.fields())
        f2.setAttribute("code_muni", "3100203")
        f2.setAttribute("name_muni", "Abaeté")

        pr.addFeatures([f2, f1])
        layer.updateExtents()

        dummy_path = tmp_path / "31municipality_2020_simplified.gpkg"
        dummy_path.touch()

        monkeypatch.setattr("logis.core.downloader.fetch", lambda url, feedback=None: dummy_path)
        monkeypatch.setattr("logis.core.network.municipios.QgsVectorLayer", lambda path, name, provider: layer)

        resultado = list_municipios("MG")
        assert len(resultado) == 2
        assert resultado[0] == ("3100104", "Abadia dos Dourados")
        assert resultado[1] == ("3100203", "Abaeté")

    def test_list_municipios_erro_reergue_runtime_error(self, monkeypatch, tmp_path):
        from logis.core.network.municipios import list_municipios

        dummy_path = tmp_path / "invalid.gpkg"
        monkeypatch.setattr("logis.core.downloader.fetch", lambda url, feedback=None: dummy_path)

        with pytest.raises(RuntimeError, match="Falha ao listar municípios de MG"):
            list_municipios("MG")


class TestLoadOsmNetworkAlgorithm:
    def test_load_osm_network_estatico(self):
        from pathlib import Path

        algorithm_path = Path(__file__).parent / "logis" / "algorithms" / "data_osm_network.py"
        assert algorithm_path.exists(), "O arquivo logis/algorithms/data_osm_network.py deve existir"

        content = algorithm_path.read_text(encoding="utf-8")

        assert "class LoadOsmNetwork" in content
        assert 'return "load_osm_network"' in content
        assert 'return "dados"' in content
        assert "downloader.cache_dir()" in content
        assert "build_osm_municipal_network" in content

        for param in ("INPUT_CODE_MUNI", "INPUT_NOME_MUNI", "FORCE", "OUTPUT_LINKS", "OUTPUT_NODES"):
            assert param in content, f"Parâmetro {param} deve estar declarado no algoritmo"

        for proibido in ("sys.executable", "subprocess", "QVariant.", "except Exception: pass", "QgsFeatureSink.FastInsert"):
            assert proibido not in content, f"Arquivo não pode conter '{proibido}'"


class TestLoadSnvNetworkAlgorithm:
    def test_load_snv_network_estatico(self):
        from pathlib import Path

        algorithm_path = Path(__file__).parent / "logis" / "algorithms" / "data_snv_network.py"
        assert algorithm_path.exists(), "O arquivo logis/algorithms/data_snv_network.py deve existir"

        content = algorithm_path.read_text(encoding="utf-8")

        assert "class LoadSnvNetwork" in content
        assert 'return "load_snv_network"' in content
        assert 'return "dados"' in content
        assert "downloader.cache_dir()" in content
        assert "build_snv_state_network" in content
        assert "siglas()" in content

        for param in ("INPUT_UF", "FORCE", "OUTPUT_LINKS", "OUTPUT_NODES"):
            assert param in content, f"Parâmetro {param} deve estar declarado no algoritmo"

        for proibido in ("sys.executable", "subprocess", "QVariant.", "except Exception: pass", "QgsFeatureSink.FastInsert"):
            assert proibido not in content, f"Arquivo não pode conter '{proibido}'"


class TestProviderRegistration:
    def test_data_algorithms_imported_and_registered(self):
        from pathlib import Path

        provider_path = Path(__file__).parent / "logis" / "provider.py"
        assert provider_path.exists(), "O arquivo logis/provider.py deve existir"

        content = provider_path.read_text(encoding="utf-8")

        assert "from .algorithms.data_osm_network import LoadOsmNetwork" in content
        assert "from .algorithms.data_snv_network import LoadSnvNetwork" in content
        assert "self.addAlgorithm(LoadOsmNetwork())" in content
        assert "self.addAlgorithm(LoadSnvNetwork())" in content

        idx_osm = content.index("self.addAlgorithm(LoadOsmNetwork())")
        idx_snv = content.index("self.addAlgorithm(LoadSnvNetwork())")
        idx_urban = content.index("self.addAlgorithm(UrbanNetworkDensity())")
        assert idx_osm < idx_snv < idx_urban




