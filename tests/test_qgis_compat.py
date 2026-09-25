# -*- coding: utf-8 -*-
"""Testes de core/qgis_compat.py.

O caso central é o (c): no PyQt6/QGIS 4 a classe QVariant ainda importa, mas
perdeu os membros de QVariant::Type. Como a suíte roda em PyQt5, o PyQt6 é
simulado com um QVariant sem o atributo — é assim que o bug do QGIS 4 se
reproduz aqui.
"""

import unittest
from unittest.mock import patch

from logis.core import qgis_compat
from logis.core.qgis_compat import field_type, is_null

try:
    from qgis.core import QgsField
    from qgis.PyQt.QtCore import QMetaType
    HAS_QGIS = True
except ImportError:  # pragma: no cover - ambiente sem QGIS
    HAS_QGIS = False


@unittest.skipUnless(HAS_QGIS, "QGIS não disponível")
class TestFieldType(unittest.TestCase):
    def test_kinds_build_a_real_qgsfield(self):
        # (a) o valor devolvido tem que ser aceito pelo construtor do QgsField
        for kind in ("int", "double", "string", "bool"):
            with self.subTest(kind=kind):
                tipo = field_type(kind)
                self.assertIsNotNone(tipo)
                campo = QgsField("campo_%s" % kind, tipo)
                self.assertEqual(campo.name(), "campo_%s" % kind)

    def test_unknown_kind_returns_invalid_without_raising(self):
        # (b) tipo desconhecido devolve o valor inválido, não levanta
        tipo = field_type("coisa_que_nao_existe")
        self.assertIsNotNone(tipo)
        QgsField("campo_invalido", tipo)

    def test_falls_back_to_qmetatype_when_qvariant_has_no_members(self):
        # (c) PyQt6 simulado: QVariant importa, mas sem os membros do enum
        class QVariantSemMembros:
            pass

        with patch.object(qgis_compat, "QVariant", QVariantSemMembros):
            self.assertEqual(field_type("string"), QMetaType.Type.QString)
            self.assertEqual(field_type("int"), QMetaType.Type.LongLong)
            self.assertEqual(field_type("double"), QMetaType.Type.Double)
            self.assertEqual(field_type("bool"), QMetaType.Type.Bool)

    def test_returns_none_when_neither_backend_exists(self):
        # (d) sem QVariant e sem QMetaType não há tipo a devolver
        with patch.object(qgis_compat, "QVariant", None), \
                patch.object(qgis_compat, "QMetaType", None):
            self.assertIsNone(field_type("string"))


class TestIsNull(unittest.TestCase):
    def test_none_is_null(self):
        self.assertTrue(is_null(None))

    def test_plain_values_are_not_null(self):
        for val in (0, 0.0, "", 12.5, "texto"):
            with self.subTest(val=val):
                self.assertFalse(is_null(val))

    def test_object_with_isnull_delegates(self):
        class Nulo:
            def isNull(self):
                return True

        self.assertTrue(is_null(Nulo()))


if __name__ == "__main__":
    unittest.main()
