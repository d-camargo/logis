# -*- coding: utf-8 -*-
import json
import sys
import types
import unittest
from unittest import mock
import os
import shutil
import tempfile

from logis.core.optim_backend import (
    _guard_path,
    guard_state,
    reset_ortools_guard,
    load_routing_solver,
    pick_backend,
    has_ortools,
)


def _fake_solver_modules():
    """Cria módulos 'ortools' e 'ortools.constraint_solver' falsos para simular import OK."""
    ortools = types.ModuleType("ortools")
    constraint_solver = types.ModuleType("ortools.constraint_solver")
    constraint_solver.pywrapcp = types.SimpleNamespace(RoutingModel=object)
    constraint_solver.routing_enums_pb2 = types.SimpleNamespace(FirstSolutionStrategy=object)
    ortools.constraint_solver = constraint_solver
    return {"ortools": ortools, "ortools.constraint_solver": constraint_solver}


class TestOptimBackendGuard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = mock.patch("logis.core.downloader.cache_dir", return_value=self.temp_dir)
        self.patcher.start()
        reset_ortools_guard()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_guard_absent_unknown_and_import_allowed(self):
        # 1. selo ausente -> unknown
        self.assertEqual(guard_state(), "unknown")
        # e o import e tentado (aqui simulado com sucesso)
        with mock.patch.dict(sys.modules, _fake_solver_modules()):
            pywrapcp, enums = load_routing_solver()
        self.assertIsNotNone(pywrapcp)
        self.assertIsNotNone(enums)

    def test_import_success_sets_ok(self):
        # 3. import bem-sucedido -> selo vira ok (deterministico, via modulos falsos)
        with mock.patch.dict(sys.modules, _fake_solver_modules()):
            load_routing_solver()
        self.assertEqual(guard_state(), "ok")

    def test_clean_import_failure_does_not_block(self):
        # Falha de import com excecao Python (processo sobreviveu) NAO pode deixar o selo
        # em "importing": senao a proxima sessao amanhece bloqueada sem ter havido crash.
        with mock.patch.dict(sys.modules, {"ortools": None, "ortools.constraint_solver": None}):
            with self.assertRaises(RuntimeError):
                load_routing_solver()
            self.assertEqual(guard_state(), "unknown")
            # com o pacote quebrado, pick_backend cai para python — mas por deteccao,
            # nao pela trava (selo nao bloqueado)
            self.assertEqual(pick_backend("ortools"), "python")
        self.assertEqual(guard_state(), "unknown")

    def test_stale_importing_stamp_blocks(self):
        # 2. selo congelado em importing (processo morreu no meio do import) -> blocked
        path = _guard_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"stage": "importing", "pid": 111, "ts": 1.0}, f)

        self.assertEqual(guard_state(), "blocked")
        self.assertFalse(has_ortools())
        self.assertEqual(pick_backend("ortools"), "python")

        # load_routing_solver levanta sem tentar importar ortools
        with mock.patch.dict(sys.modules, {"ortools": None, "ortools.constraint_solver": None}):
            with self.assertRaises(RuntimeError) as ctx:
                load_routing_solver()
        self.assertIn("OR-Tools import falhou", str(ctx.exception))

    def test_reset_returns_to_unknown(self):
        # 4. reset_ortools_guard volta para unknown
        path = _guard_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"stage": "importing"}, f)
        self.assertEqual(guard_state(), "blocked")
        reset_ortools_guard()
        self.assertEqual(guard_state(), "unknown")


if __name__ == "__main__":
    unittest.main()
