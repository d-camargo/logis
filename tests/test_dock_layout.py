# -*- coding: utf-8 -*-
# Este teste estático verifica se os painéis (docks) de UI possuem suporte a rolagem (QScrollArea).
# Ele lê o conteúdo fonte dos arquivos de dock sem importar QGIS/PyQt.

import pathlib
import re
import unittest


class TestDockLayout(unittest.TestCase):
    """Teste estático de layout dos painéis (docks) do plugin logis."""

    DOCK_FILES = [
        "logis/gui/network_dock.py",
        "logis/gui/urban_dock.py",
        "logis/gui/regional_dock.py",
        "logis/gui/waste_dock.py",
        "logis/gui/routing_dock.py",
    ]

    REQUIRED_PATTERNS = [
        (r"QScrollArea\(", "Instanciação de QScrollArea"),
        (r"setWidgetResizable\(True\)", "Habilitação de widget resizável no scroll"),
        (r"self\.setWidget\(scroll\)", "Definição de scroll como widget principal do dock"),
    ]

    def test_docks_have_scroll_area(self):
        root_dir = pathlib.Path(__file__).resolve().parent.parent

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
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/waste_dock.py").read_text(
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
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/waste_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertTrue(
            re.search(r"outer\.addWidget\(self\.txt_results\)", content),
            "self.txt_results deve ser adicionado ao layout externo (outer), "
            "fora de qualquer aba (painel de resultados compartilhado)."
        )

    def test_urban_dock_has_three_tabs(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/urban_dock.py").read_text(
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
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/urban_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertTrue(
            re.search(r"outer\.addWidget\(self\.txt_results\)", content),
            "self.txt_results deve ser adicionado ao layout externo (outer), "
            "fora de qualquer aba (painel de resultados compartilhado)."
        )

    def test_urban_dock_tabs_end_with_stretch(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/urban_dock.py").read_text(
            encoding="utf-8"
        )

        add_stretch_calls = len(re.findall(r"layout\.addStretch\(", content))
        self.assertEqual(
            add_stretch_calls, 3,
            f"Esperado exatamente 3 chamadas de layout.addStretch() no painel Urbano (1 por aba), encontrado {add_stretch_calls}."
        )

    def test_routing_dock_has_two_tabs(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("QTabWidget(", content)
        self.assertIn("def _new_tab", content)

        new_tab_calls = len(re.findall(r"self\._new_tab\(", content))
        self.assertEqual(
            new_tab_calls, 2,
            f"Esperado exatamente 2 chamadas de _new_tab, encontrado {new_tab_calls}."
        )

    def test_routing_dock_results_panel_outside_tabs(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertTrue(
            re.search(r"outer\.addWidget\(self\.txt_results\)", content),
            "self.txt_results deve ser adicionado ao layout externo (outer), "
            "fora de qualquer aba (painel de resultados compartilhado)."
        )
        self.assertTrue(
            re.search(r"outer\.addWidget\(self\.prg_run\)", content),
            "self.prg_run deve ser adicionado ao layout externo (outer), "
            "fora de qualquer aba (barra de progresso compartilhada)."
        )
        self.assertTrue(
            re.search(r"outer\.addWidget\(self\.btn_cancel\)", content),
            "self.btn_cancel deve ser adicionado ao layout externo (outer), "
            "fora de qualquer aba (botão cancelar compartilhado)."
        )

    def test_routing_dock_controls(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("self.cmb_start", content)
        self.assertIn("self.cmb_points", content)
        self.assertIn("self.cmb_end", content)
        self.assertIn("self.cmb_tsp_mode", content)
        self.assertIn("self.cmb_tsp_backend", content)
        self.assertIn("self.btn_run_tsp", content)
        self.assertIn("self.cmb_depot", content)
        self.assertIn("self.cmb_demand", content)
        self.assertIn("self.cmb_demand_field", content)
        self.assertIn("self.spin_capacity", content)
        self.assertIn("self.cmb_cvrp_backend", content)
        self.assertIn("self.chk_cvrp_improve", content)
        self.assertIn("self.btn_run_cvrp", content)
        self.assertIn("self.prg_run", content)
        self.assertIn("self.btn_cancel", content)
        self.assertIn("def _start_progress(", content)
        self.assertIn("def _update_progress(", content)
        self.assertIn("def _finish_progress(", content)
        self.assertIn("logis:vrp_tsp", content)
        self.assertIn("logis:vrp_cvrp", content)
        self.assertIn("'BACKEND': self.cmb_tsp_backend.currentIndex()", content)
        self.assertIn("'BACKEND': self.cmb_cvrp_backend.currentIndex()", content)

    def test_routing_dock_tsp_distance_mode(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            content.count("self.cmb_tsp_mode = QComboBox()"), 1,
            "Esperado exatamente 1 combo de modo do TSP (cmb_tsp_mode) no painel de roteirização."
        )
        self.assertIn("Linha reta (euclidiana)", content)
        self.assertIn("Pela rede viária (Dijkstra)", content)
        self.assertIn("self.cmb_tsp_mode.currentIndex() == 1", content)
        self.assertIn("network_layer if use_network else None", content)

    def test_routing_dock_tsp_backend(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            content.count("self.cmb_tsp_backend = QComboBox()"), 1,
            "Esperado exatamente 1 combo de backend do TSP (cmb_tsp_backend) no painel de roteirização."
        )
        self.assertIn("Automático (OR-Tools quando disponível)", content)
        self.assertIn("Python puro (heurística)", content)
        self.assertIn("OR-Tools", content)
        self.assertIn("'BACKEND': self.cmb_tsp_backend.currentIndex()", content)

    def test_routing_dock_cvrp_backend(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            content.count("self.cmb_cvrp_backend = QComboBox()"), 1,
            "Esperado exatamente 1 combo de backend do CVRP (cmb_cvrp_backend) no painel de roteirização."
        )
        self.assertIn("Automático (OR-Tools quando disponível)", content)
        self.assertIn("Python puro (heurística)", content)
        self.assertIn("OR-Tools", content)
        self.assertIn("'BACKEND': self.cmb_cvrp_backend.currentIndex()", content)

        run_cvrp_code = content.split("def run_cvrp(self):")[1]
        self.assertIn('optim_backend.guard_state() == "blocked"', run_cvrp_code)
        self.assertIn("Aviso: O OR-Tools está desativado por ter derrubado a sessão anterior.", run_cvrp_code)

    def test_routing_dock_network_selector_is_unique(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            content.count("self.cmb_network = QgsMapLayerComboBox()"), 1,
            "Esperado exatamente 1 seletor de rede viária (cmb_network) no painel de roteirização."
        )

    def test_routing_dock_local_search_description(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )
        desc_text = "Refina a rota inicial invertendo trechos (2-opt) e reposicionando paradas (Or-opt). Reduz a distância total e aumenta o tempo de cálculo."

        self.assertEqual(
            content.count(desc_text), 2,
            "Esperado que a descrição de busca local apareça exatamente 2 vezes no fonte."
        )

        pos_chk_improve = content.find("self.chk_improve = QCheckBox")
        pos_chk_cvrp_improve = content.find("self.chk_cvrp_improve = QCheckBox")

        self.assertGreater(pos_chk_improve, -1)
        self.assertGreater(pos_chk_cvrp_improve, -1)

        first_desc_pos = content.find(desc_text)
        second_desc_pos = content.find(desc_text, first_desc_pos + 1)

        self.assertGreater(
            first_desc_pos, pos_chk_improve,
            "Primeira ocorrência da descrição deve estar após self.chk_improve."
        )
        self.assertLess(
            first_desc_pos, pos_chk_cvrp_improve,
            "Primeira ocorrência da descrição deve estar antes de self.chk_cvrp_improve."
        )
        self.assertGreater(
            second_desc_pos, pos_chk_cvrp_improve,
            "Segunda ocorrência da descrição deve estar após self.chk_cvrp_improve."
        )

    def test_network_dock_has_two_tabs(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/network_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("QTabWidget(", content)
        self.assertIn("def _new_tab", content)

        new_tab_calls = len(re.findall(r"self\._new_tab\(", content))
        self.assertEqual(
            new_tab_calls, 2,
            f"Esperado exatamente 2 chamadas de _new_tab, encontrado {new_tab_calls}."
        )

    def test_network_dock_results_panel_outside_tabs(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/network_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertTrue(
            re.search(r"outer\.addWidget\(self\.txt_results\)", content),
            "self.txt_results deve ser adicionado ao layout externo (outer), "
            "fora de qualquer aba (painel de resultados compartilhado)."
        )

    def test_network_dock_controls(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/network_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("self.cmb_uf_muni", content)
        self.assertIn("self.btn_list_munis", content)
        self.assertIn("self.cmb_muni", content)
        self.assertIn("self.txt_code_muni", content)
        self.assertIn("self.chk_force_osm", content)
        self.assertIn("self.btn_download_osm", content)
        self.assertIn("self.cmb_uf_snv", content)
        self.assertIn("self.chk_force_snv", content)
        self.assertIn("self.btn_download_snv", content)
        self.assertIn("logis:load_osm_network", content)
        self.assertIn("logis:load_snv_network", content)
        self.assertIn("Qt.CursorShape.WaitCursor", content)
        self.assertIn("restoreOverrideCursor", content)
        self.assertIn("self.lbl_osm_source", content)
        self.assertIn('has_gisbr("gisbr:osm_network")', content)
        self.assertIn("municipios.normalize_code_muni(data)", content)
        self.assertIn("municipios.normalize_code_muni(self.txt_code_muni.text().strip())", content)
        self.assertIn("municipios.normalize_code_muni(selected) == code_muni", content)
        self.assertIn("carregada via", content)
        self.assertIn("class _DockFeedback", content)
        self.assertIn("self.progress_bar", content)
        self.assertIn("setRange(0, 0)", content)
        dock_fb_code = content.split("class _DockFeedback")[1].split("class NetworkDock")[0]
        self.assertIn("processEvents()", dock_fb_code)
        self.assertNotIn("_CollectingFeedback", content)
        self.assertNotIn("fb.logs", content)
        self.assertNotIn("QgsTask", content)
        self.assertNotIn("subprocess", content)

    def test_routing_dock_tsp_background_task(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("def _on_tsp_finished(self, ok, results):", content)
        self.assertIn("AlgTaskRunner(", content)
        self.assertIn("self._tsp_runner =", content)

        # Verificar que run_tsp usa AlgTaskRunner e não chama processing.run diretamente
        self.assertIn("def run_tsp(self):", content)
        run_tsp_code = content.split("def run_tsp(self):")[1].split("def _on_tsp_finished")[0]
        self.assertNotIn("processing.run(", run_tsp_code)

        # Verificar conexão de cancelamento
        self.assertIn("self.btn_cancel.clicked.connect(self._tsp_runner.cancel)", content)

        # Verificar uso de last_error no callback
        on_tsp_finished_code = content.split("def _on_tsp_finished(self, ok, results):")[1].split("def ")[0]
        self.assertIn("last_error", on_tsp_finished_code)

    def test_routing_dock_cvrp_background_task(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("def _on_cvrp_finished(self, ok, results):", content)
        self.assertIn("AlgTaskRunner(", content)
        self.assertIn("self._cvrp_runner =", content)

        # Verificar que run_cvrp usa AlgTaskRunner e não chama processing.run diretamente
        self.assertIn("def run_cvrp(self):", content)
        run_cvrp_code = content.split("def run_cvrp(self):")[1].split("def _on_cvrp_finished")[0]
        self.assertNotIn("processing.run(", run_cvrp_code)

        # Verificar conexão de cancelamento
        self.assertIn("self.btn_cancel.clicked.connect(self._cvrp_runner.cancel)", content)

        # Verificar uso de last_error no callback
        on_cvrp_finished_code = content.split("def _on_cvrp_finished(self, ok, results):")[1].split("def ")[0]
        self.assertIn("last_error", on_cvrp_finished_code)

    def test_routing_dock_start_error_handling(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        run_tsp_code = content.split("def run_tsp(self):")[1].split("def _on_tsp_finished")[0]
        self.assertIn("self._tsp_runner.start()", run_tsp_code)
        self.assertIn("except Exception as e:", run_tsp_code)
        self.assertIn("self._finish_progress()", run_tsp_code)
        start_tsp_idx = run_tsp_code.find("self._tsp_runner.start()")
        except_tsp_idx = run_tsp_code.find("except Exception as e:")
        finish_tsp_idx = run_tsp_code.find("self._finish_progress()", except_tsp_idx)
        self.assertTrue(
            start_tsp_idx < except_tsp_idx < finish_tsp_idx,
            "Em run_tsp, start() deve estar dentro de try e _finish_progress() no except correspondente"
        )

        run_cvrp_code = content.split("def run_cvrp(self):")[1].split("def _on_cvrp_finished")[0]
        self.assertIn("self._cvrp_runner.start()", run_cvrp_code)
        self.assertIn("except Exception as e:", run_cvrp_code)
        self.assertIn("self._finish_progress()", run_cvrp_code)
        start_cvrp_idx = run_cvrp_code.find("self._cvrp_runner.start()")
        except_cvrp_idx = run_cvrp_code.find("except Exception as e:")
        finish_cvrp_idx = run_cvrp_code.find("self._finish_progress()", except_cvrp_idx)
        self.assertTrue(
            start_cvrp_idx < except_cvrp_idx < finish_cvrp_idx,
            "Em run_cvrp, start() deve estar dentro de try e _finish_progress() no except correspondente"
        )

    def test_routing_dock_persist_outputs(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("def _persist_outputs(", content)
        self.assertIn("output_names(", content)
        self.assertIn("gpkg_path_from_source(", content)
        self.assertIn("write_layer_to_gpkg(", content)
        self.assertIn(".setName(", content)
        self.assertIn("camada temporária", content)
        self.assertIn("self._persist_outputs(\"TSP\",", content)
        self.assertIn("self._persist_outputs(\"CVRP\",", content)

        # Garantir que nenhum 'memory:' do dock virou caminho de arquivo cru em parâmetro de sink (D-J)
        self.assertIn("'OUTPUT_ORDER': 'memory:'", content)
        self.assertIn("'OUTPUT_ROUTE': 'memory:'", content)
        self.assertIn("'OUTPUT_ROUTES': 'memory:'", content)
        self.assertIn("'OUTPUT_STOPS': 'memory:'", content)

        on_cvrp_finished_code = content.split("def _on_cvrp_finished")[1].split("def ")[0]
        self.assertIn("self._persist_outputs(\"CVRP\",", on_cvrp_finished_code)

    def test_routing_dock_tsp_report_time_and_unit(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("Tempo de cálculo", content)
        self.assertIn("Unidade das distâncias", content)
        self.assertEqual(
            content.count("time.monotonic"), 4,
            "Esperado exatamente 4 usos de time.monotonic no routing_dock.py (início e fim do TSP e CVRP)."
        )

    def test_routing_dock_cvrp_report_time_and_unit(self):
        content = (pathlib.Path(__file__).resolve().parent.parent / "logis/gui/routing_dock.py").read_text(
            encoding="utf-8"
        )
        on_cvrp_finished_code = content.split("def _on_cvrp_finished")[1].split("def ")[0]

        self.assertIn("self._persist_outputs(\"CVRP\",", on_cvrp_finished_code)
        self.assertIn("Tempo de cálculo", on_cvrp_finished_code)
        self.assertIn("Unidade das distâncias", on_cvrp_finished_code)
        self.assertIn("&nbsp;m", on_cvrp_finished_code)


if __name__ == "__main__":
    unittest.main()

