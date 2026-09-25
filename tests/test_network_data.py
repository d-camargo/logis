import pytest
from logis.core.ufs import UFS, codigo_uf, nome_uf, siglas

try:
    from qgis.core import QgsApplication
    _qgs = QgsApplication.instance()
    if not _qgs:
        _qgs = QgsApplication([], False)
        _qgs.initQgis()
except ImportError:
    pass


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

    def test_list_municipios_gisbr_presente_float_code(self, monkeypatch):
        import sys
        import types
        from logis.core.network.municipios import list_municipios
        from qgis.core import QgsVectorLayer, QgsFeature, QgsField
        from logis.core import qgis_compat

        layer = QgsVectorLayer("Polygon?crs=EPSG:4674", "test_muni", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("code_muni", qgis_compat.field_type("double")),
            QgsField("name_muni", qgis_compat.field_type("string")),
        ])
        layer.updateFields()

        f = QgsFeature(layer.fields())
        f.setAttribute("code_muni", 3506904.0)
        f.setAttribute("name_muni", "São Paulo")
        pr.addFeature(f)
        layer.updateExtents()

        monkeypatch.setattr("logis.core.network.municipios.has_gisbr", lambda: True)

        def mock_run(alg, params):
            assert alg == "gisbr:read_municipality"
            assert params == {"CODE": "SP", "SIMPLIFIED": True, "OUTPUT": "TEMPORARY_OUTPUT"}
            return {"OUTPUT": layer}

        fake_processing = types.ModuleType("processing")
        fake_processing.run = mock_run
        monkeypatch.setitem(sys.modules, "processing", fake_processing)

        def mock_fetch(*args, **kwargs):
            pytest.fail("downloader.fetch não deveria ser chamado quando GisBR está presente e sem erros")

        monkeypatch.setattr("logis.core.downloader.fetch", mock_fetch)

        resultado = list_municipios("SP")
        assert resultado == [("3506904", "São Paulo")]

    def test_list_municipios_gisbr_ausente_float_code(self, monkeypatch, tmp_path):
        from logis.core.network.municipios import list_municipios
        from qgis.core import QgsVectorLayer, QgsFeature, QgsField
        from logis.core import qgis_compat

        layer = QgsVectorLayer("Polygon?crs=EPSG:4674", "test_muni", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("code_muni", qgis_compat.field_type("double")),
            QgsField("name_muni", qgis_compat.field_type("string")),
        ])
        layer.updateFields()

        f = QgsFeature(layer.fields())
        f.setAttribute("code_muni", 3506904.0)
        f.setAttribute("name_muni", "São Paulo")
        pr.addFeature(f)
        layer.updateExtents()

        dummy_path = tmp_path / "35municipality_2020_simplified.gpkg"
        dummy_path.touch()

        monkeypatch.setattr("logis.core.network.municipios.has_gisbr", lambda: False)
        monkeypatch.setattr("logis.core.downloader.fetch", lambda url, feedback=None: dummy_path)
        monkeypatch.setattr("logis.core.network.municipios.QgsVectorLayer", lambda path, name, provider: layer)

        resultado = list_municipios("SP")
        assert resultado == [("3506904", "São Paulo")]

    def test_list_municipios_gisbr_falhando_fallback(self, monkeypatch, tmp_path):
        import sys
        import types
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

        f = QgsFeature(layer.fields())
        f.setAttribute("code_muni", "3506904")
        f.setAttribute("name_muni", "São Paulo")
        pr.addFeature(f)
        layer.updateExtents()

        monkeypatch.setattr("logis.core.network.municipios.has_gisbr", lambda: True)

        def mock_run_error(alg, params):
            raise RuntimeError("Erro ao executar GisBR")

        fake_processing = types.ModuleType("processing")
        fake_processing.run = mock_run_error
        monkeypatch.setitem(sys.modules, "processing", fake_processing)

        dummy_path = tmp_path / "35municipality_2020_simplified.gpkg"
        dummy_path.touch()

        monkeypatch.setattr("logis.core.downloader.fetch", lambda url, feedback=None: dummy_path)
        monkeypatch.setattr("logis.core.network.municipios.QgsVectorLayer", lambda path, name, provider: layer)

        class DummyFeedback:
            def __init__(self):
                self.info_messages = []

            def pushInfo(self, msg):
                self.info_messages.append(msg)

        fb = DummyFeedback()
        resultado = list_municipios("SP", feedback=fb)
        assert resultado == [("3506904", "São Paulo")]
        assert len(fb.info_messages) > 0
        assert "GisBR" in fb.info_messages[0]


class TestLoadOsmNetworkAlgorithm:
    def test_load_osm_network_estatico(self):
        from pathlib import Path

        algorithm_path = Path(__file__).resolve().parent.parent / "logis" / "algorithms" / "data_osm_network.py"
        assert algorithm_path.exists(), "O arquivo logis/algorithms/data_osm_network.py deve existir"

        content = algorithm_path.read_text(encoding="utf-8")

        assert "class LoadOsmNetwork" in content
        assert 'return "load_osm_network"' in content
        assert 'return "dados"' in content
        assert "downloader.cache_dir()" in content
        assert "build_osm_network" in content
        assert "FlagNoThreading" in content

        for param in ("INPUT_CODE_MUNI", "INPUT_NOME_MUNI", "FORCE", "OUTPUT_LINKS", "OUTPUT_NODES"):
            assert param in content, f"Parâmetro {param} deve estar declarado no algoritmo"

        for proibido in ("sys.executable", "subprocess", "QVariant.", "except Exception: pass", "QgsFeatureSink.FastInsert"):
            assert proibido not in content, f"Arquivo não pode conter '{proibido}'"


class TestLoadSnvNetworkAlgorithm:
    def test_load_snv_network_estatico(self):
        from pathlib import Path

        algorithm_path = Path(__file__).resolve().parent.parent / "logis" / "algorithms" / "data_snv_network.py"
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

        provider_path = Path(__file__).resolve().parent.parent / "logis" / "provider.py"
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


class TestNormalizeCodeMuni:
    def test_normalize_code_muni(self):
        from logis.core.network.municipios import normalize_code_muni

        assert normalize_code_muni(3506904) == "3506904"
        assert normalize_code_muni(3506904.0) == "3506904"
        assert normalize_code_muni("3506904.0") == "3506904"
        assert normalize_code_muni(" 3506904 ") == "3506904"
        assert normalize_code_muni(None) == ""
        assert normalize_code_muni("") == ""
        assert normalize_code_muni("abc") == "abc"


class TestHasGisbr:
    def test_has_gisbr_algoritmo_presente(self, monkeypatch):
        import logis.core.data_backend as data_backend

        class FakeRegistry:
            def algorithmById(self, alg_id):
                if alg_id in ("gisbr:read_municipality", "gisbr:osm_network"):
                    return object()
                return None

        class FakeQgsApp:
            @staticmethod
            def processingRegistry():
                return FakeRegistry()

        monkeypatch.setattr(data_backend, "QgsApplication", FakeQgsApp)

        assert data_backend.has_gisbr() is True
        assert data_backend.has_gisbr("gisbr:read_municipality") is True
        assert data_backend.has_gisbr("gisbr:osm_network") is True
        assert data_backend.has_gisbr("gisbr:non_existent") is False

    def test_has_gisbr_algoritmo_ausente(self, monkeypatch):
        import logis.core.data_backend as data_backend

        class FakeRegistry:
            def algorithmById(self, alg_id):
                return None

        class FakeQgsApp:
            @staticmethod
            def processingRegistry():
                return FakeRegistry()

        monkeypatch.setattr(data_backend, "QgsApplication", FakeQgsApp)

        assert data_backend.has_gisbr() is False
        assert data_backend.has_gisbr("gisbr:read_municipality") is False
        assert data_backend.has_gisbr("gisbr:osm_network") is False

    def test_has_gisbr_qgsapplication_none(self, monkeypatch):
        import logis.core.data_backend as data_backend

        monkeypatch.setattr(data_backend, "QgsApplication", None)

        assert data_backend.has_gisbr() is False
        assert data_backend.has_gisbr("gisbr:read_municipality") is False
        assert data_backend.has_gisbr("gisbr:osm_network") is False

    def test_has_gisbr_registry_none(self, monkeypatch):
        import logis.core.data_backend as data_backend

        class FakeQgsAppNoReg:
            processingRegistry = None

        monkeypatch.setattr(data_backend, "QgsApplication", FakeQgsAppNoReg)

        assert data_backend.has_gisbr() is False

        class FakeQgsAppRegReturnsNone:
            @staticmethod
            def processingRegistry():
                return None

        monkeypatch.setattr(data_backend, "QgsApplication", FakeQgsAppRegReturnsNone)

        assert data_backend.has_gisbr() is False


class TestMunicipioPoligono:
    def test_municipio_poligono_fallback_float_string_sem_value_error(self, monkeypatch, tmp_path):
        import sys
        import types
        from logis.core.network.osm_pipeline import _municipio_poligono
        from qgis.core import QgsVectorLayer, QgsFeature, QgsField
        from logis.core import qgis_compat

        fake_processing = types.ModuleType("processing")
        monkeypatch.setitem(sys.modules, "processing", fake_processing)

        layer = QgsVectorLayer("Polygon?crs=EPSG:4674", "test_muni", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("code_muni", qgis_compat.field_type("int")),
            QgsField("name_muni", qgis_compat.field_type("string")),
        ])
        layer.updateFields()

        f = QgsFeature(layer.fields())
        f.setAttribute("code_muni", 3506904)
        f.setAttribute("name_muni", "São Paulo")
        pr.addFeature(f)
        layer.updateExtents()

        dummy_path = tmp_path / "35municipality_2020_simplified.gpkg"
        dummy_path.touch()

        monkeypatch.setattr("logis.core.network.osm_pipeline.has_gisbr", lambda: False)
        monkeypatch.setattr("logis.core.downloader.fetch", lambda url, feedback=None: dummy_path)
        monkeypatch.setattr("logis.core.network.osm_pipeline.QgsVectorLayer", lambda path, name, provider: layer)
        monkeypatch.setattr(layer, "setSubsetString", lambda expr: True)

        resultado = _municipio_poligono("3506904.0")
        assert resultado is not None
        assert resultado == layer


class TestCustosDe:
    def test_valores_normais(self):
        from logis.core.network.osm_pipeline import _custos_de

        length, speed, travel_time = _custos_de(100.0, 50.0)
        assert length == 100.0
        assert speed == 50.0
        assert travel_time == pytest.approx(7.2)

    def test_velocidade_nula(self):
        from logis.core.network.osm_pipeline import _custos_de

        length, speed, travel_time = _custos_de(100.0, None)
        assert length == 100.0
        assert speed == 40.0
        assert travel_time == pytest.approx(9.0)

    def test_velocidade_zero(self):
        from logis.core.network.osm_pipeline import _custos_de

        length, speed, travel_time = _custos_de(100.0, 0)
        assert length == 100.0
        assert speed == 40.0
        assert travel_time == pytest.approx(9.0)

        length, speed, travel_time = _custos_de(100.0, 0.0)
        assert length == 100.0
        assert speed == 40.0
        assert travel_time == pytest.approx(9.0)

    def test_velocidade_negativa(self):
        from logis.core.network.osm_pipeline import _custos_de

        length, speed, travel_time = _custos_de(100.0, -10.0)
        assert length == 100.0
        assert speed == 40.0
        assert travel_time == pytest.approx(9.0)

    def test_comprimento_nulo_zero_negativo(self):
        from logis.core.network.osm_pipeline import _custos_de

        length, speed, travel_time = _custos_de(None, 50.0)
        assert length == 0.0
        assert speed == 50.0
        assert travel_time == 0.0

        length, speed, travel_time = _custos_de(0, 50.0)
        assert length == 0.0
        assert speed == 50.0
        assert travel_time == 0.0

        length, speed, travel_time = _custos_de(-10.0, 50.0)
        assert length == 0.0
        assert speed == 50.0
        assert travel_time == 0.0


class TestAdaptaLinksGisbr:
    def test_adapta_links_gisbr_sucesso(self):
        from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPoint, QgsLineString
        from logis.core import qgis_compat
        from logis.core.network.osm_pipeline import _adapta_links_gisbr

        layer = QgsVectorLayer("LineString?crs=EPSG:4674", "gisbr_links", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("way_id", qgis_compat.field_type("int")),
            QgsField("highway", qgis_compat.field_type("string")),
            QgsField("comprimento_m", qgis_compat.field_type("double")),
            QgsField("velocidade_kmh", qgis_compat.field_type("double")),
        ])
        layer.updateFields()

        f1 = QgsFeature(layer.fields())
        line1 = QgsLineString([QgsPoint(-46.6, -23.5), QgsPoint(-46.6, -23.51)])
        f1.setGeometry(QgsGeometry(line1))
        f1["way_id"] = 101
        f1["highway"] = "residential"
        f1["comprimento_m"] = 1100.0
        f1["velocidade_kmh"] = 50.0

        f2 = QgsFeature(layer.fields())
        line2 = QgsLineString([QgsPoint(-46.6, -23.51), QgsPoint(-46.6, -23.52)])
        f2.setGeometry(QgsGeometry(line2))
        f2["way_id"] = 102
        f2["highway"] = "service"
        f2["comprimento_m"] = 550.0
        f2["velocidade_kmh"] = 0.0

        pr.addFeatures([f1, f2])

        adapted = _adapta_links_gisbr(layer)
        assert adapted is not None
        assert adapted.isValid()
        assert adapted.featureCount() == 2

        field_names = [f.name() for f in adapted.fields()]
        assert "way_id" in field_names
        assert "highway" in field_names
        assert "comprimento_m" in field_names
        assert "velocidade_kmh" in field_names
        assert "length" in field_names
        assert "speed" in field_names
        assert "travel_time" in field_names

        feats = list(adapted.getFeatures())
        assert feats[0]["way_id"] == 101
        assert feats[0]["length"] == 1100.0
        assert feats[0]["speed"] == 50.0
        assert feats[0]["travel_time"] == pytest.approx(1100.0 / (50.0 / 3.6))

        assert feats[1]["way_id"] == 102
        assert feats[1]["length"] == 550.0
        assert feats[1]["speed"] == 40.0
        assert feats[1]["travel_time"] == pytest.approx(550.0 / (40.0 / 3.6))

    def test_adapta_links_gisbr_layer_invalido(self):
        from logis.core.network.osm_pipeline import _adapta_links_gisbr

        assert _adapta_links_gisbr(None) is None


class TestBuildOsmNetwork:
    def test_build_osm_network_gisbr_presente(self, monkeypatch, tmp_path):
        import sys
        import types
        from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsPoint, QgsLineString, QgsGeometry
        from logis.core import qgis_compat
        from logis.core.network.osm_pipeline import build_osm_network

        links_layer = QgsVectorLayer("LineString?crs=EPSG:4674", "gisbr_links", "memory")
        pr_links = links_layer.dataProvider()
        pr_links.addAttributes([
            QgsField("way_id", qgis_compat.field_type("int")),
            QgsField("highway", qgis_compat.field_type("string")),
            QgsField("comprimento_m", qgis_compat.field_type("double")),
            QgsField("velocidade_kmh", qgis_compat.field_type("double")),
        ])
        links_layer.updateFields()
        f_link = QgsFeature(links_layer.fields())
        f_link.setGeometry(QgsGeometry(QgsLineString([QgsPoint(-46.6, -23.5), QgsPoint(-46.6, -23.51)])))
        f_link["way_id"] = 1
        f_link["highway"] = "primary"
        f_link["comprimento_m"] = 1000.0
        f_link["velocidade_kmh"] = 60.0
        pr_links.addFeature(f_link)

        nodes_layer = QgsVectorLayer("Point?crs=EPSG:4674", "gisbr_nodes", "memory")
        pr_nodes = nodes_layer.dataProvider()
        pr_nodes.addAttributes([
            QgsField("node_id", qgis_compat.field_type("int")),
            QgsField("x", qgis_compat.field_type("double")),
            QgsField("y", qgis_compat.field_type("double")),
        ])
        nodes_layer.updateFields()
        f_node = QgsFeature(nodes_layer.fields())
        f_node.setGeometry(QgsGeometry(QgsPoint(-46.6, -23.5)))
        f_node["node_id"] = 1
        f_node["x"] = -46.6
        f_node["y"] = -23.5
        pr_nodes.addFeature(f_node)

        monkeypatch.setattr("logis.core.network.osm_pipeline.has_gisbr", lambda alg_id="": alg_id == "gisbr:osm_network")

        def mock_run(alg, params, context=None, feedback=None, is_child_algorithm=False):
            assert alg == "gisbr:osm_network"
            assert params["CODE"] == "3100104"
            assert params["FORCE"] is False
            return {"LINKS": links_layer, "NODES": nodes_layer, "PROBLEMAS": None}

        fake_processing = types.ModuleType("processing")
        fake_processing.run = mock_run
        monkeypatch.setitem(sys.modules, "processing", fake_processing)

        def mock_internal(*args, **kwargs):
            pytest.fail("build_osm_municipal_network não deveria ter sido chamado quando GisBR está presente")

        monkeypatch.setattr("logis.core.network.osm_pipeline.build_osm_municipal_network", mock_internal)

        gpkg_file = str(tmp_path / "osm_3100104.gpkg")
        res = build_osm_network("3100104", "Abadia dos Dourados", gpkg_file)

        assert res["metadata"]["backend"] == "gisbr"
        assert res["layers"]["osm_links"] is not None
        assert res["layers"]["osm_nodes"] == nodes_layer
        assert "length" in [f.name() for f in res["layers"]["osm_links"].fields()]

    def test_build_osm_network_gisbr_ausente(self, monkeypatch, tmp_path):
        from logis.core.network.osm_pipeline import build_osm_network

        monkeypatch.setattr("logis.core.network.osm_pipeline.has_gisbr", lambda alg_id="": False)

        def mock_internal(code_muni, nome_muni, gpkg_path, force=False, feedback=None):
            return {
                "raw_cache": None,
                "layers": {"osm_links_raw": None, "osm_links": None, "osm_nodes": None},
                "metadata": {"code_muni": str(code_muni), "nome_muni": nome_muni},
            }

        monkeypatch.setattr("logis.core.network.osm_pipeline.build_osm_municipal_network", mock_internal)

        gpkg_file = str(tmp_path / "osm_3100104.gpkg")
        res = build_osm_network("3100104", "Abadia dos Dourados", gpkg_file)

        assert res["metadata"]["backend"] == "logis"
        assert res["metadata"]["code_muni"] == "3100104"

    def test_build_osm_network_gisbr_levanta_excecao(self, monkeypatch, tmp_path):
        import sys
        import types
        from logis.core.network.osm_pipeline import build_osm_network

        monkeypatch.setattr("logis.core.network.osm_pipeline.has_gisbr", lambda alg_id="": True)

        def mock_run_error(alg, params, context=None, feedback=None, is_child_algorithm=False):
            raise RuntimeError("Falha no GisBR ao processar OSM")

        fake_processing = types.ModuleType("processing")
        fake_processing.run = mock_run_error
        monkeypatch.setitem(sys.modules, "processing", fake_processing)

        def mock_internal(*args, **kwargs):
            pytest.fail("build_osm_municipal_network não deveria ter sido chamado se GisBR levantou exceção")

        monkeypatch.setattr("logis.core.network.osm_pipeline.build_osm_municipal_network", mock_internal)

        gpkg_file = str(tmp_path / "osm_3100104.gpkg")
        with pytest.raises(RuntimeError, match="Falha no GisBR ao processar OSM"):
            build_osm_network("3100104", "Abadia dos Dourados", gpkg_file)

