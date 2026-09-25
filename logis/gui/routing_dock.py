# -*- coding: utf-8 -*-
"""
Painel (dock) para Roteirização (TSP/VRP).

Licença: GPL-3.0
"""

import os
import time

try:
    from qgis.gui import QgsDockWidget, QgsMapLayerComboBox, QgsFieldComboBox
    from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsVectorLayer
    from qgis.PyQt.QtCore import Qt, QCoreApplication
    from qgis.PyQt.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QMessageBox,
        QLineEdit,
        QDoubleSpinBox,
        QSpinBox,
        QComboBox,
        QScrollArea,
        QCheckBox,
        QTabWidget,
        QProgressBar
    )
except ImportError:
    # Mocks para quando rodado fora do QGIS (ex: smoke tests ou CLI)
    class QgsDockWidget:
        def __init__(self, title, parent=None):
            pass
        def setWidget(self, widget):
            pass
    class QgsMapLayerComboBox:
        def __init__(self, parent=None):
            self.layerChanged = MockSignal()
        def setFilters(self, filters):
            pass
        def setAllowEmptyLayer(self, allow):
            pass
        def currentLayer(self):
            return None
    class QgsMapLayerProxyModel:
        class Filter:
            LineLayer = 1
            PolygonLayer = 2
            PointLayer = 3
    class QgsFieldComboBox:
        def __init__(self, parent=None):
            pass
        def setLayer(self, layer):
            pass
        def setAllowEmptyFieldName(self, allow):
            pass
        def currentField(self):
            return None
    class QgsProject:
        @staticmethod
        def instance():
            return None
    class QgsVectorLayer:
        def __init__(self, path="", name="", provider=""):
            self._path = path
            self._name = name
            self._valid = True
        def isValid(self):
            return getattr(self, "_valid", True)
        def name(self):
            return getattr(self, "_name", "")
        def source(self):
            return getattr(self, "_path", "")
    class Qt:
        pass
    class QCoreApplication:
        @staticmethod
        def translate(context, text):
            return text
    class QWidget:
        def __init__(self, parent=None):
            pass
    class QVBoxLayout:
        def __init__(self, parent=None):
            pass
        def addWidget(self, widget, *args):
            pass
        def addLayout(self, layout, *args):
            pass
        def addStretch(self, *args):
            pass
        def setContentsMargins(self, *args):
            pass
        def setSpacing(self, *args):
            pass
    class QHBoxLayout:
        def __init__(self, parent=None):
            pass
        def addWidget(self, widget, *args):
            pass
        def addLayout(self, layout, *args):
            pass
    class QLabel:
        def __init__(self, text="", parent=None):
            pass
        def setStyleSheet(self, style):
            pass
        def setWordWrap(self, wrap):
            pass
    class QPushButton:
        def __init__(self, text="", parent=None):
            self.clicked = MockSignal()
            self._enabled = True
        def setEnabled(self, enabled):
            self._enabled = enabled
        def isEnabled(self):
            return getattr(self, "_enabled", True)
        def setStyleSheet(self, style):
            pass
    class QProgressBar:
        def __init__(self, parent=None):
            self._value = 0
            self._min = 0
            self._max = 100
            self._visible = False
        def setRange(self, minimum, maximum):
            self._min = minimum
            self._max = maximum
        def setValue(self, value):
            self._value = value
        def value(self):
            return self._value
        def setVisible(self, visible):
            self._visible = visible
        def isVisible(self):
            return self._visible
        def isHidden(self):
            return not self._visible
        def hide(self):
            self._visible = False
        def show(self):
            self._visible = True
    class QCheckBox:
        def __init__(self, text="", parent=None):
            self._checked = False
        def setChecked(self, checked):
            self._checked = checked
        def isChecked(self):
            return self._checked
    class MockSignal:
        def connect(self, slot):
            pass
    class QTextEdit:
        def __init__(self, parent=None):
            pass
        def setReadOnly(self, read_only):
            pass
        def append(self, text):
            pass
        def clear(self):
            pass
        def setStyleSheet(self, style):
            pass
        def setMinimumHeight(self, height):
            pass
    class QMessageBox:
        @staticmethod
        def warning(parent, title, text):
            pass
        @staticmethod
        def critical(parent, title, text):
            pass
    class QLineEdit:
        def __init__(self, parent=None):
            pass
        def text(self):
            return ""
    class QDoubleSpinBox:
        def __init__(self, parent=None):
            pass
        def setRange(self, minimum, maximum):
            pass
        def setValue(self, value):
            pass
        def setSingleStep(self, step):
            pass
        def value(self):
            return 2.0
    class QSpinBox:
        def __init__(self, parent=None):
            pass
        def setRange(self, minimum, maximum):
            pass
        def setValue(self, value):
            pass
        def value(self):
            return 1000
    class QComboBox:
        def __init__(self, parent=None):
            pass
        def addItems(self, items):
            pass
        def currentIndex(self):
            return 0
    class QScrollArea:
        def __init__(self, parent=None):
            pass
        def setWidgetResizable(self, resizable):
            pass
        def setWidget(self, widget):
            pass
    class QTabWidget:
        def __init__(self, parent=None):
            self._tabs = []
        def addTab(self, widget, title):
            self._tabs.append(title)
            return len(self._tabs) - 1
        def count(self):
            return len(self._tabs)
        def tabText(self, index):
            return self._tabs[index]


try:
    from logis.core import optim_backend
except ImportError:
    try:
        from ..core import optim_backend
    except (ImportError, ValueError):
        optim_backend = None

try:
    from logis.core.layer_output import output_names, gpkg_path_from_source, write_layer_to_gpkg, slugify
except ImportError:
    try:
        from ..core.layer_output import output_names, gpkg_path_from_source, write_layer_to_gpkg, slugify
    except (ImportError, ValueError):
        output_names = None
        gpkg_path_from_source = None
        write_layer_to_gpkg = None
        slugify = None


class RoutingDock(QgsDockWidget):
    """
    Painel lateral (Dock Widget) para Roteirização (TSP/VRP)
    no plugin logis.
    """

    def __init__(self, iface, parent=None):
        super().__init__(QCoreApplication.translate("RoutingDock", "logis — Roteirização"), parent)
        self.iface = iface
        self._tsp_t0 = None
        self._tsp_runner = None
        self._cvrp_t0 = None
        self._cvrp_runner = None
        self._build_ui()

    def tr(self, string):
        return QCoreApplication.translate("RoutingDock", string)

    def _new_tab(self, title):
        """
        Cria uma aba com rolagem própria e devolve o layout onde as seções entram.
        """
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(10)

        tab_scroll = QScrollArea()
        tab_scroll.setWidgetResizable(True)
        tab_scroll.setWidget(page)

        self.tabs.addTab(tab_scroll, title)
        return page_layout

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(10)

        # Título principal
        title_label = QLabel(self.tr("<b>Roteirização</b>"))
        title_label.setStyleSheet("font-size: 14px; color: #2b6cb0; margin-bottom: 2px;")
        outer.addWidget(title_label)

        desc_label = QLabel(
            self.tr(
                "O painel reúne o Caixeiro Viajante e a Roteirização de Veículos "
                "Capacitados; a camada de rede viária escolhida abaixo vale para a aba CVRP e, "
                "na aba TSP, quando o modo \"pela rede viária\" está selecionado."
            )
        )
        desc_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        desc_label.setWordWrap(True)
        outer.addWidget(desc_label)

        # Seletor de Camada de Rede Viária (Linhas - opcional)
        outer.addWidget(QLabel(self.tr("Camada de rede viária (Linhas - opcional):")))
        self.cmb_network = QgsMapLayerComboBox()
        self.cmb_network.setFilters(QgsMapLayerProxyModel.Filter.LineLayer)
        if hasattr(self.cmb_network, 'setAllowEmptyLayer'):
            self.cmb_network.setAllowEmptyLayer(True)
        outer.addWidget(self.cmb_network)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)

        # Painel de resultados
        outer.addWidget(QLabel(self.tr("Resultados da Roteirização:")))
        self.prg_run = QProgressBar()
        self.prg_run.setRange(0, 100)
        self.prg_run.hide()
        outer.addWidget(self.prg_run)

        self.btn_cancel = QPushButton(self.tr("Cancelar"))
        self.btn_cancel.setEnabled(False)
        outer.addWidget(self.btn_cancel)

        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        self.txt_results.setMinimumHeight(150)
        self.txt_results.setStyleSheet(
            "font-family: monospace; font-size: 11px; background-color: #2d3748; color: #edf2f7; padding: 5px;"
        )
        outer.addWidget(self.txt_results)

        # Aba: TSP
        layout = self._new_tab(self.tr("TSP"))

        # Seletor de Camada do Ponto Inicial (Pontos)
        layout.addWidget(QLabel(self.tr("Camada do ponto inicial (Pontos):")))
        self.cmb_start = QgsMapLayerComboBox()
        self.cmb_start.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_start)

        # Seletor de Camada de Pontos a Visitar (Pontos)
        layout.addWidget(QLabel(self.tr("Camada de pontos a visitar (Pontos):")))
        self.cmb_points = QgsMapLayerComboBox()
        self.cmb_points.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_points)

        # Seletor de Camada do Ponto Final (Pontos - opcional, vazio fecha no ponto inicial)
        layout.addWidget(QLabel(self.tr("Camada do ponto final (Pontos - opcional, vazio fecha no ponto inicial):")))
        self.cmb_end = QgsMapLayerComboBox()
        self.cmb_end.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        if hasattr(self.cmb_end, 'setAllowEmptyLayer'):
            self.cmb_end.setAllowEmptyLayer(True)
        layout.addWidget(self.cmb_end)

        # Modo de cálculo da distância
        layout.addWidget(QLabel(self.tr("Modo de cálculo da distância:")))
        self.cmb_tsp_mode = QComboBox()
        self.cmb_tsp_mode.addItems([
            self.tr("Linha reta (euclidiana)"),
            self.tr("Pela rede viária (Dijkstra)")
        ])
        layout.addWidget(self.cmb_tsp_mode)

        tsp_mode_desc = QLabel(
            self.tr("Nota: O modo \"pela rede viária\" utiliza a camada de rede escolhida no topo do painel.")
        )
        tsp_mode_desc.setStyleSheet("color: #666; font-size: 11px;")
        tsp_mode_desc.setWordWrap(True)
        layout.addWidget(tsp_mode_desc)

        # Backend de otimização
        layout.addWidget(QLabel(self.tr("Backend de otimização:")))
        self.cmb_tsp_backend = QComboBox()
        self.cmb_tsp_backend.addItems([
            self.tr("Automático (OR-Tools quando disponível)"),
            self.tr("Python puro (heurística)"),
            self.tr("OR-Tools")
        ])
        layout.addWidget(self.cmb_tsp_backend)

        tsp_backend_desc = QLabel(
            self.tr("Nota: Em modo automático, o OR-Tools é utilizado se disponível, com fallback para Python puro.")
        )
        tsp_backend_desc.setStyleSheet("color: #666; font-size: 11px;")
        tsp_backend_desc.setWordWrap(True)
        layout.addWidget(tsp_backend_desc)

        # Checkbox para busca local (2-opt e Or-opt)
        self.chk_improve = QCheckBox(self.tr("Aplicar busca local (2-opt e Or-opt)"))
        self.chk_improve.setChecked(True)
        layout.addWidget(self.chk_improve)

        chk_improve_desc = QLabel(
            self.tr("Refina a rota inicial invertendo trechos (2-opt) e reposicionando paradas (Or-opt). Reduz a distância total e aumenta o tempo de cálculo.")
        )
        chk_improve_desc.setStyleSheet("color: #666; font-size: 11px;")
        chk_improve_desc.setWordWrap(True)
        layout.addWidget(chk_improve_desc)

        # Botão Calcular Rota (TSP)
        self.btn_run_tsp = QPushButton(self.tr("Calcular Rota (TSP)"))
        self.btn_run_tsp.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_tsp.clicked.connect(self.run_tsp)
        layout.addWidget(self.btn_run_tsp)

        layout.addStretch()

        # Aba: CVRP
        layout = self._new_tab(self.tr("CVRP"))

        cvrp_desc = QLabel(
            self.tr("Resolve a roteirização de uma frota com capacidade a partir de um depósito.")
        )
        cvrp_desc.setStyleSheet("color: #666; font-size: 11px;")
        cvrp_desc.setWordWrap(True)
        layout.addWidget(cvrp_desc)

        cvrp_net_desc = QLabel(
            self.tr("Nota: A camada de rede viária utilizada é a selecionada no topo do painel.")
        )
        cvrp_net_desc.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        cvrp_net_desc.setWordWrap(True)
        layout.addWidget(cvrp_net_desc)

        # Seletor de Camada de Depósito (Pontos)
        layout.addWidget(QLabel(self.tr("Camada de depósito (Pontos):")))
        self.cmb_depot = QgsMapLayerComboBox()
        self.cmb_depot.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_depot)

        # Seletor de Camada de Demanda / Clientes (Pontos)
        layout.addWidget(QLabel(self.tr("Camada de demanda / clientes (Pontos):")))
        self.cmb_demand = QgsMapLayerComboBox()
        self.cmb_demand.setFilters(QgsMapLayerProxyModel.Filter.PointLayer)
        layout.addWidget(self.cmb_demand)

        # Seletor de Campo de Peso/Demanda (opcional)
        layout.addWidget(QLabel(self.tr("Campo de peso/demanda (opcional, default = 1,0):")))
        self.cmb_demand_field = QgsFieldComboBox()
        if hasattr(self.cmb_demand_field, 'setAllowEmptyFieldName'):
            self.cmb_demand_field.setAllowEmptyFieldName(True)
        self.cmb_demand_field.setLayer(self.cmb_demand.currentLayer())
        self.cmb_demand.layerChanged.connect(self.cmb_demand_field.setLayer)
        layout.addWidget(self.cmb_demand_field)

        # Capacidade do Veículo
        layout.addWidget(QLabel(self.tr("Capacidade do veículo:")))
        self.spin_capacity = QDoubleSpinBox()
        self.spin_capacity.setRange(0.0001, 1e9)
        self.spin_capacity.setValue(100.0)
        self.spin_capacity.setSingleStep(10.0)
        layout.addWidget(self.spin_capacity)

        # Backend de otimização
        layout.addWidget(QLabel(self.tr("Backend de otimização:")))
        self.cmb_cvrp_backend = QComboBox()
        self.cmb_cvrp_backend.addItems([
            self.tr("Automático (OR-Tools quando disponível)"),
            self.tr("Python puro (heurística)"),
            self.tr("OR-Tools")
        ])
        layout.addWidget(self.cmb_cvrp_backend)

        cvrp_backend_desc = QLabel(
            self.tr("Nota: Em modo automático, o OR-Tools é utilizado se disponível, com fallback para Python puro.")
        )
        cvrp_backend_desc.setStyleSheet("color: #666; font-size: 11px;")
        cvrp_backend_desc.setWordWrap(True)
        layout.addWidget(cvrp_backend_desc)

        # Checkbox para busca local (2-opt e Or-opt)
        self.chk_cvrp_improve = QCheckBox(self.tr("Aplicar busca local (2-opt e Or-opt)"))
        self.chk_cvrp_improve.setChecked(True)
        layout.addWidget(self.chk_cvrp_improve)

        chk_cvrp_improve_desc = QLabel(
            self.tr("Refina a rota inicial invertendo trechos (2-opt) e reposicionando paradas (Or-opt). Reduz a distância total e aumenta o tempo de cálculo.")
        )
        chk_cvrp_improve_desc.setStyleSheet("color: #666; font-size: 11px;")
        chk_cvrp_improve_desc.setWordWrap(True)
        layout.addWidget(chk_cvrp_improve_desc)

        # Botão Executar Roteirização (CVRP)
        self.btn_run_cvrp = QPushButton(self.tr("Executar Roteirização (CVRP)"))
        self.btn_run_cvrp.setStyleSheet("font-weight: bold; padding: 6px; font-size: 12px;")
        self.btn_run_cvrp.clicked.connect(self.run_cvrp)
        layout.addWidget(self.btn_run_cvrp)

        layout.addStretch()

        scroll.setWidget(central)
        self.setWidget(scroll)

    def _attr(self, feat, fields, name, default):
        """
        Helper para leitura de atributo de uma feição por nome de campo.
        """
        if fields is not None and hasattr(fields, 'indexOf'):
            idx = fields.indexOf(name)
            if idx >= 0 and hasattr(feat, 'attributes'):
                attrs = feat.attributes()
                if 0 <= idx < len(attrs) and attrs[idx] is not None:
                    return attrs[idx]
        return default

    def _start_progress(self, titulo=""):
        """
        Inicia a exibição do progresso e desabilita os botões de execução.
        """
        self.prg_run.setValue(0)
        self.prg_run.show()
        self.btn_cancel.setEnabled(True)
        if hasattr(self, "btn_run_tsp"):
            self.btn_run_tsp.setEnabled(False)
        if hasattr(self, "btn_run_cvrp"):
            self.btn_run_cvrp.setEnabled(False)
        if titulo:
            self.txt_results.append(f"<b>{titulo}</b>")

    def _update_progress(self, valor):
        """
        Atualiza o valor da barra de progresso (0–100).
        """
        self.prg_run.setValue(int(valor))

    def _finish_progress(self):
        """
        Finaliza a exibição do progresso e reabilita os botões de execução.
        """
        self.prg_run.hide()
        self.btn_cancel.setEnabled(False)
        if hasattr(self, "btn_run_tsp"):
            self.btn_run_tsp.setEnabled(True)
        if hasattr(self, "btn_run_cvrp"):
            self.btn_run_cvrp.setEnabled(True)

    def _persist_outputs(self, kind, mode, layers):
        """
        Persiste e adiciona as camadas de saída ao projeto QGIS (D-J, D-K, D-L, D-M).

        :param kind: 'TSP' ou 'CVRP'
        :param mode: 'rede' ou 'euclidiana'
        :param layers: Tupla ou lista (camada_linhas, camada_pontos)
        :return: Tupla das camadas resultantes (carregadas do GPKG ou temporárias)
        """
        if not layers:
            return layers

        if all(l is None for l in layers):
            return layers

        # (a) Camada de referência pela D-K (rede do topo se houver, senão a camada de pontos a visitar / demanda)
        ref_layer = self.cmb_network.currentLayer() if hasattr(self, "cmb_network") else None
        if not ref_layer:
            if kind == "TSP" and hasattr(self, "cmb_points"):
                ref_layer = self.cmb_points.currentLayer()
            elif kind == "CVRP" and hasattr(self, "cmb_demand"):
                ref_layer = self.cmb_demand.currentLayer()

        ref_name = ref_layer.name() if (ref_layer and hasattr(ref_layer, "name")) else None
        ref_source = ref_layer.source() if (ref_layer and hasattr(ref_layer, "source")) else None

        # (b) Nomes por output_names("TSP"|"CVRP", "rede"|"euclidiana", slugify(ref.name()))
        ref_slug = slugify(ref_name) if (ref_name and slugify is not None) else None
        if output_names is not None:
            nome_linhas, nome_pontos = output_names(kind, mode, ref_slug)
        else:
            slug = ref_slug or "rede"
            nl = f"{kind}-{mode}_{slug}"
            nome_linhas, nome_pontos = (nl, f"{nl}_pontos")
        names = (nome_linhas, nome_pontos)

        for i, layer in enumerate(layers):
            if layer is not None and hasattr(layer, "setName") and i < len(names):
                layer.setName(names[i])

        # (c) Caminho por gpkg_path_from_source(ref.source())
        gpkg_path = gpkg_path_from_source(ref_source) if (ref_source and gpkg_path_from_source is not None) else None

        proj = QgsProject.instance() if hasattr(QgsProject, "instance") else None
        result_layers = []
        all_gpkg_ok = True if gpkg_path else False

        if gpkg_path is None:
            # Se vier None, parar aqui e adicionar as camadas temporárias com o nome novo
            for layer in layers:
                if layer is not None:
                    if proj is not None and hasattr(proj, "addMapLayer"):
                        proj.addMapLayer(layer)
                    result_layers.append(layer)
                else:
                    result_layers.append(None)
            if hasattr(self, "txt_results"):
                self.txt_results.append(self.tr("-> <b>Destino das saídas:</b> camada temporária"))
            return tuple(result_layers)

        # (d) Se vier caminho:
        for i, layer in enumerate(layers):
            if layer is None:
                result_layers.append(None)
                continue

            nome = names[i] if i < len(names) else (layer.name() if hasattr(layer, "name") else "output")

            # Remover do projeto a camada homônima já carregada daquele GPKG (D-M, trava no Windows)
            if proj is not None and hasattr(proj, "mapLayers"):
                map_layers = proj.mapLayers()
                if map_layers and isinstance(map_layers, dict):
                    for existing_id, existing_layer in list(map_layers.items()):
                        if (
                            existing_layer
                            and hasattr(existing_layer, "name")
                            and existing_layer.name() == nome
                            and hasattr(existing_layer, "source")
                            and str(existing_layer.source()).split("|", 1)[0] == str(gpkg_path)
                        ):
                            proj.removeMapLayer(existing_id)

            # Gravar com write_layer_to_gpkg
            ok = False
            err_msg = ""
            if write_layer_to_gpkg is not None:
                ok, err_msg = write_layer_to_gpkg(layer, gpkg_path, nome)

            if ok:
                saved_layer = None
                if QgsVectorLayer is not None:
                    try:
                        vlayer = QgsVectorLayer(f"{gpkg_path}|layername={nome}", nome, "ogr")
                        if vlayer and hasattr(vlayer, "isValid") and vlayer.isValid():
                            saved_layer = vlayer
                    except Exception as exc:
                        err_msg = str(exc)
                        saved_layer = None

                if saved_layer is not None:
                    if proj is not None and hasattr(proj, "addMapLayer"):
                        proj.addMapLayer(saved_layer)
                    result_layers.append(saved_layer)
                else:
                    # (e) Reabertura falhou, caindo na camada temporária
                    all_gpkg_ok = False
                    if hasattr(self, "txt_results"):
                        self.txt_results.append(
                            self.tr("<span style='color: #ecc94b;'>Aviso: Falha ao carregar camada do GPKG ({nome}). Usando camada temporária.</span>").format(nome=nome)
                        )
                    if proj is not None and hasattr(proj, "addMapLayer"):
                        proj.addMapLayer(layer)
                    result_layers.append(layer)
            else:
                # (e) Se a gravação falhar, escrever no log a linha de aviso com o erro e cair na camada temporária
                all_gpkg_ok = False
                if hasattr(self, "txt_results"):
                    err_str = err_msg if err_msg else self.tr("Erro desconhecido")
                    self.txt_results.append(
                        self.tr("<span style='color: #ecc94b;'>Aviso: Falha ao gravar no GPKG ({err}). Usando camada temporária.</span>").format(err=err_str)
                    )
                if proj is not None and hasattr(proj, "addMapLayer"):
                    proj.addMapLayer(layer)
                result_layers.append(layer)

        # Acrescentar ao log uma linha dizendo onde a saída foi parar
        if hasattr(self, "txt_results"):
            dest_str = os.path.basename(gpkg_path) if all_gpkg_ok else "camada temporária"
            self.txt_results.append(self.tr("-> <b>Destino das saídas:</b> {dest}").format(dest=dest_str))

        return tuple(result_layers)

    def run_tsp(self):
        """
        Executa o algoritmo de Caixeiro Viajante (TSP) em segundo plano.
        """
        self.txt_results.clear()

        start_layer = self.cmb_start.currentLayer()
        points_layer = self.cmb_points.currentLayer()
        end_layer = self.cmb_end.currentLayer()
        network_layer = self.cmb_network.currentLayer()
        use_network = self.cmb_tsp_mode.currentIndex() == 1
        improve = self.chk_improve.isChecked()

        if not start_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada do ponto inicial.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Ponto inicial não selecionado.</span>"))
            return

        if not points_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de pontos a visitar.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Pontos a visitar não selecionados.</span>"))
            return

        if use_network and not network_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr(
                    "O modo pela rede viária exige uma camada de rede viária no topo do painel "
                    "(ex: osm_links_<code_muni> do pipeline OSM)."
                )
            )
            self.txt_results.append(
                self.tr(
                    "<span style='color: #fc8181;'>Erro: O modo pela rede exige uma camada de rede viária no topo do painel "
                    "(ex: osm_links_<code_muni> do pipeline OSM).</span>"
                )
            )
            return

        self.txt_results.append(self.tr("<b>=== CALCULANDO ROTA (TSP) ===</b><br>"))

        if optim_backend and optim_backend.guard_state() == "blocked":
            self.txt_results.append(
                self.tr(
                    "<span style='color: #ecc94b;'>Aviso: O OR-Tools está desativado por ter derrubado a sessão anterior. "
                    "O rearme fica no diálogo de Dependências.</span><br>"
                )
            )

        self._tsp_t0 = time.monotonic()
        self._start_progress()

        params = {
            'INPUT_START': start_layer,
            'INPUT_POINTS': points_layer,
            'INPUT_END': end_layer if end_layer else None,
            'INPUT_NETWORK': network_layer if use_network else None,
            'IMPROVE': improve,
            'BACKEND': self.cmb_tsp_backend.currentIndex(),
            'OUTPUT_ORDER': 'memory:',
            'OUTPUT_ROUTE': 'memory:'
        }

        try:
            try:
                from logis.gui.task_runner import AlgTaskRunner
            except ImportError:
                from .task_runner import AlgTaskRunner

            self._tsp_runner = AlgTaskRunner(
                "logis:vrp_tsp",
                params,
                self._on_tsp_finished,
                on_message=self.txt_results.append,
                on_progress=self._update_progress
            )

            try:
                self.btn_cancel.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass
            self.btn_cancel.clicked.connect(self._tsp_runner.cancel)
            self._tsp_runner.start()
        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao iniciar o cálculo: {error}</span><br>").format(error=str(e))
            )
            self._finish_progress()

    def _on_tsp_finished(self, ok, results):
        """
        Callback executado quando a tarefa de cálculo do TSP é concluída.
        """
        try:
            if not ok or not results:
                runner = getattr(self, "_tsp_runner", None)
                if runner and getattr(runner, "feedback", None) and runner.feedback.isCanceled():
                    self.txt_results.append(
                        self.tr("<span style='color: #ecc94b;'>Cálculo cancelado pelo usuário.</span><br>")
                    )
                else:
                    if isinstance(results, str) and results:
                        err_msg = results
                    elif runner and getattr(runner, "feedback", None) and getattr(runner.feedback, "last_error", None):
                        err_msg = runner.feedback.last_error
                    else:
                        err_msg = self.tr("Erro ao calcular rota.")
                    self.txt_results.append(
                        self.tr("<span style='color: #fc8181;'>Erro ao calcular rota: {error}</span><br>").format(error=err_msg)
                    )
                return

            runner = getattr(self, "_tsp_runner", None)
            if runner and hasattr(runner, 'resolve_layer'):
                order_layer = runner.resolve_layer(results, 'OUTPUT_ORDER')
                route_layer = runner.resolve_layer(results, 'OUTPUT_ROUTE')
            else:
                order_layer = results.get('OUTPUT_ORDER') if results else None
                route_layer = results.get('OUTPUT_ROUTE') if results else None

            use_network = self.cmb_tsp_mode.currentIndex() == 1
            mode = "rede" if use_network else "euclidiana"
            route_layer, order_layer = self._persist_outputs("TSP", mode, (route_layer, order_layer))

            num_visited = 0
            tour_dist = 0.0
            access_dist = 0.0
            return_dist = 0.0
            dead_ratio = 0.0
            is_closed = True
            backend_str = "N/A"
            dist_mode_str = "N/A"
            straight_leg_count = 0

            if route_layer is not None and hasattr(route_layer, 'getFeatures'):
                feats = list(route_layer.getFeatures())
                if feats:
                    feat = feats[0]
                    fields = route_layer.fields() if hasattr(route_layer, 'fields') else None

                    num_visited = self._attr(feat, fields, 'stop_count', 0)
                    tour_dist = self._attr(feat, fields, 'tour_dist', 0.0)
                    access_dist = self._attr(feat, fields, 'access_dist', 0.0)
                    return_dist = self._attr(feat, fields, 'return_dist', 0.0)
                    dead_ratio = self._attr(feat, fields, 'dead_ratio', 0.0)
                    closed_val = self._attr(feat, fields, 'closed', 1)
                    is_closed = bool(closed_val)
                    backend_str = str(self._attr(feat, fields, 'backend', 'N/A'))
                    dist_mode_str = str(self._attr(feat, fields, 'dist_mode', 'N/A'))

                    for f in feats:
                        if self._attr(f, fields, 'leg_geom', '') == 'reta':
                            straight_leg_count += 1

            end_layer = self.cmb_end.currentLayer()
            if num_visited == 0 and order_layer is not None and hasattr(order_layer, 'featureCount'):
                count = order_layer.featureCount()
                num_visited = count - (2 if (end_layer and count >= 2) else 1) if count > 0 else 0
                if num_visited < 0:
                    num_visited = 0

            self.txt_results.append(
                self.tr("-> <b>Pontos visitados:</b> {n}").format(n=num_visited)
            )
            self.txt_results.append(
                self.tr("-> <b>Distância total do tour:</b> {dist:.2f}&nbsp;m").format(dist=tour_dist)
            )
            self.txt_results.append(
                self.tr("-> <b>Custo de acesso:</b> {acc:.2f}&nbsp;m").format(acc=access_dist)
            )
            self.txt_results.append(
                self.tr("-> <b>Custo de retorno:</b> {ret:.2f}&nbsp;m").format(ret=return_dist)
            )
            self.txt_results.append(
                self.tr("-> <b>Razão de deadhead (dead_ratio):</b> {dr:.4f}").format(dr=dead_ratio)
            )
            closing_str = self.tr("Sim (fecha no ponto inicial)") if is_closed else self.tr("Não (termina no ponto final)")
            self.txt_results.append(
                self.tr("-> <b>Fechamento:</b> {closed}").format(closed=closing_str)
            )
            self.txt_results.append(
                self.tr("-> <b>Modo de distância:</b> {mode}").format(mode=dist_mode_str)
            )
            self.txt_results.append(
                self.tr("-> <b>Backend de otimização:</b> {backend}").format(backend=backend_str)
            )
            t = f"{time.monotonic() - self._tsp_t0:.1f}".replace(".", ",")
            self.txt_results.append(
                self.tr("-> <b>Tempo de cálculo:</b> {t} s").format(t=t)
            )
            self.txt_results.append(
                self.tr("-> <b>Unidade das distâncias:</b> metros<br>")
            )
            if use_network and straight_leg_count > 0:
                self.txt_results.append(
                    self.tr(
                        "<span style='color: #ecc94b;'>Aviso: {n} trecho(s) caíram no segmento reto por falta de caminho na malha.</span><br>"
                    ).format(n=straight_leg_count)
                )

            self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao calcular rota: {error}</span><br>").format(error=str(e))
            )
        finally:
            self._finish_progress()

    def run_cvrp(self):
        """
        Executa o algoritmo de Roteirização de Veículos Capacitados (CVRP) em segundo plano.
        """
        self.txt_results.clear()

        depot_layer = self.cmb_depot.currentLayer()
        demand_layer = self.cmb_demand.currentLayer()
        demand_field = self.cmb_demand_field.currentField()
        capacity = self.spin_capacity.value()
        network_layer = self.cmb_network.currentLayer()
        improve = self.chk_cvrp_improve.isChecked()

        if not depot_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de depósito.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Depósito não selecionado.</span>"))
            return

        if not demand_layer:
            QMessageBox.warning(
                self,
                self.tr("Aviso"),
                self.tr("Por favor, selecione a camada de demanda / clientes.")
            )
            self.txt_results.append(self.tr("<span style='color: #fc8181;'>Erro: Camada de demanda não selecionada.</span>"))
            return

        self.txt_results.append(self.tr("<b>=== EXECUTANDO ROTEIRIZAÇÃO (CVRP) ===</b><br>"))

        if optim_backend and optim_backend.guard_state() == "blocked":
            self.txt_results.append(
                self.tr(
                    "<span style='color: #ecc94b;'>Aviso: O OR-Tools está desativado por ter derrubado a sessão anterior. "
                    "O rearme fica no diálogo de Dependências.</span><br>"
                )
            )

        self._cvrp_t0 = time.monotonic()
        self._start_progress()

        params = {
            'INPUT_DEPOT': depot_layer,
            'INPUT_DEMAND': demand_layer,
            'FIELD_DEMAND': demand_field or '',
            'CAPACITY': capacity,
            'INPUT_NETWORK': network_layer if network_layer else None,
            'IMPROVE': improve,
            'BACKEND': self.cmb_cvrp_backend.currentIndex(),
            'OUTPUT_ROUTES': 'memory:',
            'OUTPUT_STOPS': 'memory:'
        }

        try:
            try:
                from logis.gui.task_runner import AlgTaskRunner
            except ImportError:
                from .task_runner import AlgTaskRunner

            self._cvrp_runner = AlgTaskRunner(
                "logis:vrp_cvrp",
                params,
                self._on_cvrp_finished,
                on_message=self.txt_results.append,
                on_progress=self._update_progress
            )

            try:
                self.btn_cancel.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass
            self.btn_cancel.clicked.connect(self._cvrp_runner.cancel)
            self._cvrp_runner.start()
        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao iniciar o cálculo: {error}</span><br>").format(error=str(e))
            )
            self._finish_progress()

    def _on_cvrp_finished(self, ok, results):
        """
        Callback executado quando a tarefa de cálculo do CVRP é concluída.
        """
        try:
            if not ok or not results:
                runner = getattr(self, "_cvrp_runner", None)
                if runner and getattr(runner, "feedback", None) and runner.feedback.isCanceled():
                    self.txt_results.append(
                        self.tr("<span style='color: #ecc94b;'>Cálculo cancelado pelo usuário.</span><br>")
                    )
                else:
                    if isinstance(results, str) and results:
                        err_msg = results
                    elif runner and getattr(runner, "feedback", None) and getattr(runner.feedback, "last_error", None):
                        err_msg = runner.feedback.last_error
                    else:
                        err_msg = self.tr("Erro ao executar CVRP.")
                    self.txt_results.append(
                        self.tr("<span style='color: #fc8181;'>Erro ao executar CVRP: {error}</span><br>").format(error=err_msg)
                    )
                return

            runner = getattr(self, "_cvrp_runner", None)
            if runner and hasattr(runner, 'resolve_layer'):
                routes_layer = runner.resolve_layer(results, 'OUTPUT_ROUTES')
                stops_layer = runner.resolve_layer(results, 'OUTPUT_STOPS')
            else:
                routes_layer = results.get('OUTPUT_ROUTES') if results else None
                stops_layer = results.get('OUTPUT_STOPS') if results else None

            network_layer = self.cmb_network.currentLayer()
            mode = "rede" if network_layer else "euclidiana"
            routes_layer, stops_layer = self._persist_outputs("CVRP", mode, (routes_layer, stops_layer))

            total_routes = 0
            total_stops = 0
            total_load = 0.0
            total_dist = 0.0
            route_lines = []

            if routes_layer is not None and hasattr(routes_layer, 'getFeatures'):
                fields = routes_layer.fields() if hasattr(routes_layer, 'fields') else None
                for feat in routes_layer.getFeatures():
                    r_id = self._attr(feat, fields, 'route_id', 0)
                    s_count = self._attr(feat, fields, 'stop_count', 0)
                    r_load = float(self._attr(feat, fields, 'route_load', 0.0))
                    r_dist = float(self._attr(feat, fields, 'route_dist', 0.0))

                    total_routes += 1
                    total_stops += s_count
                    total_load += r_load
                    total_dist += r_dist

                    line_str = self.tr("Rota {id}: {n} paradas | carga {load:.2f} | distância {dist:.2f}&nbsp;m").format(
                        id=r_id, n=s_count, load=r_load, dist=r_dist
                    )
                    route_lines.append(line_str)

            self.txt_results.append(
                self.tr("-> <b>Rotas geradas:</b> {n}").format(n=total_routes)
            )
            self.txt_results.append(
                self.tr("-> <b>Paradas atendidas:</b> {n}").format(n=total_stops)
            )
            self.txt_results.append(
                self.tr("-> <b>Carga total:</b> {load:.2f}").format(load=total_load)
            )
            self.txt_results.append(
                self.tr("-> <b>Distância total:</b> {dist:.2f}&nbsp;m<br>").format(dist=total_dist)
            )

            for line in route_lines:
                self.txt_results.append(line)
            if route_lines:
                self.txt_results.append("")

            t0 = getattr(self, "_cvrp_t0", None)
            t = f"{time.monotonic() - t0:.1f}".replace(".", ",") if t0 is not None else "0,0"
            self.txt_results.append(
                self.tr("-> <b>Tempo de cálculo:</b> {t} s").format(t=t)
            )
            self.txt_results.append(
                self.tr("-> <b>Unidade das distâncias:</b> metros<br>")
            )

            self.txt_results.append(self.tr("<b>=== CÁLCULO CONCLUÍDO ===</b>"))
        except Exception as e:
            self.txt_results.append(
                self.tr("<span style='color: #fc8181;'>Erro ao executar CVRP: {error}</span><br>").format(error=str(e))
            )
        finally:
            self._finish_progress()

