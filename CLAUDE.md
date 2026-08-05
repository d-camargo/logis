# CLAUDE.md — logis

Documento de contexto do repositório `logis` para agentes de IA. Não é empacotado na distribuição.

---

## 1. Visão do projeto

**logis** é um complemento (plugin) do QGIS para apoiar **projetos de logística** no Brasil, com três módulos:

| Módulo | Escopo | Rede base |
|---|---|---|
| **Logística Urbana** | Uma cidade/município | Rede viária OSM tratada (pipeline herdado do GisBR) |
| **Logística Regional** | Estado ou país | Bases nacionais (DNIT/SNV, geobr) + bases estaduais |
| **Logística Especializada** | Serviços urbanos com roteirização por arcos — caso inicial: **coleta de lixo** | Rede urbana do módulo 1 |

Cada módulo entrega três camadas de funcionalidade (nível de ambição definido pelo Diego):

1. **Indicadores** — métricas calculadas sobre a rede e sobre dados demográficos/econômicos.
2. **Roteirização** — VRP/TSP (por nós) e Arc Routing (por arestas, no módulo especializado).
3. **Localização de instalações (facility location)** — p-mediana, p-centro, cobertura máxima (MCLP), cobertura de conjuntos (LSCP), para posicionar CDs, hubs, garagens, ecopontos, estações de transbordo.

**Estado atual:** repositório sem commits, sem código e sem Makefile ainda; a arquitetura da seção 7 e o roadmap da seção 8 (F1–F7) são planejados, não implementados; a Fase F1 (fundação) é o próximo trabalho a fazer.

## 2. Restrição técnica fundamental

**Apenas PyQGIS + stdlib do Python. Sem dependências externas.** (Mesma filosofia do GisBR; exceções opcionais: `pyarrow` como fallback de Parquet, herdada do GisBR, e `OR-Tools` como backend opcional de otimização.)

Consequências práticas:

- Grafos e caminhos mínimos: usar `QgsGraph`, `QgsGraphBuilder`, `QgsGraphAnalyzer` (Dijkstra) do módulo `qgis.analysis`. **Não usar** networkx, igraph, OSMnx.
- Algoritmos de processamento: preferir `processing.run()` com providers `native:` e `qgis:` (ex.: `native:shortestpathpointtopoint`, `native:serviceareafrompoint`, `qgis:distancematrix`, `native:clip`, `native:joinbylocation`).
- Otimização (VRP, facility location, arc routing): implementar **heurísticas clássicas em Python puro** (savings de Clarke-Wright, sweep, nearest neighbor, 2-opt/or-opt, Teitz-Bart para p-mediana, greedy para cobertura, matching guloso para CPP) como padrão obrigatório. OR-Tools é aceito como backend opcional de otimização (nunca obrigatório, com import lazy/guarded e fallback automático para a heurística pura em Python). Aceitar soluções boas, não ótimas — documentar isso na UI.
- Matriz OD: pré-calcular com Dijkstra multi-origem sobre `QgsGraph` e cachear em disco (o custo dominante de tudo).

### 2.1 OR-Tools — como instalar (e por que o comando cru quebra o QGIS)

O OR-Tools é backend **opcional**. Quando o plugin oferecer ao usuário instalá-lo para obter a solução ótima, o comando normativo passa a ser descrito como uma **regra** — `ortools` mais `nome==versão_instalada` para `numpy`, `pandas` e `typing_extensions` quando presentes no ambiente Python do QGIS, mais `--only-binary=:all:` —, em vez do comando literal estático.

Fixar `nome==versão_instalada` garante que o pip não substitua nem altere as versões de pacotes que o QGIS já utiliza e possui em seu `sys.path`.

(No Python do sistema em Debian/Ubuntu, acrescentar `--break-system-packages`. No Windows/macOS, usar o Python que o QGIS usa — no Windows, o *OSGeo4W Shell*.)

A trava antiga (`"pandas<3" "numpy<2" "typing_extensions==4.10.0"`) quebra em Python 3.13 (QGIS 4.2+ / Flatpak) porque não existe wheel de `numpy 1.x` para Python 3.13 (`cp313`) e `ortools>=9.15` exige `numpy>=2.0.2`.
*(Nota histórica: o comando antigo `pip install ortools "pandas<3" "numpy<2" "typing_extensions==4.10.0"` foi utilizado e validado no ambiente QGIS 3.34/VPS - D18).*

Corolário para o código: como a instalação pode falhar (em ambientes isolados como QGIS Flatpak, a instalação pode não ser possível por ausência de pacote binário), estar ausente ou estar quebrada na máquina do usuário, o import do `ortools` é **sempre lazy/guarded**, com fallback automático para a heurística Python — o plugin nunca pode deixar de funcionar porque o OR-Tools não está lá. Instalado e validado na VPS em 23/07 (`ortools 9.12.4544`); detalhes em `~/.hermes/DECISOES.md` D18.

## 3. Aproveitamento do GisBR (https://github.com/d-camargo/gisbr)

O logis **reaproveita a lógica** do GisBR (cópia adaptada de módulos, não dependência de import). Chamar os algoritmos `gisbr:read_*` via `processing.run()` é a estratégia **preferencial** quando o plugin GisBR estiver instalado; caso contrário, as cópias adaptadas (downloader/catalog) servem como fallback secundário em vez do caminho primário.

### O que copiar/adaptar do GisBR

| Origem no GisBR | Uso no logis |
|---|---|
| `core/osm_pipeline.py` | **Base do módulo Urbano.** `build_osm_municipal_network()` já faz: Overpass → `_parse_osm_ways` → camada de links (LineString) → camada de nós → clip pelo polígono do município → GPKG. Estender com: atributos de custo (comprimento, velocidade por `highway=*`, tempo), sentido de via (`oneway`), e construção do `QgsGraph`. |
| `core/connectors/osm.py` | `fetch_overpass_json(bbox)` com retry e User-Agent. Reusar direto. |
| `core/connectors/wfs.py`, `arcgis_rest.py` | Conectores para bases estaduais (IDE-Sisema/MG e outras IDEs estaduais via WFS; ArcGIS REST para DNIT/ANTT quando aplicável). |
| `core/downloader.py` | Cache em disco (`QStandardPaths.CacheLocation`) + cadeia de mirrors. Reusar padrão. |
| `algorithms/read_municipality.py`, `read_state.py`, `read_census_tract.py`, `read_statistical_grid.py`, `read_urban_area.py`, `read_urban_concentrations.py` + `join_censo` | Geografias e demografia (censobr) para indicadores de demanda: população por setor censitário/grade estatística. |
| `provider.py` + `geobr_qgis_plugin.py` + `metadata.txt` + `Makefile` | Esqueleto do plugin: Processing Provider `logis` + dock panel + `make deploy` (symlink) + `make test` (checagem de sintaxe sem QGIS). |
| `gui/diagnostico_dock.py` | Padrão de dock: seleção UF → município, checkboxes, GPKG de destino, botão Carregar. Adaptar para o fluxo do logis. |
| `core/qgis_compat.py`, `i18n/` | Compatibilidade QGIS 3.16+ e padrão de tradução PT-BR/EN. |

**CRS padrão:** SIRGAS 2000 / EPSG:4674 para dados; reprojetar para CRS métrico (UTM da zona ou EPSG:5880 Polyconic) antes de qualquer cálculo de distância/custo.

## 4. Fontes de dados

### Módulo Urbano
- **Rede viária:** OSM/Overpass (pipeline GisBR).
- **Demanda:** setores censitários + censobr (`join_censo`), grade estatística IBGE, CNEFE (endereços) quando disponível.
- **Uso do solo/equipamentos:** camadas do diagnóstico GisBR (escolas, saúde) como POIs geradores de viagem.

### Módulo Regional
- **Malha rodoviária:** DNIT — SNV (fonte `dnit_snv` já declarada no GisBR, vintage `snv_202507a`).
- **Ferrovias:** ANTT (declaração de rede).
- **Hidrovias e portos:** ANTAQ.
- **Aeroportos:** ANAC/geobr.
- **Municípios, população, PIB municipal:** geobr + IBGE/SIDRA (API JSON, stdlib `urllib`).
- **Bases estaduais:** IDEs estaduais via WFS (piloto: **IDE-Sisema / MG**, malha DER-MG). Estrutura declarativa em `core/sources.py` (padrão GisBR: `id`, `eixo`, `nome`, `protocolo`, `licenca`) permite adicionar estados incrementalmente.

## 5. Indicadores propostos

### 5.1 Urbanos (calculados sobre a rede OSM + demografia)

**De rede (estrutura):**
- Densidade viária (km de via / km²) por setor censitário ou hexgrid.
- Conectividade: índices α, β, γ (razões nós/arestas/circuitos), % de interseções de 4 pernas, % de becos sem saída.
- Circuidade média (distância na rede / distância euclidiana) — proxy de eficiência da malha.
- Centralidade de intermediação (betweenness) aproximada por amostragem de pares OD — identifica vias críticas para carga.

**De acessibilidade e demanda:**
- Área de serviço (isócronas/isodistâncias) a partir de CDs/depósitos candidatos (`native:serviceareafrompoint`).
- População coberta a X min/km de um ponto de distribuição (cruzamento isócrona × setores censitários).
- Acessibilidade gravitacional a POIs (comércio, equipamentos).
- Densidade de demanda: população, domicílios, empregos (quando houver) por célula.

**De operação urbana de carga:**
- Distância/tempo médio de entrega por zona (matriz OD depósito → centroides de setor).
- Índice de restrição de circulação: % da rede acessível a veículos de carga (filtro por `highway`, largura, `maxweight` quando existir no OSM).
- Indicador de vagas/pontos de carga-descarga por km de via comercial (se dados municipais disponíveis).

### 5.2 Regionais (calculados sobre SNV + geobr/IBGE)

**De rede:**
- Densidade rodoviária por UF/mesorregião (km/1.000 km² e km/10.000 hab).
- % da malha pavimentada / duplicada (atributos do SNV).
- Conectividade intermunicipal: nº de ligações diretas por município; identificação de pontes/arcos críticos (cut links).
- Circuidade interurbana entre pares de municípios principais.

**De acessibilidade:**
- Tempo/distância de cada sede municipal à capital, ao porto mais próximo, ao aeroporto mais próximo.
- População a até X km de rodovia federal pavimentada.
- Acessibilidade gravitacional a mercados (população/PIB dos destinos ponderados pelo custo de viagem).
- Indicador de encravamento: municípios acima de percentil de custo médio a todos os demais.

**De potencial logístico:**
- Centro de gravidade da demanda (população/PIB) — ponto de partida para localização de hubs.
- Cobertura de candidatos a hub: % da população/PIB atendida a X horas de cada candidato.
- Intermodalidade: distância de cada município ao terminal ferroviário/hidroviário mais próximo.

### 5.3 Especializados — coleta de lixo
- Extensão de vias a coletar por setor (km) e por frequência.
- Geração estimada de resíduos por setor (população × per capita kg/hab/dia, parametrizável; default SNIS ~0,9–1,0).
- Deadhead ratio: km improdutivos / km produtivos por rota.
- Equilíbrio entre setores: desvio de carga (t) e de tempo entre rotas.
- Distância média ao ponto de destino (aterro/transbordo/ecoponto).
- Cobertura: % de domicílios/vias atendidos por frequência de coleta.

## 6. Técnicas do módulo de coleta de lixo

A coleta domiciliar porta-a-porta é um problema de **roteirização por arcos** (as ruas são a demanda), não por nós. Sequência clássica do projeto, que o módulo deve espelhar como etapas do fluxo:

1. **Estimativa de geração** — população por setor × taxa per capita × % de cobertura → toneladas/dia por trecho de via (rateio da população do setor pelos metros de via).
2. **Setorização (districting)** — particionar a cidade em setores de coleta balanceados por carga e tempo, com contiguidade e compacidade. Heurística: crescimento de regiões a partir de sementes sobre o grafo + troca de arestas de fronteira para balancear.
3. **Roteirização por arcos:**
   - **CPP (Chinese Postman Problem)** — todas as vias, grafo não direcionado: emparelhamento dos nós de grau ímpar (matching guloso por menor caminho) + circuito euleriano (Hierholzer). Python puro sobre `QgsGraph`.
   - **RPP (Rural Postman)** — quando só um subconjunto de vias exige coleta.
   - **CARP (Capacitated Arc Routing)** — versão com capacidade do caminhão: heurísticas Path-Scanning ou Augment-Merge; rota fecha quando atinge a capacidade e vai ao transbordo/aterro.
   - Vias de mão única → problema misto/direcionado (usar sentido do `oneway` do OSM).
4. **Roteirização por nós (complementar)** — coleta ponto-a-ponto (contêineres, PEVs, coleta seletiva com pontos de entrega): CVRP com Clarke-Wright savings + melhorias 2-opt/or-opt.
5. **Localização de instalações** — ecopontos e estações de transbordo via MCLP/p-mediana (módulo compartilhado de facility location).
6. **Dimensionamento de frota** — nº de veículos = f(carga total, capacidade, velocidade média de coleta, jornada, tempo de descarga e deslocamento ao destino).

## 7. Arquitetura proposta do repositório

```
logis/
├── __init__.py               # entrada do plugin
├── logis_plugin.py           # registra provider + dock
├── provider.py               # Processing Provider "logis"
├── metadata.txt
├── Makefile                  # make deploy / make test (padrão GisBR)
├── core/
│   ├── network/
│   │   ├── osm_pipeline.py   # adaptado do GisBR (urbano)
│   │   ├── snv_pipeline.py   # SNV → grafo regional
│   │   ├── graph_builder.py  # camada → QgsGraph com custos (dist/tempo), oneway
│   │   └── od_matrix.py      # Dijkstra multi-origem + cache em disco
│   ├── connectors/           # osm.py, wfs.py, arcgis_rest.py (do GisBR)
│   ├── downloader.py         # cache + mirrors (do GisBR)
│   ├── sources.py            # fontes declarativas (nacionais + estaduais)
│   ├── indicators/
│   │   ├── urban.py
│   │   ├── regional.py
│   │   └── waste.py
│   ├── routing/
│   │   ├── vrp.py            # savings, sweep, 2-opt
│   │   └── arc_routing.py    # CPP, RPP, CARP heurísticos
│   ├── location/
│   │   └── facility.py       # p-mediana (Teitz-Bart), MCLP, LSCP (greedy)
│   └── qgis_compat.py
├── algorithms/               # Processing algorithms expostos (1 por função)
├── gui/                      # docks por módulo
├── i18n/                     # PT-BR / EN (padrão GisBR)
└── docs/                     # pesquisa e especificações (não empacotado)
```

**Padrão de exposição:** toda funcionalidade vira um **Processing algorithm** (`logis:*`), scriptável via console; os docks são orquestradores que chamam os algoritmos — igual ao GisBR (dock chama `processing.run("gisbr:...")`).

## 8. Roadmap por fases

- **F1 — Fundação:** esqueleto do plugin, cópia adaptada de connectors/downloader/osm_pipeline, `graph_builder` + `od_matrix` com cache. Piloto urbano em um município de MG.
- **F2 — Indicadores urbanos:** algoritmos de indicadores 5.1 + dock do módulo Urbano.
- **F3 — Rede regional:** `snv_pipeline` (SNV → grafo), indicadores 5.2, conector estadual piloto (IDE-Sisema/MG).
- **F4 — Facility location:** p-mediana, MCLP, LSCP compartilhados entre módulos.
- **F5 — Roteirização por nós:** CVRP heurístico (savings + 2-opt).
- **F6 — Coleta de lixo:** estimativa de geração, setorização, CPP/CARP, dimensionamento de frota.
- **F7 — Empacotamento:** tradução, docs, publicação no repositório oficial de plugins do QGIS.

## 9. Regras para agentes

- Idioma do código: inglês; UI e commits: PT-BR com tradução EN via `i18n/` (padrão GisBR).
- Nunca introduzir dependência externa sem aprovação explícita do Diego (regra da seção 2).
- Todo algoritmo novo precisa: docstring com referência bibliográfica da técnica, teste de sintaxe compatível com `make test` (sem QGIS), e limite de complexidade documentado (tamanho de rede testado).
- Reprojetar para CRS métrico antes de cálculos de custo; devolver saídas em EPSG:4674.
- Cache: `QStandardPaths.CacheLocation` → `.../logis/`. Nunca gravar fora do cache ou do GPKG escolhido pelo usuário.
- Licença: GPL-3.0 (herdada da lógica do GisBR).
- Compatibilidade Qt6/QGIS 4: todo acesso a enum do Qt/QGIS deve ser escopado (`Qt.DockWidgetArea.RightDockWidgetArea`, `QgsProcessing.SourceType.TypeVectorLine`, `QgsProcessingParameterNumber.Type.Double`, `QgsWkbTypes.Type.*` / `QgsWkbTypes.GeometryType.*`, `QgsTask.Flag.*`), tipos de campo só se criam via `core.qgis_compat.field_type()` (nunca `QVariant.*` direto) e `exec_()` não pode ser usado (PyQt6/QGIS 4 removeram as formas soltas; as escopadas valem também no QGIS 3.16+; verificado por `test_qt6_compat.py`).
