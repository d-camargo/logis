# PLAN — logis

## Objetivo

**Estado herdado (fechado):** F1, F2 (seção 5.1), F3 (seção 5.2), F4
(seção 5.4/facility location), F5 (roteirização por nós — CVRP) e o
ciclo extra do `README.md` bilíngue — todos completos e commitados.
`git log` confirma: `5449a4e` → `6875f67` → `1fcf27c` (F3) →
`5e789da` (F5, CVRP: `core/routing/vrp.py`,
`algorithms/vrp_cvrp.py`, `test_vrp.py`, 15 algorithms) → `524ed28`
("F5" na mensagem, conteúdo real F6 rodada 1: `core/indicators/waste.py`,
`algorithms/waste_generation_estimate.py`, `test_waste.py`) →
`b1127f7` (F6 rodada 2, setorização) → `50dd820` ("package: logis
0.1.0") → `80465b7` ("F6", conteúdo real F6 rodada 3 — CPP) →
`34bbbf4` ("F6", conteúdo real F6 rodada 4 — RPP) → `3fbfde9`
("F6", conteúdo real: fechamento do passo 19 — `route_is_connector`
em `waste_rpp_route.py` — **e** F6 rodada 5 completa — CARP) →
`25890bf` ("F6", conteúdo real: F6 rodada 6 completa —
dimensionamento de frota: `estimate_fleet_size` em
`core/indicators/waste.py`, `algorithms/waste_fleet_sizing.py`,
`logis:waste_fleet_sizing` registrado em `provider.py`).

**F6 — Coleta de lixo: FECHADO.** As quatro entregas do roadmap
formal (seção 8 do CLAUDE.md: "estimativa de geração, setorização,
CPP/CARP, dimensionamento de frota") estão todas implementadas,
testadas e commitadas. Verificado nesta revisão (2026-07-21), lendo o
código-fonte diretamente (não apenas o plano herdado):
- `algorithms/waste_fleet_sizing.py` existe (12488 bytes);
  `core/indicators/waste.py` tem `def estimate_fleet_size` na linha
  100, ao lado de `sector_waste_generation` (linha 8) e
  `allocate_generation_by_street_length` (linha 51).
- `grep -c "addAlgorithm" provider.py` → **21**, incluindo
  `self.addAlgorithm(WasteFleetSizing())`.
- `python3 -m unittest discover -s . -p "test_*.py"` → **171 testes,
  OK** (o plano herdado tinha registrado 168 na verificação do commit
  `3fbfde9`; o crescimento para 171 é consistente com os testes de
  `estimate_fleet_size` e do algorithm `waste_fleet_sizing` somados na
  rodada 6, commit `25890bf`).
- `make test` → `sintaxe OK`.
- `git status` → limpo, nada pendente de commit. `git show --stat
  25890bf` confirma que esse commit é exatamente a rodada 6 (diff
  isolado em `algorithms/waste_fleet_sizing.py`,
  `core/indicators/waste.py`, `provider.py`, `test_waste.py`, 521
  inserções).

**Decisão (herdada, ainda vigente): validação manual no QGIS
adiada.** Pedido explícito do Diego ("deixar o teste do QGIS pra
depois, vamos avançar") permanece em vigor. Os passos de revisão
visual das rodadas 2 a 6 (passos 7, 13, 18, 27 e 33) continuam
agrupados para uma revisão em lote única quando o Diego tiver
ambiente QGIS disponível — não bloqueiam o avanço do plano.

**Achado (herdado — OR-Tools):** infraestrutura de
detecção/instalação/UI (`core/optim_backend.py`,
`core/ortools_installer.py`, `gui/dependencies_dialog.py`) existe
desde o primeiro commit, mas nenhum solver (`vrp.py`, `facility.py`,
`arc_routing.py`, `districting.py`) chama `pick_backend()`. Continua
fora de escopo até o Diego decidir qual solver ganha o backend
alternativo primeiro.

**Ciclo em andamento: F6 rodada 7 — Indicador 5.3 "Deadhead ratio"
como Processing algorithm dedicado** (seção 5.3 do CLAUDE.md: "Deadhead
ratio: km improdutivos / km produtivos por rota"). Hoje esse número já
é *calculado* dentro de `waste_cpp_route.py`, `waste_rpp_route.py` e
`waste_carp_route.py` (cada um soma deadhead à sua maneira e só o
imprime via `feedback.pushInfo`), mas não existe como indicador
persistido/consultável — não sai como campo de atributo nem como
tabela exportável, então não pode alimentar outro algorithm, um
relatório ou um dock futuro. Esta rodada fecha essa lacuna com o
menor incremento possível, reaproveitando exatamente o padrão que a
rodada 4 já usou para RPP (`route_is_connector`, passo 19): marcar o
deadhead como um campo booleano por feição de saída, e então agregar
esse campo num indicador formal.

Confirmado por leitura de código nesta revisão (não é suposição):
- `algorithms/waste_cpp_route.py`: a saída já duplica a feição de
  cada trecho de deadhead (para representar a segunda passagem no
  circuito), mas **não marca qual das duas cópias é a duplicata** —
  não há nenhum campo booleano de deadhead.
- `algorithms/waste_rpp_route.py`: já tem `route_is_connector`
  (`out_fields` linha 242) — semanticamente **já é** o indicador de
  deadhead por feição para RPP (um conector é, por definição, um
  trecho percorrido que não fazia parte da cobertura obrigatória).
  Nenhuma mudança necessária aqui.
- `algorithms/waste_carp_route.py`: o loop de escrita (linhas 377-410)
  escreve **todas** as arestas de `route["edges"]` (obrigatórias +
  conectoras/deadhead) sem diferenciá-las por campo — o cálculo de
  `deadhead_km` (linha 384) usa `req_id_set` só para o
  `feedback.pushInfo`, não grava esse booleano na feição.

**Fora de escopo nesta revisão do plano (deferido, não esquecido):**
- **Renomear `route_is_connector` (RPP) para um nome comum com CPP/CARP**
  — decisão explícita: **não** renomear um campo já commitado e
  testado sem ganho funcional (regra geral do projeto contra
  mudanças cosméticas). O algorithm indicador (passo 39) aceita
  qualquer nome de campo booleano via `QgsProcessingParameterField`,
  então a diferença de nome entre RPP e CPP/CARP não é um problema
  técnico, só uma linha a mais de documentação no `shortHelpString`.
- **Os outros três indicadores de 5.3** (equilíbrio entre setores —
  desvio de carga e tempo entre rotas —, distância média ao ponto de
  destino, cobertura por frequência de coleta) — cada um depende de
  dados que ainda não têm um "dono" natural óbvio (equilíbrio: precisa
  agregar por setor a saída de `waste_fleet_sizing`/`waste_carp_route`;
  distância ao destino: precisa de facility location de
  ecopontos/aterros, módulo `core/location/facility.py`, ainda não
  amarrado ao módulo waste; cobertura por frequência: precisa de um
  parâmetro de frequência que hoje não existe em nenhuma camada).
  Ficam para rodadas 8, 9 e 10 do F6, uma de cada vez, mesmo raciocínio
  de escopo enxuto das rodadas anteriores.
- **Augment-Merge** (segunda heurística de CARP, seção 6 item 3) —
  inalterado, só entra se a qualidade do Path-Sconning simples não for
  suficiente na prática.
- **Vias de mão única / grafo misto-direcionado** (seção 6, item 3,
  `oneway` do OSM) — inalterado, rodada dedicada depois do F6.
- **Split-delivery** — fora de escopo, decisão já tomada na rodada 5.
- **Integração em GUI (dock)** para o módulo de coleta de lixo —
  inalterado, mesmo raciocínio de todos os ciclos anteriores.
- **Validação manual no QGIS** (rodadas 2 a 6) — decisão mantida,
  revisão em lote posterior.
- **Conectar o backend OR-Tools a algum solver real** — inalterado.
- **F7 — Empacotamento** — só depois do F6 fechado (agora está) E da
  validação manual no QGIS em lote (ainda pendente). F6 fechado não
  libera F7 sozinho; a rodada 7 em diante continua sendo trabalho de
  polimento do F6 (indicadores 5.3), não o início do F7.

## Decisões de arquitetura

### Herdadas das rodadas 2-6 — confirmadas corretas no código atual

- `core/routing/districting.py` e `core/routing/arc_routing.py`, sem
  import de `qgis.*`; representação de grafo em lista de dicts
  (`id`, `from_node`, `to_node`, `length`[, `load`]), `node_key`
  calculado pela camada de algorithm (arredondamento em grade), não
  pelas funções puras.
- `arc_routing.py` tem `find_odd_degree_nodes`,
  `shortest_path_between_nodes`, `match_odd_degree_nodes`,
  `build_eulerian_circuit`, `connect_required_components` e
  `solve_carp_path_scanning` — seis funções puras cobrindo CPP, RPP e
  CARP.
- `core/indicators/waste.py` tem três funções puras de fórmula (não de
  grafo), todas no mesmo padrão de docstring (fórmula, referência
  bibliográfica, limite de complexidade, `Args`/`Returns`/`Raises`):
  `sector_waste_generation`, `allocate_generation_by_street_length`,
  `estimate_fleet_size`. A rodada 7 acrescenta uma quarta função,
  `compute_deadhead_ratio`, no mesmo arquivo e mesmo padrão.
- Algorithms `logis:waste_districting`, `logis:waste_cpp_route`,
  `logis:waste_rpp_route`, `logis:waste_carp_route` e
  `logis:waste_fleet_sizing`, grupo "Logística Especializada — Coleta
  de Lixo" (`groupId="waste"`), 21 algorithms registrados em
  `provider.py`.
- `logis:waste_fleet_sizing` foi o primeiro algorithm do módulo waste
  com saída em tabela sem geometria (`QgsWkbTypes.NoGeometry`) — a
  rodada 7 segue o mesmo padrão de saída para o indicador de deadhead
  ratio, pelo mesmo motivo (resultado é um indicador escalar por
  rota/setor, não uma geometria nova).

### Novas para a rodada 7 (indicador de deadhead ratio)

- **`algorithms/waste_cpp_route.py` ganha o campo booleano
  `route_is_deadhead`** no mesmo lugar onde hoje monta `out_fields`
  (linhas 195-201): ao escrever cada feição do circuito, marcar
  `True` na(s) ocorrência(s) extra de um `edge_id` que já apareceu
  antes na sequência do circuito (i.e., a segunda e demais cópias de
  um trecho duplicado para eulerianizar o grafo), `False` na primeira
  ocorrência de cada `edge_id`. Não muda a lógica de duplicação já
  existente, só rotula o que já é escrito.
- **`algorithms/waste_carp_route.py` ganha o campo booleano
  `route_is_deadhead`**, calculado exatamente com o dado que o
  algorithm já tem em mãos na linha 374 (`req_id_set = {e["id"] for e
  in req_edges}`): ao escrever cada feição na linha 405-409,
  `route_is_deadhead = edge_id not in req_id_set`. Mesma fonte de
  verdade que já alimenta o `feedback.pushInfo` de deadhead_km da
  linha 384 — só passa a gravar por feição, não só relatar em texto.
- **`algorithms/waste_rpp_route.py` não muda** — `route_is_connector`
  já cumpre esse papel; o algorithm indicador da rodada 7 trata os
  dois nomes de campo como equivalentes (o usuário escolhe qual campo
  booleano usar, via `QgsProcessingParameterField`).
- **Nova função pura `compute_deadhead_ratio(lengths_km,
  deadhead_flags, route_ids=None) -> Dict`** em
  `core/indicators/waste.py`, mesmo estilo de `estimate_fleet_size`
  (função pura, sem `qgis.*`, uma entrada por feição/trecho de rota):
  - `lengths_km`: `List[float]`, comprimento de cada trecho (feição)
    em km, já convertido pelo algorithm a partir de `$length`
    ou de um campo de comprimento existente.
  - `deadhead_flags`: `List[bool]`, mesmo tamanho de `lengths_km` —
    `True` = trecho improdutivo (deadhead/conector), `False` =
    trecho produtivo (cobertura obrigatória).
  - `route_ids`: `Optional[List]`, mesmo tamanho, identificador de
    rota/setor por trecho; se `None`, trata toda a entrada como uma
    única rota (mesmo comportamento "sem campo de setor = uma rota
    só" já usado em CPP/RPP/CARP).
  - Valida: listas não vazias, mesmo tamanho entre
    `lengths_km`/`deadhead_flags`/`route_ids` (quando fornecido),
    `lengths_km` só com valores ≥ 0 (`ValueError` caso contrário).
  - Algoritmo: agrupa por `route_id` (ou um grupo único), soma
    `productive_km` (soma de `lengths_km` onde `deadhead_flags` é
    `False`) e `deadhead_km` (soma onde `True`) por grupo;
    `deadhead_ratio = deadhead_km / productive_km` se
    `productive_km > 0`, senão `None` (evita `ZeroDivisionError`
    quando uma rota é 100% deadhead — caso degenerado que não deveria
    ocorrer na prática, mas a função não assume isso).
  - Retorna `{"by_route": {route_id: {"productive_km": float,
    "deadhead_km": float, "deadhead_ratio": Optional[float]}},
    "total": {"productive_km": float, "deadhead_km": float,
    "deadhead_ratio": Optional[float]}}`.
  - Referência bibliográfica: reaproveita a mesma citação já presente
    em `arc_routing.py` (Edmonds & Johnson 1973) para o conceito de
    deadhead/duplicação em roteirização por arcos — a função em si é
    soma/razão simples, não uma heurística nova, então o docstring
    documenta a fórmula, não um algoritmo de otimização.
  - Complexidade: O(N), N = número de feições/trechos de entrada —
    uma passada de agrupamento, sem laço aninhado.
- **Algorithm novo: `algorithms/waste_deadhead_ratio.py`
  (`logis:waste_deadhead_ratio`)**, mesmo grupo "Logística
  Especializada — Coleta de Lixo". Parâmetros: camada de entrada
  (linha, saída de `logis:waste_cpp_route`, `waste_rpp_route` ou
  `waste_carp_route`); campo booleano de deadhead
  (`QgsProcessingParameterField`, `DataType=Boolean`, não opcional —
  o usuário informa `route_is_deadhead` ou `route_is_connector`
  conforme a origem da camada); campo de agrupamento de rota opcional
  (`QgsProcessingParameterField`, `optional=True` — `route_id` para
  saída de CARP, `route_sector_id` para saída de CPP/RPP; se omitido,
  trata a camada inteira como uma única rota). Lê o comprimento de
  cada feição via `feature.geometry().length()` (camada já deve estar
  em CRS métrico, mesmo padrão de leitura de geometria já usado nos
  outros algorithms do módulo waste — não inventa uma segunda forma
  de medir comprimento). Monta `lengths_km`, `deadhead_flags`,
  `route_ids` e chama `compute_deadhead_ratio`. **Saída: tabela sem
  geometria** (`QgsWkbTypes.NoGeometry`, mesmo padrão de
  `waste_fleet_sizing`) com uma feição por rota: campos `route_id`,
  `productive_km`, `deadhead_km`, `deadhead_ratio` — mais uma feição
  final com `route_id = NULL` representando o total agregado. Reporta
  via `feedback.pushInfo` o total geral (km produtivos, km de
  deadhead, razão) e um aviso informativo por rota com
  `deadhead_ratio > 0.5` (mais deadhead do que trabalho produtivo —
  mesmo padrão de aviso informativo, não erro, já usado em
  `waste_carp_route`/`waste_fleet_sizing`). Registrar import +
  `addAlgorithm` em `provider.py` no mesmo passo (22 algorithms).
- **Testes:** `test_waste.py` ganha casos para `compute_deadhead_ratio`:
  (a) uma rota sem nenhum deadhead (ratio 0.0); (b) uma rota com
  deadhead conhecido (ratio calculado à mão); (c) múltiplas rotas via
  `route_ids` (agregação correta por grupo + total); (d) rota 100%
  deadhead (`productive_km == 0` → `deadhead_ratio is None`, sem
  levantar exceção); (e) listas de tamanho incompatível
  (`ValueError`); (f) entrada vazia (`ValueError`). Mais um teste de
  metadata do algorithm (`test_waste_deadhead_ratio_algorithm_metadata`),
  mesmo padrão dos algorithms anteriores. `test_waste.py` também
  ganha um caso de regressão para `route_is_deadhead` em
  `waste_cpp_route.py` (confirma `True` na cópia duplicada e `False`
  na original, mesmo estilo do teste que a rodada 4 já fez para
  `route_is_connector` em RPP) e outro para `waste_carp_route.py`
  (confirma `True` exatamente nos `edge_id` fora de `req_id_set`).

## Passos (executor marca [x] ao concluir)

**Rodada 2 (setorização) — fechamento de código:**

- [x] 1. `core/routing/districting.py` com as três funções puras
      (`select_seed_edges_farthest_first`, `grow_sectors_from_seeds`,
      `rebalance_boundary_edges`), formato de edge-dict, sem import de
      `qgis.*`. — arquivos: `core/routing/districting.py`

- [x] 2. `test_districting.py` cobrindo as três funções (válidos +
      inválidos, grafo desconectado). — arquivos: `test_districting.py`

- [x] 3. `algorithms/waste_districting.py` (`logis:waste_districting`)
      registrado em `provider.py`. — arquivos:
      `algorithms/waste_districting.py`, `provider.py`

- [x] 4. `core/routing/__init__.py` sem import quebrado. — arquivos:
      `core/routing/__init__.py`

- [x] 5. `python3 -m unittest discover -s . -p "test_*.py"` e
      `make test` (sintaxe OK) passando com a versão commitada. —
      arquivos: nenhum (verificação)

- [x] 6. Commitar e dar push da rodada 2 (commit `b1127f7`). —
      arquivos: nenhum novo

- [x] 7. **(Adiado a pedido do Diego — não bloqueia rodadas
      seguintes.)** Diego revisa manualmente no QGIS a versão
      commitada (`b1127f7`): abre o plugin, roda
      `logis:waste_districting` com uma camada de vias de teste (com
      e sem campo de carga), confirma visualmente que os setores
      resultantes são contíguos, compactos e balanceados. Fica
      agrupado com os passos 13, 18, 27 e 33 para uma revisão em lote
      quando o Diego retomar os testes no QGIS. — arquivos: nenhum
      (revisão manual pelo Diego)

**Rodada 3 (CPP — roteirização por arcos) — fechada e commitada (`80465b7`):**

- [x] 8. Criar `core/routing/arc_routing.py` com
      `find_odd_degree_nodes(edges)` e
      `shortest_path_between_nodes(edges, source, target)` (Dijkstra
      ponderado por `length`), cada uma com docstring, referência
      bibliográfica e limite de complexidade. — arquivos:
      `core/routing/arc_routing.py`

- [x] 9. Adicionar `match_odd_degree_nodes(edges, odd_nodes)`
      (emparelhamento guloso usando `shortest_path_between_nodes`). —
      arquivos: `core/routing/arc_routing.py`

- [x] 10. Adicionar `build_eulerian_circuit(edges, duplicated_edge_ids)`
      (Hierholzer). — arquivos: `core/routing/arc_routing.py`

- [x] 11. Criar `test_arc_routing.py` com casos: ciclo simples (0 nós
      ímpares), grafo com exatamente 2 nós ímpares, grafo com 4+ nós
      ímpares (testa o emparelhamento), e casos inválidos (edges vazio,
      nó inexistente, setor desconexo). Rodar
      `python3 -m unittest test_arc_routing -v` e `make test` como
      parte deste mesmo passo, e só marcar `[x]` quando ambos
      passarem. — arquivos: `test_arc_routing.py`

- [x] 12. Criar `algorithms/waste_cpp_route.py`
      (`logis:waste_cpp_route`): parâmetros = camada de vias, campo
      `collection_sector_id` opcional, tolerância de nó (metros).
      Roda CPP por setor (ou uma vez, se sem campo de setor), grava
      `route_visit_order` e `route_sector_id` na camada de saída
      (com feições duplicadas para trechos de deadhead), reporta
      trechos duplicados e km de deadhead por setor via
      `feedback.pushInfo`. Registrar import + `addAlgorithm` em
      `provider.py` no mesmo passo. Rodar `make test` e
      `python3 -m unittest discover -s . -p "test_*.py"` como parte
      deste mesmo passo (confirma que o novo algorithm e o
      `provider.py` atualizado — 18 algorithms — não quebram nada) e
      só marcar `[x]` quando passarem. — arquivos:
      `algorithms/waste_cpp_route.py`, `provider.py`

- [x] 13. **(Adiado a pedido do Diego — não bloqueia rodadas
      seguintes.)** Diego revisa manualmente no QGIS: roda
      `logis:waste_cpp_route` sobre a saída de `logis:waste_districting`,
      confirma visualmente que a sequência de rota cobre todas as vias
      do setor e que o deadhead reportado é razoável para o tamanho da
      rede de teste. Agrupado com os passos 7, 18, 27 e 33 para revisão
      em lote quando o Diego retomar os testes no QGIS — até lá, a
      rodada 3 é considerada "código fechado, validação visual
      pendente" e o plano segue para a rodada seguinte do F6 sem
      esperar por ela. — arquivos: nenhum (revisão manual pelo Diego)

**Rodada 4 (RPP — roteirização por arcos com subconjunto obrigatório) — fechada e commitada (`34bbbf4`):**

- [x] 14. Adicionar `connect_required_components(required_edges, full_edges)`
      a `core/routing/arc_routing.py`: identifica componentes conexos
      do subgrafo de `required_edges` (BFS/union-find), escolhe um nó
      representante por componente, calcula distâncias entre
      representantes via `shortest_path_between_nodes` sobre
      `full_edges`, monta MST (Kruskal com union-find) sobre os
      componentes, retorna a união (sem duplicatas) dos `edge_id` dos
      caminhos mínimos escolhidos. Retorna lista vazia se já houver
      um único componente. Levanta `ValueError` se algum componente
      não puder ser conectado. Docstring com referência (Frederickson
      1979) e limite de complexidade (O(C² log V + C² log C), C = nº
      de componentes). — arquivos: `core/routing/arc_routing.py`

- [x] 15. Ampliar `test_arc_routing.py` com casos para
      `connect_required_components`: subgrafo já conexo (retorna
      vazio), dois componentes conectados por um único trecho
      opcional, três ou mais componentes (testa a MST), e caso
      inválido (componente sem caminho possível). Rodar
      `python3 -m unittest test_arc_routing -v` e `make test` como
      parte deste mesmo passo, e só marcar `[x]` quando ambos
      passarem. — arquivos: `test_arc_routing.py`

- [x] 16. Criar `algorithms/waste_rpp_route.py`
      (`logis:waste_rpp_route`): parâmetros = camada de vias, campo
      booleano de trecho obrigatório (não opcional), campo de setor de
      coleta opcional, tolerância de nó (metros). Para cada setor (ou
      uma vez, se sem campo de setor): separa obrigatórios de todos,
      chama `connect_required_components`, monta `combined_edges`,
      roda `find_odd_degree_nodes` → `match_odd_degree_nodes` →
      `build_eulerian_circuit` sobre `combined_edges`. Grava na saída
      só as feições do circuito (obrigatórias + conectores usados),
      com `route_visit_order` e `route_sector_id`. Reporta via
      `feedback.pushInfo`, por setor: nº de trechos obrigatórios, nº
      de conectores adicionados, km de deadhead. Registrar import +
      `addAlgorithm` em `provider.py` no mesmo passo (19 algorithms). —
      arquivos: `algorithms/waste_rpp_route.py`, `provider.py`

- [x] 17. Rodar `make test` e
      `python3 -m unittest discover -s . -p "test_*.py"` para
      confirmar que o novo algorithm e o `provider.py` atualizado (19
      algorithms) não quebram nada; corrigir o que for necessário até
      passar. Commitar e dar push da rodada 4. — arquivos: nenhum novo
      (verificação + commit)

- [x] 18. **(Adiado a pedido do Diego — não bloqueia rodadas
      seguintes.)** Diego revisa manualmente no QGIS: roda
      `logis:waste_rpp_route` sobre uma camada de teste com um
      subconjunto de trechos marcados como obrigatórios, confirma
      visualmente que todos os trechos obrigatórios são cobertos, que
      os conectores adicionados fazem sentido (menor desvio possível)
      e que trechos opcionais não usados não aparecem na saída.
      Agrupado com os passos 7, 13, 27 e 33 para revisão em lote quando
      o Diego retomar os testes no QGIS — até lá, a rodada 4 é
      considerada "código fechado, validação visual pendente". —
      arquivos: nenhum (revisão manual pelo Diego)

**Fechamento da rodada 4 (gap encontrado em revisão anterior) — fechado e commitado (`3fbfde9`):**

- [x] 19. Adicionar o campo booleano `route_is_connector` à saída de
      `algorithms/waste_rpp_route.py`: capturar `original_req_ids =
      {e["id"] for e in req_edges}` ANTES do loop que infla
      `req_id_set` com os conectores; ao escrever cada feição do
      circuito, gravar `route_is_connector = edge_id not in
      original_req_ids`. `QgsField("route_is_connector",
      qgis_compat.field_type("bool"))` adicionado a `out_fields`.
      `test_waste.py` ampliado com caso que confirma o valor do campo
      para um setor com componentes desconexos. `make test` e
      `python3 -m unittest discover` confirmados passando. — arquivos:
      `algorithms/waste_rpp_route.py`, `test_waste.py`

**Rodada 5 (CARP — roteirização por arcos com capacidade do veículo) — fechada e commitada (`3fbfde9`):**

- [x] 20. Adicionar `solve_carp_path_scanning(required_edges,
      full_edges, depot_node, vehicle_capacity)` a
      `core/routing/arc_routing.py`: validação de `load` por trecho,
      construção gulosa de rotas por nearest-neighbor respeitando
      capacidade, fechamento de rota no depósito. Docstring com
      referência (Golden, DeArmon & Baker, 1983) e limite de
      complexidade/escala documentado (~500 trechos obrigatórios por
      setor). — arquivos: `core/routing/arc_routing.py`

- [x] 21. Ampliar `test_arc_routing.py` com os cinco casos de
      `solve_carp_path_scanning` (uma rota, duas rotas por
      capacidade, trecho isolado excedendo capacidade, rota trivial
      de um trecho, `required_edges` vazio). — arquivos:
      `test_arc_routing.py`

- [x] 22. Criar `algorithms/waste_carp_route.py`
      (`logis:waste_carp_route`): parâmetros = camada de vias, campo
      de trecho obrigatório (opcional), campo numérico de demanda
      (não opcional), camada de ponto do depósito (exatamente 1
      feição), capacidade do veículo em kg, campo de setor (opcional),
      tolerância de nó. Snapa o depósito ao node_key mais próximo por
      distância euclidiana. Para cada setor, separa obrigatórios,
      chama `solve_carp_path_scanning`, grava a saída com
      `route_visit_order`, `route_id` e `route_sector_id`. —
      arquivos: `algorithms/waste_carp_route.py`

- [x] 23. Validar a camada de ponto do depósito no
      `processAlgorithm` (exatamente 1 feição; `QgsProcessingException`
      caso contrário) e implementar o snap por distância euclidiana
      ao `node_key` mais próximo, mantendo o dict auxiliar `node_key
      -> (x, y)` durante a leitura das feições de via. — arquivos:
      `algorithms/waste_carp_route.py`

- [x] 24. Reportar via `feedback.pushInfo`, por setor: nº de
      rotas/viagens geradas, carga (kg) e km de deadhead por rota, e
      aviso informativo para rotas com aproveitamento de capacidade
      abaixo de 50%. — arquivos: `algorithms/waste_carp_route.py`

- [x] 25. Registrar `WasteCarpRoute` (import + `addAlgorithm`) em
      `provider.py` (20 algorithms). Adicionar teste de metadata em
      `test_waste.py`. — arquivos: `provider.py`, `test_waste.py`

- [x] 26. Rodar `make test` e `python3 -m unittest discover -s . -p
      "test_*.py"` para confirmar que o novo algorithm e o
      `provider.py` atualizado (20 algorithms) não quebram nada;
      corrigir o que for necessário até passar. Commitar e dar push
      da rodada 5. Verificado: commit `3fbfde9`, testes OK, `make
      test` OK, `git status` limpo. — arquivos: nenhum novo
      (verificação + commit)

- [x] 27. **(Adiado a pedido do Diego — mesma decisão das rodadas
      anteriores, não bloqueia rodadas seguintes.)** Diego revisa
      manualmente no QGIS: roda `logis:waste_carp_route` sobre uma
      camada de teste com demanda e capacidade que force pelo menos
      duas rotas, confirma visualmente que cada rota respeita a
      capacidade, que o depósito é o ponto de partida/chegada de
      todas as rotas e que o nº de viagens reportado bate com a
      camada de saída. Agrupado com os passos 7, 13, 18 e 33 para a
      revisão em lote futura. — arquivos: nenhum (revisão manual pelo
      Diego)

**Rodada 6 (Dimensionamento de frota — item 6 da seção 6 do CLAUDE.md, último item formal do F6) — fechada e commitada (`25890bf`):**

- [x] 28. Adicionar `estimate_fleet_size(route_distances_km,
      avg_collection_speed_kmh, shift_duration_h, unload_time_h,
      travel_time_to_destination_h) -> Dict` a
      `core/indicators/waste.py`: heurística First-Fit Decreasing
      de bin packing, validação de entradas, `ValueError` se alguma
      rota isolada exceder `shift_duration_h` sozinha. Docstring no
      mesmo padrão de `sector_waste_generation` (fórmula, referência
      bibliográfica — Johnson 1973 —, limite de complexidade,
      `Args`/`Returns`/`Raises`). — arquivos: `core/indicators/waste.py`

- [x] 29. Adicionar a `test_waste.py` os cinco casos de
      `estimate_fleet_size` (um veículo, dois veículos forçados, rota
      isolada excedendo a jornada, lista vazia, parâmetro inválido).
      Rodar `python3 -m unittest test_waste -v` e `make test`; só
      marcar `[x]` quando ambos passarem. — arquivos: `test_waste.py`

- [x] 30. Criar `algorithms/waste_fleet_sizing.py`
      (`logis:waste_fleet_sizing`): parâmetros = camada de saída de
      `logis:waste_carp_route` (linha), campo `route_id` (não
      opcional), campo `route_sector_id` (opcional),
      `avg_collection_speed_kmh`, `shift_duration_h`,
      `unload_time_h`, `travel_time_to_destination_h`
      (`QgsProcessingParameterNumber`). Agrupa feições por
      (setor, `route_id`), soma `length` (km) por rota, chama
      `estimate_fleet_size` por setor. Saída = tabela sem geometria
      (`QgsWkbTypes.NoGeometry`) com campos `sector_id`,
      `fleet_size`, `num_routes`, `total_route_time_h`,
      `avg_utilization`. Reporta via `feedback.pushInfo` por setor;
      aviso informativo se `avg_utilization` < 0.5. — arquivos:
      `algorithms/waste_fleet_sizing.py`

- [x] 31. Registrar `WasteFleetSizing` (import + `addAlgorithm`) em
      `provider.py` (21 algorithms). Adicionar teste de metadata em
      `test_waste.py` (`test_waste_fleet_sizing_algorithm_metadata`,
      mesmo padrão dos algorithms anteriores de arc routing). —
      arquivos: `provider.py`, `test_waste.py`

- [x] 32. Rodar `make test` e `python3 -m unittest discover -s . -p
      "test_*.py"` para confirmar que o novo algorithm e o
      `provider.py` atualizado (21 algorithms) não quebram nada;
      corrigir o que for necessário até passar. Commitar e dar push
      da rodada 6. Verificado: commit `25890bf`, 171 testes OK, `make
      test` OK, `git status` limpo. — arquivos: nenhum novo
      (verificação + commit)

- [x] 33. **(Adiado a pedido do Diego — mesma decisão das rodadas
      anteriores, não bloqueia rodadas seguintes.)** Diego revisa
      manualmente no QGIS: roda `logis:waste_fleet_sizing` sobre a
      saída de `logis:waste_carp_route` de um setor de teste,
      confirma que o nº de veículos estimado e a utilização média
      fazem sentido para os parâmetros informados. Agrupado com os
      passos 7, 13, 18 e 27 para a revisão em lote futura. —
      arquivos: nenhum (revisão manual pelo Diego)

**Rodada 7 (Indicador 5.3 — Deadhead ratio como Processing algorithm dedicado):**

- [x] 34. Adicionar o campo booleano `route_is_deadhead` à saída de
      `algorithms/waste_cpp_route.py`: ao gravar cada feição do
      circuito, marcar `True` quando o `edge_id` já apareceu antes na
      sequência (é a cópia extra do trecho duplicado), `False` na
      primeira ocorrência. `QgsField("route_is_deadhead",
      qgis_compat.field_type("bool"))` adicionado a `out_fields`.
      Atualizar `shortHelpString`. — arquivos:
      `algorithms/waste_cpp_route.py`

- [x] 35. Adicionar o campo booleano `route_is_deadhead` à saída de
      `algorithms/waste_carp_route.py`: usar `req_id_set` (já
      calculado na linha 374) para marcar `route_is_deadhead =
      edge_id not in req_id_set` em cada feição escrita (linhas
      405-409). `QgsField("route_is_deadhead",
      qgis_compat.field_type("bool"))` adicionado a `out_fields`.
      Atualizar `shortHelpString`. — arquivos:
      `algorithms/waste_carp_route.py`

- [x] 36. `test_waste.py`: caso de regressão confirmando
      `route_is_deadhead` em `waste_cpp_route.py` (True na cópia
      duplicada, False na original) e em `waste_carp_route.py` (True
      exatamente nos `edge_id` fora de `req_id_set`), mesmo estilo do
      teste que a rodada 4 já fez para `route_is_connector`. Rodar
      `python3 -m unittest test_waste -v` e `make test`; só marcar
      `[x]` quando ambos passarem. — arquivos: `test_waste.py`

- [x] 37. Adicionar `compute_deadhead_ratio(lengths_km,
      deadhead_flags, route_ids=None) -> Dict` a
      `core/indicators/waste.py` (ver "Decisões de arquitetura — Novas
      para a rodada 7" acima): agrupamento por rota, soma de
      `productive_km`/`deadhead_km`, razão com proteção contra divisão
      por zero (`None` se `productive_km == 0`), validação de listas
      vazias/tamanho incompatível/valores negativos. Docstring no
      mesmo padrão das funções existentes do módulo. — arquivos:
      `core/indicators/waste.py`

- [x] 38. Adicionar a `test_waste.py` os seis casos de
      `compute_deadhead_ratio` listados em "Decisões de arquitetura"
      (sem deadhead, com deadhead calculado à mão, múltiplas rotas com
      agregação e total, rota 100% deadhead → `None` sem exceção,
      listas de tamanho incompatível, entrada vazia). Rodar
      `python3 -m unittest test_waste -v` e `make test`; só marcar
      `[x]` quando ambos passarem. — arquivos: `test_waste.py`

- [x] 39. Criar `algorithms/waste_deadhead_ratio.py`
      (`logis:waste_deadhead_ratio`): parâmetros = camada de entrada
      (linha, saída de `waste_cpp_route`/`waste_rpp_route`/
      `waste_carp_route`), campo booleano de deadhead
      (`QgsProcessingParameterField`, `DataType=Boolean`, não
      opcional), campo de agrupamento de rota opcional
      (`QgsProcessingParameterField`, `optional=True`). Lê
      comprimento via `feature.geometry().length()`, monta as três
      listas paralelas, chama `compute_deadhead_ratio`. Saída = tabela
      sem geometria (`QgsWkbTypes.NoGeometry`) com uma feição por rota
      (`route_id`, `productive_km`, `deadhead_km`, `deadhead_ratio`) +
      uma feição de total agregado (`route_id = NULL`). Reporta via
      `feedback.pushInfo` o total geral e aviso informativo por rota
      com `deadhead_ratio > 0.5`. `shortHelpString` documenta
      explicitamente que o campo de deadhead pode ser
      `route_is_deadhead` (CPP/CARP) ou `route_is_connector` (RPP).
      Registrar import + `addAlgorithm` em `provider.py` no mesmo
      passo (22 algorithms). — arquivos:
      `algorithms/waste_deadhead_ratio.py`, `provider.py`

- [x] 40. Adicionar `test_waste_deadhead_ratio_algorithm_metadata` em
      `test_waste.py`, mesmo padrão dos algorithms anteriores. Rodar
      `make test` e `python3 -m unittest discover -s . -p
      "test_*.py"` para confirmar que o novo algorithm e o
      `provider.py` atualizado (22 algorithms) não quebram nada;
      corrigir o que for necessário até passar. Commitar e dar push
      da rodada 7. — arquivos: `test_waste.py`, nenhum arquivo novo
      além do já listado no passo 39 (verificação + commit)

- [x] 41. **(Adiado a pedido do Diego — mesma decisão das rodadas
      anteriores, não bloqueia rodadas seguintes.)** Diego revisa
      manualmente no QGIS: roda `logis:waste_deadhead_ratio` sobre a
      saída de `waste_cpp_route`, `waste_rpp_route` e
      `waste_carp_route` de um setor de teste, confirma que a razão
      calculada bate com o `feedback.pushInfo` que os três algorithms
      de rota já imprimiam antes desta rodada. Agrupado com os passos
      7, 13, 18, 27 e 33 para a revisão em lote futura. — arquivos:
      nenhum (revisão manual pelo Diego)

## Critério de aceite

- **Passos 1-33 (F1-F6 completo, incluindo dimensionamento de frota):
  já satisfeitos e verificados nesta revisão** — ver "Objetivo" acima
  (commit `25890bf`, 171 testes, `make test` OK, `git status` limpo).
- **Rodada 7 (deadhead ratio):** `core/indicators/waste.py` ganha
  `compute_deadhead_ratio`, sem import de `qgis.*`, com docstring no
  mesmo padrão das três funções existentes — elas permanecem
  inalteradas.
- `algorithms/waste_cpp_route.py` e `algorithms/waste_carp_route.py`
  passam a gravar `route_is_deadhead` (booleano) por feição de saída,
  sem alterar nenhum campo ou comportamento já existente
  (`route_visit_order`, `route_sector_id`, `route_id` continuam iguais).
  `algorithms/waste_rpp_route.py` não muda.
- `test_waste.py` cobre `compute_deadhead_ratio` (sem deadhead, com
  deadhead, múltiplas rotas + total, rota 100% deadhead, listas
  incompatíveis, entrada vazia) e os dois casos de regressão de
  `route_is_deadhead` (CPP e CARP); continua passando junto com todos
  os testes das rodadas anteriores.
- Novo Processing algorithm `logis:waste_deadhead_ratio` registrado em
  `provider.py`, em `algorithms/waste_deadhead_ratio.py`, mesmo grupo
  "Logística Especializada — Coleta de Lixo" (22 algorithms no
  total), com saída em formato de tabela (sem geometria) e aceitando
  tanto `route_is_deadhead` quanto `route_is_connector` como campo de
  entrada.
- `make test` e `python3 -m unittest discover -s . -p "test_*.py"`
  continuam passando depois da mudança.
- Nenhuma dependência externa nova — só PyQGIS + stdlib.
- Ao fechar a rodada 7, um dos quatro indicadores de 5.3 ainda
  informais (deadhead ratio) passa a ser um Processing algorithm
  formal e reutilizável; os outros três (equilíbrio entre setores,
  distância média ao destino, cobertura por frequência) continuam
  explicitamente fora de escopo — ver "Fora de escopo" no Objetivo —
  e cada um vira sua própria rodada futura.
- **A validação manual no QGIS (passos 7, 13, 18, 27, 33 e 41) NÃO é
  critério de fechamento desta rodada de código** — fica marcada como
  pendente e agrupada para revisão em lote posterior, por decisão
  explícita do Diego. O critério de "código fechado" desta rodada é
  satisfeito pelos itens acima (testes automatizados + `make test` +
  registro em `provider.py`), independentemente da revisão visual.
- **F7 (empacotamento) continua fora de escopo** até a rodada 7 (e
  idealmente as rodadas 8-10 dos indicadores 5.3 restantes) fecharem
  E a validação manual no QGIS em lote acontecer — nenhuma dessas duas
  condições está satisfeita ainda.
