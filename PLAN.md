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

**Achado (OR-Tools) — atualizado nesta revisão (2026-07-21):**
infraestrutura de detecção/instalação/UI (`core/optim_backend.py`,
`core/ortools_installer.py`, `gui/dependencies_dialog.py`) existe
desde o primeiro commit. Pedido explícito do Diego nesta revisão
conecta o primeiro solver: **CVRP está sendo conectado ao backend
OR-Tools** — `core/routing/vrp.py` ganha `solve_cvrp_ortools()` (mesma
assinatura de entrada/saída de `solve_cvrp()`) e `solve_cvrp()` ganha
o parâmetro `backend` que usa `pick_backend()` para escolher entre a
heurística pura e o OR-Tools, com fallback silencioso + log de aviso
(mesmo comportamento que `pick_backend()` já implementa). Ver "Nova
frente solicitada pelo Diego" e os passos 64-68 abaixo — **desenho
travado nesta revisão, implementação ainda pendente** (este plano não
implementa código, só planeja). `facility.py`, `arc_routing.py` e
`districting.py` continuam sem chamar `pick_backend()` — fora de
escopo até o Diego pedir explicitamente para cada um.

**F6 rodada 7 (deadhead ratio) — FECHADA e commitada (`edf4796`,
mensagem "F6 atualiza").** Verificado nesta revisão (2026-07-21) por
leitura direta do código, não por confiança no plano herdado:
- `algorithms/waste_cpp_route.py` linha 202 e
  `algorithms/waste_carp_route.py` linha 311: ambos gravam o campo
  `route_is_deadhead` em `out_fields`, exatamente como desenhado.
- `core/indicators/waste.py` linha 209: `compute_deadhead_ratio`
  implementada, mesmo padrão de docstring das três funções
  anteriores.
- `algorithms/waste_deadhead_ratio.py` existe (265 linhas),
  `logis:waste_deadhead_ratio` registrado — `grep -c "addAlgorithm"
  provider.py` → **22**.
- `python3 -m unittest discover -s . -p "test_*.py"` → **176 testes,
  OK** (crescimento de 171 → 176 é consistente com os 5 casos de
  `compute_deadhead_ratio` + regressão de `route_is_deadhead` da
  rodada 7).
- `git status` → limpo, nada pendente de commit.

**F6 rodada 8 (equilíbrio entre setores) — FECHADA e commitada
(`b2db10c`, mensagem "F6 5").** Verificado nesta revisão
(2026-07-21) por leitura direta do código e execução da suíte, não
por confiança no plano herdado:
- `algorithms/waste_carp_route.py` grava `route_load_kg` e
  `route_distance_km` por feição (diff do commit: `+14/-7` linhas,
  só no bloco de escrita da feição — nenhum campo existente mudou).
- `core/indicators/waste.py` ganhou `compute_route_balance` (145
  linhas novas), quinta função pura do módulo, mesmo padrão de
  docstring das quatro anteriores.
- `algorithms/waste_sector_balance.py` existe (412 linhas),
  `logis:waste_sector_balance` registrado — `grep -c "addAlgorithm"
  provider.py` → **23**.
- `python3 -m unittest discover -s . -p "test_*.py"` → **185 testes,
  OK** (crescimento de 176 → 185 é consistente com os 6 casos de
  `compute_route_balance` + regressão de `route_load_kg`/
  `route_distance_km` + metadata do novo algorithm).
- `git status` → limpo, nada pendente de commit.

**F6 — as quatro entregas do roadmap formal e dois dos quatro
indicadores de 5.3 (deadhead ratio, equilíbrio entre setores):
FECHADOS.** Restam dois indicadores de 5.3 (distância média ao ponto
de destino, cobertura por frequência de coleta) para fechar
completamente a seção 5.3 do CLAUDE.md — são as rodadas 9 e 10
planejadas abaixo.

**Descoberta desta revisão que simplifica a rodada 9:** o módulo
Urbano já resolve exatamente o mesmo problema de "distância ao ponto
mais próximo de um conjunto de candidatos, via rede viária" —
`algorithms/urban_delivery_distance.py` (`logis:urban_delivery_distance`)
já compõe `core/network/graph_builder.build_graph` +
`core/network/od_matrix.compute_od_matrix` +
`core/indicators/urban.nearest_depot_cost` para calcular a distância
de cada zona ao depósito candidato mais próximo. A rodada 9
("distância média ao ponto de destino — aterro/transbordo/ecoponto")
é o mesmo problema com outro rótulo de domínio (destino de descarte em
vez de depósito de origem) — reaproveita as três funções existentes
sem duplicar lógica de grafo/Dijkstra em `core/indicators/waste.py`,
que hoje só tem funções puras sem `qgis.*` (rodada 9 é a primeira do
módulo waste a depender de `qgis.analysis` via `graph_builder`/
`od_matrix`, e por isso vive só na camada de algorithm, não em
`core/indicators/waste.py`).

**Ciclo em andamento: F6 rodadas 9 e 10 — os dois últimos indicadores
de 5.3.** Ver "Decisões de arquitetura — Novas para a rodada 9" e
"Novas para a rodada 10" abaixo para o desenho completo.

**Fora de escopo nesta revisão do plano (deferido, não esquecido):**
- **Renomear `route_is_connector` (RPP) para um nome comum com CPP/CARP**
  — decisão explícita: **não** renomear um campo já commitado e
  testado sem ganho funcional (regra geral do projeto contra
  mudanças cosméticas).
- **Extrair a fórmula de duração de rota (`dist/velocidade +
  descarga + deslocamento`) para uma função compartilhada entre
  `estimate_fleet_size` e `compute_route_balance`** — decisão
  explícita: **não** extrair um helper para três linhas de aritmética
  repetidas (regra geral do projeto: "três linhas parecidas é melhor
  que abstração prematura"). Reavaliar só se um terceiro consumidor da
  mesma fórmula aparecer.
- **Augment-Merge** (segunda heurística de CARP, seção 6 item 3) —
  inalterado, só entra se a qualidade do Path-Scanning simples não for
  suficiente na prática.
- **Vias de mão única / grafo misto-direcionado** (seção 6, item 3,
  `oneway` do OSM) — inalterado. Candidato natural a próxima grande
  iniciativa **depois** que as rodadas 9-10 fecharem a seção 5.3
  inteira, mas é uma mudança estrutural em `core/routing/arc_routing.py`
  (CPP/RPP/CARP passam a tratar arestas dirigidas), não um indicador
  incremental — precisa de uma decisão de prioridade com o Diego antes
  de virar uma rodada dedicada, não está pré-aprovada por este plano.
- **Split-delivery** — fora de escopo, decisão já tomada na rodada 5.
- **Integração em GUI (dock)** para o módulo de coleta de lixo — os
  módulos Urbano e Regional já têm dock (`gui/urban_dock.py`,
  `gui/regional_dock.py`); o módulo waste não tem nenhum. Continua
  deferido pela mesma razão de todos os ciclos anteriores (nenhum
  pedido explícito do Diego), mas é uma decisão que o Diego precisa
  tomar explicitamente antes de considerar o F7 "pronto para
  publicar" — um plugin público sem dock para 1 dos 3 módulos pode ser
  aceitável (uso só via console/Processing Toolbox) ou não, dependendo
  do padrão de qualidade que o Diego quer para a primeira publicação.
  Não assumir a resposta — perguntar antes de iniciar esse trabalho.
- **Validação manual no QGIS** (rodadas 2 a 8, mais 9 e 10 quando
  fecharem) — decisão mantida, revisão em lote posterior, ver passo
  novo consolidado abaixo.
- **Conectar o backend OR-Tools a algum solver real** — inalterado.
- **F7 — Empacotamento** — só começa a preparação (não a publicação)
  depois que as rodadas 9-10 fecharem a seção 5.3 inteira. A
  publicação em si no repositório oficial de plugins do QGIS depende
  também da validação manual no QGIS em lote (ainda pendente) — ver
  passos de F7 no final do plano, que já podem ser preparados em
  paralelo (i18n, LICENSE, ícone) sem esperar a validação manual.

**Nova frente solicitada pelo Diego nesta revisão (2026-07-21),
prioritária — executar antes de retomar a rodada 9: backend OR-Tools
para o CVRP.** Pedido explícito, mais detalhado que a rodada anterior
(que só tinha o desenho geral) — **esta revisão substitui as decisões
de arquitetura da rodada anterior sobre este tópico** (arquivo irmão
`vrp_ortools.py` e "wiring do `pick_backend()` fora de escopo"), com
um desenho mais específico que o Diego pediu diretamente:

- `solve_cvrp_ortools()` implementada **dentro de `core/routing/vrp.py`**
  (não em um arquivo irmão), mesma assinatura de entrada/retorno de
  `solve_cvrp()`, usando `ortools.constraint_solver.routing`
  (`RoutingIndexManager`, `RoutingModel`,
  `AddDimensionWithVehicleCapacity` para a restrição de capacidade).
  Import lazy/guardado, mesmo padrão de `core/optim_backend.py`.
- `solve_cvrp()` ganha um parâmetro **`backend`** que chama
  `pick_backend()` (já existente em `core/optim_backend.py`) para
  decidir entre a heurística pura e o OR-Tools, com fallback
  silencioso + log de aviso — **isso É a seleção automática que a
  rodada anterior tinha marcado como fora de escopo; o Diego pediu
  explicitamente agora**, então deixa de ser uma decisão pendente.
- Testes em `test_vrp.py` (não em um arquivo `test_vrp_ortools.py`
  separado): instância pequena resolvida via OR-Tools, fallback com
  `ImportError` mockado (confirma que `pick_backend()` degrada para a
  heurística pura mesmo que o ambiente de teste não tenha OR-Tools
  instalado, sem depender do estado real do ambiente), e os dois
  backends retornando no formato esperado (`routes`, `total_distance`,
  `route_loads`).
- Docstring no mesmo estilo do restante de `vrp.py` (referência
  bibliográfica, limite de complexidade, `Args`/`Returns`/`Raises` em
  PT).

Continua **fora de escopo** (decisão que não mudou): nenhum novo
Processing algorithm `logis:*`, nenhuma mudança em
`algorithms/vrp_cvrp.py`/`provider.py` — a seleção de backend via UI
do Processing Toolbox é uma decisão de UX separada que o Diego não
pediu nesta rodada. Não bloqueia nem depende das rodadas 9-10 do F6
(módulos diferentes, sem sobreposição de arquivos) — pode ser feita em
paralelo ou antes, na ordem que o executor preferir; continua como
passos novos ao final da lista de "Passos" (não renumerando os passos
1-63 já existentes) para não perturbar as referências cruzadas já
registradas neste plano (ex.: passo 58 cita "passos 7, 13, 18, 27, 33,
41, 49").

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

### Novas para o backend OR-Tools do CVRP (solicitado pelo Diego — revisão 2026-07-21, substitui a decisão anterior)

- **`solve_cvrp_ortools()` dentro do próprio `core/routing/vrp.py`,
  não em arquivo irmão** (decisão explícita do Diego nesta revisão,
  substitui a decisão anterior de `core/routing/vrp_ortools.py`). O
  import do OR-Tools continua 100% lazy/guardado (ver abaixo), então o
  "custo" de manter o arquivo livre de `ortools` mesmo guardado — o
  motivo original da separação — deixa de ser um problema real: quem
  não usa OR-Tools nunca executa o `import` porque ele vive dentro do
  corpo da função, só acionado quando `backend` resolve para
  `"ortools"`. Atualizar o docstring de módulo de `vrp.py` (hoje diz
  "VRP pure-Python heuristics module") para mencionar que o módulo
  também expõe um backend OR-Tools opcional.
- **Assinatura de `solve_cvrp_ortools` idêntica a `solve_cvrp`**
  (exigência explícita do Diego, mantida): `solve_cvrp_ortools(
  distance_matrix, demands, capacity, depot=0, improve=True) ->
  Tuple[List[List[int]], float, List[float]]`.
- **`solve_cvrp()` ganha o parâmetro `backend: str = "python"`.**
  Default `"python"` preserva o comportamento atual para todo código
  existente que já chama `solve_cvrp()` sem esse argumento (nenhuma
  mudança de comportamento por padrão) — consistente com a seção 2 do
  CLAUDE.md ("heurística pura... como padrão obrigatório; OR-Tools...
  nunca obrigatório"). No início de `solve_cvrp`, `resolved =
  pick_backend(backend)` (importado de `core.optim_backend`, mesmo
  padrão de import guardado relativo/absoluto já usado em
  `core/ortools_installer.py`: `try: from ..optim_backend import
  pick_backend / except ImportError: from core.optim_backend import
  pick_backend`); se `resolved == "ortools"`, delega diretamente para
  `solve_cvrp_ortools(distance_matrix, demands, capacity, depot=depot,
  improve=improve)` e retorna o resultado; caso contrário (`"python"`,
  seja porque foi o pedido ou porque `pick_backend` fez o fallback
  silencioso) segue o caminho já existente (Clarke-Wright + 2-opt/Or-
  opt). O fallback silencioso + log de aviso já é comportamento de
  `pick_backend()` — `solve_cvrp` não precisa reimplementar isso, só
  consumir o resultado. Documentar `backend` no `Args` do docstring
  (valores aceitos, comportamento de fallback).
- **Reaproveitar a validação de entrada já existente em `vrp.py` em vez
  de duplicá-la.** `_validate_matrix_and_depot` já é reutilizável
  diretamente (mesmo arquivo agora, sem import cruzado). A lista de
  checagens de demanda (tamanho compatível, não-negativa, capacidade >
  0, demanda de nó não excede capacidade) hoje vive inline dentro de
  `clarke_wright_savings` — extrair para um helper privado
  `_validate_demands(demands, capacity, num_nodes, depot)` chamado por
  `clarke_wright_savings` e por `solve_cvrp_ortools` é reúso legítimo
  (~15 linhas de validação já testada, não abstração prematura de "três
  linhas parecidas") e evita duplicar regra de negócio entre os dois
  caminhos dentro do mesmo arquivo.
- **Import do OR-Tools 100% lazy, dentro de `solve_cvrp_ortools`, não
  no topo do módulo.** `from ortools.constraint_solver import
  pywrapcp, routing_enums_pb2` só é executado dentro da função, depois
  da validação de entrada. Isso garante que: (a) a validação de entrada
  (e os testes que a cobrem) funciona mesmo sem OR-Tools instalado; (b)
  `import core.routing.vrp` nunca falha por causa de uma dependência
  ausente — só falha a chamada de `solve_cvrp_ortools` (ou
  `solve_cvrp(backend="ortools")` sem fallback, o que não acontece
  porque `pick_backend` já filtra isso antes) — com uma mensagem clara
  em PT-BR (mesmo estilo de `core/optim_backend.pick_backend`),
  orientando a instalar via `core/ortools_installer.py` ou usar
  `solve_cvrp()` (heurística pura) como alternativa. Consistente com a
  seção 2 do CLAUDE.md ("OR-Tools... nunca obrigatório, com import
  lazy/guarded e fallback automático para a heurística pura").
- **Número de veículos: limite superior calculado, não parâmetro
  novo** (a assinatura não pode ganhar parâmetro extra). OR-Tools exige
  um número fixo de veículos no modelo; usar
  `num_vehicles = min(len(customers), max(1, ceil(sum(demands) /
  capacity)) + 2)` — o mesmo raciocínio de "veículos suficientes para
  cobrir a demanda total, com uma folga pequena para o solver ter
  liberdade de balancear rotas", limitado ao número de clientes (pior
  caso: um veículo por cliente, mesmo ponto de partida do
  Clarke-Wright). Documentar no docstring como limitação conhecida:
  entradas com distribuição de demanda muito desigual podem, em teoria,
  exigir mais veículos do que essa folga cobre — se o solver não achar
  solução, a função levanta `RuntimeError` claro em vez de silenciar ou
  tentar de novo com mais veículos (mantém a implementação simples;
  reavaliar só se o Diego encontrar um caso real que precise disso).
- **Escala para inteiros nos callbacks do OR-Tools, sem perda de
  precisão no retorno.** `RoutingModel`/`AddDimensionWithVehicleCapacity`
  exigem custos e capacidades inteiros. O callback de distância
  registra `round(distance_matrix[i][j] * 1000)` (3 casas decimais de
  precisão) e o callback de demanda registra `round(demands[i] *
  1000)`/`round(capacity * 1000)` na mesma escala. Esses valores
  inteiros são usados **só para o solver decidir o agrupamento/ordem
  dos clientes** — depois de extrair as rotas (lista de índices de
  cliente por veículo, ignorando veículos com rota vazia
  depósito→depósito), a função recalcula `total_distance` e
  `route_loads` a partir dos valores `float` originais usando
  `compute_route_distance` já existente em `vrp.py` (reúso direto, mesma
  função que `solve_cvrp` usa) — garante que o valor retornado tem a
  mesma precisão/formato de `solve_cvrp`, sem arredondamento vazando
  para o resultado.
- **Parâmetro `improve` mapeado para a estratégia de busca do
  OR-Tools**, não para um novo conceito: `improve=False` usa só a
  primeira solução (`PATH_CHEAPEST_ARC`, sem metaheurística) — equivalente
  a "só construção", como `solve_cvrp(improve=False)` retorna só o
  resultado do Clarke-Wright sem 2-opt/Or-opt; `improve=True` (padrão)
  ativa `GUIDED_LOCAL_SEARCH` como metaheurística de melhoria, com um
  limite de tempo interno curto e fixo (constante de módulo, ex.:
  `_TIME_LIMIT_SECONDS = 10` — não é parâmetro, pois a assinatura não
  pode mudar). Documentar a constante no docstring como o "orçamento de
  tempo" do backend.
- **Caso sem clientes** (`demands` todos zero, exceto o depósito):
  retorna `([], 0.0, [])`, mesmo comportamento de `solve_cvrp` — checado
  antes de montar o modelo do OR-Tools (evita instanciar
  `RoutingIndexManager` com zero clientes).
- **Referência bibliográfica:** Perron, L., & Furnon, V. (2019).
  *OR-Tools* (Google, versão open source). Documentação oficial do
  módulo `ortools.constraint_solver.routing` — é a referência já usada
  pelo próprio pacote OR-Tools para o VRP Solver baseado em
  Constraint Programming/busca local.
- **Fora de escopo desta rodada (decisão explícita, não esquecida):**
  - **Exposição do parâmetro `backend` na UI do Processing algorithm
    (`algorithms/vrp_cvrp.py`)** — diferente da rodada anterior, o
    `pick_backend()` agora É chamado (dentro de `solve_cvrp()`, a
    pedido explícito do Diego), mas `vrp_cvrp.py` continua chamando
    `solve_cvrp(...)` sem passar `backend` — usa o default `"python"`
    implicitamente. Adicionar um `QgsProcessingParameterBoolean` ("usar
    OR-Tools se disponível") para o usuário final do plugin escolher é
    uma mudança de UX separada que o Diego não pediu nesta rodada.
  - **Nenhum novo Processing algorithm `logis:*`** — `solve_cvrp_ortools`
    é só mais uma função pura em `core/routing/vrp.py`, no mesmo nível
    de `clarke_wright_savings`/`two_opt`/`or_opt` (que também não têm
    algorithm próprio — só `solve_cvrp` tem, via `vrp_cvrp.py`).
    `provider.py` não muda nesta rodada.
  - **Nenhuma tentativa automática de aumentar `num_vehicles` e
    tentar de novo se o solver não achar solução** — ver acima.

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

### Novas para a rodada 8 (indicador de equilíbrio entre setores)

- **`algorithms/waste_carp_route.py` ganha dois campos numéricos por
  feição, `route_load_kg` e `route_distance_km`**, no mesmo lugar
  onde hoje monta `out_fields` (linhas 300-311): `route_load_kg` =
  `route["load_kg"]` da rota à qual a feição pertence (mesmo valor
  repetido em todas as feições do mesmo `route_id`, igual ao padrão
  já usado para `route_sector_id`); `route_distance_km` =
  `route["distance_m"] / 1000.0`, também repetido por `route_id`.
  Fonte: os dois valores já existem em `route` dentro do loop `for
  route_idx, route in enumerate(routes, start=1)` (linha ~377), só
  não são gravados na feição — mesmo tipo de gap que a rodada 7
  fechou para `route_is_deadhead`. Não muda nenhum campo ou
  comportamento existente. Atualizar `shortHelpString`.
- **Nova função pura `compute_route_balance(route_loads_kg,
  route_times_h, sector_ids=None) -> Dict`** em
  `core/indicators/waste.py`, mesmo estilo de `compute_deadhead_ratio`
  (função pura, sem `qgis.*`, uma entrada por rota):
  - `route_loads_kg`: `List[float]`, carga de cada rota em kg (valores
    ≥ 0).
  - `route_times_h`: `List[float]`, duração de cada rota em horas
    (valores ≥ 0), mesmo tamanho de `route_loads_kg`.
  - `sector_ids`: `Optional[List[Any]]`, mesmo tamanho, identificador
    de setor por rota; se `None`, trata todas as rotas como um único
    grupo (mesmo padrão "sem campo de setor = um grupo só" já usado em
    `compute_deadhead_ratio`).
  - Valida: listas não vazias, mesmo tamanho entre as três listas
    (quando `sector_ids` fornecido), valores não-negativos
    (`ValueError` caso contrário).
  - Algoritmo: agrupa por `sector_id` (ou um grupo único); por grupo e
    no total, calcula `num_routes`, média (`*_mean`), desvio-padrão
    populacional (`*_std`, fórmula `sqrt(sum((x - mean)²) / N)`) e
    coeficiente de variação (`*_cv = std / mean` se `mean > 0`, senão
    `None` — mesma proteção contra divisão por zero já usada em
    `compute_deadhead_ratio`) — para carga (`load_mean_kg`,
    `load_std_kg`, `load_cv`) e para tempo (`time_mean_h`,
    `time_std_h`, `time_cv`) separadamente.
  - Retorna `{"sectors": {sector_id: {"num_routes": int,
    "load_mean_kg": float, "load_std_kg": float, "load_cv":
    Optional[float], "time_mean_h": float, "time_std_h": float,
    "time_cv": Optional[float]}}, "total": {mesmos campos, agregado
    sobre todas as rotas}}`.
  - Referência bibliográfica: Daganzo, C. F. (2005). *Logistics
    Systems Analysis* (4th ed.). Springer — capítulo sobre
    balanceamento de distritos/rotas em sistemas logísticos (mesma
    obra de referência para o problema de equilíbrio entre setores,
    ainda não citada em `core/indicators/waste.py`).
  - Complexidade: O(N), N = número de rotas de entrada — uma passada
    de agrupamento e soma, sem laço aninhado.
  - **Sem extração de helper com `estimate_fleet_size`** — a fórmula
    de duração por rota é recalculada inline no algorithm da rodada 8
    (três linhas), não dentro desta função nem importada de
    `estimate_fleet_size` (decisão registrada em "Fora de escopo"
    acima).
- **Algorithm novo: `algorithms/waste_sector_balance.py`
  (`logis:waste_sector_balance`)**, mesmo grupo "Logística
  Especializada — Coleta de Lixo". Parâmetros: camada de entrada
  (linha, saída de `logis:waste_carp_route`, já com `route_id`,
  `route_load_kg` e `route_distance_km` após o passo anterior); campo
  `route_id` (`QgsProcessingParameterField`, não opcional); campo de
  setor opcional (`route_sector_id`, `optional=True`); campo
  `route_load_kg` (`QgsProcessingParameterField`, não opcional, default
  `'route_load_kg'`); campo `route_distance_km`
  (`QgsProcessingParameterField`, não opcional, default
  `'route_distance_km'`); `avg_collection_speed_kmh`,
  `unload_time_h`, `travel_time_to_destination_h`
  (`QgsProcessingParameterNumber`, mesmos nomes, defaults e limites já
  usados em `waste_fleet_sizing.py`, para manter os parâmetros
  reconhecíveis entre os dois algorithms). Agrupa feições por
  `route_id` (uma rota = várias feições/trechos repetindo o mesmo
  `route_id`; lê `route_load_kg`/`route_distance_km`/`route_sector_id`
  uma vez por `route_id`, já que são repetidos por feição), calcula
  `route_time_h = route_distance_km / avg_collection_speed_kmh +
  unload_time_h + travel_time_to_destination_h` por rota (mesma
  fórmula de `estimate_fleet_size`, linhas duplicadas de propósito),
  monta `route_loads_kg`, `route_times_h`, `sector_ids` e chama
  `compute_route_balance`. **Saída: tabela sem geometria**
  (`QgsWkbTypes.NoGeometry`, mesmo padrão de `waste_fleet_sizing` e
  `waste_deadhead_ratio`) com uma feição por setor (`sector_id`,
  `num_routes`, `load_mean_kg`, `load_std_kg`, `load_cv`,
  `time_mean_h`, `time_std_h`, `time_cv`) — mais uma feição final com
  `sector_id = NULL` representando o total agregado (só quando há mais
  de um setor, mesmo padrão condicional já usado em
  `waste_deadhead_ratio`). Reporta via `feedback.pushInfo` o total
  geral e um aviso informativo por setor com `load_cv > 0.3` ou
  `time_cv > 0.3` (mais de 30% de variação entre rotas — desequilíbrio
  relevante; mesmo padrão de aviso informativo, não erro, já usado em
  `waste_carp_route`/`waste_fleet_sizing`). Registrar import +
  `addAlgorithm` em `provider.py` no mesmo passo (23 algorithms).
- **Testes:** `test_waste.py` ganha casos para `compute_route_balance`:
  (a) rotas perfeitamente equilibradas (`*_std` e `*_cv` = 0); (b)
  rotas desequilibradas com desvio calculado à mão; (c) múltiplos
  setores via `sector_ids` (agregação correta por grupo + total); (d)
  grupo com média zero (`load_mean_kg == 0` → `load_cv is None`, sem
  levantar exceção); (e) listas de tamanho incompatível
  (`ValueError`); (f) entrada vazia (`ValueError`). Mais um teste de
  metadata do algorithm (`test_waste_sector_balance_algorithm_metadata`).
  `test_waste.py` também ganha um caso de regressão para
  `route_load_kg`/`route_distance_km` em `waste_carp_route.py`
  (confirma que o valor gravado em cada feição bate com
  `route["load_kg"]`/`route["distance_m"]` da rota correspondente,
  mesmo estilo do teste que a rodada 7 já fez para
  `route_is_deadhead`).

### Novas para a rodada 9 (indicador 5.3 — distância média ao ponto de destino)

- **Nenhuma função nova em `core/indicators/waste.py`.** Reaproveitar
  integralmente `core/network/graph_builder.build_graph`,
  `core/network/od_matrix.compute_od_matrix` e
  `core/indicators/urban.nearest_depot_cost` — as três já
  implementam "distância de N zonas ao candidato mais próximo de M
  pontos, via caminho mínimo na rede" (usadas hoje por
  `algorithms/urban_delivery_distance.py`). Importar
  `nearest_depot_cost` de `core.indicators.urban` a partir do
  algorithm do módulo waste é reúso explícito entre módulos, não
  duplicação — a função é genérica (assinatura em termos de matriz
  OD, sem nada específico de entrega urbana).
- **Algorithm novo: `algorithms/waste_destination_distance.py`
  (`logis:waste_destination_distance`)**, grupo "Logística
  Especializada — Coleta de Lixo". Estrutura de
  `processAlgorithm` **copiada** de `urban_delivery_distance.py`
  (mesmos 7 passos: reprojeção para EPSG:5880, leitura de destinos,
  leitura de zonas, `build_graph` com `points=destinos+zonas`,
  `compute_od_matrix` com `cache_id="waste_destination_distance"`,
  `nearest_depot_cost`, escrita do campo). Parâmetros:
  - `INPUT_NETWORK`: camada de rede viária (linha) — mesma rede usada
    para gerar as rotas do setor.
  - `INPUT_DESTINATIONS`: camada de pontos candidatos de destino
    (aterro/estação de transbordo/ecoponto) — 1 ou mais feições.
  - `INPUT_ZONES`: camada de pontos representando setores de coleta
    (centroide do setor ou ponto de referência da rota, ex.: saída de
    `logis:waste_districting` dissolvida e centroide extraído fora do
    plugin, ou qualquer camada de ponto por setor que o usuário já
    tenha).
  - `CRITERION`: enum Distância/Tempo, mesmo padrão de
    `urban_delivery_distance.py`.
  - `OUTPUT`: cópia da camada de zonas + campo `dist_destino`
    (`double`), mesmo padrão de `dist_entrega`.
  - `shortHelpString` deixa explícito que "destino" aqui é
    aterro/transbordo/ecoponto (não depósito/garagem — esse já é
    coberto por `logis:waste_fleet_sizing`/`waste_carp_route` via o
    parâmetro de depósito do CARP).
  - Reporta via `feedback.pushInfo` a distância/tempo médio (`sum(costs)
    / len(costs)`, calculado inline — não vira função nova, é uma
    linha de aritmética, mesma regra de "não abstrair 3 linhas" já
    registrada acima) e mínimo/máximo entre as zonas.
  - Registrar import + `addAlgorithm` em `provider.py` no mesmo passo
    (24 algorithms).
- **Testes:** `test_waste.py` (ou `test_delivery_distance.py`, a
  decidir pelo padrão de nomenclatura já em uso — algorithms movidos
  ao módulo waste testam em `test_waste.py` nas rodadas anteriores,
  manter consistência) ganha `test_waste_destination_distance_algorithm_metadata`,
  mesmo padrão dos algorithms anteriores. Não precisa de novo teste de
  lógica de grafo — `nearest_depot_cost` e `compute_od_matrix` já têm
  cobertura própria; o teste aqui é só metadata (name/displayName/
  group/groupId) igual às rodadas 7 e 8, já que o corpo do algorithm
  não roda sem uma instância QGIS.

### Novas para a rodada 10 (indicador 5.3 — cobertura por frequência de coleta)

- **Interpretação adotada (mais simples que modelar frequência por
  aresta):** "frequência" é um **rótulo descritivo do rodada de
  execução**, não um atributo persistido por trecho de via. O usuário
  já teria, antes de rodar este algorithm, uma camada de vias
  filtrada/marcada com um campo booleano "exige coleta nesta faixa de
  frequência" (mesmo padrão de campo booleano já usado no RPP para
  "trecho obrigatório") — roda o algorithm uma vez por faixa de
  frequência que quiser medir (ex.: uma vez para "diária", outra para
  "semanal"), passando o rótulo como parâmetro de texto só para
  aparecer no relatório/saída. Evita inventar um novo esquema de
  atributo de frequência por aresta sem um pedido concreto do Diego
  sobre como essa frequência é de fato armazenada nos dados reais dele.
- **Nova função pura `compute_collection_coverage(required_km,
  covered_km, sector_ids=None) -> Dict`** em
  `core/indicators/waste.py`, mesmo estilo de `compute_deadhead_ratio`
  (agrupamento por setor ou grupo único, uma entrada por setor desta
  vez — não por trecho — já que required/covered já chegam como somas
  por setor calculadas no algorithm):
  - `required_km`: `List[float]`, km de via que exige coleta na faixa
    de frequência, por setor (valores ≥ 0).
  - `covered_km`: `List[float]`, km efetivamente cobertos por uma rota
    real (trechos produtivos, i.e. onde o campo de deadhead é
    `False`), mesmo tamanho de `required_km`.
  - `sector_ids`: `Optional[List[Any]]`, mesmo tamanho; se `None`,
    trata como um único setor (mesmo padrão das funções anteriores).
  - Valida: listas não vazias, mesmo tamanho, valores não-negativos
    (`ValueError` caso contrário).
  - `coverage_pct = covered_km / required_km` por setor (capado em
    `min(1.0, ...)` — cobertura acima de 100% é fisicamente possível
    se o setor recebe mais de uma passada, mas o indicador reporta
    cobertura de *extensão distinta*, não de passadas repetidas;
    documentar essa decisão no docstring), `None` se `required_km ==
    0` (mesma proteção contra divisão por zero das funções anteriores).
  - Retorna `{"by_sector": {sector_id: {"required_km": float,
    "covered_km": float, "coverage_pct": Optional[float]}}, "total":
    {mesmos campos, agregado}}`.
  - Referência bibliográfica: Toregas et al. (1971) — mesma citação já
    usada em `core/location/facility.py` para LSCP, aplicável aqui
    porque cobertura de extensão de rede é o mesmo conceito de
    cobertura de conjunto (set covering) aplicado a comprimento em vez
    de contagem de nós.
  - Complexidade: O(N), N = número de setores.
- **Algorithm novo: `algorithms/waste_collection_coverage.py`
  (`logis:waste_collection_coverage`)**, mesmo grupo "Logística
  Especializada — Coleta de Lixo". Parâmetros: camada de vias exigidas
  nesta faixa de frequência (linha, campo de setor opcional); camada
  de rota coberta (linha, saída de `waste_cpp_route`/`waste_rpp_route`/
  `waste_carp_route`, com o campo booleano de deadhead
  `route_is_deadhead`/`route_is_connector` — mesmo campo aceito por
  `waste_deadhead_ratio`, reaproveitar o mesmo
  `QgsProcessingParameterField` de tipo Boolean); campo de setor
  opcional na camada de rota; rótulo de frequência (`QgsProcessingParameterString`,
  ex.: "diária", "2x/semana" — só para exibição, não entra no cálculo).
  Soma `required_km` por setor (via `feature.geometry().length()` na
  camada exigida) e `covered_km` por setor (soma de comprimento na
  camada de rota onde o campo de deadhead é `False`), chama
  `compute_collection_coverage`. **Saída: tabela sem geometria**
  (`QgsWkbTypes.NoGeometry`, mesmo padrão de `waste_deadhead_ratio`/
  `waste_sector_balance`) com uma feição por setor (`sector_id`,
  `frequency_label`, `required_km`, `covered_km`, `coverage_pct`) +
  feição de total agregado (`sector_id = NULL`) quando há mais de um
  setor. Reporta via `feedback.pushInfo` o total geral e aviso
  informativo por setor com `coverage_pct < 0.8` (menos de 80% da
  extensão exigida efetivamente coberta pela rota gerada — mesmo
  padrão de aviso informativo, não erro, das rodadas anteriores).
  Registrar import + `addAlgorithm` em `provider.py` no mesmo passo
  (25 algorithms).
- **Testes:** `test_waste.py` ganha casos para
  `compute_collection_coverage`: (a) cobertura completa (100%); (b)
  cobertura parcial calculada à mão; (c) múltiplos setores via
  `sector_ids` (agregação + total); (d) `required_km == 0` →
  `coverage_pct is None` sem exceção; (e) cobertura > 100% (capada em
  1.0); (f) listas de tamanho incompatível (`ValueError`); (g) entrada
  vazia (`ValueError`). Mais `test_waste_collection_coverage_algorithm_metadata`.

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

**Rodada 8 (Indicador 5.3 — Equilíbrio entre setores: desvio de carga e tempo entre rotas):**

- [x] 42. Adicionar os campos numéricos `route_load_kg` e
      `route_distance_km` à saída de `algorithms/waste_carp_route.py`:
      dentro do loop `for route_idx, route in enumerate(routes,
      start=1)` (linha ~377), capturar `route["load_kg"]` e
      `route["distance_m"] / 1000.0`; ao escrever cada feição do
      circuito (linha ~412-414), acrescentar os dois valores em
      `out_feat.setAttributes(...)` (mesmo valor repetido em todas as
      feições do mesmo `route_id`, igual ao padrão já usado para
      `route_sector_id`). `QgsField("route_load_kg",
      qgis_compat.field_type("double"))` e `QgsField(
      "route_distance_km", qgis_compat.field_type("double"))`
      adicionados a `out_fields`. Atualizar `shortHelpString`. Não
      alterar nenhum campo ou comportamento já existente
      (`route_visit_order`, `route_sector_id`, `route_is_deadhead`
      continuam iguais). — arquivos: `algorithms/waste_carp_route.py`

- [x] 43. `test_waste.py`: caso de regressão confirmando que
      `route_load_kg` e `route_distance_km` gravados em cada feição
      batem com `route["load_kg"]`/`route["distance_m"]` da rota
      correspondente (mesmo `route_id`), mesmo estilo do teste que a
      rodada 7 já fez para `route_is_deadhead`. Rodar `python3 -m
      unittest test_waste -v` e `make test`; só marcar `[x]` quando
      ambos passarem. — arquivos: `test_waste.py`

- [x] 44. Adicionar `compute_route_balance(route_loads_kg,
      route_times_h, sector_ids=None) -> Dict` a
      `core/indicators/waste.py` (ver "Decisões de arquitetura — Novas
      para a rodada 8" acima): agrupamento por setor (ou grupo único),
      cálculo de `num_routes`, média, desvio-padrão populacional e
      coeficiente de variação (`std/mean`, `None` se `mean == 0`) para
      carga e para tempo, validação de listas vazias/tamanho
      incompatível/valores negativos. Docstring no mesmo padrão das
      funções existentes do módulo, referência Daganzo (2005). —
      arquivos: `core/indicators/waste.py`

- [x] 45. Adicionar a `test_waste.py` os seis casos de
      `compute_route_balance` listados em "Decisões de arquitetura"
      (rotas equilibradas, rotas desequilibradas calculadas à mão,
      múltiplos setores com agregação e total, grupo com média zero →
      `cv is None` sem exceção, listas de tamanho incompatível,
      entrada vazia). Rodar `python3 -m unittest test_waste -v` e
      `make test`; só marcar `[x]` quando ambos passarem. — arquivos:
      `test_waste.py`

- [x] 46. Criar `algorithms/waste_sector_balance.py`
      (`logis:waste_sector_balance`): parâmetros = camada de entrada
      (linha, saída de `waste_carp_route`), campo `route_id` (não
      opcional), campo de setor opcional, campo `route_load_kg` (não
      opcional, default `'route_load_kg'`), campo `route_distance_km`
      (não opcional, default `'route_distance_km'`),
      `avg_collection_speed_kmh`, `unload_time_h`,
      `travel_time_to_destination_h` (mesmos nomes/defaults/limites de
      `waste_fleet_sizing.py`). Agrupa feições por `route_id`, calcula
      `route_time_h = route_distance_km / avg_collection_speed_kmh +
      unload_time_h + travel_time_to_destination_h` por rota (fórmula
      duplicada de propósito, sem helper compartilhado — ver "Fora de
      escopo"), chama `compute_route_balance`. Saída = tabela sem
      geometria (`QgsWkbTypes.NoGeometry`) com uma feição por setor
      (`sector_id`, `num_routes`, `load_mean_kg`, `load_std_kg`,
      `load_cv`, `time_mean_h`, `time_std_h`, `time_cv`) + feição de
      total agregado quando há mais de um setor (`sector_id = NULL`).
      Reporta via `feedback.pushInfo` o total geral e aviso
      informativo por setor com `load_cv > 0.3` ou `time_cv > 0.3`. —
      arquivos: `algorithms/waste_sector_balance.py`

- [x] 47. Registrar `WasteSectorBalance` (import + `addAlgorithm`) em
      `provider.py` (23 algorithms). Adicionar
      `test_waste_sector_balance_algorithm_metadata` em
      `test_waste.py`, mesmo padrão dos algorithms anteriores. —
      arquivos: `provider.py`, `test_waste.py`

- [x] 48. Rodar `make test` e `python3 -m unittest discover -s . -p
      "test_*.py"` para confirmar que os novos campos, a nova função e
      o novo algorithm (23 algorithms em `provider.py`) não quebram
      nada; corrigir o que for necessário até passar. Commitar e dar
      push da rodada 8. — arquivos: nenhum novo (verificação + commit)

- [x] 49. **(Adiado a pedido do Diego — mesma decisão das rodadas
      anteriores, não bloqueia rodadas seguintes.)** Diego revisa
      manualmente no QGIS: roda `logis:waste_sector_balance` sobre a
      saída de `waste_carp_route` de um cenário de teste com setores
      propositalmente desbalanceados (um setor com rotas de carga/tempo
      muito distintas), confirma que o desvio-padrão e o coeficiente
      de variação calculados fazem sentido e que o aviso de
      desequilíbrio (`cv > 0.3`) aparece quando esperado. Agrupado com
      os passos 7, 13, 18, 27, 33 e 41 para a revisão em lote futura. —
      arquivos: nenhum (revisão manual pelo Diego)

**Rodada 9 (Indicador 5.3 — distância média ao ponto de destino):**

- [x] 50. Criar `algorithms/waste_destination_distance.py`
      (`logis:waste_destination_distance`), estrutura copiada de
      `algorithms/urban_delivery_distance.py` (ver "Decisões de
      arquitetura — Novas para a rodada 9"): parâmetros
      `INPUT_NETWORK`, `INPUT_DESTINATIONS` (pontos de
      aterro/transbordo/ecoponto), `INPUT_ZONES` (pontos de setor),
      `CRITERION` (Distância/Tempo), `OUTPUT` (cópia de zonas + campo
      `dist_destino`). Reaproveita `build_graph`, `compute_od_matrix`,
      `core.indicators.urban.nearest_depot_cost` — nenhuma função nova
      em `core/indicators/waste.py`. Registrar import + `addAlgorithm`
      em `provider.py` (24 algorithms). — arquivos:
      `algorithms/waste_destination_distance.py`, `provider.py`

- [x] 51. Adicionar `test_waste_destination_distance_algorithm_metadata`
      em `test_waste.py` (name/displayName/group/groupId, mesmo padrão
      dos algorithms anteriores). Rodar `make test` e `python3 -m
      unittest discover -s . -p "test_*.py"` para confirmar que o novo
      algorithm e o `provider.py` atualizado (24 algorithms) não
      quebram nada; corrigir o que for necessário até passar. Commitar
      e dar push da rodada 9. — arquivos: `test_waste.py`, nenhum
      arquivo novo além do já listado no passo 50 (verificação +
      commit)

**Rodada 10 (Indicador 5.3 — cobertura por frequência de coleta):**

- [x] 52. Adicionar `compute_collection_coverage(required_km,
      covered_km, sector_ids=None) -> Dict` a
      `core/indicators/waste.py` (ver "Decisões de arquitetura — Novas
      para a rodada 10"): agrupamento por setor, `coverage_pct =
      covered_km / required_km` capado em 1.0, proteção contra divisão
      por zero (`None` se `required_km == 0`), validação de listas
      vazias/tamanho incompatível/valores negativos. Docstring no
      mesmo padrão das funções existentes, referência Toregas et al.
      (1971). — arquivos: `core/indicators/waste.py`

- [x] 53. Adicionar a `test_waste.py` os sete casos de
      `compute_collection_coverage` listados em "Decisões de
      arquitetura" (cobertura completa, parcial calculada à mão,
      múltiplos setores + total, `required_km == 0` → `None`,
      cobertura > 100% capada, listas incompatíveis, entrada vazia).
      Rodar `python3 -m unittest test_waste -v` e `make test`; só
      marcar `[x]` quando ambos passarem. — arquivos: `test_waste.py`

- [x] 54. Criar `algorithms/waste_collection_coverage.py`
      (`logis:waste_collection_coverage`): parâmetros = camada de vias
      exigidas na faixa de frequência (linha, campo de setor
      opcional), camada de rota coberta (linha, saída de
      `waste_cpp_route`/`waste_rpp_route`/`waste_carp_route`, campo
      booleano de deadhead — `route_is_deadhead` ou
      `route_is_connector`, campo de setor opcional), rótulo de
      frequência (`QgsProcessingParameterString`). Soma `required_km`
      e `covered_km` por setor a partir da geometria, chama
      `compute_collection_coverage`. Saída = tabela sem geometria
      (`QgsWkbTypes.NoGeometry`) com uma feição por setor (`sector_id`,
      `frequency_label`, `required_km`, `covered_km`, `coverage_pct`) +
      feição de total agregado quando há mais de um setor. Reporta via
      `feedback.pushInfo` o total geral e aviso informativo por setor
      com `coverage_pct < 0.8`. — arquivos:
      `algorithms/waste_collection_coverage.py`

- [x] 55. Registrar `WasteCollectionCoverage` (import + `addAlgorithm`)
      em `provider.py` (25 algorithms). Adicionar
      `test_waste_collection_coverage_algorithm_metadata` em
      `test_waste.py`, mesmo padrão dos algorithms anteriores. —
      arquivos: `provider.py`, `test_waste.py`

- [x] 56. Rodar `make test` e `python3 -m unittest discover -s . -p
      "test_*.py"` para confirmar que a nova função, o novo algorithm
      e o `provider.py` atualizado (25 algorithms) não quebram nada;
      corrigir o que for necessário até passar. Commitar e dar push da
      rodada 10. — arquivos: nenhum novo (verificação + commit)

**Fechamento formal da seção 5.3 do CLAUDE.md:**

- [ ] 57. Atualizar a seção "Objetivo" deste plano confirmando que os
      quatro indicadores de 5.3 (deadhead ratio, equilíbrio entre
      setores, distância média ao destino, cobertura por frequência)
      estão implementados como Processing algorithms formais — F6
      passa de "roadmap formal fechado" para "seção 5.3 inteira
      fechada". — arquivos: nenhum (atualização de plano)

- [ ] 58. **(Revisão manual do Diego no QGIS — consolidada, não
      bloqueia o início dos passos de F7 abaixo.)** Numa única sessão,
      com um município piloto de MG e rede OSM real: revisar em lote
      os passos adiados 7, 13, 18, 27, 33, 41, 49 (setorização, CPP,
      RPP, CARP, dimensionamento de frota, equilíbrio entre setores) e
      as duas rodadas novas (distância ao destino, cobertura por
      frequência). Só depois desta revisão o F6 é considerado
      "encerrado" para fins de decidir publicar o plugin (F7) — a
      preparação de F7 abaixo pode rodar em paralelo, mas a publicação
      em si (passo 63) espera este passo. — arquivos: nenhum (revisão
      manual pelo Diego)

**F7 — Preparação para empacotamento (pode começar em paralelo à revisão do passo 58; publicação em si espera):**

- [ ] 59. Perguntar ao Diego, antes de iniciar qualquer trabalho de
      GUI: o módulo de coleta de lixo entra no F7 sem dock (uso só via
      Processing Toolbox/console, como hoje), ou o Diego quer um
      `gui/waste_dock.py` no padrão de `gui/urban_dock.py`/
      `gui/regional_dock.py` antes da primeira publicação? Não assumir
      a resposta — é uma decisão de escopo do Diego, não técnica. Se a
      resposta for "sim, quero o dock", isso vira uma rodada própria
      (fora deste plano até a resposta chegar). — arquivos: nenhum
      (decisão do Diego)

- [ ] 60. Criar a estrutura `i18n/` (hoje ausente, embora
      `__init__.py` já referencie `i18n/logis_{locale}.qm` na linha
      10): arquivo fonte de tradução `i18n/logis_pt_BR.ts` e
      `i18n/logis_en.ts` gerados a partir das strings `self.tr(...)`
      já espalhadas pelos algorithms/gui (via `pylupdate5` ou
      equivalente), traduzir as strings, compilar para `.qm`
      (`lrelease`). Confirmar que o plugin carrega sem erro tanto com
      locale pt_BR quanto com outro locale (fallback). — arquivos:
      `i18n/logis_pt_BR.ts`, `i18n/logis_en.ts`,
      `i18n/logis_pt_BR.qm`, `i18n/logis_en.qm`

- [ ] 61. Adicionar `LICENSE` (texto GPL-3.0, conforme seção 9 do
      CLAUDE.md) e `icon.png` (arquivo referenciado em
      `metadata.txt` na chave `icon=icon.png` mas ausente do
      repositório) — ambos exigidos pelo processo de submissão ao
      repositório oficial de plugins do QGIS. — arquivos: `LICENSE`,
      `icon.png`

- [ ] 62. Revisar `metadata.txt` com o Diego antes do empacotamento
      final: decidir se `experimental=True` deve virar `False`,
      confirmar `version` (semver) e o texto de `about`/`description`
      ainda refletem o estado atual (25 algorithms, 3 módulos). Ajustar
      o `Makefile` com um alvo `make package` que gera
      `dist/logis-<version>.zip` a partir do estado commitado (hoje só
      existe `dist/logis-0.1.0.zip`, sem alvo de Makefile que o gere —
      confirmar como foi criado e automatizar). — arquivos:
      `metadata.txt`, `Makefile`

- [ ] 63. Publicação: gerar o zip final com `make package`, testar
      instalação a partir do zip (não do symlink de `make deploy`) numa
      instância limpa do QGIS, e o Diego submete ao repositório oficial
      de plugins do QGIS (plugins.qgis.org) — ação externa/manual do
      Diego, fora do escopo de execução automatizada. Só depois do
      passo 58 (validação manual em lote) estar concluído. — arquivos:
      nenhum (ação manual do Diego)

**Nova rodada — backend OR-Tools para o CVRP (prioritária, executar
antes de retomar a rodada 9; desenho revisado nesta sessão — mesmo
arquivo `vrp.py`, parâmetro `backend` em `solve_cvrp()`; ver "Decisões
de arquitetura — Novas para o backend OR-Tools do CVRP" acima para o
desenho completo):**

- [ ] 64. Em `core/routing/vrp.py`, extrair de dentro de
      `clarke_wright_savings` um helper privado `_validate_demands(
      demands, capacity, num_nodes, depot)` com as checagens que já
      existem ali (tamanho de `demands` compatível com a matriz,
      demanda negativa, `capacity <= 0`, demanda de nó excedendo
      `capacity`) — mesmas mensagens de `ValueError` de hoje, só
      movidas para a função nova; `clarke_wright_savings` passa a
      chamar `_validate_demands(...)` no lugar do bloco inline. Rodar
      `python3 -m unittest test_vrp -v` e `make test` para confirmar
      que nenhum teste existente quebrou (mesmas mensagens/comportamento,
      só refatorado) antes de seguir para o próximo passo. — arquivos:
      `core/routing/vrp.py`

- [ ] 65. Adicionar `solve_cvrp_ortools(distance_matrix, demands,
      capacity, depot=0, improve=True) -> Tuple[List[List[int]], float,
      List[float]]` em `core/routing/vrp.py` (logo após `solve_cvrp`):
      valida a entrada reaproveitando `_validate_matrix_and_depot` +
      `_validate_demands` (passo 64); trata o caso sem clientes
      retornando `([], 0.0, [])` antes de tocar no OR-Tools; só então
      faz o import lazy de
      `ortools.constraint_solver.pywrapcp`/`routing_enums_pb2` dentro da
      função, capturando `ImportError` e levantando `RuntimeError` com
      mensagem clara em PT-BR (instalar via `core/ortools_installer.py`
      ou usar `solve_cvrp`); monta `RoutingIndexManager(num_nodes,
      num_vehicles, depot)` com `num_vehicles = min(len(customers),
      max(1, ceil(sum(demands) / capacity)) + 2)`; registra callback de
      distância e de demanda com valores escalados para inteiro
      (`round(x * 1000)`); chama `AddDimensionWithVehicleCapacity` com
      a capacidade escalada; define estratégia de busca conforme
      `improve` (só `PATH_CHEAPEST_ARC` se `False`; +
      `GUIDED_LOCAL_SEARCH` com limite de tempo interno fixo
      `_TIME_LIMIT_SECONDS` se `True`); resolve; se não achar solução,
      levanta `RuntimeError` claro; extrai as rotas por veículo
      (ignorando veículos com rota vazia depósito→depósito) e recalcula
      `total_distance`/`route_loads` com os valores `float` originais
      via `compute_route_distance` (já no mesmo arquivo). Docstring com
      referência bibliográfica (Perron & Furnon, OR-Tools), limite de
      complexidade/escala documentado e a mesma seção
      `Args`/`Returns`/`Raises` das demais funções de `vrp.py`. —
      arquivos: `core/routing/vrp.py`

- [ ] 66. Adicionar o parâmetro `backend: str = "python"` a
      `solve_cvrp()`: import guardado de `pick_backend` no topo de
      `vrp.py` (`try: from ..optim_backend import pick_backend / except
      ImportError: from core.optim_backend import pick_backend`, mesmo
      padrão relativo/absoluto de `core/ortools_installer.py`); logo no
      início do corpo de `solve_cvrp`, `resolved = pick_backend(backend)`
      — se `resolved == "ortools"`, delega para
      `solve_cvrp_ortools(distance_matrix, demands, capacity,
      depot=depot, improve=improve)` e retorna o resultado direto; caso
      contrário (`"python"`, seja por pedido direto ou por fallback
      silencioso do `pick_backend`) segue o caminho já existente
      (Clarke-Wright + 2-opt/Or-opt), sem nenhuma outra mudança de
      comportamento. Atualizar o docstring de `solve_cvrp` (`Args` ganha
      `backend`, explicando os valores aceitos `"python"`/`"ortools"` e
      o fallback silencioso com log de aviso). Rodar `python3 -m
      unittest test_vrp -v` e `make test`; confirmar que todos os testes
      que já chamam `solve_cvrp(...)` sem `backend` continuam passando
      inalterados (default `"python"` preserva o comportamento atual). —
      arquivos: `core/routing/vrp.py`

- [ ] 67. Ampliar `test_vrp.py` (não criar arquivo novo) com: (a)
      instância pequena (reaproveitar `self.distance_matrix`/
      `self.demands`/`self.capacity` de `setUp`) resolvida via
      `solve_cvrp_ortools` diretamente **e** via
      `solve_cvrp(backend="ortools")`, guardada com
      `@unittest.skipUnless(has_ortools(), "OR-Tools não instalado")`
      (importar `has_ortools` de `core.optim_backend`) — confirma
      formato de retorno (`routes`/`total_distance`/`route_loads`) e
      solução válida (todo cliente em exatamente uma rota, nenhuma rota
      excede `capacity`), rodando com `improve=True` e `improve=False`;
      (b) teste de fallback com `ImportError` **mockado** via
      `unittest.mock.patch` — força a ausência do OR-Tools
      independentemente do que está instalado no ambiente (ex.:
      `patch("core.optim_backend.has_ortools", return_value=False)` ou
      equivalente no ponto onde `pick_backend` decide) e confirma que
      `solve_cvrp(backend="ortools")` não levanta exceção, cai no
      caminho heurístico puro e retorna exatamente o mesmo resultado de
      `solve_cvrp(backend="python")` para a mesma instância — este teste
      roda sempre, independente de OR-Tools estar instalado ou não; (c)
      teste de regressão confirmando que `solve_cvrp(...)` sem `backend`
      (default) continua com o resultado idêntico ao já coberto por
      `test_solve_cvrp_without_improve`/`test_solve_cvrp_with_improve`;
      (d) validação de entrada de `solve_cvrp_ortools` reaproveitando os
      mesmos casos inválidos já testados para `clarke_wright_savings`
      (matriz vazia, demanda incompatível, demanda negativa, demanda
      excede capacidade, depósito inválido) e o caso sem clientes
      (`([], 0.0, [])`) — todos rodam sempre, pois a validação acontece
      antes do import lazy do OR-Tools. Rodar `python3 -m unittest
      test_vrp -v` e `make test`; só marcar `[x]` quando ambos
      passarem — neste ambiente de desenvolvimento o OR-Tools não está
      instalado, então os casos guardados com `skipUnless(has_ortools()
      ...)` (item a) aparecerão como `SKIPPED`, o que é esperado; o
      teste de fallback mockado (item b) **não** é `SKIPPED` — roda e
      precisa passar de fato aqui, mesmo sem OR-Tools instalado. —
      arquivos: `test_vrp.py`

- [ ] 68. Rodar `python3 -m unittest discover -s . -p "test_*.py"` e
      `make test` para confirmar que as mudanças em `vrp.py` não
      quebram nada existente (nenhuma mudança em `provider.py` ou em
      `algorithms/vrp_cvrp.py` nesta rodada — `vrp_cvrp.py` continua
      chamando `solve_cvrp(...)` sem passar `backend`, usa o default
      `"python"` implicitamente). Commitar e dar push. — arquivos:
      nenhum novo (verificação + commit)

## Critério de aceite

- **Passos 64-68 (backend OR-Tools para o CVRP — prioritário, desenho
  revisado nesta sessão):** `core/routing/vrp.py` (mesmo arquivo, sem
  módulo irmão) expõe `solve_cvrp_ortools()` com a mesma assinatura de
  entrada/saída de `solve_cvrp()`; import do OR-Tools é lazy (dentro da
  função) e `RuntimeError` claro é levantado se a biblioteca não
  estiver instalada, sem quebrar `import core.routing.vrp`; validação
  de entrada reaproveita `_validate_matrix_and_depot` +
  `_validate_demands` (helper extraído no passo 64); `solve_cvrp()`
  ganha o parâmetro `backend: str = "python"` que chama `pick_backend(
  backend)` (de `core.optim_backend`) e delega para
  `solve_cvrp_ortools` quando resolvido para `"ortools"`, com fallback
  silencioso + log de aviso herdado do próprio `pick_backend()`;
  `test_vrp.py` (mesmo arquivo, sem arquivo de teste separado) cobre
  validação (sempre), o teste de fallback com `ImportError`/
  `has_ortools` mockado (sempre, roda de fato mesmo sem OR-Tools
  instalado) e o caminho `solve_cvrp_ortools` real guardado com
  `skipUnless(has_ortools())` (`SKIPPED` neste ambiente, aceitável);
  `provider.py` e `algorithms/vrp_cvrp.py` **não mudam** nesta rodada
  (nenhum novo Processing algorithm, nenhuma exposição de `backend` na
  UI); `make test` e `python3 -m unittest discover -s . -p
  "test_*.py"` continuam passando.
- **Passos 1-49 (F1-F6 completo, incluindo deadhead ratio e equilíbrio
  entre setores): já satisfeitos e verificados nesta revisão** — ver
  "Objetivo" acima (commit `b2db10c`, 185 testes, `make test` OK,
  `git status` limpo, 23 algorithms em `provider.py`).
- **Rodada 9 (distância média ao ponto de destino):** novo Processing
  algorithm `logis:waste_destination_distance`
  (`algorithms/waste_destination_distance.py`), reaproveitando
  `build_graph`/`compute_od_matrix`/`nearest_depot_cost` já existentes
  (nenhuma função nova em `core/indicators/waste.py`); registrado em
  `provider.py` (24 algorithms); metadata coberta em `test_waste.py`.
- **Rodada 10 (cobertura por frequência de coleta):**
  `core/indicators/waste.py` ganha `compute_collection_coverage`, sem
  import de `qgis.*`, mesmo padrão de docstring das funções
  existentes; `test_waste.py` cobre os sete casos listados em
  "Decisões de arquitetura"; novo Processing algorithm
  `logis:waste_collection_coverage` registrado em `provider.py` (25
  algorithms), saída em tabela (sem geometria), uma feição por setor +
  total agregado.
- `make test` e `python3 -m unittest discover -s . -p "test_*.py"`
  continuam passando depois de cada rodada (9 e 10).
- Nenhuma dependência externa nova — só PyQGIS + stdlib — em nenhuma
  das duas rodadas.
- **Ao fechar a rodada 10, a seção 5.3 do CLAUDE.md fica 100%
  implementada como Processing algorithms formais** (os quatro
  indicadores: deadhead ratio, equilíbrio entre setores, distância ao
  destino, cobertura por frequência) — critério que fecha
  definitivamente o roadmap do F6.
- **A validação manual no QGIS (passo consolidado 58, cobrindo os
  passos adiados 7, 13, 18, 27, 33, 41, 49 e as rodadas 9-10) NÃO é
  critério de fechamento do código das rodadas 9-10** — mesma decisão
  já aplicada às rodadas anteriores. O critério de "código fechado" é
  satisfeito pelos testes automatizados + `make test` + registro em
  `provider.py`, independentemente da revisão visual.
- **F7 (preparação) pode começar em paralelo à revisão manual do passo
  58** — i18n (passo 60), LICENSE/ícone (passo 61) e revisão de
  `metadata.txt`/`Makefile` (passo 62) não dependem de QGIS rodando,
  só de decisões e arquivos. **A publicação em si (passo 63) espera**
  tanto o fechamento do F6 (rodadas 9-10) quanto a validação manual em
  lote (passo 58) — nenhuma das duas condições está satisfeita ainda.
- **A decisão sobre dock de GUI para o módulo waste (passo 59) é do
  Diego, não deste plano** — não presumir a resposta nem implementar
  antes de perguntar.
