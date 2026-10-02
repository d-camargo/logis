# -*- coding: utf-8 -*-
import os
import unittest

from logis.core.routing.districting import UNASSIGNED_SECTOR, is_unassigned_sector

try:
    from qgis.core import (
        QgsApplication,
        QgsVectorLayer,
        QgsField,
        QgsFeature,
        QgsGeometry,
        QgsPointXY,
        QgsProcessingContext,
        QgsProcessingException,
        QgsProcessingFeedback,
        QgsProject,
    )
    from qgis.PyQt.QtCore import QVariant

    _qgs = QgsApplication.instance()
    if not _qgs:
        _qgs = QgsApplication([], False)
        _qgs.initQgis()
    _HAS_QGIS = True
except ImportError:
    _HAS_QGIS = False


class LogFeedback(QgsProcessingFeedback if _HAS_QGIS else object):
    def __init__(self):
        if _HAS_QGIS:
            super().__init__()
        self.infos = []
        self.warnings = []

    def pushInfo(self, info):
        self.infos.append(info)

    def pushWarning(self, warning):
        self.warnings.append(warning)
        if _HAS_QGIS:
            super().pushWarning(warning)


@unittest.skipUnless(_HAS_QGIS, "QGIS não disponível")
class TestWasteDistrictingAlgorithm(unittest.TestCase):
    """Testes do logis:waste_districting com QGIS real (padrão de tests/test_vrp_cvrp.py)."""

    # SRC métrico (UTM 23S), coordenadas válidas perto de (500000, 7500000).
    X0 = 500000.0
    Y0 = 7500000.0

    def _make_layer(self, lines):
        layer = QgsVectorLayer("LineString?crs=EPSG:31983", "streets", "memory")
        dp = layer.dataProvider()
        for pts in lines:
            f = QgsFeature()
            f.setGeometry(
                QgsGeometry.fromPolylineXY(
                    [QgsPointXY(self.X0 + x, self.Y0 + y) for x, y in pts]
                )
            )
            dp.addFeature(f)
        layer.updateExtents()
        return layer

    def _run(self, layer, num_sectors, fb=None):
        from logis.algorithms.waste_districting import WasteDistricting

        alg = WasteDistricting()
        alg.initAlgorithm()
        context = QgsProcessingContext()
        context.setProject(QgsProject.instance())
        fb = fb if fb is not None else LogFeedback()
        params = {
            "INPUT_STREETS": layer,
            "NUM_SECTORS": num_sectors,
            "OUTPUT": "memory:",
        }
        res = alg.processAlgorithm(params, context, fb)
        return res, context, fb

    def _resolve_output(self, context, val):
        if isinstance(val, str):
            lay = context.getMapLayer(val)
            if lay is not None and lay.isValid():
                return lay
            return QgsVectorLayer(val, "out", "ogr")
        return val

    def test_internal_vertex_connects_and_all_get_sector(self):
        # (i) rua A com 3 vértices, rua B começa no vértice do meio de A,
        # rua C continua da ponta de B -> k=2: todas com setor >= 0, nenhuma com -1.
        layer = self._make_layer(
            [
                [(0, 0), (0, 10), (0, 20)],      # A
                [(0, 10), (10, 10)],             # B (toca A no vértice do meio)
                [(10, 10), (10, 20)],            # C (continua de B)
            ]
        )
        res, context, fb = self._run(layer, num_sectors=2)
        out = self._resolve_output(context, res["OUTPUT"])

        sectors = {f.id(): f.attribute("collection_sector_id") for f in out.getFeatures()}
        self.assertEqual(len(sectors), 3)
        self.assertTrue(all(s >= 0 for s in sectors.values()), sectors)
        self.assertNotIn(-1, sectors.values())

    def test_isolated_edge_gets_minus_one_and_warning(self):
        # (ii) grade com 6 trechos + 1 trecho isolado longe, k=2 -> termina sem erro,
        # o isolado sai com -1, os outros com 0 ou 1; aviso e log de conclusão.
        layer = self._make_layer(
            [
                [(0, 0), (5, 0), (10, 0)],        # 0: base (vértice do meio em (5,0))
                [(10, 0), (10, 5), (10, 10)],     # 1: direita
                [(10, 10), (5, 10), (0, 10)],     # 2: topo
                [(0, 10), (0, 5), (0, 0)],        # 3: esquerda
                [(5, 0), (5, 10)],                # 4: cruza a base no vértice do meio
                [(0, 5), (10, 5)],                # 5: cruza a esquerda/direita no vértice do meio
                [(100, 100), (100, 110)],         # ilha isolada
            ]
        )
        fids = [f.id() for f in layer.getFeatures()]
        isolated_fid = fids[-1]

        res, context, fb = self._run(layer, num_sectors=2)
        out = self._resolve_output(context, res["OUTPUT"])

        sectors = {f.id(): f.attribute("collection_sector_id") for f in out.getFeatures()}
        self.assertEqual(sectors[isolated_fid], -1)
        self.assertTrue(
            all(sectors[fid] in (0, 1) for fid in fids[:-1]),
            sectors,
        )

        self.assertTrue(
            any("fora da rede principal" in w for w in fb.warnings),
            fb.warnings,
        )
        self.assertTrue(
            any(str(isolated_fid) in w for w in fb.warnings),
            fb.warnings,
        )
        self.assertTrue(
            any("trechos sem setor (-1): 1" in info for info in fb.infos),
            fb.infos,
        )

    def test_too_fragmented_network_raises(self):
        # (iii) três ilhas desconexas de carga igual -> ~67% da carga fora do principal
        # -> QgsProcessingException.
        layer = self._make_layer(
            [
                [(0, 0), (0, 10)],
                [(100, 0), (100, 10)],
                [(200, 0), (200, 10)],
            ]
        )
        with self.assertRaises(QgsProcessingException) as ctx:
            self._run(layer, num_sectors=2)
        msg = str(ctx.exception)
        self.assertIn("Rede fragmentada demais", msg)
        self.assertIn("%", msg)

    def test_num_sectors_above_main_component_raises(self):
        # (iv) k maior que os trechos do componente principal -> QgsProcessingException.
        layer = self._make_layer(
            [
                [(0, 0), (10, 0)],
                [(10, 0), (10, 10)],
                [(100, 100), (100, 110)],  # ilha (~1/3 da carga, abaixo de 50%)
            ]
        )
        with self.assertRaises(QgsProcessingException) as ctx:
            self._run(layer, num_sectors=3)
        msg = str(ctx.exception)
        self.assertIn("rede principal", msg)


class TestUnassignedSector(unittest.TestCase):
    """Testes puros (sem QGIS) para UNASSIGNED_SECTOR e is_unassigned_sector."""

    def test_unassigned_sector_constant_is_minus_one(self):
        # O valor é contrato de dados: camadas 0.7.1 já gravadas levam -1 no campo.
        self.assertEqual(UNASSIGNED_SECTOR, -1)

    def test_unassigned_sector_truthy(self):
        for val in (-1, -1.0, "-1", " -1 "):
            with self.subTest(val=val):
                self.assertTrue(is_unassigned_sector(val))

    def test_is_unassigned_sector_falsy(self):
        for val in (0, 1, None, "abc", -2):
            with self.subTest(val=val):
                self.assertFalse(is_unassigned_sector(val))


if __name__ == "__main__":
    unittest.main()
