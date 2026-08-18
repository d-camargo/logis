# Guia de Desenvolvimento

Este guia documenta a estrutura do repositório **logis**, os comandos de automação do `Makefile`, como executar a suíte de testes, as regras de compatibilidade para QGIS 4 / Qt6, o papel dos scripts utilitários em `tools/` e a instrução para servidor e build local da documentação.

---

## 1. Estrutura do Repositório

A organização do código fonte e dos artefatos do projeto é dividida da seguinte forma:

```
logis/
├── logis/                    # Código-fonte do plugin QGIS
│   ├── __init__.py           # Entrada do plugin (instancia LogisPlugin)
│   ├── logis_plugin.py       # Gerenciador da interface, menus e dock panels
│   ├── provider.py           # Processing Provider "logis"
│   ├── metadata.txt          # Metadados do plugin QGIS
│   ├── core/                 # Núcleo de lógica de negócios e algoritmos puros
│   │   ├── network/          # Pipelines de rede (osm_pipeline, snv_pipeline, graph_builder, od_matrix)
│   │   ├── connectors/       # Conectores HTTP/WFS/REST (osm, wfs, arcgis_rest)
│   │   ├── indicators/       # Indicadores (urban, regional, waste)
│   │   ├── routing/          # Algoritmos de roteirização (vrp, arc_routing)
│   │   ├── location/         # Otimização de localização de instalações (facility)
│   │   ├── downloader.py     # Cache em disco e gerenciador de downloads
│   │   ├── sources.py        # Registro declarativo de fontes de dados
│   │   └── qgis_compat.py    # Camada de compatibilidade Qt5/Qt6 e QGIS 3/4
│   ├── algorithms/           # Algoritmos do QGIS Processing (logis:*)
│   ├── gui/                  # Painéis de interface (dock panels) por módulo
│   └── i18n/                 # Arquivos de internacionalização (.ts e .qm)
├── tools/                    # Scripts de teste headless e validação em desenvolvimento
├── docs/                     # Documentação do projeto (MkDocs)
├── dist/                     # Pacotes zip gerados para distribuição
├── Makefile                  # Tarefas de automação de desenvolvimento
└── mkdocs.yml                # Configuração do site de documentação
```

---

## 2. Alvos do Makefile

O `Makefile` centraliza os comandos de desenvolvimento, instalação local no QGIS e empacotamento:

| Alvo | Descrição |
|---|---|
| `help` | Exibe o resumo dos alvos disponíveis no `Makefile`. |
| `deploy` | Cria um symlink do plugin no perfil default do QGIS 3 do sistema (`~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/logis`). |
| `deploy-flatpak` | Cria um symlink no perfil default da instalação Flatpak do QGIS 3 (`~/.var/app/org.qgis.qgis/data/QGIS/QGIS3/profiles/default/python/plugins/logis`). |
| `undeploy` | Remove o symlink instalado no perfil QGIS3 do sistema. |
| `undeploy-flatpak` | Remove o symlink instalado no perfil Flatpak do QGIS3. |
| `clean` | Limpa diretórios `__pycache__` e arquivos compilados `.pyc`. |
| `test` | Executa o *smoke test* estático de verificação de sintaxe Python sem exigir interface gráfica do QGIS. |
| `package` | Gera o pacote zip de distribuição do plugin em `dist/logis-<versão>.zip` via `qgis-plugin-ci`. |
| `i18n` | Extrai as strings marcadas com `self.tr(...)` para o arquivo de tradução `logis/i18n/logis_pt_BR.ts`. |
| `transcompile` | Compila os arquivos de tradução `.ts` do Qt para binários `.qm` usando `lrelease`. |
| `docs-deps` | Cria o ambiente virtual `.venv-docs` e instala as dependências de documentação de `docs/requirements.txt`. |
| `docs-serve` | Sobe o servidor local de documentação (`mkdocs serve`), em `http://127.0.0.1:8000`. |
| `docs-build` | Compila o site de documentação em modo estrito (`mkdocs build --strict`). |

---

## 3. Como Rodar os Testes

O projeto utiliza duas estratégias complementares para validação e testes:

### Smoke Test de Sintaxe
Para checar rapidamente a sintaxe Python de todos os arquivos do projeto sem dependência de ambiente QGIS rodando:
```bash
make test
```

### Suíte de Testes Unitários e de Integração
Para rodar a suíte completa de testes unitários com o `pytest`:
```bash
python3 -m pytest -q
```

---

## 4. Regras de Compatibilidade Qt6 / QGIS 4

Para garantir que o **logis** seja totalmente compatível tanto com o QGIS 3 (Qt5/PyQt5) quanto com o futuro QGIS 4 (Qt6/PyQt6), todo o código deve seguir rigorosamente as três regras abaixo:

### 1. Enums Escopados (*Scoped Enums*)
O PyQt6 removeu os enums não escopados. Sempre acesse os enums utilizando o namespace completo da classe:

- `Qt.DockWidgetArea.RightDockWidgetArea` (nunca `Qt.RightDockWidgetArea`)
- `QgsProcessing.SourceType.TypeVectorLine` (nunca `QgsProcessing.TypeVectorLine`)
- `QgsProcessingParameterNumber.Type.Double` (nunca `QgsProcessingParameterNumber.Double`)
- `QgsWkbTypes.Type.LineString` / `QgsWkbTypes.GeometryType.Line` (nunca `QgsWkbTypes.LineString`)
- `QgsTask.Flag.CanCancel` (nunca `QgsTask.CanCancel`)

### 2. Tipos de Campo via `field_type()`
Em Qt6, a enumeração `QVariant.Type` foi substituída por `QMetaType.Type`. Para evitar quebras ao instanciar campos de vetores (`QgsField`), utilize **apenas** a função auxiliar compatível do projeto:

```python
from logis.core.qgis_compat import field_type
from qgis.PyQt.QtCore import QVariant

# Forma correta e agnóstica entre Qt5 e Qt6:
field = QgsField("nome", field_type(QVariant.String))
```

### 3. Proibição de `exec_()`
O método `exec_()` com underline legado do PyQt4/PyQt5 foi totalmente removido no PyQt6. Use exclusivamente `exec()` em caixas de diálogo (`QDialog`) e modais:

```python
# Correto:
dialog.exec()

# Proibido:
dialog.exec_()
```

Para verificar se o seu ambiente atende às regras de compatibilidade, você pode rodar o utilitário `tools/qgis4_compat_check.py`.

---

## 5. Scripts de Utilidade (`tools/`)

Os scripts localizados em `tools/` apoiam o desenvolvimento e a validação *headless* fora do ambiente GUI do QGIS:

- **`tools/pilot_urbano_mg.py`**: Piloto *headless* ponta-a-ponta do Módulo Urbano (Fase F1). Encadeia a extração e tratamento OSM (`osm_pipeline`), a montagem do grafo (`graph_builder`) e o cálculo de matriz OD (`od_matrix`) para o município de Serra da Saudade/MG (`code_muni=3166600`).
- **`tools/pilot_regional_mg.py`**: Piloto *headless* ponta-a-ponta do Módulo Regional (Fase F3). Encadeia o download e corte da malha SNV (`snv_pipeline`), montagem do grafo regional (`graph_builder`) e matriz OD (`od_matrix`) para o estado de Minas Gerais.
- **`tools/qgis4_compat_check.py`**: Script de inspeção de compatibilidade entre QGIS 4 / Qt6 e QGIS 3 / Qt5. Relata a presença e suporte dos enums escopados, suporte a `QMetaType` em `QgsField` e suporte ao método `.exec()`.
- **`tools/verify_delivery_distance.py`**: Script de validação *headless* para o algoritmo `logis:urban_delivery_distance`. Carrega os dados da rede piloto, cria camadas em memória de depósitos e zonas e valida se as métricas de distância e tempo são calculadas corretamente pelo Processing Provider.

---

## 6. Como Rodar o Site Localmente

A documentação do **logis** é construída com o [MkDocs](https://www.mkdocs.org/) e o tema [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

### Configuração e Servidor Local

Os alvos do `Makefile` cuidam do ambiente virtual de documentação, que fica isolado do plugin:

```bash
make docs-deps   # cria .venv-docs e instala docs/requirements.txt
make docs-serve  # sobe o servidor em http://127.0.0.1:8000
```

`docs-serve` já depende de `docs-deps` (roda antes automaticamente), e as dependências do site (MkDocs, Material etc.) vivem só no `.venv-docs` — nunca entram no ambiente do plugin QGIS.

### Verificação Estrita antes do Commit

Antes de submeter modificações na documentação, execute:

```bash
make docs-build
```

Esse alvo roda `mkdocs build --strict` com o bloco `validation:` do `mkdocs.yml` ativo, de modo que página órfã (fora da `nav`), link quebrado ou âncora quebrada derrubam o build.
