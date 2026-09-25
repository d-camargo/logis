# logis

Complemento (plugin) do QGIS para apoiar projetos de logística no Brasil.

**Versão:** consulte [`logis/metadata.txt`](logis/metadata.txt); histórico completo no [changelog](docs/changelog.md).  
**Licença:** GPL-3.0  
**Idioma:** **Português** | [English](#english)

---

## Português

📖 Documentação: https://logis.dcamargo.com.br

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

### Algoritmos de Processamento (28 registrados)

O plugin atua como um **Processing Provider** (`logis`), expondo os seguintes algoritmos na Caixa de Ferramentas do QGIS, agrupados exatamente como aparecem lá (grupo/`displayName()` de cada algoritmo em `logis/provider.py`):

#### Dados
- `logis:load_osm_network` — Baixar rede viária urbana (OSM, município): baixa e processa a rede viária urbana de um município a partir do OpenStreetMap.
- `logis:load_snv_network` — Baixar rede viária federal (SNV/DNIT, UF): baixa e processa a rede viária federal de uma UF a partir dos dados do SNV/DNIT.

#### Indicadores Urbanos
- `logis:urban_network_density` — Densidade de Rede Viária Urbana.
- `logis:urban_network_connectivity` — Conectividade de Rede Viária Urbana (índices α, β, γ).
- `logis:urban_mean_circuity` — Circuidade Média de Rede Viária Urbana.
- `logis:urban_cargo_restriction` — Índice de Restrição de Circulação de Carga.
- `logis:urban_demand_density` — Densidade de Demanda Urbana por área/setor.
- `logis:urban_gravity_accessibility` — Acessibilidade Gravitacional Urbana a pontos de interesse/atratores.
- `logis:urban_edge_betweenness` — Centralidade de Intermediação de Arestas (Betweenness) por amostragem.
- `logis:urban_delivery_distance` — Distância de Entrega Urbana e custo médio ao depósito mais próximo.

#### Indicadores Regionais
- `logis:regional_network_density` — Densidade da Malha Rodoviária Regional por estado/região.
- `logis:regional_pavement_percentage` — Percentual de Pavimentação e Duplicação da malha rodoviária.
- `logis:regional_critical_links` — Pontes/Arcos Críticos da Malha Regional (*cut links*).

#### Localização de Instalações
- `logis:facility_p_median` — Localização p-Mediana (Teitz-Bart): minimiza o custo/distância total ponderado de deslocamento da demanda às instalações.
- `logis:facility_mclp` — Localização de Cobertura Máxima (MCLP): maximiza a demanda coberta dentro do raio limite com k instalações.
- `logis:facility_lscp` — Localização de Cobertura de Conjuntos (LSCP): minimiza o número de instalações para cobrir 100% da demanda.

#### Roteirização
- `logis:vrp_tsp` — Caixeiro Viajante (TSP): sequenciamento otimizado de visitas a pontos por um único veículo.
- `logis:vrp_cvrp` — Roteirização de Veículos Capacitados (CVRP): rotas otimizadas com restrição de capacidade a partir de um depósito.

#### Logística Especializada — Coleta de Lixo
- `logis:waste_generation_estimate` — Estimativa de Geração de Resíduos Sólidos: estima a geração diária e semanal por trecho de via.
- `logis:waste_districting` — Setorização de Coleta de Resíduos (Districting): particiona a rede viária em setores de coleta contíguos e balanceados por carga (sementes farthest-first + crescimento de regiões + troca de trechos de fronteira).
- `logis:waste_cpp_route` — Roteirização por Arcos (CPP): percurso euleriano de menor custo percorrendo todas as vias da rede (Chinese Postman Problem).
- `logis:waste_rpp_route` — Roteirização por Arcos (RPP): percurso otimizado cobrindo apenas o subconjunto de vias com coleta ativa (Rural Postman Problem).
- `logis:waste_carp_route` — Roteirização por Arcos Capacitada (CARP): rotas de veículos capacitados para coleta por arcos (Capacitated Arc Routing Problem).
- `logis:waste_fleet_sizing` — Dimensionamento de Frota de Coleta: calcula o número de caminhões coletores segundo volume de resíduos, turnos e capacidade nominal.
- `logis:waste_deadhead_ratio` — Razão de Deadhead por Rota: extensão produtiva (coleta) vs. improdutiva (deadhead/conector) e a razão deadhead_km / productive_km, por rota e no total.
- `logis:waste_sector_balance` — Equilíbrio entre Setores/Rotas de Coleta: métricas de variância, amplitude e desvio de carga e extensão entre setores.
- `logis:waste_destination_distance` — Distância ao Destino de Resíduos: distância e tempo de deslocamento ao aterro sanitário ou ponto de destino mais próximo.
- `logis:waste_collection_coverage` — Cobertura da Coleta de Resíduos por Setor: extensão de via exigida vs. coberta e percentual de atendimento por setor.

### Interface com Usuário (GUI)

- **Painel de Rede Viária** (`gui/network_dock.py`): Interface dock em duas abas — Município (OSM) e Estado (SNV/DNIT) —, baixa arcos e nós direto para o projeto, com barra de progresso do download.
- **Painel de Logística Urbana** (`gui/urban_dock.py`): Interface dock interativa em três abas — Rede, Demanda e Carga —, com o seletor de rede viária e o painel de resultados compartilhados fora das abas. A restrição de circulação de carga tem botão e campo de expressão próprios na aba Carga, executada de forma independente do pacote de indicadores de rede. A centralidade de intermediação (aba Rede) aceita uma semente opcional de amostragem, para tornar o resultado reproduzível entre execuções.
- **Painel de Logística Regional** (`gui/regional_dock.py`): Interface dock dedicada a análises de redes rodoviárias estaduais e nacionais.
- **Painel de Roteirização** (`gui/routing_dock.py`): Interface dock em duas abas — TSP e CVRP —, com seletor de rede viária compartilhado e painel de resultados único no rodapé.
- **Painel de Coleta de Lixo** (`gui/waste_dock.py`): Interface dock em quatro abas — Geração (estimativa de geração + setorização), Roteirização (CPP, RPP, CARP), Frota (dimensionamento) e Indicadores (deadhead ratio, equilíbrio entre setores, distância ao destino, cobertura por frequência) —, com rolagem por aba e painel de resultados único no rodapé, fora das abas.
- **Diálogo de Dependências** (`gui/dependencies_dialog.py`): Detecção do ambiente (SO, Python, interpretador, pip) e instalação do `OR-Tools` em um clique no Python do próprio QGIS, sem executar processo externo, mantendo o comando manual como alternativa.
- **Documentação**: Item de menu (`Complementos → logis → Documentação`) que abre o site da documentação oficial no navegador padrão.

### Estrutura do Repositório

```
logis/
├── logis/                    # Código-fonte do plugin QGIS
│   ├── __init__.py           # Ponto de entrada do plugin
│   ├── logis_plugin.py       # Registrador de GUI e Provider
│   ├── provider.py           # Processing Provider "logis" (28 algoritmos)
│   ├── metadata.txt          # Metadados do plugin QGIS (versão atual)
│   ├── core/                 # Núcleo de lógica técnica
│   │   ├── network/          # Pipelines OSM/SNV, construtor de grafos e matriz OD
│   │   ├── connectors/       # Conectores Overpass OSM e WFS
│   │   ├── indicators/       # Indicadores urbanos, regionais e de coleta de lixo (waste.py)
│   │   ├── routing/          # VRP, arc routing e setorização
│   │   ├── location/         # Facility location (p-mediana, MCLP, LSCP)
│   │   ├── downloader.py     # Downloader com cache e suporte a mirrors
│   │   ├── sources.py        # Fontes de dados declarativas (nacionais/estaduais)
│   │   ├── qgis_compat.py    # Compatibilidade PyQGIS
│   │   ├── data_backend.py   # Tratamento de backends de dados
│   │   └── optim_backend.py  # Gerenciamento de otimizadores (OR-Tools / Python puro)
│   ├── algorithms/           # Algoritmos expostos no Processing (2 de dados + 8 urbanos + 3 regionais + 3 de localização + 2 de roteirização + 10 de coleta de lixo)
│   ├── gui/                  # Painéis dock e diálogos de interface
│   └── i18n/                 # Traduções PT-BR/EN
├── tests/                    # Suíte de testes automatizados (pytest)
├── tools/                    # Scripts de teste headless e manutenção
├── docs/                     # Documentação e especificações (MkDocs)
├── dist/                     # Pacotes zip gerados para distribuição
├── Makefile                  # Comandos de deploy, testes e empacotamento
└── mkdocs.yml                # Configuração do site de documentação
```

### Requisitos e Instalação (Desenvolvimento)

- **Requisitos:** QGIS 3.16 ou superior.
- **Ambiente Validado:** O plugin foi testado pelo autor no **QGIS 4.2 "Belém do Pará" sobre Ubuntu** (orientação de instalação do OR-Tools pelo diálogo "Dependências" fixa nas versões já instaladas no ambiente, validada). No **Windows**, o comando antigo apontava para o `qgis-bin.exe` e não funcionava, e a instalação passa a ser feita pelo botão. No **QGIS 4.2 Flatpak / Python 3.13**, a instalação do OR-Tools pode falhar por ausência de pacote binário — o plugin opera normalmente com as heurísticas em Python puro.
- **Instalação para Desenvolvimento:**
  ```bash
  cd ~/projects/logis/
  make deploy        # Cria link simbólico para o diretório de plugins do QGIS
  ```
- **Execução dos Testes:**
  ```bash
  make test          # Validação rápida de sintaxe em todos os arquivos .py
  QT_QPA_PLATFORM=offscreen python3 -m pytest -q   # Suíte completa em tests/
  ```
- **Empacotamento:** `make package` gera o pacote de distribuição em `dist/logis-<versão>.zip` via `qgis-plugin-ci`.
- **Verificação de Compatibilidade QGIS 4 / Qt6:** Execute `python3 tools/qgis4_compat_check.py` (ou cole o conteúdo no Console Python do QGIS) para validar versões e a presença de símbolos legados/escopados.
- **Documentação:** https://logis.dcamargo.com.br (endereço declarado em `homepage=` no `logis/metadata.txt`).

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

📖 Documentation: https://logis.dcamargo.com.br

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

### Processing Algorithms (28 registered)

The plugin acts as a **Processing Provider** (`logis`), exposing the following algorithms in the QGIS Processing Toolbox, grouped exactly as they appear there (group/`displayName()` of each algorithm in `logis/provider.py`):

#### Data
- `logis:load_osm_network` — Download urban road network (OSM, municipality): downloads and processes a municipality's urban road network from OpenStreetMap.
- `logis:load_snv_network` — Download federal road network (SNV/DNIT, state): downloads and processes a state's federal road network from SNV/DNIT data.

#### Urban Indicators
- `logis:urban_network_density` — Urban Road Network Density.
- `logis:urban_network_connectivity` — Urban Road Network Connectivity (α, β, γ indices).
- `logis:urban_mean_circuity` — Average Circuity of Urban Road Network.
- `logis:urban_cargo_restriction` — Freight Traffic Restriction Index.
- `logis:urban_demand_density` — Urban Demand Density by area/zone.
- `logis:urban_gravity_accessibility` — Urban Gravitational Accessibility to points of interest/attractors.
- `logis:urban_edge_betweenness` — Edge Betweenness Centrality by sampling.
- `logis:urban_delivery_distance` — Urban Delivery Distance and average cost to the nearest depot.

#### Regional Indicators
- `logis:regional_network_density` — Regional Highway Network Density by state/region.
- `logis:regional_pavement_percentage` — Paving and Dual-Carriageway Percentage of the road network.
- `logis:regional_critical_links` — Critical Bridges/Links of Regional Network (*cut links*).

#### Facility Location
- `logis:facility_p_median` — p-Median Location (Teitz-Bart): minimizes total weighted travel cost/distance from demand to facilities.
- `logis:facility_mclp` — Maximum Coverage Location (MCLP): maximizes covered demand within threshold radius with k facilities.
- `logis:facility_lscp` — Set Covering Location (LSCP): minimizes the number of facilities to cover 100% of demand.

#### Routing
- `logis:vrp_tsp` — Traveling Salesperson (TSP): optimized route to visit a list of points.
- `logis:vrp_cvrp` — Capacitated Vehicle Routing (CVRP): optimized routes with capacity constraints from a depot.

#### Specialized Logistics — Waste Collection
- `logis:waste_generation_estimate` — Solid Waste Generation Estimation: estimates daily and weekly generation per road segment.
- `logis:waste_districting` — Waste Collection Districting: partitions the road network into contiguous, load-balanced collection sectors (farthest-first seeds + region growing + boundary edge swapping).
- `logis:waste_cpp_route` — Arc Routing (CPP): minimum cost Eulerian tour traversing all network roads (Chinese Postman Problem).
- `logis:waste_rpp_route` — Arc Routing (RPP): optimized tour covering only the subset of roads with active collection (Rural Postman Problem).
- `logis:waste_carp_route` — Capacitated Arc Routing (CARP): capacity-constrained vehicle routes for arc collection (Capacitated Arc Routing Problem).
- `logis:waste_fleet_sizing` — Collection Fleet Sizing: calculates the number of collection trucks based on waste volume, shifts, and nominal capacity.
- `logis:waste_deadhead_ratio` — Deadhead Ratio by Route: productive (collection) vs. unproductive (deadhead/connector) distance and the deadhead_km / productive_km ratio, per route and overall.
- `logis:waste_sector_balance` — Balance between Collection Sectors/Routes: variance, amplitude, and deviation metrics for load and length across sectors.
- `logis:waste_destination_distance` — Distance to Waste Destination: distance and travel time to the nearest landfill or destination point.
- `logis:waste_collection_coverage` — Waste Collection Coverage by Sector: required vs. covered road length and service percentage per sector.

### User Interface (GUI)

- **Road Network Panel** (`gui/network_dock.py`): Dock interface with two tabs — Municipality (OSM) and State (SNV/DNIT) —, downloads links and nodes directly into the project, with a download progress bar.
- **Urban Logistics Panel** (`gui/urban_dock.py`): Interactive dock interface with three tabs — Network, Demand, and Cargo —, with the road network selector and the results panel shared outside the tabs. Freight vehicle circulation restriction has its own button and expression field in the Cargo tab, run independently of the network indicators batch. Betweenness centrality (Network tab) accepts an optional sampling seed to make the result reproducible across runs.
- **Regional Logistics Panel** (`gui/regional_dock.py`): Dedicated dock interface for state and national road network analyses.
- **Routing Panel** (`gui/routing_dock.py`): Dock interface with two tabs — TSP and CVRP —, with shared road network selector and single results panel at the footer.
- **Waste Collection Panel** (`gui/waste_dock.py`): Dock interface with four tabs — Generation (generation estimate + districting), Routing (CPP, RPP, CARP), Fleet (sizing), and Indicators (deadhead ratio, sector balance, waste destination distance, collection coverage) —, with tab scrolling and a single results panel at the footer, outside the tabs.
- **Dependencies Dialog** (`gui/dependencies_dialog.py`): Environment detection (OS, Python, interpreter, pip) and one-click installation of `OR-Tools` in QGIS's Python without external processes, keeping the manual command as an alternative.
- **Documentation**: Menu item (`Plugins → logis → Documentation`) opening the official documentation website in the default browser.

### Repository Structure

```
logis/
├── logis/                    # Plugin source code
│   ├── __init__.py           # Plugin entry point
│   ├── logis_plugin.py       # GUI and Provider registrar
│   ├── provider.py           # Processing Provider "logis" (28 algorithms)
│   ├── metadata.txt          # QGIS plugin metadata (current version)
│   ├── core/                 # Technical logic core
│   │   ├── network/          # OSM/SNV pipelines, graph builder, and OD matrix
│   │   ├── connectors/       # Overpass OSM and WFS connectors
│   │   ├── indicators/       # Urban, regional, and waste collection indicators (waste.py)
│   │   ├── routing/          # VRP, arc routing, and districting
│   │   ├── location/         # Facility location (p-median, MCLP, LSCP)
│   │   ├── downloader.py     # Downloader with caching and mirror support
│   │   ├── sources.py        # Declarative data sources (national/state)
│   │   ├── qgis_compat.py    # PyQGIS compatibility
│   │   ├── data_backend.py   # Data backend handling
│   │   └── optim_backend.py  # Optimizer management (OR-Tools / Pure Python)
│   ├── algorithms/           # Algorithms exposed in Processing (2 data + 8 urban + 3 regional + 3 location + 2 routing + 10 waste collection)
│   ├── gui/                  # Dock panels and interface dialogs
│   └── i18n/                 # PT-BR/EN translations
├── tests/                    # Automated test suite (pytest)
├── tools/                    # Headless test scripts and maintenance tools
├── docs/                     # Documentation and specifications (MkDocs)
├── dist/                     # Distribution zip packages
├── Makefile                  # Deployment, testing, and packaging commands
└── mkdocs.yml                # Documentation site configuration
```

### Requirements and Installation (Development)

- **Requirements:** QGIS 3.16 or higher.
- **Validated Environment:** The plugin was tested by the author on **QGIS 4.2 "Belém do Pará" on Ubuntu** (OR-Tools installation guidance via "Dependencies" dialog fixed to versions already installed in the environment, validated). On **Windows**, the old manual command pointed to `qgis-bin.exe` and failed, and installation is now done via the button. On **QGIS 4.2 Flatpak / Python 3.13**, OR-Tools installation may fail due to missing binary packages — the plugin operates normally with pure Python heuristics.
- **Development Installation:**
  ```bash
  cd ~/projects/logis/
  make deploy        # Creates a symbolic link to the QGIS plugins directory
  ```
- **Running Tests:**
  ```bash
  make test          # Quick syntax validation across all .py files
  QT_QPA_PLATFORM=offscreen python3 -m pytest -q   # Full suite in tests/
  ```
- **Packaging:** `make package` builds the distribution package at `dist/logis-<version>.zip` via `qgis-plugin-ci`.
- **QGIS 4 / Qt6 Compatibility Check:** Run `python3 tools/qgis4_compat_check.py` (or paste its content into the QGIS Python Console) to inspect Qt6/QGIS 4 version details and legacy/scoped symbols.
- **Documentation:** https://logis.dcamargo.com.br (address declared in `homepage=` in `logis/metadata.txt`).

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
