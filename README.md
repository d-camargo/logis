# logis

Complemento (plugin) do QGIS para apoiar projetos de logística no Brasil.

**Versão:** 0.1.2 (`experimental`)  
**Licença:** GPL-3.0  
**Idioma:** **Português** | [English](#english)

---

## Português

O **logis** é um plugin para o QGIS desenvolvido para apoiar projetos e análises de logística no Brasil, atuando em três módulos estratégicos: **Logística Urbana**, **Logística Regional** e **Logística Especializada** (com foco inicial em coleta de resíduos sólidos urbanos).

### Visão Geral

O plugin está estruturado em três módulos operacionais e três níveis de capacidade:

| Módulo | Escopo | Rede Base |
|---|---|---|
| **Logística Urbana** | Cidade / Município | Rede viária OSM tratada (pipeline derivado do GisBR) |
| **Logística Regional** | Estado / País | Bases nacionais (DNIT/SNV, geobr) + bases estaduais (ex: IDE-Sisema/MG) |
| **Logística Especializada** | Serviços urbanos com roteirização por arcos | Coleta de lixo sobre a rede urbana |

Para cada módulo, o plugin disponibiliza:
1. **Indicadores** — Métricas calculadas sobre a rede e dados demográficos/econômicos.
2. **Roteirização** — Algoritmos de VRP/TSP (por nós) e Arc Routing (por arestas).
3. **Localização de Instalações (*Facility Location*)** — Heurísticas para p-mediana, p-centro, cobertura máxima (MCLP) e cobertura de conjuntos (LSCP).

### Restrição Técnica Fundamental

O plugin adota a filosofia de **zero dependências externas obrigatórias**:
- **PyQGIS nativo + stdlib do Python:** Todo cálculo de rede, grafos e caminhos mínimos é realizado através das classes nativas do QGIS (`QgsGraph`, `QgsGraphBuilder`, `QgsGraphAnalyzer`) e de algoritmos do Processing (`native:` e `qgis:`).
- **Sem networkx/OSMnx:** Heurísticas clássicas (savings de Clarke-Wright, sweep, 2-opt, Teitz-Bart, matching euleriano) implementadas em Python puro.
- **Dependências Opcionais:**
  - `pyarrow`: Fallback para leitura de arquivos no formato Parquet quando o driver GDAL Parquet não estiver disponível no sistema.
  - `OR-Tools`: Backend opcional para otimização avançada, com importação *lazy* e fallback automático para as heurísticas em Python puro.
- **Referencial Espacial:** Todos os dados são processados e entregues em SIRGAS 2000 / EPSG:4674, utilizando CRS métrico (UTM) apenas para computações intermediárias de distância e tempo.

### Algoritmos de Processamento (12 registrados)

O plugin atua como um **Processing Provider** (`logis`), expondo os seguintes algoritmos na Caixa de Ferramentas do QGIS:

#### Módulo Urbano
- `logis:urban_network_density` — Densidade viária urbana.
- `logis:urban_network_connectivity` — Conectividade de rede viária urbana (índices α, β, γ).
- `logis:urban_mean_circuity` — Circuidade média da malha viária urbana.
- `logis:urban_cargo_restriction` — Índice de restrição de circulação de veículos de carga.
- `logis:urban_demand_density` — Densidade de demanda urbana por área/setor.
- `logis:urban_gravity_accessibility` — Acessibilidade gravitacional a pontos de interesse/atratores.
- `logis:urban_edge_betweenness` — Centralidade de intermediação de arestas (*edge betweenness*) por amostragem.
- `logis:urban_delivery_distance` — Distância e custo médio de entrega ao depósito mais próximo.

#### Módulo Regional
- `logis:regional_network_density` — Densidade de rede rodoviária regional por estado/região.
- `logis:regional_pavement_percentage` — Percentual de pavimentação da malha rodoviária.
- `logis:regional_critical_links` — Identificação de arcos e conexões críticas na rede regional (*cut links*).

#### Módulo Especializado — Coleta de Lixo
- `logis:waste_districting` — Setorização: particiona a rede viária em setores de coleta contíguos e balanceados por carga (sementes farthest-first + crescimento de regiões + troca de trechos de fronteira).
- `logis:waste_deadhead_ratio` — Razão de Deadhead: extensão produtiva (coleta) vs. improdutiva (deadhead/conector) e a razão deadhead_km / productive_km, por rota e no total.

### Interface com Usuário (GUI)

- **Painel de Logística Urbana** (`gui/urban_dock.py`): Interface dock interativa para configuração de parâmetros e execução de diagnósticos urbanos.
- **Painel de Logística Regional** (`gui/regional_dock.py`): Interface dock dedicada a análises de redes rodoviárias estaduais e nacionais.
- **Diálogo de Dependências** (`gui/dependencies_dialog.py`): Verificação e diagnóstico visual de pacotes opcionais (`OR-Tools`, `pyarrow`).

### Estrutura do Repositório

```
logis/
├── __init__.py               # Ponto de entrada do plugin
├── logis_plugin.py           # Registrador de GUI e Provider
├── provider.py               # Processing Provider "logis" (11 algoritmos)
├── metadata.txt              # Metadados do plugin QGIS (versão 0.1.2)
├── Makefile                  # Comandos de deploy e testes de sintaxe
├── core/                     # Núcleo de lógica técnica
│   ├── network/              # Pipelines OSM/SNV, construtor de grafos e matriz OD
│   ├── connectors/           # Conectores Overpass OSM e WFS
│   ├── indicators/           # Cálculo de indicadores urbanos e regionais
│   ├── downloader.py         # Downloader com cache e suporte a mirrors
│   ├── sources.py            # Fontes de dados declarativas (nacionais/estaduais)
│   ├── qgis_compat.py        # Compatibilidade PyQGIS
│   ├── data_backend.py       # Tratamento de backends de dados
│   └── optim_backend.py      # Gerenciamento de otimizadores (OR-Tools / Python puro)
├── algorithms/               # Algoritmos expostos no Processing (8 urbanos + 3 regionais)
├── gui/                      # Painéis dock e diálogos de interface
└── docs/                     # Scripts de teste e especificações
```

### Requisitos e Instalação (Desenvolvimento)

- **Requisitos:** QGIS 3.16 ou superior.
- **Ambiente Validado:** O plugin foi testado pelo autor no **QGIS 4.2 "Belém do Pará" sobre Ubuntu**, e a instalação do OR-Tools pelo diálogo "Dependências" (comando com as travas `pandas<3`, `numpy<2`, `typing_extensions==4.10.0`) foi validada nesse ambiente.
- **Instalação para Desenvolvimento:**
  ```bash
  cd ~/projects/logis/
  make deploy        # Cria link simbólico para o diretório de plugins do QGIS
  ```
- **Execução dos Testes:**
  ```bash
  make test          # Validação rápida de sintaxe em todos os arquivos .py
  ```
- **Verificação de Compatibilidade QGIS 4 / Qt6:** Execute `python3 docs/qgis4_compat_check.py` (ou cole o conteúdo no Console Python do QGIS) para validar versões e a presença de símbolos legados/escopados.

### Uso no Console Python do QGIS

Exemplo de chamada de algoritmo de processamento via console:

```python
import processing

# Calcular densidade de rede viária urbana
processing.run("logis:urban_network_density", {
    "INPUT_NETWORK": "caminho/para/rede_urbana.gpkg",
    "OUTPUT": "memory:"
})
```

### Licença e Contexto

- **Licença:** [GPL-3.0](LICENSE)
- **Autor:** Diego Camargo (<diegocamargo.bft@gmail.com>)
- **Documentação Detalhada:** Para especificações de arquitetura, decisões técnicas e roadmap por fases (F1-F7), consulte o arquivo [`CLAUDE.md`](CLAUDE.md).

## English

**logis** is a QGIS plugin developed to support logistics projects and analyses in Brazil, operating across three strategic modules: **Urban Logistics**, **Regional Logistics**, and **Specialized Logistics** (with an initial focus on municipal solid waste collection).

### Overview

The plugin is structured into three operational modules and three capability tiers:

| Module | Scope | Base Network |
|---|---|---|
| **Urban Logistics** | City / Municipality | Processed OSM road network (pipeline derived from GisBR) |
| **Regional Logistics** | State / Country | National databases (DNIT/SNV, geobr) + state databases (e.g., IDE-Sisema/MG) |
| **Specialized Logistics** | Urban services with arc routing | Solid waste collection over the urban network |

For each module, the plugin provides:
1. **Indicators** — Metrics calculated over the network and demographic/economic data.
2. **Routing** — VRP/TSP algorithms (node-based) and Arc Routing (edge-based).
3. **Facility Location** — Heuristics for p-median, p-center, Maximum Coverage (MCLP), and Set Covering (LSCP).

### Fundamental Technical Constraint

The plugin adopts a **zero mandatory external dependencies** philosophy:
- **Native PyQGIS + Python stdlib:** All network, graph, and shortest-path computations are performed using native QGIS classes (`QgsGraph`, `QgsGraphBuilder`, `QgsGraphAnalyzer`) and Processing algorithms (`native:` and `qgis:`).
- **No networkx/OSMnx:** Classic heuristics (Clarke-Wright savings, sweep, 2-opt, Teitz-Bart, Eulerian matching) implemented in pure Python.
- **Optional Dependencies:**
  - `pyarrow`: Fallback for reading Parquet format files when the GDAL Parquet driver is unavailable on the system.
  - `OR-Tools`: Optional backend for advanced optimization, with *lazy* import and automatic fallback to pure Python heuristics.
- **Spatial Reference System:** All data is processed and delivered in SIRGAS 2000 / EPSG:4674, using a metric CRS (UTM) only for intermediate distance and time calculations.

### Processing Algorithms (12 registered)

The plugin acts as a **Processing Provider** (`logis`), exposing the following algorithms in the QGIS Processing Toolbox:

#### Urban Module
- `logis:urban_network_density` — Urban road network density.
- `logis:urban_network_connectivity` — Urban road network connectivity (α, β, γ indices).
- `logis:urban_mean_circuity` — Average circuity of the urban road network.
- `logis:urban_cargo_restriction` — Freight vehicle circulation restriction index.
- `logis:urban_demand_density` — Urban demand density by area/zone.
- `logis:urban_gravity_accessibility` — Gravitational accessibility to points of interest/attractors.
- `logis:urban_edge_betweenness` — Edge betweenness centrality by sampling.
- `logis:urban_delivery_distance` — Average delivery distance and cost to the nearest depot.

#### Regional Module
- `logis:regional_network_density` — Regional road network density by state/region.
- `logis:regional_pavement_percentage` — Pavement percentage of the road network.
- `logis:regional_critical_links` — Identification of critical arcs and connections in the regional network (*cut links*).

#### Specialized Module — Waste Collection
- `logis:waste_districting` — Districting: partitions the road network into contiguous, load-balanced collection sectors (farthest-first seeds + region growing + boundary edge swapping).
- `logis:waste_deadhead_ratio` — Deadhead Ratio: productive (collection) vs. unproductive (deadhead/connector) distance and the deadhead_km / productive_km ratio, per route and overall.

### User Interface (GUI)

- **Urban Logistics Panel** (`gui/urban_dock.py`): Interactive dock interface for parameter configuration and urban diagnostics execution.
- **Regional Logistics Panel** (`gui/regional_dock.py`): Dedicated dock interface for state and national road network analyses.
- **Dependencies Dialog** (`gui/dependencies_dialog.py`): Visual check and diagnostics of optional packages (`OR-Tools`, `pyarrow`).

### Repository Structure

```
logis/
├── __init__.py               # Plugin entry point
├── logis_plugin.py           # GUI and Provider registrar
├── provider.py               # Processing Provider "logis" (11 algorithms)
├── metadata.txt              # QGIS plugin metadata (version 0.1.2)
├── Makefile                  # Deployment and syntax testing commands
├── core/                     # Technical logic core
│   ├── network/              # OSM/SNV pipelines, graph builder, and OD matrix
│   ├── connectors/           # Overpass OSM and WFS connectors
│   ├── indicators/           # Urban and regional indicators calculation
│   ├── downloader.py         # Downloader with caching and mirror support
│   ├── sources.py            # Declarative data sources (national/state)
│   ├── qgis_compat.py        # PyQGIS compatibility
│   ├── data_backend.py       # Data backend handling
│   └── optim_backend.py      # Optimizer management (OR-Tools / Pure Python)
├── algorithms/               # Algorithms exposed in Processing (8 urban + 3 regional)
├── gui/                      # Dock panels and interface dialogs
└── docs/                     # Test scripts and specifications
```

### Requirements and Installation (Development)

- **Requirements:** QGIS 3.16 or higher.
- **Validated Environment:** The plugin was tested by the author on **QGIS 4.2 "Belém do Pará" on Ubuntu**, and the OR-Tools installation via the "Dependencies" dialog (command with constraints `pandas<3`, `numpy<2`, `typing_extensions==4.10.0`) was validated in this environment.
- **Development Installation:**
  ```bash
  cd ~/projects/logis/
  make deploy        # Creates a symbolic link to the QGIS plugins directory
  ```
- **Running Tests:**
  ```bash
  make test          # Quick syntax validation across all .py files
  ```
- **QGIS 4 / Qt6 Compatibility Check:** Run `python3 docs/qgis4_compat_check.py` (or paste its content into the QGIS Python Console) to inspect Qt6/QGIS 4 version details and legacy/scoped symbols.

### Usage in QGIS Python Console

Example calling a processing algorithm via console:

```python
import processing

# Calculate urban road network density
processing.run("logis:urban_network_density", {
    "INPUT_NETWORK": "path/to/urban_network.gpkg",
    "OUTPUT": "memory:"
})
```

### License and Context

- **License:** [GPL-3.0](LICENSE)
- **Author:** Diego Camargo (<diegocamargo.bft@gmail.com>)
- **Detailed Documentation:** For architecture specifications, technical decisions, and roadmap by phases (F1-F7), see the [`CLAUDE.md`](CLAUDE.md) file.
