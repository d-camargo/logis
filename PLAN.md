# PLAN — logis

## Objetivo

**Nota (2026-07-30) — F10: abas no painel de Indicadores Urbanos
(pedido explícito do Diego).** Depois de ver as abas do painel de Coleta
de Lixo funcionando (entrega do F9), o Diego pediu o mesmo tratamento
para o módulo Urbano: *"Na parte de Indicadores urbanos temos várias
opções também, vamos pelo mesmo caminho da coleta de lixo e criar abas
para que seja possível o usuário fazer 1 parte de cada vez."*

**Estado verificado no início desta revisão** (execução real, não
confiança no plano): `git status` limpo em `main`, `git log` em `4d4eaae`
("package: logis 0.1.2"); `python3 -m unittest discover -s . -p
"test_*.py"` → **Ran 228 tests, OK**; `make test` → `sintaxe OK`. F9 está
fechado no código — `logis/gui/waste_dock.py:190` tem `_new_tab`, quatro
`self._new_tab(...)` (linhas 234, 347, 493, 563) e `txt_results` no
`outer`; `urban_dock.py:177` e `regional_dock.py` já têm `QScrollArea`.

**O que o painel Urbano é hoje** (`logis/gui/urban_dock.py`, 680 linhas):
uma coluna única com rolagem, cinco blocos empilhados e **um único
`txt_results`** compartilhado por todos:

| Bloco (linhas atuais) | Método | Algorithms `logis:*` |
|---|---|---|
| Indicadores de rede (186-226) | `calculate_indicators` (319) | `urban_network_density`, `urban_network_connectivity`, `urban_mean_circuity`, **`urban_cargo_restriction`** |
| Densidade de Demanda (228-243) | `calculate_demand_density` (447) | `urban_demand_density` |
| Acessibilidade Gravitacional (245-275) | `calculate_gravity_accessibility` (501) | `urban_gravity_accessibility` |
| Betweenness (277-290) | `calculate_edge_betweenness` (570) | `urban_edge_betweenness` |
| Distância de Entrega (292-314) | `calculate_delivery_distance` (617) | `urban_delivery_distance` |

**Dois achados desta revisão que moldam o desenho:**

1. **Não há lacuna de cobertura** — diferente do que aconteceu no dock
   Waste (onde faltavam duas seções, passos 108-109), os **8** algorithms
   urbanos registrados em `provider.py` (`ls logis/algorithms/urban_*.py`)
   estão todos acessíveis pelo painel. F10 é remontagem de layout, não
   fechamento de lacuna.
2. **`cmb_network` é compartilhado por quatro fluxos** — linhas 326, 506,
   575 e 622 leem `self.cmb_network.currentLayer()`. Se ele for para
   dentro de uma aba, os fluxos das outras abas passam a depender de um
   widget invisível: o usuário abriria a aba "Carga" sem ter onde escolher
   a rede. Por isso o seletor de rede viária **fica no cabeçalho, fora
   das abas** (ver "Decisões de arquitetura — F10"). `cmb_area` só é lido
   em 327 (densidade) e vai para dentro da aba "Rede".

**Consequência do pedido "fazer 1 parte de cada vez": a restrição de
carga sai do botão-pacote.** Hoje `calculate_indicators` roda quatro
algorithms em sequência num único clique, e o quarto
(`urban_cargo_restriction`, linhas 425-442) é justamente o indicador de
**operação de carga** — a família que dá nome à terceira aba na seção 5.1
do CLAUDE.md. Mantê-lo dentro do pacote deixaria a aba "Carga" com uma
seção só e obrigaria o usuário a rodar três cálculos de rede para obter
um indicador de carga. Ele vira seção própria com botão próprio
(`calculate_cargo_restriction`), e o pacote passa a ser de **três**
indicadores de rede. É a única mudança de comportamento de F10, e é
exatamente o que o Diego pediu.

**Nota (2026-07-29, segunda revisão do dia) — F9: usabilidade dos painéis
no QGIS 4.2 ("Belém do Pará").** O Diego instalou a versão 0.1.1 (saída
do F8) no **QGIS 4.2 sobre Ubuntu** e trouxe quatro constatações e um
pedido:

1. **Painel sem rolagem** — "tem mais informações que aparecem, mas não
   tem a opção de rolar para baixo": os painéis **Urbano** e **Regional**
   cortam o conteúdo. Confirmado no código nesta revisão: `grep -n
   "QScrollArea" logis/gui/*.py` só encontra `waste_dock.py`;
   `urban_dock.py:305` e `regional_dock.py:237` fazem
   `self.setWidget(central)` direto, sem área de rolagem. O `urban_dock`
   tem 8 seções em coluna única (linha 168-305) e o `regional_dock`, 5 —
   nenhum cabe numa dock lateral em tela normal.
2. **QGIS 4.2 é o ambiente-alvo real** do teste — o F8 já entregou
   `supportsQt6=True` e os enums escopados; nada a refazer aí, mas o
   número da versão testada passa a ser registrado no README.
3. **Diálogo "Dependências" abre com o texto errado** — "é uma questão
   de dimensionamento da janela". Duas causas prováveis, ambas visíveis
   no fonte: (a) `gui/dependencies_dialog.py:193` e `:227` aplicam
   `setStyleSheet("font-weight: bold; padding: 10px;")` **no QGroupBox
   sem seletor**, o que no Qt6 faz o título do grupo sobrepor/cortar o
   conteúdo (o `padding` passa a valer para o box inteiro e o título
   continua ancorado na borda); (b) o diálogo é aberto com
   `resize(550, 420)` fixo (linha 165) enquanto o conteúdo real —
   dois grupos com parágrafos `setWordWrap(True)`, barra de progresso,
   área de log de 100 px e aviso de reinício — pede mais altura, e sem
   rolagem o excedente simplesmente não aparece.
4. **A instalação do OR-Tools no Ubuntu funcionou** (validação do
   comando com as três travas da seção 2.1 do CLAUDE.md, entregue no
   passo 94) — nada a corrigir, só a registrar.
5. **Pedido explícito: abas no painel de Coleta de Lixo.** O painel
   funciona e tem rolagem, mas o Diego quer as opções em **abas** em vez
   de todas empilhadas. Ver "Decisões de arquitetura — F9" para o
   agrupamento escolhido.

**Achado desta revisão, não relatado pelo Diego: o dock de Coleta de
Lixo só cobre 8 dos 10 algorithms do módulo.** `grep -n "logis:waste"
logis/gui/waste_dock.py` lista `waste_generation_estimate`,
`waste_cpp_route`, `waste_rpp_route`, `waste_carp_route`,
`waste_fleet_sizing`, `waste_sector_balance`,
`waste_destination_distance`, `waste_collection_coverage` — **faltam
`logis:waste_districting` (Setorização) e `logis:waste_deadhead_ratio`
(Deadhead Ratio)**, apesar de os passos 71 e 76 estarem marcados `[x]` e
de a decisão de arquitetura do dock (2026-07-23) prever "dez seções, uma
por algorithm". Os dois algorithms existem e estão registrados em
`provider.py`; o que falta é só a seção de UI. Como a reorganização em
abas já vai mexer em todas as seções, é a hora barata de fechar a
lacuna — entra nesta rodada (passos 108 e 109).

**Estado verificado no início desta revisão** (execução real, não
confiança no plano): `git status` limpo em `main`, `git log` no commit
`6c152b7` ("package: logis 0.1.1"); `python3 -m unittest discover -s .
-p "test_*.py"` → **Ran 224 tests, OK**; `make test` → `sintaxe OK`.
F8 está fechado no código; F9 é uma rodada de **UI/UX apenas** — nenhum
algorithm, nenhuma função de `core/`, nenhuma dependência nova.

**Nota (2026-07-29) — F8: compatibilidade com QGIS 4 / Qt 6 (PyQt6).**
O Diego rodou o plugin no QGIS 4 (perfil `.../QGIS/QGIS4/profiles/default`,
Flatpak) e recebeu dois `AttributeError` no log:

- `logis_plugin.py:69` → `type object 'Qt' has no attribute
  'RightDockWidgetArea'. Did you mean: 'DockWidgetArea'?`
- `gui/dependencies_dialog.py:158` → `type object 'Qt' has no attribute
  'WindowMinMaxButtonsHint'`

Causa raiz única: **no PyQt6 todos os enums do Qt são escopados**
(`Qt.DockWidgetArea.RightDockWidgetArea`, `Qt.WindowType.WindowMinMax
ButtonsHint`); as formas "soltas" do PyQt5 deixaram de existir. Os dois
tracebacks são só a ponta visível — a auditoria feita nesta revisão
encontrou o mesmo padrão em várias outras famílias de enum e mais duas
quebras independentes do PyQt6. Inventário verificado no código atual
(2026-07-29, `grep` no repo):

| Sítio | Ocorrências | Quebra no Qt6? |
|---|---|---|
| `Qt.RightDockWidgetArea` (`logis_plugin.py`) | 3 | **sim (confirmado pelo log)** |
| `Qt.WindowMinMaxButtonsHint`/`Qt.WindowCloseButtonHint` (`gui/dependencies_dialog.py`) | 2 | **sim (confirmado pelo log)** |
| `QVariant.Int/Double/Bool/LongLong/String` direto em 7 algorithms | 21 | **sim** — `QVariant::Type` foi removido no Qt6 |
| `core/qgis_compat.py::field_type()` | 1 função | **sim** — testa `QVariant is not None`, mas no PyQt6 `QVariant` importa e não tem `.String`; levanta `AttributeError` antes de chegar ao fallback `QMetaType` |
| `QgsWkbTypes.LineString / NoGeometry / PointGeometry` | 12 | provável (enum escopado) |
| `QgsProcessing.TypeVectorLine/Point/Polygon` | 43 | provável (enum escopado) |
| `QgsProcessingParameterNumber.Double/Integer` | 28 | provável (enum escopado) |
| `QgsTask.CanCancel` (`core/ortools_installer.py`) | 1 | provável (enum escopado) |
| `self.dialog.exec_()` (`logis_plugin.py:71`) | 1 | **sim** — o PyQt6 removeu os apelidos `exec_()` |

**Descoberta que torna a correção barata:** neste ambiente de
desenvolvimento (QGIS 3.34.4 / Qt 5.15 / PyQt 5.15) as **formas
escopadas já funcionam** para todos esses casos — verificado por
execução direta nesta revisão: `Qt.DockWidgetArea.RightDockWidgetArea`,
`Qt.WindowType.WindowMinMaxButtonsHint`, `QgsWkbTypes.Type.LineString`,
`QgsWkbTypes.GeometryType.PointGeometry`, `QgsProcessing.SourceType.
TypeVectorLine`, `QgsProcessingParameterNumber.Type.Double`,
`QgsTask.Flag.CanCancel` e `QDialog.exec()` **todos existem no PyQt5/
QGIS 3.34**. Ou seja: **não é preciso shim nenhum para enums** — basta
escrever a forma escopada, que é válida nas duas versões. Só o
`QVariant`/`QMetaType` precisa de código condicional, porque aí a
diferença é real (o `QgsField(nome, QMetaType.Type)` **não** existe no
QGIS 3.34 — confirmado: `QgsField('a', QMetaType.Type.QString)` levanta
`arguments did not match any overloaded call`). Isso mantém
`qgisMinimumVersion=3.16` intacto.

**Segundo achado desta auditoria (independente do Qt6):** a suíte de
testes está **vermelha no `main`** — `Ran 211 tests ... FAILED
(failures=1, errors=10)`. Nada a ver com Qt6: é resíduo do commit
`4c49617` (plugin movido para a subpasta `logis/`). Dez erros são
`patch('gui.waste_dock...')` / `patch('core.optim_backend...')` /
`patch('core.connectors.wfs...')` apontando para os módulos no caminho
antigo (topo do repo) em vez de `logis.gui...`/`logis.core...`; a falha
restante é `test_i18n` procurando `i18n/logis_en.qm` na raiz quando o
arquivo está em `logis/i18n/`. **Isso tem que ser o primeiro passo da
rodada** — sem suíte verde, nenhum passo seguinte consegue cumprir o
"rode a suíte antes de marcar [x]".

**Terceiro achado (violação da seção 2.1 do CLAUDE.md):**
`core/ortools_installer.py` roda `pip install --user ortools` **sem as
travas obrigatórias** (`"pandas<3" "numpy<2" "typing_extensions==
4.10.0"`). Esse é exatamente o comando que o CLAUDE.md proíbe, porque
sobrepõe o numpy do QGIS e quebra a instalação inteira do usuário. É um
bug de dano real, disparável por um clique no mesmo diálogo
"Dependências" que o Diego estava usando quando viu o traceback —
entra nesta rodada.

**Nota (2026-07-23) — encerramento formal de F6 e início de F7:** pedido
explícito do Diego nesta revisão: "vamos encerrar F6", confirmando que a
validação manual no QGIS (passo 58) **não pode ser feita agora** ("estou
sem computador") e que o plano deve seguir em frente sem esperar por
ela — mesma decisão de não-bloqueio já registrada para os passos 7, 13,
18, 27, 33, 41, 49, só que agora estendida explicitamente ao passo 58
consolidado. Verificado nesta revisão, lendo o estado real do repositório
(não confiando em nenhuma cópia do plano): `git status` limpo, `git log`
mostra `0ec789f` já em `origin/main`; `python3 -m unittest discover -s .
-p "test_*.py"` → **194 testes, OK**; `make test` → `sintaxe OK`; `grep -c
"addAlgorithm" provider.py` → **25**. Nenhuma mudança de código desde a
revisão anterior (2026-07-21) além de um commit de empacotamento e um de
`.gitattributes`, nenhum dos dois de código do plugin. **Conclusão: F6
está formalmente encerrado no código** (roadmap formal + seção 5.3
inteira); resta só a validação visual do Diego, que fica indefinidamente
adiada e não bloqueia nada — nem F7, nem a rodada OR-Tools pendente
(passos 64-68, ainda não iniciada — segue disponível para quando o
executor retomar, mas não é o foco desta revisão).

Nesta mesma revisão, o Diego tomou as duas decisões que estavam
pendentes para iniciar F7 (respondendo ao passo 59 e destravando o passo
60):
- **Quer dock para o módulo Waste** (resposta ao passo 59, que
  perguntava exatamente isso) — módulo de coleta de lixo passa a ter
  GUI própria, no mesmo padrão de `gui/urban_dock.py`/
  `gui/regional_dock.py`, antes da primeira publicação. Ver "Decisões de
  arquitetura — Dock do módulo Waste" e passos 69-81 abaixo.
- **Quer que a rodada de i18n (passo 60) comece já**, em paralelo ao
  Diego preparar `icon.svg` por conta própria — ou seja, o passo 61
  (LICENSE + ícone) se divide: LICENSE é trabalho do executor agora,
  ícone é entrega do Diego (ver passo 61 revisado e passo 88 novo).
  **Atualização, mesmo dia:** o Diego já entregou o conteúdo de
  `icon.svg` colado na conversa — passo 88 deixa de estar bloqueado e
  passa a ser executável (ver "Decisões de arquitetura — Ícone" para o
  conteúdo exato a gravar). A
  revisão do desenho herdado do passo 60 (ver "Decisões de arquitetura —
  i18n") encontrou um ponto que o desenho original não tinha percebido:
  as strings de origem em `self.tr(...)` do logis **já estão em
  Português** (diferente do GisBR, onde a origem é inglês) — `grep -c
  "self.tr("` → 632 ocorrências, todas em PT-BR (ex.: `"Calcular
  Indicadores"`, `"Camada de rede viária (Linhas):"`). Combinado com
  `locale = (...)[:2]` em `__init__.py` (trunca `pt_BR` para `"pt"`),
  isso significa que só é preciso gerar **`i18n/logis_en.qm`** — um
  usuário com locale `pt_BR` nunca vai encontrar `logis_pt.qm` e cai no
  fallback de origem, que já é PT-BR. O passo 60 original (que previa
  gerar `logis_pt_BR.ts` **e** `logis_en.ts`) fica superado por esse
  achado — ver passo 60 revisado e passos 82-87 novos.

**Nota (2026-07-21):** todos os testes que precisam de QGIS real (25
Processing algorithms + 2 docks) foram mapeados em detalhe num documento
separado — `/home/diego/.hermes/projects/logis/PLAN_TESTES_QGIS.md`
(pedido explícito do Diego: "planejamento à parte", já que ele está sem
computador nesta revisão). Esse arquivo substitui a necessidade de
vasculhar os passos adiados espalhados neste plano (7, 13, 18, 27, 33, 41,
49, 58) — quando os testes forem executados, marcar `[x]` **nos dois
lugares** (lá e aqui) para não repetir a divergência de cópias já
registrada abaixo em "Nota de processo".

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

**F6 — seção 5.3 do CLAUDE.md: FECHADA (atualizado nesta revisão,
2026-07-21, passo 57).** As rodadas 9 e 10 fecharam os dois últimos
indicadores de 5.3 (distância média ao ponto de destino, cobertura por
frequência de coleta), completando os quatro indicadores da seção
(deadhead ratio e equilíbrio entre setores já fechados nas rodadas 7-8).
Verificado nesta revisão lendo o código e o histórico do git
diretamente, não confiando em checkbox: `algorithms/waste_destination_distance.py`
(`logis:waste_destination_distance`) e `algorithms/waste_collection_coverage.py`
(`logis:waste_collection_coverage`) existem e estão registrados em
`provider.py` (`grep -c "addAlgorithm" provider.py` → 25);
`core/indicators/waste.py` tem `compute_collection_coverage`; a
distância ao destino reaproveita `nearest_depot_cost` de
`core/indicators/urban.py` (ver diagnóstico do passo 56 abaixo — uma
duplicação dessa função foi introduzida na rodada 9 e corrigida antes
do fechamento). `python3 -m unittest discover -s . -p "test_*.py"` →
**194 testes, OK**; `make test` → `sintaxe OK`; `git status` limpo;
`git log`/`git branch -vv` confirmam que o commit mais recente
(`5aeed4e`, "F6 rodada 10 - verificação e testes") já está em
`origin/main` — nada pendente de commit ou push.

Com isso, **F6 está formalmente completo**: as quatro entregas do
roadmap (seção 8) e os quatro indicadores da seção 5.3 implementados,
testados e commitados. O que resta antes de considerar o módulo de
coleta de lixo pronto para publicação não é mais implementação, e sim
os passos 58 em diante (revisão manual no QGIS, decisão de GUI/dock,
preparação de F7) — ver "Passos" abaixo.

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

### Novas para F10 — abas no painel de Indicadores Urbanos (2026-07-30)

- **Copiar o padrão de `waste_dock.py`, linha por linha, em vez de
  inventar outro.** O helper `_new_tab(title)` (`waste_dock.py:190-204`),
  o mock `class QTabWidget` (linhas 164-173, com `count()`/`tabText()`),
  o `outer` layout e a ordem `título → descrição → tabs → resultados` já
  estão validados por `test_dock_layout.py` e pela suíte. F10 replica
  isso em `urban_dock.py` sem variação — mesmo nome de helper, mesmo mock,
  mesmos nomes de variável local (`outer`, `scroll`, `central`, `layout`),
  para que os dois arquivos continuem legíveis lado a lado.
- **Três abas, agrupadas pelas três famílias da seção 5.1 do CLAUDE.md** —
  não uma aba por algorithm (oito abas não cabem na largura de uma dock
  lateral) e não uma aba por método (`calculate_*`), que é recorte de
  implementação, não do domínio:
  1. **"Rede"** — o botão-pacote de estrutura (densidade viária,
     conectividade α/β/γ, circuidade média) + Centralidade de
     Intermediação. Corresponde a "De rede (estrutura)" da seção 5.1.
  2. **"Demanda"** — Densidade de Demanda + Acessibilidade Gravitacional.
     Corresponde a "De acessibilidade e demanda".
  3. **"Carga"** — Restrição de Circulação de Carga (seção nova, extraída
     do pacote) + Distância de Entrega. Corresponde a "De operação urbana
     de carga".
- **`cmb_network` (rede viária) fica no cabeçalho, acima das abas, e é
  compartilhado.** Quatro métodos o leem (linhas 326, 506, 575, 622);
  duplicá-lo por aba criaria três combos independentes e o usuário teria
  de escolher a mesma camada três vezes — e os métodos teriam de mudar
  para saber qual combo ler. Mantê-lo único e visível em todas as abas
  é o que permite que **nenhum** dos cinco métodos existentes mude de
  linha por causa da remontagem. `cmb_area` (só lido em 327) vai para
  dentro da aba "Rede", ao lado do botão que o usa.
- **O painel de resultados (`txt_results`) fica FORA das abas, no rodapé**
  — mesma decisão do dock Waste, pelos mesmos dois motivos: o usuário roda
  um cálculo e troca de aba sem perder o log, e `self.txt_results` segue
  sendo um único atributo, então os cinco métodos `calculate_*` continuam
  escrevendo nele sem saber que existem abas.
- **Cada aba tem sua própria `QScrollArea`** (é o que o `_new_tab` faz), e
  a `QScrollArea` externa do dock **permanece** — `test_dock_layout.py`
  exige `self.setWidget(scroll)` nos três docks, e `waste_dock.py` já
  mantém as duas camadas. Não remover a externa "porque agora as abas
  rolam".
- **Extrair `calculate_cargo_restriction()` de `calculate_indicators()` é
  a única mudança de comportamento**, e é mecânica: o bloco 425-442 vira
  método próprio com o mesmo preâmbulo de guarda dos outros métodos
  (checar `cmb_network`, `import processing` dentro de `try`, escrever
  erro em `txt_results`). No pacote que sobra, renumerar o log de "1) 2)
  3) 4)" para "1) 2) 3)" e ajustar a docstring ("os três algoritmos de
  estrutura de rede"). **Não** mexer em mais nada dos outros três blocos.
- **A seção nova de Carga expõe `RESTRICTION_EXPRESSION`**, que hoje é
  passado hardcoded como `''` (linha 430). Um `QLineEdit`
  (`self.txt_cargo_expression`) com placeholder e vazio por padrão
  preserva exatamente o comportamento atual e destrava o filtro por
  `highway`/`maxweight` previsto na seção 5.1 do CLAUDE.md. É um widget e
  uma linha de leitura — não é escopo novo, é a seção deixar de ser um
  botão solo.
- **Nenhum widget renomeado, nenhum atributo removido.** Todos os
  `self.cmb_*`/`self.spin_*`/`self.txt_*`/`self.btn_*` mantêm os nomes
  atuais, e `test_plugin.py::test_urban_dock_delivery_distance_controls`
  tem que continuar passando **sem edição** durante os passos 113-116 — é
  o que prova que a remontagem não perdeu nada. Só o passo 117 acrescenta
  atributos (`txt_cargo_expression`, `btn_calculate_cargo`) e só o 118
  edita testes.
- **Ordem obrigatória: estrutura primeiro (113), depois uma aba por passo
  (114-116), depois a extração da restrição de carga (117).** Assim cada
  passo isolado deixa o painel funcionando; se a rodada for interrompida,
  o pior estado possível é "abas prontas, restrição de carga ainda dentro
  do pacote" — que é o comportamento de hoje, não uma regressão.
- **`test_dock_layout.py` cresce em vez de ganhar arquivo novo.** Ele já é
  o teste estático de layout dos três docks; F10 acrescenta lá o par de
  asserções de aba para o Urbano (`QTabWidget(`, três `_new_tab`,
  `outer.addWidget(self.txt_results)`), espelhando
  `test_waste_dock_has_four_tabs`. Como neste ambiente `import qgis`
  funciona, instanciar o dock não exercitaria os mocks — leitura de fonte
  continua sendo a técnica certa (mesma justificativa do F9).
- **F10 não toca em `core/`, `algorithms/` nem `provider.py`**, e não
  acrescenta dependência. Só `logis/gui/urban_dock.py`, dois testes, os
  arquivos de i18n, `metadata.txt` e `README.md`.
- **`regional_dock.py` fica fora desta rodada.** Ele tem 5 seções e
  também caberia em abas, mas o Diego pediu o Urbano; agrupar o Regional
  (indicadores de rede × acessibilidade × potencial logístico) é a
  próxima rodada natural, quando ele pedir — não presumir.
- **Bug latente do `Makefile` a corrigir de passagem no passo 119:**
  `transcompile` roda `lrelease i18n/*.ts`, mas os `.ts` vivem em
  `logis/i18n/` desde a reestruturação em subpasta (o `i18n/` da raiz está
  vazio). O alvo `i18n` já usa `$(PLUGINNAME)/i18n/...`; `transcompile`
  ficou para trás. Sem isso o passo de tradução não regenera `.qm` nenhum.
- **A validação visual final é do Diego, no QGIS 4.2** — mesma decisão de
  não-bloqueio de todas as rodadas anteriores (passo 58). Fechamento do
  código de F10 = suíte verde + `make test` + `test_dock_layout.py`.

### Novas para F9 — usabilidade dos painéis no QGIS 4.2 (2026-07-29, segunda revisão)

- **Rolagem: replicar exatamente o padrão de `waste_dock.py`, não
  inventar outro.** `gui/waste_dock.py:180-181,645-646` já resolve o
  problema com quatro linhas — `scroll = QScrollArea()`,
  `scroll.setWidgetResizable(True)`, `scroll.setWidget(central)`,
  `self.setWidget(scroll)`. `urban_dock.py` e `regional_dock.py` passam a
  fazer o mesmo, com o mesmo mock `QScrollArea` no bloco `except
  ImportError`. **Não** usar `setMinimumWidth`/`setFixedHeight` nem
  políticas de barra de rolagem escopadas (`Qt.ScrollBarPolicy.*`): o
  `setWidgetResizable(True)` já elimina a barra horizontal, e evitar o
  enum mantém intacto o mock `class Qt: pass` dos dois docks.
- **A regressão de layout é coberta por teste estático de fonte, não por
  instanciação de widget.** Neste ambiente `import qgis` funciona (QGIS
  3.34 instalado), então os mocks dos docks **não** são exercidos pela
  suíte e um `isinstance(dock._widget, QScrollArea)` provaria pouco.
  Novo `test_dock_layout.py` lê os três `gui/*_dock.py` como texto
  (`pathlib` + `re`, mesma técnica de `test_qt6_compat.py`) e afirma:
  cada dock instancia `QScrollArea`, chama `setWidgetResizable(True)` e
  termina com `self.setWidget(scroll)`; `waste_dock.py` instancia
  `QTabWidget` e registra as quatro abas. É o guarda barato contra
  alguém reescrever `_build_ui` e perder a rolagem.
- **Diálogo de dependências: corrigir a causa (stylesheet do
  `QGroupBox`) antes de mexer em tamanho.** O `setStyleSheet(
  "font-weight: bold; padding: 10px;")` sem seletor é o defeito clássico
  de QSS em `QGroupBox`: a regra cascateia para os filhos e o título fica
  ancorado na borda, sobrepondo a primeira linha. Trocar por regra
  escopada com título reposicionado — `QGroupBox { font-weight: bold;
  margin-top: 12px; padding: 10px; } QGroupBox::title {
  subcontrol-origin: margin; left: 8px; padding: 0 4px; }`. Vale para os
  dois grupos (GisBR e OR-Tools).
- **Diálogo de dependências: rolagem + tamanho maior, cinto e
  suspensório.** O conteúdo (dois grupos com parágrafos que quebram
  linha, barra de progresso, log de 100 px, aviso de reinício) tem altura
  dependente de fonte/DPI — qualquer número fixo erra em alguma máquina.
  Estrutura nova: `QVBoxLayout(self)` → `QScrollArea` (com um `QWidget`
  de conteúdo que recebe o layout atual) → **rodapé fixo fora da
  rolagem** com o botão "Fechar" (o botão nunca pode sair da tela).
  `resize(620, 560)` e `setMinimumSize(520, 420)`. Mocks novos no bloco
  `except ImportError`: `QScrollArea` e `QWidget`.
- **Abas no dock de Coleta de Lixo: quatro abas, agrupadas pelo fluxo da
  seção 6 do CLAUDE.md** — não uma aba por algorithm (dez abas não
  cabem na largura de uma dock lateral, e a barra viraria um carrossel):
  1. **"Geração"** — Estimativa de Geração (`waste_generation_estimate`)
     + Setorização (`waste_districting`, seção nova, passo 108).
  2. **"Roteirização"** — CPP, RPP, CARP.
  3. **"Frota"** — Dimensionamento de Frota.
  4. **"Indicadores"** — Deadhead Ratio (seção nova, passo 109),
     Equilíbrio entre Setores, Distância ao Destino, Cobertura por
     Frequência.
- **O painel de resultados fica FORA das abas**, no rodapé do dock,
  compartilhado por todas. Motivo funcional (o usuário roda um cálculo e
  troca de aba sem perder o log) e motivo de compatibilidade: mantém
  `self.txt_results` como um único atributo, e os oito métodos
  `run_*`/`calculate_*` (linhas 648-1180) **não mudam nem uma linha** —
  a rodada é só remontagem de layout.
- **Cada aba tem sua própria `QScrollArea`.** A aba "Roteirização"
  sozinha tem três seções com 15+ widgets; a rolagem por aba é o que
  torna a divisão útil em vez de cosmética. Helper privado
  `_new_tab(title)` que cria `QWidget` + `QVBoxLayout` + `QScrollArea`,
  chama `self.tabs.addTab(scroll, title)` e devolve o layout — evita
  repetir seis linhas quatro vezes.
- **Nenhum widget renomeado, nenhum atributo removido.** Todos os
  `self.cmb_*`/`self.spin_*`/`self.btn_*` mantêm os nomes atuais; o
  `test_waste_dock.py` existente (que afirma `hasattr` de ~50 widgets)
  tem que continuar passando **sem edição** durante os passos 104-107 —
  é justamente o que prova que a remontagem não perdeu nada pelo
  caminho. Só os passos 108-109 (seções novas) acrescentam atributos, e
  só o passo 110 edita o teste.
- **Ordem obrigatória: rolagem primeiro (99-101), diálogo depois
  (102-103), abas por último (104-110).** Os dois primeiros blocos são
  as regressões que o Diego encontrou em uso real; o terceiro é
  melhoria pedida. Assim, se a rodada for interrompida, o que ficou
  pronto é o que mais importa.
- **Sem `QgsCollapsibleGroupBox`, sem `QToolBox`, sem `QSplitter`.**
  Foram considerados como alternativas às abas (o `QgsCollapsibleGroupBox`
  é o idioma nativo do QGIS para seções longas) e **rejeitados**: o
  Diego pediu abas explicitamente, e `QTabWidget` é PyQt puro — não
  acrescenta superfície de API do QGIS a mockar nos testes.
- **F9 não toca em `core/`, `algorithms/` nem `provider.py`.** Só
  `logis/gui/*.py`, um teste novo, o teste do dock waste, os arquivos de
  i18n regenerados, `metadata.txt` (versão) e `README.md`.
- **A validação visual final é do Diego, no QGIS 4.2** — mesma decisão
  de não-bloqueio de todas as rodadas anteriores (passo 58). Fechamento
  do código de F9 = suíte verde + `make test` + `test_dock_layout.py`.

### Novas para F8 — compatibilidade QGIS 3.16+ e QGIS 4 / Qt 6 (2026-07-29)

- **Regra única do projeto, a partir de agora: todo acesso a enum do Qt
  ou do QGIS é escopado.** `Qt.DockWidgetArea.RightDockWidgetArea`, não
  `Qt.RightDockWidgetArea`. Vale para `Qt.*`, `QgsWkbTypes.*`,
  `QgsProcessing.*`, `QgsProcessingParameterNumber.*`, `QgsTask.*`,
  `Qgis.*`. Motivo: a forma escopada funciona nas duas versões (PyQt5 do
  QGIS 3.34 e PyQt6 do QGIS 4), então é uma regra sem custo e sem
  bifurcação de código. Essa regra vai para o CLAUDE.md (seção 9) para
  valer para todo código futuro.
- **Nada de shim/wrapper para enum.** Foi considerado criar um
  `enum_value(owner, member, scope)` em `core/qgis_compat.py`; **rejeitado**
  — como a forma escopada já é válida em ambas as versões, um resolvedor
  genérico só adicionaria indireção, custo de teste e um lugar a mais
  para errar. Compat só onde a API realmente diverge (ver item seguinte).
- **`field_type()` é o único ponto de compat de tipo, e o bug dele é a
  condição de guarda, não a ordem.** A ordem atual (QVariant primeiro,
  QMetaType depois) está **correta e deve ser preservada** — o motivo
  documentado na docstring foi reconfirmado por execução nesta revisão:
  no QGIS 3.34 o construtor `QgsField(nome, QMetaType.Type)` não existe.
  O defeito é `if QVariant is not None:` — no PyQt6 o `QVariant` importa
  normalmente, só não tem mais os membros de `QVariant::Type`. Correção:
  guardar por **presença de membro** (`hasattr(QVariant, "String")`),
  não por presença do módulo. Mesma correção na guarda do `QMetaType`.
- **Os 7 algorithms que ainda usam `QVariant.*` direto passam a usar
  `field_type()`.** Não existe motivo para dois caminhos: `field_type`
  já é o padrão em 16 arquivos. Mapeamento: `QVariant.Int` →
  `field_type("int")` (que devolve `LongLong` — **mudança de tipo
  deliberada e inócua**: o GPKG grava inteiro de 64 bits do mesmo jeito,
  e é o que os outros 16 arquivos já fazem), `QVariant.Double` →
  `field_type("double")`, `QVariant.Bool` → `field_type("bool")`.
  Arquivos: `algorithms/waste_districting.py`,
  `algorithms/regional_critical_links.py`, `algorithms/vrp_cvrp.py`,
  `algorithms/facility_mclp.py`, `algorithms/facility_lscp.py`,
  `algorithms/facility_p_median.py`,
  `algorithms/urban_edge_betweenness.py`. Depois disso, **`QVariant` só
  pode ser importado em `core/qgis_compat.py`** — vira invariante
  testável (passo do teste estático).
- **`exec_()` → `exec()`.** O PyQt6 removeu os apelidos com underscore;
  o `exec()` existe no PyQt5 desde sempre (confirmado no QGIS 3.34).
  Um sítio só: `logis_plugin.py:71`. **Não** criar teste que chame
  `exec()` — é modal e travaria a suíte; a cobertura é o teste estático.
- **Mocks das GUIs acompanham a forma escopada.** O bloco `except
  ImportError` de `gui/dependencies_dialog.py` define `class Qt` com
  atributos soltos (`WindowMinMaxButtonsHint = 0`); passa a ter a classe
  aninhada `WindowType`. Os mocks `class Qt: pass` dos três docks não
  mudam (eles não acessam membro nenhum).
- **Enums do Processing e do WKB são troca mecânica, verificável aqui
  mesmo.** `QgsProcessing.TypeVectorX` → `QgsProcessing.SourceType.
  TypeVectorX`; `QgsProcessingParameterNumber.Double/Integer` →
  `QgsProcessingParameterNumber.Type.Double/Integer`;
  `QgsWkbTypes.LineString/NoGeometry` → `QgsWkbTypes.Type.X`;
  `QgsWkbTypes.PointGeometry` → `QgsWkbTypes.GeometryType.PointGeometry`
  (atenção: são **dois** enums diferentes com nomes parecidos — tipo de
  geometria vs. tipo WKB; conferir sítio a sítio, não passar `sed` cego).
  Todos validados como existentes no QGIS 3.34 nesta revisão, então a
  suíte local prova a mudança.
- **Teste estático de regressão em vez de fé.** Novo `test_qt6_compat.py`
  varre os `.py` de `logis/` procurando os padrões proibidos
  (`Qt.<Membro>` solto para a lista conhecida, `QVariant.` fora de
  `core/qgis_compat.py`, `.exec_(`, `QgsProcessing.TypeVector`,
  `QgsProcessingParameterNumber.Double|Integer`, `QgsWkbTypes.LineString|
  NoGeometry|PointGeometry`, `QgsTask.CanCancel`). É o único jeito de a
  regra sobreviver — a suíte roda em PyQt5, onde a forma errada **não**
  falha em runtime. O teste lê o fonte como texto (`pathlib` + `re`),
  sem importar QGIS.
- **Instalador do OR-Tools: usar exatamente o comando da seção 2.1 do
  CLAUDE.md.** `[sys.executable, "-m", "pip", "install", "--user",
  "ortools", "pandas<3", "numpy<2", "typing_extensions==4.10.0"]`, e
  acrescentar `--break-system-packages` quando o pip reclamar de
  `externally-managed-environment` (detectar pela mensagem e repetir uma
  vez, em vez de tentar adivinhar a distro antes). Mantém `--user`
  (funciona no Flatpak, onde o prefixo do sistema é read-only).
- **Não mexer em `Qgis.MessageLevel.*`** — os 6 sítios em
  `core/optim_backend.py` e `core/network/od_matrix.py` já estão
  escopados e corretos.
- **Nada de novo módulo, nada de dependência nova.** F8 não cria
  arquivo em `core/` nem em `algorithms/`; só edita sítios existentes,
  mais um teste novo e um script de diagnóstico em `docs/` (não
  empacotado).
- **Diagnóstico na máquina do Diego, porque é lá que o Qt6 está.** Um
  script `docs/qgis4_compat_check.py` (colável no console Python do QGIS
  4) reporta quais nomes legados ainda existem no QGIS 4 dele — cobre
  justamente os itens marcados "provável" na tabela do Objetivo. Não é
  passo bloqueante: as trocas escopadas são seguras de qualquer forma; o
  script serve para confirmar o diagnóstico e para a próxima vez.
- **Makefile aponta só para perfis QGIS3.** O plugin do Diego está em
  `.../QGIS/QGIS4/profiles/default/...`, mas `make deploy`/`deploy-flatpak`
  escrevem em `QGIS3`. Decisão: **detectar o perfil** — variável
  `QGIS_MAJOR` (default `3`) usada nos caminhos, mais alvos
  `deploy-qgis4`/`deploy-flatpak-qgis4`. Simples, sem quebrar quem usa
  os alvos atuais.
- **`metadata.txt` ganha `supportsQt6=True`** (chave oficial do
  repositório de plugins do QGIS para sinalizar compatibilidade Qt6) e
  a versão sobe para `0.1.1` — o Diego vai reinstalar, e um número igual
  com conteúdo diferente confunde o gerenciador de complementos.
- **A validação final continua sendo do Diego, no QGIS 4** — a suíte
  local roda em PyQt5 e por construção não consegue provar o
  comportamento no PyQt6. O critério de fechamento do código de F8 é
  suíte verde + teste estático, igual às rodadas anteriores (mesma
  decisão de não-bloqueio do passo 58).

### Novas para o dock do módulo Waste (F6→F7, decisão desta revisão — 2026-07-23)

- **Um arquivo só, `gui/waste_dock.py`**, mesmo padrão de `gui/
  urban_dock.py`/`gui/regional_dock.py` (classe `WasteDock` estende
  `QgsDockWidget`, bloco de mocks no `try/except ImportError` no topo
  para rodar fora do QGIS, `self.tr(...)` em todas as strings de UI,
  cada seção chama `processing.run("logis:waste_*", {...})` e escreve o
  resultado num `QTextEdit`). Não criar múltiplos arquivos/mixins — o
  padrão dos dois docks existentes já é um arquivo único, mesmo sendo
  grande (`urban_dock.py` tem 668 linhas para 8 seções).
- **Dez seções, uma por algorithm do módulo `waste`**, na ordem do
  fluxo descrito na seção 6 do CLAUDE.md: Estimativa de Geração
  (`waste_generation_estimate`) → Setorização (`waste_districting`) →
  Roteirização CPP (`waste_cpp_route`) → RPP (`waste_rpp_route`) → CARP
  (`waste_carp_route`) → Dimensionamento de Frota
  (`waste_fleet_sizing`) → Deadhead Ratio (`waste_deadhead_ratio`) →
  Equilíbrio entre Setores (`waste_sector_balance`) → Distância ao
  Destino (`waste_destination_distance`) → Cobertura por Frequência
  (`waste_collection_coverage`). Cada seção reusa os widgets já
  padronizados em `urban_dock.py`/`regional_dock.py`:
  `QgsMapLayerComboBox` (com `QgsMapLayerProxyModel.Filter` apropriado —
  `LineLayer` para vias/rotas, `PointLayer` para depósito/destinos,
  `PolygonLayer` para setores quando aplicável) + `QgsFieldComboBox`
  para campos (inclusive booleanos, ex.: `route_is_deadhead`/
  `route_is_connector`) + `QDoubleSpinBox`/`QSpinBox` para parâmetros
  numéricos com os mesmos defaults já usados nos algorithms
  correspondentes (ex.: taxa per capita ~0,9-1,0 kg/hab/dia) + um
  `QPushButton` que chama `processing.run(...)` e escreve o resultado
  formatado no `QTextEdit` da seção.
- **`QScrollArea` envolvendo o conteúdo do dock** — diferença
  deliberada em relação a `urban_dock.py`/`regional_dock.py` (que não
  usam, ver `grep -n "QScrollArea" gui/urban_dock.py` → nada). Dez
  seções com parâmetros de CPP/RPP/CARP (mais campos cada uma que os
  indicadores dos outros dois módulos) tornariam o dock alto demais para
  caber na tela sem rolagem. Não retrofitar `QScrollArea` nos dois docks
  existentes — fora de escopo, nenhum problema relatado neles.
- **Registro em `logis_plugin.py` é puramente mecânico**, repete
  exatamente o padrão já usado duas vezes (`show_urban_dock`/
  `show_regional_dock`): `self.action_waste`, `self.dock_waste = None`
  no `__init__`, `QAction(self.tr("Coleta de Lixo"), ...)` +
  `addPluginToMenu` em `initGui`, `show_waste_dock()` que instancia
  `WasteDock` uma vez e reusa, limpeza espelhada em `unload()`
  (`removePluginMenu` + `removeDockWidget` com o mesmo guard
  `sip.isdeleted`).
- **Nenhuma mudança em `provider.py` ou nos dez `algorithms/waste_*.py`**
  — o dock só chama `processing.run` sobre algorithms já registrados e
  testados; é uma camada de UI por cima do que já existe, não uma nova
  funcionalidade de backend.

### Novas para i18n (F7, decisão desta revisão — 2026-07-23, corrige o desenho herdado do passo 60)

- **Só `i18n/logis_en.ts` → `i18n/logis_en.qm` precisam existir.**
  Achado desta revisão (ver "Objetivo" acima): as strings de origem em
  `self.tr(...)` já estão em PT-BR (diferente do GisBR, cuja origem é
  inglês — confirmado lendo `i18n/gisbr_pt.ts` do repositório GisBR:
  `language="pt_BR"`, `<source>` em inglês, `<translation>` em
  português). Combinado com `locale = (QSettings().value(
  "locale/userLocale") or "en")[:2]` em `__init__.py` (trunca `pt_BR`
  para `"pt"`), um arquivo `logis_pt_BR.qm` (como o passo 60 original
  previa) **nunca seria carregado** — o código procura
  `i18n/logis_pt.qm`. Não criar esse arquivo também é a escolha certa:
  como a origem já é PT-BR, um usuário com locale `pt`/`pt_BR` cai no
  fallback (nenhum `.qm` encontrado → `QCoreApplication.translate`
  devolve a própria string de origem, que já é a UI em português
  desejada) — não precisa de tradução alguma para o idioma-alvo
  principal do plugin (Brasil).
- **`Makefile` ganha dois alvos novos, mesmo padrão do `Makefile` do
  GisBR** (`grep -n -A3 "i18n\|\.ts\|\.qm" ~/projects/gisbr/Makefile`):
  `i18n` (`@mkdir -p i18n && pylupdate5 provider.py logis_plugin.py
  gui/*.py algorithms/*.py -ts i18n/logis_en.ts`) e `transcompile`
  (`@lrelease i18n/logis_en.ts`). Ferramentas confirmadas presentes
  neste ambiente (`which pylupdate5 lrelease` → `/usr/bin/pylupdate5`,
  `/usr/bin/lrelease`).
- **Tradução para inglês é trabalho manual do executor dentro do
  `.ts` gerado** (preencher `<translation>` para cada `<source>` em
  português) — não é um script, é reescrever ~632 ocorrências de
  `self.tr(...)` (número bruto de chamadas, incluindo repetições; o
  `.ts` deduplicado por string única será bem menor) em inglês corrido,
  mesmo tom técnico das strings de origem.
- **Verificação sem QGIS instalado:** `qgis.PyQt` é só um alias que o
  QGIS expõe para o PyQt5 do sistema — como `python3 -c "import PyQt5"`
  já funciona neste ambiente (verificado), um teste `test_i18n.py`
  pode importar `PyQt5.QtCore.QTranslator` diretamente (sem precisar de
  `import qgis`), carregar `i18n/logis_en.qm` compilado e confirmar que
  uma string de origem conhecida (ex.: `"Calcular Indicadores"`) traduz
  para o texto em inglês esperado — mesmo espírito de `make test`
  (verificação sem depender de uma instância QGIS real), mas cobrindo
  especificamente o mecanismo de tradução, que os outros testes não
  tocam.
- **Fora de escopo desta rodada:** gerar `logis_pt.qm` (decisão
  explícita acima — não é necessário); qualquer mudança de string em
  `self.tr(...)` já existente (a rodada só adiciona o arquivo de
  tradução, não deve alterar comportamento nem texto em PT-BR).

### Ícone (passo 88 revisado — entregue pelo Diego em 2026-07-23)

- **O Diego entregou o conteúdo de `icon.svg` nesta revisão** (colado
  diretamente na conversa, não como arquivo em disco) — destrava o
  passo 88, que até aqui estava bloqueado esperando essa entrega (ver
  "Objetivo" e nota do passo 61). Conteúdo exato a gravar em
  `icon.svg` na raiz do repositório:

  ```svg
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="100%" height="100%">
    <!-- Fundo transparente implícito -->

    <!-- Mapa do Brasil (Silhueta Geométrica/Flat baseada no padrão anterior) -->
    <polygon
      points="22,6 28,7 32,10 42,16 40,24 36,30 31,34 27,43 24,43 21,38 18,34 15,31 17,27 7,23 5,19 11,16 16,10"
      fill="#2E7D32"
      stroke="#2E7D32"
      stroke-width="2"
      stroke-linejoin="round"
    />

    <!-- Fundo/Contorno Branco do Caminhão (Para separar visualmente do mapa de fundo) -->
    <g fill="#FFFFFF" stroke="#FFFFFF" stroke-width="3" stroke-linejoin="round">
      <!-- Silhueta geral do caminhão -->
      <path d="M 12 18 H 26 V 22 H 31 L 34 26 V 30 H 12 Z" />
      <!-- Silhueta das rodas -->
      <circle cx="17" cy="30" r="3" />
      <circle cx="29" cy="30" r="3" />
    </g>

    <!-- Caminhão de Logística (Cores e Detalhes) -->
    <g>
      <!-- Baú e Cabine (Amarelo) -->
      <path
        d="M 12 18 H 26 V 22 H 31 L 34 26 V 30 H 12 Z"
        fill="#FFC107"
      />

      <!-- Janela da Cabine (Branco) -->
      <polygon
        points="27,23 30.5,23 32.5,26 27,26"
        fill="#FFFFFF"
      />

      <!-- Rodas (Usando o Verde do mapa para manter o limite de 3 cores no design) -->
      <circle cx="17" cy="30" r="2.5" fill="#2E7D32" />
      <circle cx="29" cy="30" r="2.5" fill="#2E7D32" />
    </g>
  </svg>
  ```

- **Gravar exatamente como colado** (sem "melhorar" traços, cores ou
  pontos do desenho — decisão visual é do Diego, não do executor).
- **`metadata.txt` aponta hoje para `icon=icon.png`, que nunca existiu**
  (`icon.png` não está no repositório — confirmado nesta revisão,
  `find . -iname "icon*"` só retorna `metadata.txt`). Passo 88 muda para
  `icon=icon.svg`.
- **Suporte a SVG no QGIS Plugin Manager:** `QIcon` do Qt/PyQt5 carrega
  SVG nativamente (plugin `QSvgIconEngine`, parte padrão do PyQt5 que o
  QGIS já embute) — não é preciso gerar PNG a partir do SVG por
  limitação técnica. Mesmo assim, o passo 88 pede uma confirmação
  rápida (doc de submissão do repositório oficial de plugins do QGIS,
  `docs.qgis.org`/`plugins.qgis.org`) antes de fechar, porque a
  validação manual real do Plugin Manager (passo 58/consolidado) segue
  adiada — se a documentação dos requisitos de submissão exigir PNG,
  gerar `icon.png` a partir do SVG fica registrado como decisão a
  tomar com o Diego, não assumida agora.
- **Ícones dos `logis:*` individuais na Processing Toolbox continuam
  fora de escopo** (nenhum `algorithms/*.py`/`provider.py` sobrescreve
  `icon()` hoje — mesma verificação já registrada no passo 88 original;
  não muda com esta entrega).

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

      **Diagnóstico do erro repetido nesta revisão (2026-07-21) — causa
      raiz real, não sintoma:** o passo 50 (rodada 9) tinha implementado
      `algorithms/waste_destination_distance.py` chamando uma função
      **nova e duplicada**, `waste_destination_distance()` dentro de
      `core/indicators/waste.py`, em vez de reaproveitar
      `nearest_depot_cost()` de `core/indicators/urban.py` — exatamente
      o reúso que o próprio plano já tinha decidido em "Descoberta desta
      revisão que simplifica a rodada 9" (seção Objetivo). Essa
      duplicação não quebra a sintaxe nem os testes por si só (por isso
      passou despercebida nos passos 50-55), mas viola a decisão de
      arquitetura registrada — é o tipo de coisa que o passo 56, sendo o
      primeiro a rodar a suíte completa depois da rodada inteira, existe
      para pegar. O executor rodou o passo 56 várias vezes reportando
      erro; a causa não era um bug de sintaxe ou teste falhando, e sim
      confusão de estado entre **dois arquivos `PLAN.md` distintos**:
      este arquivo (`/home/diego/.hermes/projects/logis/PLAN.md`, fora
      do repo, canônico) e uma **cópia commitada dentro do repo**
      (`logis/PLAN.md`, rastreada pelo git desde pelo menos o commit
      `3fbfde9`). A cópia do repo já tinha os passos 54-55 marcados
      `[x]` e o commit `5aeed4e` ("F6 rodada 10 - verificação e testes")
      já tinha corrigido a duplicação (removida `waste_destination_distance()`
      de `core/indicators/waste.py`, `algorithms/waste_destination_distance.py`
      passou a importar e chamar `nearest_depot_cost` de `core/indicators/urban.py`,
      teste duplicado removido de `test_waste.py`) e feito commit+push —
      mas **este** arquivo canônico continuava com o passo 56 em `[ ]`.
      A cada nova tentativa do passo 56, o executor rodava a suíte
      (que já passava), tentava commitar de novo e não tinha nada para
      commitar (working tree limpo) — reportado como erro/loop, quando
      na verdade o trabalho já estava feito e publicado.
      **Verificado nesta revisão, lendo o estado real do repo (não
      confiando em nenhuma cópia do plano):** `git status` limpo,
      `git log` mostra `5aeed4e` já em `origin/main` (`git branch -vv`
      confirma `[origin/main]` no mesmo commit — nada para dar push).
      `python3 -m unittest discover -s . -p "test_*.py"` → **194 testes,
      OK**. `make test` → `sintaxe OK`. `grep -c "addAlgorithm"
      provider.py` → **25**. `grep -rn "waste_destination_distance"
      --include="*.py" .` só aparece como nome do arquivo/algorithm
      (`provider.py`, `test_waste.py: alg.name()`), não como função em
      `core/indicators/waste.py` — a duplicação foi mesmo removida.
      **Passo 56 fechado por esta verificação; nenhuma ação de código
      necessária.**

**Nota de processo (não é um passo de código — registrar para não repetir a confusão):**
Existe uma cópia de `PLAN.md` commitada dentro do repo `logis`
(`git log --oneline --all -- PLAN.md`), mantida em paralelo a este
arquivo canônico desde antes desta revisão — aparentemente um hábito
já estabelecido do executor de espelhar o plano a cada rodada de commit
do F6. Isso não é, por si, um problema (não é código, não afeta
`make test`/testes/o plugin), mas as duas cópias podem divergir — foi
exatamente essa divergência (passo 56 marcado `[x]` na cópia do repo,
`[ ]` aqui) que causou o loop de erro relatado pelo Diego. **Decisão:**
manter este arquivo (`/home/diego/.hermes/projects/logis/PLAN.md`) como
única fonte de verdade para o estado dos passos; se a cópia do repo
continuar sendo mantida por hábito do executor, ela deve ser tratada
como um artefato histórico read-only (snapshot do commit), nunca como
referência para decidir se um passo já foi concluído — essa decisão só
se toma lendo o estado real do código/testes/git (como feito acima),
nunca lendo checkboxes de qualquer cópia do plano sem verificação.

**Fechamento formal da seção 5.3 do CLAUDE.md:**

- [x] 57. Atualizar a seção "Objetivo" deste plano confirmando que os
      quatro indicadores de 5.3 (deadhead ratio, equilíbrio entre
      setores, distância média ao destino, cobertura por frequência)
      estão implementados como Processing algorithms formais — F6
      passa de "roadmap formal fechado" para "seção 5.3 inteira
      fechada". — arquivos: nenhum (atualização de plano). **Feito
      nesta revisão** — ver bloco novo no topo da seção Objetivo
      ("F6 — seção 5.3 do CLAUDE.md: FECHADA").

- [x] 58. **(Revisão manual do Diego no QGIS — consolidada, adiada
      indefinidamente a pedido do Diego nesta revisão de 2026-07-23:
      "a validação manual eu não consigo, estou sem computador, por
      enquanto vamos dando sequência". Marcado `[x]` seguindo a mesma
      convenção já usada nos passos 7, 13, 18, 27, 33, 41 e 49 (adiado
      a pedido do Diego, não bloqueia o run) — não significa que a
      validação visual foi feita, só que não bloqueia mais o avanço do
      plano. Não bloqueia o F7 nem a publicação além do que o passo 63
      já previa.)** Numa única
      sessão, com um município piloto de MG e rede OSM real: revisar em
      lote os passos adiados 7, 13, 18, 27, 33, 41, 49 (setorização,
      CPP, RPP, CARP, dimensionamento de frota, equilíbrio entre
      setores) e as duas rodadas novas (distância ao destino, cobertura
      por frequência). Continua sendo o único item que falta para F6
      ser considerado "encerrado" incluindo validação visual — mas
      **o código de F6 (roadmap formal + seção 5.3 inteira) já está
      encerrado independentemente deste passo**, verificado nesta
      revisão (194 testes OK, `make test` OK, `git status` limpo, 25
      algorithms em `provider.py`). F7 segue em paralelo sem esperar
      por este passo; só a publicação final (passo 63) continua
      condicionada a ele. — arquivos: nenhum (revisão manual pelo
      Diego, sem previsão)

**F7 — Preparação para empacotamento (rodando em paralelo à revisão do passo 58; publicação em si espera):**

- [x] 59. Perguntar ao Diego, antes de iniciar qualquer trabalho de
      GUI: o módulo de coleta de lixo entra no F7 sem dock (uso só via
      Processing Toolbox/console, como hoje), ou o Diego quer um
      `gui/waste_dock.py` no padrão de `gui/urban_dock.py`/
      `gui/regional_dock.py` antes da primeira publicação? Não assumir
      a resposta — é uma decisão de escopo do Diego, não técnica. Se a
      resposta for "sim, quero o dock", isso vira uma rodada própria
      (fora deste plano até a resposta chegar). — arquivos: nenhum
      (decisão do Diego). **Respondido em 2026-07-23: sim, o Diego quer
      o dock** ("Quero uma dock para Waste"). Ver "Decisões de
      arquitetura — Dock do módulo Waste" e passos 69-81 abaixo.

- [x] 60. **(Superado pela revisão de 2026-07-23 — não executar como
      escrito; ver passos 82-87 para o desenho corrigido e executável.
      Marcado `[x]` a pedido do Diego nesta revisão ("item 60 foi
      superado. Marcar como feito senão o run não inicia") — mesma
      convenção já usada no passo 58: `[x]` aqui não significa "tarefa
      original executada", significa "não bloqueia mais o avanço do
      plano", porque a tarefa original foi substituída, não cumprida.)**
      ~~Criar a estrutura `i18n/` (...): arquivo fonte de tradução
      `i18n/logis_pt_BR.ts` e `i18n/logis_en.ts` (...)~~ — o desenho
      original previa dois arquivos de tradução; a revisão de
      2026-07-23 descobriu que as strings de origem já estão em PT-BR
      e que `__init__.py` usa `locale[:2]`, então só `i18n/logis_en.ts`
      → `i18n/logis_en.qm` precisam existir (ver "Decisões de
      arquitetura — i18n" acima). — arquivos: nenhum (passo substituído)

- [x] 61. Adicionar `LICENSE` (texto GPL-3.0, conforme seção 9 do
      CLAUDE.md) — exigido pelo processo de submissão ao repositório
      oficial de plugins do QGIS. **Revisado em 2026-07-23: o ícone
      (`icon.png`/`icon.svg`) sai deste passo** — o Diego está
      preparando `icon.svg` por conta própria em paralelo a esta
      revisão; ver passo 88 novo para a integração do ícone quando ele
      for entregue. — arquivos: `LICENSE`

- [x] 62. Revisar `metadata.txt` com o Diego antes do empacotamento
      final: decidir se `experimental=True` deve virar `False`,
      confirmar `version` (semver) e o texto de `about`/`description`
      ainda refletem o estado atual (25 algorithms, 3 módulos). Ajustar
      o `Makefile` com um alvo `make package` que gera
      `dist/logis-<version>.zip` a partir do estado commitado (hoje só
      existe `dist/logis-0.1.0.zip`, sem alvo de Makefile que o gere —
      confirmar como foi criado e automatizar). — arquivos:
      `metadata.txt`, `Makefile`

- [x] 63. Publicação: gerar o zip final com `make package`, testar
      instalação a partir do zip (não do symlink de `make deploy`) numa
      instância limpa do QGIS, e o Diego submete ao repositório oficial
      de plugins do QGIS (plugins.qgis.org) — ação externa/manual do
      Diego, fora do escopo de execução automatizada. Só depois do
      passo 58 (validação manual em lote) estar concluído. — arquivos:
      nenhum (ação manual do Diego)

**Rodada nova — Dock do módulo Waste (resolve o passo 59, pedido
explícito do Diego em 2026-07-23; ver "Decisões de arquitetura — Dock do
módulo Waste" acima para o desenho completo):**

- [x] 69. Criar o esqueleto de `gui/waste_dock.py`: bloco de mocks no
      `try/except ImportError` (copiado do topo de `gui/urban_dock.py`,
      acrescentando qualquer widget novo que as seções seguintes
      precisarem), classe `WasteDock(QgsDockWidget)`, `__init__(self,
      iface, parent=None)` monta um `QScrollArea` com um `QWidget`
      central de `QVBoxLayout` (ver decisão de usar `QScrollArea`,
      diferente dos outros dois docks), título `self.tr("<b>Coleta de
      Lixo</b>")`, ainda sem seções. Rodar `make test` (sintaxe OK) como
      parte deste passo. — arquivos: `gui/waste_dock.py`

- [x] 70. Adicionar a seção "Estimativa de Geração"
      (`logis:waste_generation_estimate`) a `gui/waste_dock.py`: camada
      de setores (polígono), campo de população, taxa per capita
      kg/hab/dia (`QDoubleSpinBox`, default 0.9-1.0, mesmo range do
      algorithm), % de cobertura, botão que chama `processing.run(...)`
      e escreve o resultado num `QTextEdit` da seção. — arquivos:
      `gui/waste_dock.py`

- [x] 71. Adicionar a seção "Setorização" (`logis:waste_districting`) a
      `gui/waste_dock.py`, mesmo padrão da seção anterior (camada de
      vias, campo de carga opcional, nº de setores, parâmetros de
      balanceamento já expostos pelo algorithm). — arquivos:
      `gui/waste_dock.py`

- [x] 72. Adicionar a seção "Roteirização CPP"
      (`logis:waste_cpp_route`) a `gui/waste_dock.py` (camada de vias,
      campo de setor opcional, tolerância de nó). — arquivos:
      `gui/waste_dock.py`

- [x] 73. Adicionar a seção "Roteirização RPP"
      (`logis:waste_rpp_route`) a `gui/waste_dock.py` (camada de vias,
      campo booleano de trecho obrigatório, campo de setor opcional,
      tolerância de nó). — arquivos: `gui/waste_dock.py`

- [x] 74. Adicionar a seção "Roteirização CARP"
      (`logis:waste_carp_route`) a `gui/waste_dock.py` (camada de vias,
      campo de trecho obrigatório opcional, campo de demanda, camada de
      ponto do depósito — `QgsMapLayerComboBox` filtrado a
      `PointLayer`, capacidade do veículo, campo de setor opcional,
      tolerância de nó). — arquivos: `gui/waste_dock.py`

- [x] 75. Adicionar a seção "Dimensionamento de Frota"
      (`logis:waste_fleet_sizing`) a `gui/waste_dock.py` (camada de
      saída de CARP, campo `route_id`, campo de setor opcional,
      velocidade média, jornada, tempo de descarga, tempo de
      deslocamento ao destino). — arquivos: `gui/waste_dock.py`

- [x] 76. Adicionar a seção "Deadhead Ratio"
      (`logis:waste_deadhead_ratio`) a `gui/waste_dock.py` (camada de
      entrada, campo booleano de deadhead via `QgsFieldComboBox`, campo
      de agrupamento de rota opcional). — arquivos: `gui/waste_dock.py`

- [x] 77. Adicionar a seção "Equilíbrio entre Setores"
      (`logis:waste_sector_balance`) a `gui/waste_dock.py` (camada de
      saída de CARP, campo `route_id`, campo de setor opcional, campos
      `route_load_kg`/`route_distance_km`, mesmos parâmetros de
      velocidade/tempo da seção de frota). — arquivos:
      `gui/waste_dock.py`

- [x] 78. Adicionar a seção "Distância ao Destino"
      (`logis:waste_destination_distance`) a `gui/waste_dock.py`
      (camada de rede, camada de destinos — pontos, camada de zonas —
      pontos, critério Distância/Tempo). — arquivos: `gui/waste_dock.py`

- [x] 79. Adicionar a seção "Cobertura por Frequência"
      (`logis:waste_collection_coverage`) a `gui/waste_dock.py` (camada
      de vias exigidas, campo de setor opcional, camada de rota
      coberta, campo booleano de deadhead, campo de setor opcional,
      rótulo de frequência via `QLineEdit`). — arquivos:
      `gui/waste_dock.py`

- [x] 80. Registrar `WasteDock` em `logis_plugin.py`: `self.action_waste
      = None` e `self.dock_waste = None` no `__init__`; em `initGui`,
      `QAction(self.tr("Coleta de Lixo"), ...)` +
      `addPluginToMenu("logis", self.action_waste)`, mesmo padrão de
      `action_urban`/`action_regional`; `show_waste_dock()` que
      instancia `WasteDock` uma única vez e reusa (mesmo padrão de
      `show_urban_dock`/`show_regional_dock`); limpeza espelhada em
      `unload()` (`removePluginMenu` + `removeDockWidget` com guard
      `sip.isdeleted`). — arquivos: `logis_plugin.py`

- [x] 81. Rodar `make test` e `python3 -m unittest discover -s . -p
      "test_*.py"` para confirmar que `gui/waste_dock.py` e
      `logis_plugin.py` atualizados não quebram nada (194 testes
      continuam OK — o dock não tem teste próprio, mesma situação de
      `urban_dock.py`/`regional_dock.py`, que também não têm; a
      cobertura é indireta via `make test`, que faz `ast.parse` de todo
      `.py` do repo, incluindo `gui/waste_dock.py`). Corrigir o que for
      necessário até passar. Commitar e dar push da rodada do dock
      Waste. — arquivos: nenhum novo (verificação + commit)

**Rodada nova — i18n (resolve o passo 60, pedido explícito do Diego em
2026-07-23, "enquanto eu faço o icon.svg"; ver "Decisões de arquitetura —
i18n" acima para o desenho completo):**

- [x] 82. Adicionar os alvos `i18n` e `transcompile` ao `Makefile`
      (mesmo padrão do `Makefile` do GisBR): `i18n` roda `@mkdir -p
      i18n && pylupdate5 provider.py logis_plugin.py gui/*.py
      algorithms/*.py -ts i18n/logis_en.ts`; `transcompile` roda
      `@lrelease i18n/logis_en.ts`. Atualizar também o `help` do
      Makefile com as duas linhas novas. — arquivos: `Makefile`

- [x] 83. Rodar `make i18n` para gerar `i18n/logis_en.ts` a partir das
      632 ocorrências de `self.tr(...)` já espalhadas por
      `provider.py`, `logis_plugin.py`, `gui/*.py` (incluindo o
      `waste_dock.py` da rodada anterior) e `algorithms/*.py`.
      Confirmar que o arquivo foi gerado e que `make test` continua OK.
      — arquivos: `i18n/logis_en.ts` (gerado)

- [x] 84. Traduzir para inglês todas as entradas `<translation
      type="unfinished"></translation>` de `i18n/logis_en.ts`,
      preenchendo com o texto em inglês correspondente a cada
      `<source>` em português. Não alterar nenhuma string de origem em
      `self.tr(...)` no código Python — só o arquivo `.ts`. — arquivos:
      `i18n/logis_en.ts`

- [x] 85. Rodar `make transcompile` para compilar `i18n/logis_en.qm` a
      partir do `.ts` traduzido. Confirmar que o arquivo `.qm` foi
      gerado e que `make test` continua OK. — arquivos:
      `i18n/logis_en.qm` (gerado)

- [x] 86. Criar `test_i18n.py`: usando `PyQt5.QtCore.QTranslator`
      diretamente (sem `import qgis`, já que não há QGIS instalado
      neste ambiente — `qgis.PyQt` é só um alias para o PyQt5 do
      sistema), carregar `i18n/logis_en.qm` e confirmar que uma string
      de origem conhecida (ex.: `"Calcular Indicadores"`) traduz
      corretamente para o inglês esperado; confirmar também que
      `i18n/logis_pt.qm` **não existe** (documenta a decisão de que o
      fallback de origem PT-BR é suficiente — ver "Decisões de
      arquitetura — i18n"). Rodar `python3 -m unittest test_i18n -v` e
      `make test`; só marcar `[x]` quando ambos passarem. — arquivos:
      `test_i18n.py`

_(Passo 87 — "rodar a suíte e commitar/pushar a rodada i18n" — removido: era
verificação-pura, sem diff, que o gate F1 não marca e travava o run-all. A
verificação já está embutida nos passos 85/86; o commit+push saiu de fato em
`6ecee4b` e o restante fecha por `/review`+`/push`.)_

**Item avulso — integração do ícone (entregue pelo Diego em 2026-07-23,
conteúdo exato em "Decisões de arquitetura — Ícone", fora da rodada
i18n):**

- [x] 88. Gravar `icon.svg` na raiz do repositório com exatamente o
      conteúdo colado pelo Diego (ver "Decisões de arquitetura —
      Ícone" — não alterar traços/cores/pontos). Atualizar
      `metadata.txt` (`icon=icon.svg`, hoje aponta para `icon.png` que
      nunca existiu). Confirmar na documentação de submissão do
      repositório oficial de plugins do QGIS que SVG é aceito como
      ícone de listagem (o `QIcon`/`QSvgIconEngine` do PyQt5 carrega
      SVG nativamente — não é limitação técnica, só confirmar o
      requisito formal de submissão); se a documentação exigir PNG,
      não gerar `icon.png` sozinho — voltar ao Diego com a decisão.
      Nenhum `algorithms/*.py`/`provider.py` hoje sobrescreve `icon()`
      (verificado — `grep -n "def icon" provider.py algorithms/*.py`
      não retorna nada), então os ícones individuais de cada `logis:*`
      na Processing Toolbox continuam o padrão do QGIS; perguntar ao
      Diego se ele quer usar o SVG também ali antes de mudar isso (fora
      de escopo até ele pedir). Rodar `make test` para confirmar que
      nada quebrou e commitar. — arquivos: `metadata.txt`, `icon.svg`

**Nova rodada — backend OR-Tools para o CVRP (prioritária, executar
antes de retomar a rodada 9; desenho revisado nesta sessão — mesmo
arquivo `vrp.py`, parâmetro `backend` em `solve_cvrp()`; ver "Decisões
de arquitetura — Novas para o backend OR-Tools do CVRP" acima para o
desenho completo):**

- [x] 64. Em `core/routing/vrp.py`, extrair de dentro de
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

- [x] 65. Adicionar `solve_cvrp_ortools(distance_matrix, demands,
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

- [x] 66. Adicionar o parâmetro `backend: str = "python"` a
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

- [x] 67. Ampliar `test_vrp.py` (não criar arquivo novo) com: (a)
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

_(Passo 68 — "rodar a suíte e commitar/pushar" — removido: verificação-pura sem
diff, que trava o gate F1. A verificação da rodada OR-Tools já está embutida no
passo 67 (`unittest test_vrp` + `make test`); commit+push saem por `/review`+`/push`.)_

**F8 — compatibilidade QGIS 4 / Qt 6 (rodada 2026-07-29). Executar na
ordem: o passo 89 destrava todos os outros (a suíte está vermelha hoje).**

- [x] 89. [T02] Consertar a suíte quebrada pelo commit `4c49617` (plugin
      movido para a subpasta `logis/`): trocar os alvos de `patch()` que
      ainda usam o caminho antigo pelos novos —
      `patch('gui.waste_dock.QMessageBox...')` →
      `patch('logis.gui.waste_dock.QMessageBox...')` (8 ocorrências em
      `test_waste_dock.py`), `patch("core.optim_backend.has_ortools")` →
      `patch("logis.core.optim_backend.has_ortools")` (`test_vrp.py`),
      `@patch('core.connectors.wfs.fetch_layer')` →
      `@patch('logis.core.connectors.wfs.fetch_layer')`
      (`test_snv_pipeline.py`); e em `test_i18n.py` apontar os caminhos
      de `.qm` para `logis/i18n/` (`os.path.join(os.path.dirname(
      __file__), "logis", "i18n", ...)`, nos dois casos do arquivo —
      o `logis_en.qm` que deve existir e o `logis_pt.qm` que não deve).
      Conferir se os módulos importados no topo desses testes também
      usam o prefixo `logis.`; se algum ainda importar sem prefixo,
      ajustar junto. Antes de marcar `[x]`: `python3 -m unittest
      discover -s . -p "test_*.py"` tem que sair **OK** (hoje: 211
      testes, 1 failure + 10 errors) e `make test` continuar `sintaxe
      OK`. — arquivos: `test_waste_dock.py`, `test_vrp.py`,
      `test_snv_pipeline.py`, `test_i18n.py`

- [x] 90. [T03] Corrigir a guarda de `field_type()` em
      `logis/core/qgis_compat.py`: trocar `if QVariant is not None:` por
      um teste de **presença de membro** (`if QVariant is not None and
      hasattr(QVariant, "String"):`) e, no bloco `QMetaType`, manter a
      checagem de `getattr(QMetaType, "Type", None)`. Preservar a ordem
      QVariant→QMetaType e ampliar a docstring explicando o porquê da
      nova guarda (no PyQt6 o `QVariant` importa mas perdeu os membros
      de `QVariant::Type`, então testar o import não detecta nada).
      Criar `test_qgis_compat.py` com: (a) `field_type("int")`,
      `("double")`, `("string")`, `("bool")` devolvem algo aceito por
      `QgsField(nome, tipo)` de fato (construir o `QgsField` no teste);
      (b) `field_type("coisa_que_nao_existe")` devolve o valor inválido
      sem levantar; (c) simulação do PyQt6 — com
      `unittest.mock.patch.object(qgis_compat, "QVariant", <objeto sem
      atributo String>)` e `QMetaType` real, `field_type("string")`
      devolve `QMetaType.Type.QString` em vez de estourar
      `AttributeError` (é este caso que reproduz o bug do QGIS 4 aqui no
      PyQt5); (d) caso em que ambos são `None` → devolve `None`. Rodar
      `python3 -m unittest test_qgis_compat -v` e a suíte completa antes
      de marcar. — arquivos: `logis/core/qgis_compat.py`,
      `test_qgis_compat.py`

- [x] 91. [T02] Corrigir os dois tracebacks relatados pelo Diego:
      em `logis/logis_plugin.py`, trocar as 3 ocorrências de
      `Qt.RightDockWidgetArea` (linhas 78, 86, 94) por
      `Qt.DockWidgetArea.RightDockWidgetArea` e `self.dialog.exec_()`
      (linha 71) por `self.dialog.exec()`; em
      `logis/gui/dependencies_dialog.py` (linha 158), trocar
      `Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint` por
      `Qt.WindowType.WindowMinMaxButtonsHint |
      Qt.WindowType.WindowCloseButtonHint`, e no bloco de mocks
      (`except ImportError`) substituir os atributos soltos da `class
      Qt` por uma classe aninhada `WindowType` com
      `WindowMinMaxButtonsHint = 0` e `WindowCloseButtonHint = 0`
      (manter `Window = 0` se algo ainda usar). Não criar teste que
      chame `exec()` (é modal, travaria a suíte). Antes de marcar:
      suíte completa OK (`test_plugin.py` já exercita
      `show_urban_dock`, que é exatamente o caminho do primeiro
      traceback) + `make test`. — arquivos: `logis/logis_plugin.py`,
      `logis/gui/dependencies_dialog.py`

- [x] 92. [T02] Eliminar o uso direto de `QVariant` nos 7 algorithms,
      substituindo por `field_type()` (import relativo
      `from ..core.qgis_compat import field_type`, padrão dos outros 16
      arquivos) e removendo o `from qgis.PyQt.QtCore import QVariant`
      de cada um: `QVariant.Int` → `field_type("int")`,
      `QVariant.Double` → `field_type("double")`, `QVariant.Bool` →
      `field_type("bool")`. Arquivos:
      `logis/algorithms/waste_districting.py`,
      `logis/algorithms/regional_critical_links.py`,
      `logis/algorithms/vrp_cvrp.py`, `logis/algorithms/facility_mclp.py`,
      `logis/algorithms/facility_lscp.py`,
      `logis/algorithms/facility_p_median.py`,
      `logis/algorithms/urban_edge_betweenness.py`. Conferir com
      `grep -rn "QVariant" logis/` que só sobra `core/qgis_compat.py`.
      Antes de marcar: suíte completa OK + `make test`. — arquivos: os 7
      acima

- [x] 93. [T02] Escopar os enums do Processing e do WKB em todos os
      arquivos de `logis/`: `QgsProcessing.TypeVectorLine|TypeVectorPoint|
      TypeVectorPolygon` → `QgsProcessing.SourceType.<mesmo nome>` (43
      sítios), `QgsProcessingParameterNumber.Double|Integer` →
      `QgsProcessingParameterNumber.Type.<mesmo nome>` (28 sítios),
      `QgsWkbTypes.LineString|NoGeometry` → `QgsWkbTypes.Type.<mesmo
      nome>` e `QgsWkbTypes.PointGeometry` →
      `QgsWkbTypes.GeometryType.PointGeometry`. **Conferir sítio a
      sítio** — `PointGeometry` é do enum `GeometryType` e `LineString`
      é do enum `Type`, apesar de virem os dois de `QgsWkbTypes`; e
      pular as ocorrências que já estão escopadas (`grep -n
      "QgsWkbTypes\.\(GeometryType\|Type\)\."` antes de editar). Todas
      as formas escopadas foram verificadas como existentes no QGIS
      3.34, então a suíte local prova a mudança: antes de marcar, suíte
      completa OK + `make test`. — arquivos: `logis/algorithms/*.py`,
      `logis/core/network/*.py` (os que aparecerem no grep)

- [x] 94. [T02] Corrigir `logis/core/ortools_installer.py`: (a) trocar
      `QgsTask.CanCancel` por `QgsTask.Flag.CanCancel` na chamada
      `super().__init__(...)` e ajustar o mock `class QgsTask` do bloco
      `except ImportError` para expor `Flag.CanCancel` em vez de
      `CanCancel` solto; (b) trocar o comando de instalação por
      exatamente o da seção 2.1 do CLAUDE.md — `[sys.executable, "-m",
      "pip", "install", "--user", "ortools", "pandas<3", "numpy<2",
      "typing_extensions==4.10.0"]` — e, se a saída do pip contiver
      `externally-managed-environment`, repetir **uma** vez com
      `--break-system-packages` acrescentado, logando essa segunda
      tentativa via `log_received`; (c) atualizar o texto do
      `ortools_desc` em `gui/dependencies_dialog.py` para mencionar que
      a instalação usa versões travadas de `numpy`/`pandas` para não
      danificar o QGIS. Adicionar a `test_plugin.py` (ou novo
      `test_ortools_installer.py`, à escolha do executor) um teste que
      monta o comando e afirma que as três travas estão presentes e que
      `pip install ortools` "puro" **não** é usado. Antes de marcar:
      suíte completa OK + `make test`. — arquivos:
      `logis/core/ortools_installer.py`,
      `logis/gui/dependencies_dialog.py`, `test_ortools_installer.py`

- [x] 95. [T02] Criar `test_qt6_compat.py`: teste estático que lê como
      texto todos os `.py` sob `logis/` (`pathlib.Path(...).rglob("*.py")`,
      pulando `__pycache__` e `i18n/`) e falha se encontrar qualquer
      padrão proibido, com mensagem apontando arquivo:linha —
      `\bQt\.(Right|Left|Top|Bottom)DockWidgetArea\b`,
      `\bQt\.Window[A-Za-z]*Hint\b`, `\bQVariant\.` (exceto em
      `core/qgis_compat.py`), `\.exec_\(`,
      `\bQgsProcessing\.TypeVector`,
      `\bQgsProcessingParameterNumber\.(Double|Integer)\b`,
      `\bQgsWkbTypes\.(LineString|NoGeometry|PointGeometry)\b`,
      `\bQgsTask\.CanCancel\b`. Sem importar QGIS (roda em qualquer
      Python). Incluir no próprio teste um comentário curto explicando
      por que ele existe (a suíte roda em PyQt5, onde a forma errada não
      falha em runtime). Ele tem que passar ao final dos passos 90-94 —
      se algum sítio escapou, este teste é quem acusa. Antes de marcar:
      `python3 -m unittest test_qt6_compat -v` OK + suíte completa OK. —
      arquivos: `test_qt6_compat.py`

- [x] 96. [T02] Registrar a regra no CLAUDE.md (seção 9, "Regras para
      agentes"): item novo dizendo que todo acesso a enum do Qt/QGIS é
      **escopado** (`Qt.DockWidgetArea.RightDockWidgetArea`,
      `QgsProcessing.SourceType.TypeVectorLine`,
      `QgsProcessingParameterNumber.Type.Double`, `QgsWkbTypes.Type.*` /
      `QgsWkbTypes.GeometryType.*`, `QgsTask.Flag.*`), que tipo de campo
      só se cria via `core.qgis_compat.field_type()` (nunca `QVariant.*`
      direto) e que `exec_()` não pode ser usado — com a justificativa em
      uma linha (PyQt6/QGIS 4 removeu as formas soltas; as escopadas
      valem também no QGIS 3.16+) e a menção de que `test_qt6_compat.py`
      é quem faz cumprir. — arquivos: `CLAUDE.md`

- [x] 97. [T02] Ajustar `metadata.txt` e `Makefile` para o QGIS 4:
      em `logis/metadata.txt`, acrescentar `supportsQt6=True` e subir
      `version` para `0.1.1` (mantendo `qgisMinimumVersion=3.16` e
      `qgisMaximumVersion=4.99`); no `Makefile`, introduzir
      `QGIS_MAJOR ?= 3` e usar `QGIS$(QGIS_MAJOR)` nos caminhos de
      `QGIS_PLUGINS`/`FLATPAK_PLUGINS`, mais os alvos `deploy-qgis4` e
      `deploy-flatpak-qgis4` (que só chamam os alvos existentes com
      `QGIS_MAJOR=4`), com as linhas correspondentes no `help` e nos
      `.PHONY`. Antes de marcar: `make help` lista os alvos novos,
      `make test` continua `sintaxe OK` e a suíte completa passa. —
      arquivos: `logis/metadata.txt`, `Makefile`

- [x] 98. [T02] Criar `docs/qgis4_compat_check.py` (não empacotado):
      script colável no console Python do QGIS 4 do Diego que imprime um
      relatório de uma tela — versões (`Qgis.QGIS_VERSION`,
      `QT_VERSION_STR`, `PYQT_VERSION_STR`) e, para cada nome legado da
      tabela do Objetivo, se ele ainda existe (`hasattr`) e se a forma
      escopada existe: `Qt.RightDockWidgetArea` vs
      `Qt.DockWidgetArea.RightDockWidgetArea`, `QVariant.String`,
      `QMetaType.Type.QString`, `QgsWkbTypes.LineString` vs
      `QgsWkbTypes.Type.LineString`, `QgsProcessing.TypeVectorLine` vs
      `QgsProcessing.SourceType.TypeVectorLine`,
      `QgsProcessingParameterNumber.Double` vs `...Type.Double`,
      `QgsTask.CanCancel` vs `QgsTask.Flag.CanCancel`, `QDialog.exec_`
      vs `QDialog.exec`, e se `QgsField("t", QMetaType.Type.QString)`
      constrói sem erro. Cada linha no formato `OK/AUSENTE  <nome>`.
      Documentar no `README.md` (uma linha, seção de
      desenvolvimento/solução de problemas) como usá-lo. Rodar o script
      aqui mesmo com `python3 docs/qgis4_compat_check.py` antes de
      marcar — ele tem que rodar sem exceção no QGIS 3.34 também
      (relatando as diferenças, não estourando). — arquivos:
      `docs/qgis4_compat_check.py`, `README.md`

### F9 — usabilidade dos painéis no QGIS 4.2 (rodada 2026-07-29, segunda revisão)

- [x] 99. [T02] Dar rolagem ao painel Urbano: em
      `logis/gui/urban_dock.py`, acrescentar `QScrollArea` à lista de
      imports de `qgis.PyQt.QtWidgets` (bloco `try`), acrescentar o mock
      `class QScrollArea` com `__init__`, `setWidgetResizable` e
      `setWidget` no bloco `except ImportError` (copiar o de
      `waste_dock.py:156-162`), e no início de `_build_ui` criar
      `scroll = QScrollArea()` + `scroll.setWidgetResizable(True)`,
      trocando o `self.setWidget(central)` do fim (linha ~305) por
      `scroll.setWidget(central)` + `self.setWidget(scroll)`. Não mexer
      em nenhuma seção nem em nenhum widget existente. Rodar `make test`
      e `python3 -m unittest discover -s . -p "test_*.py"` (224 testes,
      OK) antes de marcar. — arquivos: `logis/gui/urban_dock.py`
- [x] 100. [T02] Dar rolagem ao painel Regional: mesma mudança do passo
      99 aplicada a `logis/gui/regional_dock.py` (`self.setWidget(
      central)` está na linha ~237). Rodar `make test` e a suíte antes de
      marcar. — arquivos: `logis/gui/regional_dock.py`
- [x] 101. [T02] Criar `test_dock_layout.py`: teste estático que lê
      `logis/gui/urban_dock.py`, `logis/gui/regional_dock.py` e
      `logis/gui/waste_dock.py` como texto (`pathlib.Path.read_text` +
      `re`, mesma técnica de `test_qt6_compat.py`, sem importar QGIS) e
      afirma, para os três: contém `QScrollArea(`, contém
      `setWidgetResizable(True)` e contém `self.setWidget(scroll)`. O
      guarda das abas (`waste_dock.py` contém `QTabWidget(`) **não** entra
      agora — só valeria a partir do passo 104 e deixaria a suíte
      vermelha; ele é acrescentado no passo 110. Rodar a suíte (225+
      testes, OK) antes de marcar. — arquivos: `test_dock_layout.py`
- [x] 102. [T02] Corrigir o stylesheet dos dois `QGroupBox` de
      `logis/gui/dependencies_dialog.py` (linhas 193 e 227), que é a
      causa provável do texto sobreposto relatado pelo Diego: trocar
      `"font-weight: bold; padding: 10px;"` pela regra escopada
      `"QGroupBox { font-weight: bold; margin-top: 12px; padding: 10px; }
      QGroupBox::title { subcontrol-origin: margin; left: 8px; padding:
      0 4px; }"`. Nenhuma outra mudança neste passo. Rodar `make test` e
      a suíte antes de marcar. — arquivos:
      `logis/gui/dependencies_dialog.py`
- [x] 103. [T02] Redimensionar e dar rolagem ao diálogo de dependências:
      em `logis/gui/dependencies_dialog.py`, trocar `resize(550, 420)`/
      `setMinimumSize(500, 350)` por `resize(620, 560)`/
      `setMinimumSize(520, 420)`; em `init_ui`, criar `outer =
      QVBoxLayout(self)`, um `QScrollArea` com `setWidgetResizable(True)`
      cujo widget de conteúdo (`QWidget`) recebe o layout atual (título,
      descrição e os dois `QGroupBox`), e mover o rodapé do botão
      "Fechar" para **fora** da rolagem, direto no `outer`. Acrescentar
      `QScrollArea`/`QWidget` aos imports do bloco `try` e os mocks
      correspondentes ao bloco `except ImportError`. Não alterar texto de
      nenhuma string nem a lógica de `refresh_status`/
      `start_ortools_install`. Rodar `make test` e a suíte antes de
      marcar. — arquivos: `logis/gui/dependencies_dialog.py`
- [x] 104. [T03] Introduzir a estrutura de abas em
      `logis/gui/waste_dock.py`: importar `QTabWidget` (bloco `try`) e
      mocká-lo no `except ImportError` (`__init__`, `addTab`, `count`,
      `tabText`); reescrever o topo de `_build_ui` para montar
      `central`/`layout` só com o título, a descrição, `self.tabs =
      QTabWidget()` e, no rodapé, o painel de resultados existente
      (`QLabel("Resultados:")` + `self.txt_results`, hoje nas linhas
      634-642) — o `QScrollArea` externo do dock permanece; acrescentar o
      helper privado `_new_tab(self, title)` que cria `QWidget` +
      `QVBoxLayout` (margens 10, espaçamento 10) dentro de uma
      `QScrollArea` com `setWidgetResizable(True)`, chama
      `self.tabs.addTab(scroll, title)` e devolve o layout; mover a seção
      "Estimativa de Geração" (linhas ~203-262) para a aba
      `self.tr("Geração")`. As seções ainda não migradas (CPP em diante)
      vão temporariamente para uma aba `self.tr("Outros")` criada pelo
      mesmo helper, para que **todos** os widgets continuem existindo.
      Nenhum atributo renomeado, nenhum método `run_*` alterado.
      `test_waste_dock.py` tem que passar **sem edição**; rodar `make
      test` e a suíte antes de marcar. — arquivos:
      `logis/gui/waste_dock.py`
- [x] 105. [T02] Mover as três seções de roteirização (CPP, RPP e CARP —
      hoje linhas ~263-403) da aba temporária "Outros" para uma aba
      `self.tr("Roteirização")` criada com `_new_tab`, mantendo a ordem
      CPP → RPP → CARP e os títulos `<b>...</b>` de cada seção como
      separadores dentro da aba. Nenhum widget renomeado.
      `test_waste_dock.py` passa sem edição; rodar `make test` e a suíte
      antes de marcar. — arquivos: `logis/gui/waste_dock.py`
- [x] 106. [T02] Mover a seção "Dimensionamento de Frota" (hoje linhas
      ~404-468) da aba "Outros" para uma aba `self.tr("Frota")` criada
      com `_new_tab`. `test_waste_dock.py` passa sem edição; rodar `make
      test` e a suíte antes de marcar. — arquivos:
      `logis/gui/waste_dock.py`
- [x] 107. [T02] Mover as três seções restantes (Equilíbrio entre
      Setores, Distância ao Destino, Cobertura por Frequência — hoje
      linhas ~469-632) para uma aba `self.tr("Indicadores")` criada com
      `_new_tab` e **remover a aba temporária "Outros"**, que fica vazia.
      Ao fim deste passo o dock tem exatamente quatro abas (Geração,
      Roteirização, Frota, Indicadores) e o painel de resultados no
      rodapé, fora delas. `test_waste_dock.py` passa sem edição; rodar
      `make test` e a suíte antes de marcar. — arquivos:
      `logis/gui/waste_dock.py`
- [x] 108. [T02] Fechar a lacuna da Setorização: acrescentar à aba
      "Geração" a seção `<b>Setorização</b>` que chama
      `processing.run("logis:waste_districting", ...)`, lendo os nomes e
      defaults exatos dos parâmetros em
      `logis/algorithms/waste_districting.py` (não inventar); widgets no
      padrão das seções vizinhas (`QgsMapLayerComboBox` com
      `QgsMapLayerProxyModel.Filter.*` escopado, `QgsFieldComboBox` com
      `layerChanged` conectado, `QDoubleSpinBox`/`QSpinBox`,
      `self.btn_run_districting`), todas as strings em `self.tr(...)`, e
      o método `run_districting` copiando a estrutura de
      `calculate_waste_generation` (validação de camada nula com
      `QMessageBox.warning`, `try/except` com `QMessageBox.critical`,
      log em `self.txt_results`). Rodar `make test` e a suíte antes de
      marcar. — arquivos: `logis/gui/waste_dock.py`
- [x] 109. [T02] Fechar a lacuna do Deadhead Ratio: acrescentar à aba
      "Indicadores" a seção `<b>Deadhead Ratio</b>` que chama
      `processing.run("logis:waste_deadhead_ratio", ...)`, com os
      parâmetros lidos de `logis/algorithms/waste_deadhead_ratio.py`,
      mesmo padrão de widgets/strings/método do passo 108
      (`self.btn_run_deadhead`, `run_deadhead_ratio`). Rodar `make test`
      e a suíte antes de marcar. — arquivos: `logis/gui/waste_dock.py`
- [x] 110. [T02] Ampliar a cobertura de teste da nova estrutura: em
      `test_waste_dock.py`, acrescentar asserts de `hasattr` para os
      widgets das seções novas dos passos 108-109 e para `self.tabs`; em
      `test_dock_layout.py`, acrescentar o caso estático das abas
      (`waste_dock.py` contém `QTabWidget(`, contém `def _new_tab` e
      registra exatamente quatro chamadas de `_new_tab`) e o caso de que
      `self.txt_results` é criado fora de qualquer aba (painel de
      resultados compartilhado). Rodar `make test` e a suíte antes de
      marcar. — arquivos: `test_waste_dock.py`, `test_dock_layout.py`
- [x] 111. [T02] Atualizar a tradução para inglês com as strings novas de
      F9: rodar `make i18n` (regenera `i18n/logis_en.ts`), preencher em
      inglês as entradas `<translation type="unfinished">` criadas pelos
      passos 104-109 (títulos das quatro abas, rótulos e botões das
      seções Setorização e Deadhead Ratio), rodar `make transcompile`
      para regerar `i18n/logis_en.qm` e conferir que `test_i18n.py`
      continua passando. Não alterar nenhuma string PT-BR já existente.
      Rodar `make test` e a suíte antes de marcar. — arquivos:
      `i18n/logis_en.ts`, `i18n/logis_en.qm`
- [x] 112. [T02] Registrar o ambiente validado e subir a versão:
      `metadata.txt` passa a `version=0.1.2`; `README.md` ganha, na seção
      de compatibilidade/instalação, a nota de que o plugin foi testado
      pelo autor no **QGIS 4.2 "Belém do Pará" sobre Ubuntu** e de que a
      instalação do OR-Tools pelo diálogo "Dependências" (comando com as
      travas `pandas<3`, `numpy<2`, `typing_extensions==4.10.0`) foi
      validada nesse ambiente. Rodar `make test` e a suíte antes de
      marcar. — arquivos: `metadata.txt`, `README.md`

### F10 — abas no painel de Indicadores Urbanos (rodada 2026-07-30)

- [x] 113. [T03] Introduzir a estrutura de abas em
      `logis/gui/urban_dock.py`, copiando o padrão de `waste_dock.py`:
      acrescentar `QTabWidget` ao import do bloco `try` e o mock
      correspondente no `except ImportError` (cópia literal de
      `waste_dock.py:164-173`, com `addTab`/`count`/`tabText`); criar o
      helper `_new_tab(title)` idêntico ao de `waste_dock.py:190-204`; em
      `_build_ui`, renomear o layout externo para `outer` e montar a
      ordem título → descrição → **seletor `cmb_network` (compartilhado,
      fora das abas)** → `self.tabs = QTabWidget()` → rótulo
      "Resultados dos Indicadores:" + `outer.addWidget(self.txt_results)`
      no rodapé; criar a primeira aba com
      `layout = self._new_tab(self.tr("Rede"))` e mover para ela o bloco
      de estrutura de rede que hoje está nas linhas 206-216 (rótulo +
      `cmb_area` + `btn_calculate`). Manter a `QScrollArea` externa e
      `self.setWidget(scroll)`. Nenhum método `calculate_*` muda.
      `test_plugin.py` e `test_dock_layout.py` têm que passar **sem
      edição**; rodar `make test` e a suíte antes de marcar. — arquivos:
      `logis/gui/urban_dock.py`
- [x] 114. [T02] Mover a seção "Centralidade de Intermediação
      (Betweenness)" (hoje linhas 277-290: título,
      `spin_betweenness_samples`, `btn_calculate_betweenness`) para
      dentro da aba "Rede" criada no passo 113, logo abaixo do
      botão-pacote. Só recorte e colagem de `layout.addWidget(...)` — sem
      renomear widget, sem tocar em `calculate_edge_betweenness`. Rodar
      `make test` e a suíte antes de marcar. — arquivos:
      `logis/gui/urban_dock.py`
- [x] 115. [T02] Criar a aba "Demanda"
      (`layout = self._new_tab(self.tr("Demanda"))`) e mover para ela, na
      ordem, as seções "Densidade de Demanda" (linhas 228-243:
      `txt_code_muni`, `txt_population_field`, `btn_calculate_demand`) e
      "Acessibilidade Gravitacional" (linhas 245-275:
      `cmb_gravity_origin`, `cmb_gravity_dest`,
      `cmb_gravity_weight_field` com o `layerChanged.connect`,
      `spin_gravity_beta`, `btn_calculate_gravity`). Manter a conexão
      `cmb_gravity_dest.layerChanged.connect(...)` intacta. Rodar
      `make test` e a suíte antes de marcar. — arquivos:
      `logis/gui/urban_dock.py`
- [x] 116. [T02] Criar a aba "Carga"
      (`layout = self._new_tab(self.tr("Carga"))`) e mover para ela a
      seção "Distância de Entrega" (linhas 292-314:
      `cmb_delivery_depots`, `cmb_delivery_zones`,
      `cmb_delivery_criterion`, `btn_calculate_delivery`). Ao fim deste
      passo `_build_ui` não deve ter mais nenhuma seção fora das abas
      além do cabeçalho (`cmb_network`) e do rodapé (`txt_results`).
      `test_plugin.py::test_urban_dock_delivery_distance_controls` tem
      que continuar passando sem edição. Rodar `make test` e a suíte
      antes de marcar. — arquivos: `logis/gui/urban_dock.py`
- [x] 117. [T02] Separar a restrição de carga do botão-pacote: criar o
      método `calculate_cargo_restriction()` com o bloco hoje nas linhas
      425-442 (`processing.run("logis:urban_cargo_restriction", ...)` e o
      tratamento de resultado/erro), precedido do mesmo preâmbulo de
      guarda dos outros métodos (ler `cmb_network`, `QMessageBox.warning`
      se vazio, `import processing` em `try/except` com
      `QMessageBox.critical`), passando
      `'RESTRICTION_EXPRESSION': self.txt_cargo_expression.text().strip()`;
      remover esse bloco de `calculate_indicators`, renumerar o log
      restante para "1) 2) 3)" e ajustar a docstring para "os três
      algoritmos de estrutura de rede"; acrescentar na aba "Carga",
      **acima** da Distância de Entrega, a seção "Restrição de Circulação
      de Carga" com título, rótulo + `QLineEdit`
      `self.txt_cargo_expression` (vazio por padrão, placeholder com
      exemplo de expressão sobre `highway`/`maxweight`) e
      `self.btn_calculate_cargo` ligado ao método novo. Rodar `make test`
      e a suíte antes de marcar. — arquivos: `logis/gui/urban_dock.py`
- [x] 118. [T02] Cobrir a estrutura nova com teste: em
      `test_dock_layout.py`, acrescentar `test_urban_dock_has_three_tabs`
      (espelhando `test_waste_dock_has_four_tabs`) afirmando que
      `logis/gui/urban_dock.py` contém `QTabWidget(`, `def _new_tab` e
      exatamente **três** chamadas `self._new_tab(`, e
      `test_urban_dock_results_panel_outside_tabs` afirmando
      `outer.addWidget(self.txt_results)`; em `test_plugin.py`,
      acrescentar asserções `hasattr` para `tabs`, `txt_cargo_expression`,
      `btn_calculate_cargo` e `calculate_cargo_restriction` (mesmo estilo
      de `test_urban_dock_delivery_distance_controls`). Rodar `make test`
      e a suíte antes de marcar (base: 228 testes). — arquivos:
      `test_dock_layout.py`, `test_plugin.py`
- [x] 119. [T02] Atualizar a tradução para inglês com as strings novas de
      F10 e consertar o alvo `transcompile`: no `Makefile`, trocar
      `lrelease i18n/*.ts` por `lrelease $(PLUGINNAME)/i18n/*.ts` (os
      `.ts` estão em `logis/i18n/` desde a reestruturação; o alvo `i18n`
      já usa o caminho certo); rodar `make i18n`, preencher em inglês as
      entradas `<translation type="unfinished">` criadas pelos passos
      113-117 (títulos das três abas — Rede/Demanda/Carga — e os rótulos,
      placeholder e botão da seção de Restrição de Circulação de Carga),
      rodar `make transcompile` e conferir que `test_i18n.py` continua
      passando. Não alterar nenhuma string PT-BR já existente. Rodar
      `make test` e a suíte antes de marcar. — arquivos: `Makefile`,
      `logis/i18n/logis_en.ts`, `logis/i18n/logis_en.qm`
- [x] 120. [T02] Subir a versão e registrar a mudança: `metadata.txt`
      passa a `version=0.1.3`; `README.md` descreve o painel Urbano em
      três abas (Rede, Demanda, Carga), com o seletor de rede viária e o
      painel de resultados compartilhados fora das abas, e registra que a
      restrição de circulação de carga agora tem botão e campo de
      expressão próprios (deixou de ser executada junto do pacote de
      indicadores de rede). Rodar `make test` e a suíte antes de marcar.
      — arquivos: `logis/metadata.txt`, `README.md`

## Critério de aceite

- **F10 — abas no painel de Indicadores Urbanos (passos 113-120, rodada
  2026-07-30):**
  - `logis/gui/urban_dock.py` tem **três abas** (Rede, Demanda, Carga):
    `grep -c "self._new_tab(" logis/gui/urban_dock.py` → 3, e
    `test_dock_layout.py` prova isso estaticamente, sem QGIS.
  - O seletor `cmb_network` e o `txt_results` ficam **fora** das abas
    (cabeçalho e rodapé): `outer.addWidget(self.txt_results)` presente, e
    nenhum dos quatro métodos que leem `cmb_network` precisou saber que
    existem abas.
  - Os oito algorithms urbanos continuam todos acessíveis pelo painel —
    nenhuma seção perdida na remontagem, provado por
    `test_plugin.py` passando **sem edição** nos passos 113-116.
  - `logis:urban_cargo_restriction` tem botão próprio
    (`btn_calculate_cargo` → `calculate_cargo_restriction`) e campo de
    expressão (`txt_cargo_expression`, vazio por padrão = comportamento
    de hoje); `calculate_indicators` roda **três** algorithms.
  - `make test` → `sintaxe OK` e `python3 -m unittest discover -s . -p
    "test_*.py"` → OK ao fim de **cada** passo (base: 228 testes no
    início da rodada).
  - `make transcompile` regenera de fato `logis/i18n/logis_en.qm` (alvo
    corrigido para `$(PLUGINNAME)/i18n/*.ts`); `test_i18n.py` continua
    passando.
  - `metadata.txt` em `version=0.1.3`; `README.md` descreve as três abas.
  - **Nada fora de `logis/gui/urban_dock.py`, dos dois testes, do i18n,
    do `Makefile`, de `metadata.txt` e do `README.md`** — F10 não toca
    `core/`, `algorithms/`, `provider.py` nem `regional_dock.py`, e não
    acrescenta dependência.
  - **A confirmação visual no QGIS 4.2 é do Diego e não bloqueia o
    fechamento do código** (mesma decisão de não-bloqueio do passo 58).

- **F9 — usabilidade dos painéis no QGIS 4.2 (passos 99-112, rodada
  2026-07-29, segunda revisão):**
  - Os três docks rolam: `grep -c "QScrollArea" logis/gui/urban_dock.py
    logis/gui/regional_dock.py logis/gui/waste_dock.py` > 0 nos três, e
    `test_dock_layout.py` (novo) prova isso estaticamente, sem QGIS.
  - O diálogo "Dependências" abre mostrando todo o texto: `QGroupBox`
    com regra QSS escopada (título com `subcontrol-origin: margin`),
    conteúdo dentro de `QScrollArea` e botão "Fechar" fixo no rodapé,
    fora da rolagem; tamanho inicial 620×560, mínimo 520×420.
  - `gui/waste_dock.py` tem **quatro abas** (Geração, Roteirização,
    Frota, Indicadores) montadas pelo helper `_new_tab`, cada uma com
    rolagem própria, e um único painel de resultados
    (`self.txt_results`) no rodapé, compartilhado, fora das abas.
  - **Os dez algorithms do módulo waste estão no dock** — `grep -c
    "logis:waste" logis/gui/waste_dock.py` cobre também
    `waste_districting` e `waste_deadhead_ratio`, hoje ausentes (o dock
    cobre 8 de 10; era lacuna dos passos 71/76, marcados `[x]` sem a
    seção existir).
  - Nenhum atributo de widget renomeado ou removido: `test_waste_dock.py`
    passa **sem edição** ao fim de cada um dos passos 104-107 (só os
    passos 108-110 o ampliam), e nenhum dos oito métodos `run_*`/
    `calculate_*` existentes muda.
  - `make test` → `sintaxe OK` e `python3 -m unittest discover -s . -p
    "test_*.py"` → OK ao fim de **cada** passo (base: 224 testes no
    início da rodada).
  - `i18n/logis_en.qm` regenerado com as strings novas; `test_i18n.py`
    continua passando.
  - `metadata.txt` em `version=0.1.2`; `README.md` registra o teste no
    QGIS 4.2 "Belém do Pará"/Ubuntu e a instalação bem-sucedida do
    OR-Tools por lá.
  - **Nada fora de `logis/gui/`, dos testes, do i18n, de `metadata.txt`
    e do `README.md`** — F9 não toca `core/`, `algorithms/` nem
    `provider.py`, e não acrescenta dependência.
  - **A confirmação visual no QGIS 4.2 é do Diego e não bloqueia o
    fechamento do código** (mesma decisão de não-bloqueio do passo 58).

- **F8 — QGIS 4 / Qt 6 (passos 89-98, rodada 2026-07-29):**
  - `python3 -m unittest discover -s . -p "test_*.py"` volta a **OK**
    (hoje está `FAILED (failures=1, errors=10)`) e continua OK ao fim de
    cada passo; `make test` continua `sintaxe OK`.
  - Os dois `AttributeError` relatados pelo Diego deixam de existir no
    fonte: nenhum `Qt.RightDockWidgetArea` nem `Qt.WindowMinMaxButtonsHint`
    solto em `logis/`.
  - `grep -rn "QVariant" logis/` só retorna `core/qgis_compat.py`;
    `field_type()` sobrevive à ausência dos membros de `QVariant::Type`
    (coberto por `test_qgis_compat.py` com o `QVariant` mockado ao estilo
    PyQt6, sem precisar de PyQt6 instalado).
  - `test_qt6_compat.py` passa e passa a ser o guarda da regra — sem ele
    a suíte (que roda em PyQt5) não consegue acusar regressão, porque as
    formas soltas continuam funcionando aqui.
  - `logis/core/ortools_installer.py` instala com as três travas da seção
    2.1 do CLAUDE.md (`pandas<3`, `numpy<2`,
    `typing_extensions==4.10.0`), com fallback para
    `--break-system-packages`; o comando `pip install ortools` puro,
    que sobrepõe o numpy do QGIS, não existe mais no código.
  - `metadata.txt` declara `supportsQt6=True` e `version=0.1.1`;
    `make deploy-qgis4`/`make deploy-flatpak-qgis4` instalam no perfil
    `QGIS4` (que é onde o plugin do Diego roda).
  - `CLAUDE.md` registra a regra do enum escopado, para o código futuro
    já nascer certo.
  - **Nenhuma dependência externa nova, nenhum módulo novo em `core/` ou
    `algorithms/`, nenhuma mudança de comportamento de algoritmo** — F8 é
    só compatibilidade (mais o bug do instalador).
  - **A confirmação no QGIS 4 é do Diego e não bloqueia o fechamento do
    código** (mesma decisão de não-bloqueio do passo 58): a suíte roda em
    PyQt5 e, por construção, não prova o runtime do PyQt6. O
    `docs/qgis4_compat_check.py` (passo 98) é o instrumento dessa
    confirmação; o que ele reportar sobre os itens marcados "provável" na
    tabela do Objetivo vira, se necessário, rodada seguinte.

- **F6 encerrado no código (2026-07-23):** roadmap formal (estimativa de
  geração, setorização, CPP/CARP, dimensionamento de frota) e seção 5.3
  inteira (deadhead ratio, equilíbrio entre setores, distância ao
  destino, cobertura por frequência) implementados, testados (194
  testes) e commitados; `git status` limpo, `provider.py` com 25
  algorithms. **A validação manual (passo 58) fica indefinidamente
  adiada a pedido do Diego e não é mais tratada como bloqueio de F7** —
  só a publicação final (passo 63) continua condicionada a ela.
- **Rodada do dock Waste (passos 69-81):** `gui/waste_dock.py` novo,
  mesmo padrão de `urban_dock.py`/`regional_dock.py` (dock com mocks
  para rodar fora do QGIS, `self.tr(...)` em toda string de UI,
  `processing.run` por seção), com `QScrollArea` e dez seções (uma por
  algorithm do módulo `waste`, ver "Decisões de arquitetura"); registrado
  em `logis_plugin.py` (`action_waste`, `dock_waste`, `show_waste_dock`,
  limpeza em `unload`); nenhuma mudança em `provider.py` ou nos
  algorithms; `make test` e a suíte de testes continuam passando.
- **Rodada i18n (passos 82-87):** `Makefile` ganha os alvos `i18n`/
  `transcompile`; só `i18n/logis_en.ts`/`.qm` são gerados (não
  `logis_pt_BR.*` — origem já é PT-BR, ver "Decisões de arquitetura —
  i18n"); todas as strings traduzidas para inglês; `test_i18n.py` novo
  confirma a tradução carregando `i18n/logis_en.qm` via `PyQt5`
  diretamente, sem depender de QGIS instalado; suíte completa (195
  testes esperados) e `make test` continuam passando.
- **Ícone (passo 88):** entregue pelo Diego em 2026-07-23 (conteúdo
  colado na conversa, registrado em "Decisões de arquitetura —
  Ícone"); passo pronto para o executor gravar `icon.svg` e atualizar
  `metadata.txt` (`icon=icon.svg`) na próxima rodada.
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
