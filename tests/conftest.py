# -*- coding: utf-8 -*-
"""Configuração comum da suíte de testes do logis.

Os testes importam `logis.*` como se a raiz do repositório estivesse no
`sys.path` (é o pacote do plugin, não instalado via pip). Antes, os arquivos
viviam na raiz e isso funcionava por acaso; movidos para `tests/`, é preciso
inserir explicitamente o pai deste diretório (a raiz do repo) no `sys.path`
para que `import logis` continue resolvendo, de qualquer `cwd`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
