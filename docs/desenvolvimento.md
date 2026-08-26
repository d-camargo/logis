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
Para rodar a suíte completa de testes unitários com o `pytest`, em ambiente com sessão gráfica:
```bash
python3 -m pytest -q
```

!!! warning "Ambiente sem display (headless)"
    Em servidor/VPS ou CI sem X11, o comando cru **derruba o processo com falha de
    segmentação do Qt**. É preciso forçar a plataforma offscreen antes de rodar o
    `pytest`:
    ```bash
    QT_QPA_PLATFORM=offscreen python3 -m pytest -q
    ```
    Resultado esperado, medido em 2026-08-22 nesta VPS: **240 testes passando + 9
    subtests, em ~22 s**.

---

## 4. Regras de Compatibilidade e Segurança

Para garantir que o **logis** seja totalmente compatível tanto com o QGIS 3 (Qt5/PyQt5) quanto com o futuro QGIS 4 (Qt6/PyQt6) — e que o pacote passe no analisador estático do `plugins.qgis.org` — todo o código deve seguir rigorosamente as cinco regras abaixo. As três primeiras são de compatibilidade e são verificadas por `test_qt6_compat.py`; as duas últimas são de segurança e são verificadas por `test_security_scan.py`.

### 1. Enums Escopados (*Scoped Enums*)
O PyQt6 removeu os enums não escopados. Sempre acesse os enums utilizando o namespace completo da classe:

- `Qt.DockWidgetArea.RightDockWidgetArea` (nunca `Qt.RightDockWidgetArea`)
- `QgsProcessing.SourceType.TypeVectorLine` (nunca `QgsProcessing.TypeVectorLine`)
- `QgsProcessingParameterNumber.Type.Double` (nunca `QgsProcessingParameterNumber.Double`)
- `QgsWkbTypes.Type.LineString` / `QgsWkbTypes.GeometryType.Line` (nunca `QgsWkbTypes.LineString`)
- `QgsTask.Flag.CanCancel` (nunca `QgsTask.CanCancel`)
- `QgsFeatureSink.Flag.FastInsert` (nunca `QgsFeatureSink.FastInsert`)
- `QgsProcessingParameterField.DataType.Numeric` (nunca `QgsProcessingParameterField.Numeric`)
- `QgsVectorLayerDirector.Direction.DirectionBoth` (nunca `QgsVectorLayerDirector.DirectionBoth`)
- `QNetworkReply.NetworkError.NoError` (nunca `QNetworkReply.NoError`)

Em PyQt5, a forma antiga e a forma escopada escrevem o mesmo inteiro — o código funciona e ninguém percebe a diferença. Por isso essa lista não vive apenas nesta documentação: ela é verificada estaticamente por `test_qt6_compat.py`, que reprova qualquer forma desescopada (o QGIS 4/PyQt6 faria o código falhar em runtime).

### 2. Tipos de Campo via `field_type()`
Em Qt6, a enumeração `QVariant.Type` foi substituída por `QMetaType.Type`. Para evitar quebras ao instanciar campos de vetores (`QgsField`), utilize **apenas** a função auxiliar compatível do projeto:

```python
from logis.core.qgis_compat import field_type
from qgis.PyQt.QtCore import QVariant

# Forma correta e agnóstica entre Qt5 e Qt6:
field = QgsField("nome", field_type(QVariant.String))
```

### 3. Proibição de `exec_()` e de `exec()`
O método `exec_()` com underline legado do PyQt4/PyQt5 foi totalmente removido no PyQt6. Mas o substituto `exec()` **também é proibido** no logis: ele abre o diálogo de forma modal (bloqueando o laço de eventos do QGIS) e tem o mesmo nome da função *built-in* `exec` do Python, que o analisador estático Bandit sinaliza como **B102** (`exec_used`). Em vez de silenciar o aviso com `# nosec`, os diálogos do plugin são exibidos de forma não modal com `.show()`:

```python
# Correto:
dialog.show()

# Proibido:
dialog.exec()
dialog.exec_()
```

Diálogos não modais continuam vivos depois de `show()`, então quem os cria é responsável por fechá-los e liberar a referência no `unload()` do plugin (ver `LogisPlugin.unload` em `logis/logis_plugin.py`). A regra é verificada automaticamente por `test_security_scan.py`, que falha se qualquer arquivo sob `logis/` contiver `exec()`, `.exec()` ou `.exec_()`.

Para verificar se o seu ambiente atende às regras de compatibilidade, você pode rodar o utilitário `tools/qgis4_compat_check.py`.

### 4. Amostragem e Hash
O gerador `random` da biblioteca padrão e os hashes `hashlib.md5()` / `hashlib.sha1()` não
entram no pacote. O scanner do `plugins.qgis.org` os sinaliza como **B311**
(*pseudo-random generators*) e **B324** (*hash inseguro*) e **ignora comentários
`# nosec`**, o que reprova o pacote na publicação. Para amostragem (por exemplo, a de
pares OD do cálculo de *betweenness*), use o gerador determinístico do próprio plugin;
para chave de cache, use `hashlib.sha256()`:

```python
from logis.core.sampling import DeterministicRandom

rng = DeterministicRandom(seed=42)
amostra = rng.sample(nos, 100)
```

`DeterministicRandom` implementa SplitMix64 em Python puro (`randrange`, `shuffle`,
`sample`) e é **determinístico por construção** — mesma semente, mesmo resultado, o que
também torna os indicadores reprodutíveis entre execuções. Ele **não é
criptograficamente seguro**: nunca o utilize para segredos, tokens, chaves ou senhas.

### 5. Subprocessos
O plugin **não executa nenhum processo externo**: `subprocess` é proibido em qualquer
arquivo sob `logis/`, e `shell=True` é proibido em qualquer lugar do repositório. A
proibição elimina o achado **B603** (*subprocesso com entrada não confiável*) do scanner
do `plugins.qgis.org`, que ignora comentários `# nosec`.

A consequência prática está no instalador opcional do OR-Tools: em vez de rodar o `pip`,
`logis/core/ortools_installer.py` apenas **monta e exibe** o comando, e quem o executa é
o usuário, no console do ambiente Python do QGIS (ver
[Instalação do OR-Tools](ortools.md)). `build_command()` devolve a lista de argumentos a
partir de literais, de `sys.executable` e das versões detectadas por
`installed_versions()`; `command_text()` transforma essa lista na linha pronta para
cópia, entre aspas quando o token contém espaço.

Versão lida de metadados de terceiros continua validada por expressão regular — a que
não casar com `^[A-Za-z0-9][A-Za-z0-9._+!-]*$` é descartada, para que uma string
começando com `-` nunca vire flag do `pip` no comando mostrado ao usuário.

Para rodar apenas as guardas de segurança:

```bash
python3 -m pytest -q test_security_scan.py
```

O `test_security_scan.py` cobre ainda os invariantes herdados das rodadas anteriores —
proibição de `pickle`, de `except`/`pass` silencioso e de bypass de verificação SSL
(`PeerVerifyMode` + `VerifyNone`). A lista completa está na §9 do `GEMINI.md`.

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
