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
0.1.0").

**F6 rodada 1 — Estimativa de geração de resíduos: fechada, commitada**
(inalterado).

**F6 rodada 2 — Setorização (districting): código completo, correto e
COMMITADO/PUSHED** (commit `b1127f7`, "feat(routing): setorizacao de
coleta (rodada 2)"; `git status` confirma working tree limpo).
`core/routing/districting.py`, `test_districting.py` e
`algorithms/waste_districting.py` implementam
`select_seed_edges_farthest_first` (Gonzalez 1985),
`grow_sectors_from_seeds` e `rebalance_boundary_edges` (Kalcsics,
Nickel & Schröder 2005). `provider.py` registra
`logis:waste_districting` (17 algorithms).

**Decisão desta revisão (pedido explícito do Diego): "deixar o teste
do QGIS pra depois, vamos avançar".** A validação manual no QGIS
(passo 7, herdado da rodada 2, e o futuro passo 15 da rodada 3) deixa
de ser pré-requisito para iniciar/fechar rodadas de código. Esses
passos continuam na lista, marcados como adiados, e viram uma revisão
em lote a fazer quando o Diego tiver ambiente QGIS disponível. O
executor segue direto para os passos de código da rodada 3 (CPP) sem
esperar por eles.

**Ciclo em andamento: F6 rodada 3 — Roteirização por arcos, CPP
(Chinese Postman Problem)** (seção 6, item 3 do CLAUDE.md, primeira
sub-técnica apenas: "todas as vias, grafo não direcionado:
emparelhamento dos nós de grau ímpar (matching guloso por menor
caminho) + circuito euleriano (Hierholzer)"). Esta rodada consome a
saída da rodada 2 (`collection_sector_id` por trecho) para gerar, por
setor, uma sequência de trechos (rota) que cobre todas as vias do
setor pelo menor custo adicional de repetição (deadhead). Mesmo
raciocínio de escopo enxuto das rodadas anteriores: **só CPP
não-direcionado nesta rodada** — RPP (subconjunto de vias) e CARP
(capacidade do caminhão) ficam para rodadas futuras do F6, porque cada
um adiciona uma dimensão de complexidade nova (RPP: nem toda aresta
precisa ser coberta; CARP: a rota fecha e reabre por capacidade) que
merece seu próprio ciclo de teste e revisão, como já ocorreu com
setorização vs. estimativa de geração.

Nenhum código de `arc_routing.py` existe ainda no repositório (só
está descrito em "Decisões de arquitetura" abaixo) — confirmado por
busca no working tree nesta revisão. Os passos 8–14 são, portanto, o
próximo trabalho real a executar.

**Fora de escopo nesta revisão do plano (deferido, não esquecido):**
- **RPP e CARP** (seção 6, item 3, sub-bullets 2 e 3) — próximas
  rodadas do F6 depois que CPP estiver implementado.
- **Vias de mão única / grafo misto-direcionado** (seção 6, item 3,
  último sub-bullet, usando `oneway` do OSM) — CPP nesta rodada assume
  grafo não direcionado, igual ao CLAUDE.md descreve como primeiro
  passo; direção fica para quando RPP/CARP entrarem (ou uma rodada
  dedicada, a decidir).
- **Dimensionamento de frota** (item 6 da seção 6) — depende de km
  produtivos/rota, que só existe depois de CPP/CARP.
- **Indicadores 5.3 restantes** (deadhead ratio, equilíbrio entre
  setores, distância média ao destino, cobertura por frequência) —
  "deadhead ratio" em particular fica trivial de calcular assim que
  CPP existir (comparação entre soma de `length` da rota e soma de
  `length` das vias do setor), mas o indicador em si (Processing
  algorithm dedicado) continua para depois, junto dos demais 5.3.
- **Integração em GUI (dock).** Mesmo raciocínio de todos os ciclos
  anteriores.
- **Validação manual no QGIS** (rodadas 2 e 3) — ver decisão acima;
  vira uma etapa de revisão em lote, agendada quando o Diego decidir
  retomar (não bloqueia o avanço do plano até lá).

## Decisões de arquitetura

### Herdadas da rodada 2 (setorização) — confirmadas corretas no código atual

- `core/routing/districting.py`, sem import de `qgis.*`; representação
  de grafo em lista de dicts (`id`, `from_node`, `to_node`, `length`,
  `load`), `node_key` calculado pela camada de algorithm (arredondamento
  em grade), não pelas funções puras.
- Três funções: `select_seed_edges_farthest_first` (Gonzalez k-center),
  `grow_sectors_from_seeds` (crescimento por menor carga acumulada),
  `rebalance_boundary_edges` (troca de fronteira com checagem de
  conectividade por BFS).
- Algorithm `logis:waste_districting` em `algorithms/waste_districting.py`,
  grupo "Logística Especializada — Coleta de Lixo" (`groupId="waste"`),
  saída = camada de vias com campo novo `collection_sector_id`.

### Novas para a rodada 3 (CPP)

- **Novo arquivo `core/routing/arc_routing.py`** (já previsto na árvore
  da seção 7, ao lado de `vrp.py` e `districting.py`) — sem import de
  `qgis.*`, mesma representação de edge da rodada 2 (reaproveita o
  mesmo formato de dict, permitindo passar a saída de
  `waste_districting` direto como entrada, filtrada por
  `collection_sector_id`).
- **Diferença chave em relação à rodada 2:** CPP precisa de caminho
  mínimo **ponderado por `length`** entre nós de grau ímpar (não hop
  count como o BFS de `select_seed_edges_farthest_first`). Isso exige
  um Dijkstra simples sobre o grafo de nós (não de trechos) — nós já
  existem implicitamente como `from_node`/`to_node` dos edges, então
  não é necessário reaproveitar `core/network/graph_builder.py`
  (mesma decisão de simplicidade da rodada 2: não precisamos de
  `QgsGraphBuilder`/`QgsVectorLayerDirector` para isso).
- **Quatro funções puras em `core/routing/arc_routing.py`:**
  1. `find_odd_degree_nodes(edges) -> List[node_key]` — grau de cada nó
     = número de trechos incidentes (contando trechos paralelos/loops
     corretamente); retorna os nós de grau ímpar. O(E).
  2. `shortest_path_between_nodes(edges, source, target) -> Tuple[float, List[edge_id]]`
     — Dijkstra padrão ponderado por `length` sobre o grafo de nós
     derivado de `edges`; retorna distância total e a lista ordenada
     de `edge_id` do caminho. Levanta `ValueError` se `source`/`target`
     não pertencem ao grafo ou se não há caminho (setor desconectado).
     O(E log V).
  3. `match_odd_degree_nodes(edges, odd_nodes) -> List[Tuple[node_key, node_key, List[edge_id]]]`
     — emparelhamento guloso (não é o matching ótimo de Edmonds/blossom;
     aceito como heurística "boa, não ótima" pela seção 2 do CLAUDE.md):
     repete até não sobrar nó — pega o primeiro nó ímpar ainda não
     emparelhado, calcula `shortest_path_between_nodes` até cada outro
     nó ímpar ainda não emparelhado, empareha com o mais próximo,
     remove os dois do conjunto. Retorna os pares junto com o caminho
     (lista de `edge_id`) que será duplicado. O(K² log V), K = número
     de nós de grau ímpar (tipicamente pequeno numa rede de bairro).
  4. `build_eulerian_circuit(edges, duplicated_edge_ids) -> List[edge_id]`
     — algoritmo de Hierholzer sobre o multigrafo obtido duplicando,
     no grafo original, os trechos em `duplicated_edge_ids` (a união
     dos caminhos retornados pelo emparelhamento, que torna todos os
     graus pares); retorna a sequência ordenada de `edge_id` do
     circuito euleriano (trechos duplicados aparecem duas vezes na
     sequência, na ordem de travessia). Levanta `ValueError` se, após
     a duplicação, ainda existir nó de grau ímpar (bug interno) ou se
     o grafo (do setor) for desconexo. O(E).
  - Referência bibliográfica única para o módulo (citada nas 4
    docstrings): Edmonds, J., & Johnson, E. L. (1973). Matching, Euler
    tours and the Chinese postman. *Mathematical Programming*, 5(1),
    88-124 — e Hierholzer, C. (1873). Über die Möglichkeit, einen
    Linienzug ohne Wiederholung und ohne Unterbrechung zu umfahren.
    *Mathematische Annalen*, 6(1), 30-32 (o artigo clássico do circuito
    euleriano).
  - Complexidade documentada nas docstrings, testado até a mesma escala
    da rodada 2 (~5.000 trechos por setor — CPP roda por setor, não na
    rede inteira de uma vez, então o volume por chamada é sempre menor
    ou igual ao de um setor de `waste_districting`).
- **Orquestração fica no algorithm, não em uma quinta função "solve_cpp".**
  Mesma decisão de estilo da rodada 2 (a rodada 2 também deixou a
  composição sequencial das 3 funções para o `processAlgorithm`, não
  criou uma função "faz tudo"): mantém cada função pura testável
  isoladamente e o algorithm apenas chama
  `find_odd_degree_nodes` → `match_odd_degree_nodes` → (união dos
  caminhos) → `build_eulerian_circuit`.
- **Testes:** `test_arc_routing.py` na raiz, mesmo padrão dos demais —
  topologias pequenas desenhadas à mão: um ciclo simples (0 nós
  ímpares, circuito euleriano direto sem duplicação), um grafo em
  forma de "Y" ou grade pequena com exatamente 2 nós de grau ímpar
  (duplicação de 1 caminho), um caso com 4+ nós ímpares (testa o
  emparelhamento guloso), e casos inválidos (edges vazio, `source`/
  `target` inexistente em `shortest_path_between_nodes`, setor
  desconexo).
- **Algorithm novo: `algorithms/waste_cpp_route.py`
  (`logis:waste_cpp_route`)**, mesmo grupo "Logística Especializada —
  Coleta de Lixo". Parâmetros: camada de vias (linha, tipicamente a
  saída de `logis:waste_districting`); campo `collection_sector_id`
  opcional (`QgsProcessingParameterField`, `optional=True` — se
  omitido, trata a camada inteira como um único setor, permitindo
  rodar CPP sem depender da rodada 2); tolerância de nó em metros
  (mesmo papel que na rodada 2, default igual, `0.01`). Para cada valor
  distinto de setor (ou uma vez só, se o campo for omitido):
  monta `edges` a partir da geometria, roda
  `find_odd_degree_nodes` → `match_odd_degree_nodes` →
  `build_eulerian_circuit`, e grava na camada de saída dois campos
  novos: `route_visit_order` (posição do trecho na sequência do
  circuito — trechos duplicados geram uma feição extra copiada, com
  `route_visit_order` diferente, para representar o deadhead) e
  `route_sector_id` (replica o valor do setor de origem, ou `0` se o
  campo foi omitido). Reporta via `feedback.pushInfo`, por setor: nº
  de trechos duplicados e km de deadhead (soma de `length` dos
  duplicados) — dado que o Diego vai olhar nessa métrica quando fizer
  a revisão manual (adiada) para julgar se o deadhead é razoável.
  Registrar import + `addAlgorithm` em `provider.py` no mesmo passo.
- **Saída:** camada de vias **com feições duplicadas** para os trechos
  cobertos duas vezes pelo circuito (diferente da rodada 2, que só
  adicionava um campo sem duplicar feições) — é a forma mais simples de
  representar uma rota com deadhead numa camada de linha sem inventar
  uma estrutura de dados nova (ex.: não cria uma tabela separada
  "sequência de rota"; usa o próprio modelo de camada vetorial que o
  QGIS já sabe desenhar e exportar).

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

- [x] 7. **(Adiado a pedido do Diego — não bloqueia a rodada 3.)**
      Diego revisa manualmente no QGIS a versão commitada (`b1127f7`):
      abre o plugin, roda `logis:waste_districting` com uma camada de
      vias de teste (com e sem campo de carga), confirma visualmente
      que os setores resultantes são contíguos, compactos e
      balanceados. Fica agrupado com o passo 15 para uma revisão em
      lote quando o Diego retomar os testes no QGIS. — arquivos:
      nenhum (revisão manual pelo Diego)

**Rodada 3 (CPP — roteirização por arcos) — próximos passos executáveis agora:**

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
      nó inexistente, setor desconexo). — arquivos:
      `test_arc_routing.py`

- [x] 12. Rodar `python3 -m unittest test_arc_routing -v` e
      `make test`; confirmar que passam antes de seguir para o
      algorithm. — arquivos: nenhum (verificação)

- [x] 13. Criar `algorithms/waste_cpp_route.py`
      (`logis:waste_cpp_route`): parâmetros = camada de vias, campo
      `collection_sector_id` opcional, tolerância de nó (metros).
      Roda CPP por setor (ou uma vez, se sem campo de setor), grava
      `route_visit_order` e `route_sector_id` na camada de saída
      (com feições duplicadas para trechos de deadhead), reporta
      trechos duplicados e km de deadhead por setor via
      `feedback.pushInfo`. Registrar import + `addAlgorithm` em
      `provider.py` no mesmo passo. — arquivos:
      `algorithms/waste_cpp_route.py`, `provider.py`

- [x] 14. Rodar `make test` e
      `python3 -m unittest discover -s . -p "test_*.py"` de novo para
      confirmar que o novo algorithm e o `provider.py` atualizado
      (18 algorithms) não quebram nada. — arquivos: nenhum (verificação)

- [x] 15. **(Adiado a pedido do Diego — não bloqueia rodadas
      seguintes.)** Diego revisa manualmente no QGIS: roda
      `logis:waste_cpp_route` sobre a saída de `logis:waste_districting`,
      confirma visualmente que a sequência de rota cobre todas as vias
      do setor e que o deadhead reportado é razoável para o tamanho da
      rede de teste. Agrupado com o passo 7 para revisão em lote
      quando o Diego retomar os testes no QGIS — até lá, a rodada 3 é
      considerada "código fechado, validação visual pendente" e o
      plano segue para a rodada seguinte do F6 sem esperar por ela. —
      arquivos: nenhum (revisão manual pelo Diego)

**Rodada 4 (RPP — Rural Postman Problem):**

- [x] 16. Adicionar `connect_required_components(required_edges, full_edges)`
      em `core/routing/arc_routing.py` (conecta componentes obrigatórios
      desconexos usando MST de caminhos mínimos sobre a rede completa). —
      arquivos: `core/routing/arc_routing.py`

- [x] 17. Criar `algorithms/waste_rpp_route.py` (`logis:waste_rpp_route`)
      e registrar em `provider.py` (19 algorithms no total). — arquivos:
      `algorithms/waste_rpp_route.py`, `provider.py`

- [x] 18. **(Adiado a pedido do Diego — não bloqueia rodadas
      seguintes.)** Diego revisa manualmente no QGIS: roda
      `logis:waste_rpp_route` sobre subconjunto de vias obrigatórias,
      confirma visualmente que a sequência de rota conecta os componentes
      e cobre todas as vias obrigatórias do setor. Agrupado com os passos 7
      e 15 para revisão em lote quando o Diego retomar os testes no QGIS —
      até lá, a rodada 4 é considerada "código fechado, validação visual
      pendente" e o plano segue para a rodada seguinte do F6 sem esperar
      por ela. — arquivos: nenhum (revisão manual pelo Diego)

## Critério de aceite

- `core/routing/arc_routing.py` existe com quatro funções puras
  (`find_odd_degree_nodes`, `shortest_path_between_nodes`,
  `match_odd_degree_nodes`, `build_eulerian_circuit`), sem import de
  `qgis.*`, cada uma com docstring citando referência bibliográfica
  (Edmonds & Johnson 1973; Hierholzer 1873) e limite de complexidade
  testado.
- `test_arc_routing.py` cobre as quatro funções (grafo já euleriano,
  2 nós ímpares, 4+ nós ímpares, casos inválidos) e passa em
  `python3 -m unittest`.
- Novo Processing algorithm registrado em `provider.py`
  (`logis:waste_cpp_route`), em `algorithms/waste_cpp_route.py`,
  mesmo grupo "Logística Especializada — Coleta de Lixo" (18
  algorithms no total).
- `make test` e `python3 -m unittest discover -s . -p "test_*.py"`
  continuam passando depois da mudança.
- A rota gerada cobre cada trecho do setor pelo menos uma vez; trechos
  cobertos duas vezes (deadhead) correspondem exatamente à união dos
  caminhos mínimos do emparelhamento de nós de grau ímpar — não precisa
  ser o emparelhamento ótimo (regra da seção 2 do CLAUDE.md: heurística
  gulosa aceita, documentada no `shortHelpString`).
- Nenhuma dependência externa nova — só PyQGIS + stdlib.
- RPP, CARP, vias de mão única, dimensionamento de frota e os
  indicadores 5.3 restantes ficam explicitamente fora desta rodada —
  ver "Fora de escopo" no Objetivo; cada um vira sua própria rodada
  futura dentro do F6.
- **A validação manual no QGIS (passos 7 e 15) NÃO é critério de
  fechamento desta rodada de código** — fica marcada como pendente e
  agrupada para revisão em lote posterior, por decisão explícita do
  Diego. O critério de "código fechado" desta rodada é satisfeito
  pelos itens acima (testes automatizados + `make test` + registro em
  `provider.py`), independentemente da revisão visual.
