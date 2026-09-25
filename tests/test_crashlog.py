# -*- coding: utf-8 -*-
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from logis.core.crashlog import mark, read_tail, reset, trace_path


class TestCrashlog(unittest.TestCase):

    def test_mark_writes_to_disk_before_close(self):
        """(a) mark grava e o conteudo esta no disco (flush+fsync) antes de fechar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with patch("logis.core.downloader.cache_dir", return_value=tmp_path):
                fsync_calls = []
                orig_fsync = os.fsync

                def mock_fsync(fd):
                    fsync_calls.append(fd)
                    return orig_fsync(fd)

                with patch("os.fsync", side_effect=mock_fsync):
                    mark("INICIO", "detalhe_a")

                self.assertTrue(len(fsync_calls) > 0)
                log_file = tmp_path / "diagnostico.log"
                self.assertTrue(log_file.exists())
                content = log_file.read_text(encoding="utf-8")
                self.assertIn("INICIO", content)
                self.assertIn("detalhe_a", content)
                self.assertIn(str(os.getpid()), content)

    def test_multiple_marks_accumulate_in_order(self):
        """(b) varias mark acumulam em ordem."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with patch("logis.core.downloader.cache_dir", return_value=tmp_path):
                mark("ETAPA_1", "primeiro")
                mark("ETAPA_2", "segundo")
                mark("ETAPA_3", "terceiro")

                tail = read_tail(10)
                self.assertEqual(len(tail), 3)
                self.assertIn("ETAPA_1", tail[0])
                self.assertIn("ETAPA_2", tail[1])
                self.assertIn("ETAPA_3", tail[2])

    def test_read_tail_returns_last_stage(self):
        """(c) read_tail devolve a ultima etapa."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with patch("logis.core.downloader.cache_dir", return_value=tmp_path):
                for i in range(35):
                    mark(f"ETAPA_{i}", f"detalhe_{i}")

                tail = read_tail(5)
                self.assertEqual(len(tail), 5)
                self.assertIn("ETAPA_34", tail[-1])
                self.assertIn("detalhe_34", tail[-1])
                self.assertIn("ETAPA_30", tail[0])

    def test_write_failure_does_not_raise(self):
        """(d) falha de escrita (diretorio inexistente) nao levanta."""
        with patch("logis.core.crashlog.trace_path", return_value=Path("/diretorio_inexistente_xyz_123/diagnostico.log")):
            try:
                mark("ETAPA_FALHA", "sem_permissao")
            except Exception as e:
                self.fail(f"mark() nao deveria levantar excecao em falha de escrita: {e}")

        with patch("builtins.open", side_effect=OSError("Erro de I/O forçado")):
            try:
                mark("ETAPA_ERRO_OPEN", "detalhe")
            except Exception as e:
                self.fail(f"mark() nao deveria levantar excecao em erro de open: {e}")

    def test_reset_truncates_log(self):
        """reset limpa/trunca o arquivo de diagnostico."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with patch("logis.core.downloader.cache_dir", return_value=tmp_path):
                mark("ETAPA_TESTE", "detalhe")
                self.assertEqual(len(read_tail(10)), 1)
                reset()
                self.assertEqual(len(read_tail(10)), 0)

    def test_trace_path_fallback(self):
        """trace_path usa fallback quando downloader.cache_dir falha."""
        with patch("logis.core.downloader.cache_dir", side_effect=Exception("Sem QGIS")):
            path = trace_path()
            self.assertEqual(path, Path.home() / ".cache" / "logis" / "diagnostico.log")


if __name__ == "__main__":
    unittest.main()
