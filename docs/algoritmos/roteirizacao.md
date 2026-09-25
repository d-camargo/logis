# Algoritmos de Roteirização

Esta página documenta os **algoritmos de processamento** do grupo **Roteirização** (`logis:vrp_*`), projetados para a otimização de rotas de transporte de cargas e serviços pontuais sobre redes de transporte urbanas ou regionais — tanto a roteirização de uma frota com capacidade (VRP/CVRP - *Vehicle Routing Problem*) quanto o sequenciamento de visitas de um único veículo (TSP - *Traveling Salesman Problem*).

---

## Natureza Algorítmica: Heurísticas Nativas vs. Backend OR-Tools

Por diretriz arquitetural do plugin **logis**, todos os algoritmos do grupo de roteirização possuem implementações nativas em **Python puro sem dependências externas obrigatórias**.

### 1. Heurísticas em Python Puro (Padrão Obrigatório)
Os algoritmos utilizam heurísticas clássicas e consagráveis da literatura de Pesquisa Operacional e Logística:
- **Construção Inicial (Economias de Clarke & Wright):** Algoritmo de economias (*Savings Algorithm*) de Clarke & Wright (1964) para agrupamento e construção de rotas viáveis a partir de um depósito central, respeitando a capacidade máxima dos veículos.
- **Melhoria Intra-Rota (Busca Local 2-opt e Or-opt):** Combinação das heurísticas de busca local **2-opt** (Lin, 1965) para eliminação de cruzamentos por inversão de subsegmentos e **Or-opt** (Or, 1976) para realocação de blocos contíguos de 1, 2 e 3 paradas na mesma rota.

> [!NOTE]
> **Soluções Boas vs. Soluções Ótimas:** As heurísticas nativas garantem que o plugin funcione em qualquer ambiente Python/PyQGIS sem necessidade de compilação ou instalação de bibliotecas externas, entregando **soluções de alta qualidade (boas), mas não garantidamente ótimas**. Para problemas de porte médio ou planejamento operacional diário, os resultados heurísticos possuem excelente desempenho e velocidade computacional.

### 2. Backend Opcional de Otimização (Google OR-Tools)
Quando o pacote opcional **Google OR-Tools** está instalado e ativo no ambiente Python do QGIS, os algoritmos de roteirização podem delegar a resolução para os resolvedores de Programação por Restrições e Busca Local (*Constraint Programming / Routing*) do OR-Tools:
- **Estratégia Inicial:** Utiliza o construtor `PATH_CHEAPEST_ARC` para geração da rota inicial.
- **Metaheurística:** Aplica a metaheurística `GUIDED_LOCAL_SEARCH` com limite de tempo parametrizado (`_TIME_LIMIT_SECONDS = 10` segundos) para escapar de ótimos locais.
- **Fallback Automático e Transparente:** A seleção e verificação do backend é realizada via `pick_backend` (em `core.optim_backend`). Se o OR-Tools não estiver instalado, falhar ou não conseguir resolver a instância, o `logis` executa um **fallback automático e silencioso para a heurística pura em Python** (Clarke-Wright + 2-opt/Or-opt), garantindo que o usuário receba uma solução válida e sem interrupções.

---

## Execução em Segundo Plano: Progresso e Cancelamento

Os dois algoritmos reportam progresso e aceitam cancelamento pelo objeto `feedback` do
Processing — vale para o diálogo do algoritmo, para o console e para o painel **logis —
Roteirização**, que os despacha ao gerenciador de tarefas do QGIS (ver
[Guia de Roteirização §8](../guias/roteirizacao.md#8-execução-em-segundo-plano-e-destino-das-saídas)).

O progresso é repartido em **faixas por etapa** (`core.progress.PhaseProgress` remapeia o
progresso 0–100 de cada etapa para a sua faixa dentro do total), de modo que a barra
avança uma só vez, de 0 a 100, na ordem **grafo → matriz OD → solver → saídas**:

| Etapa | Com rede viária (`INPUT_NETWORK`) | Sem rede (euclidiana) |
|---|---|---|
| Leitura dos pontos de entrada | 0 – 8 | 0 – 8 |
| Construção do grafo (`QgsGraph`) | 8 – 35 | — |
| Matriz OD (Dijkstra multi-origem) | 35 – 70 | — |
| Matriz de distâncias euclidianas | — | 8 – 40 |
| Otimização (solver) | 70 – 90 | 40 – 85 |
| Gravação das saídas | 90 – 100 | 85 – 100 |

**Progresso e cancelamento valem para os dois backends**, com granularidade diferente:

- **Heurística Python pura** — a barra avança a cada rodada de busca local (2-opt/Or-opt)
  e o pedido de cancelamento é consultado entre as rodadas e entre as passadas de cada
  busca; a interrupção é imediata.
- **OR-Tools** — a barra avança pela fração do limite de tempo já consumida, e o
  cancelamento é consultado no retorno de **cada solução nova** do solver, quando o
  plugin manda encerrar a busca corrente. Numa fase nativa longa sem solução nova, o
  encerramento efetivo da thread pode esperar até o limite de 10 segundos
  (`_TIME_LIMIT_SECONDS`).

Cancelamento aceito interrompe a execução **antes de gravar qualquer saída**.

> [!NOTE]
> **CRS métrico obrigatório — por isso as distâncias são sempre em metros.** O cálculo
> nunca corre em coordenadas geográficas: havendo `INPUT_NETWORK`, os pontos e a malha são
> reprojetados para **EPSG:5880** (SIRGAS 2000 / Brazil Polyconic); sem rede, o CRS da
> camada de pontos só é mantido quando suas **unidades de mapa já são metros**, e nos
> demais casos o algoritmo também reprojeta para EPSG:5880. Se a transformação para
> EPSG:5880 falhar, o algoritmo adota como fallback o **UTM SIRGAS da zona** dos pontos
> (por exemplo, EPSG:31983 em São Paulo), com aviso no log; se o UTM também falhar, a
> execução para com erro e diagnóstico completo (SRC de origem/destino, ponto de prova
> antes/depois, versões do QGIS e do PROJ). Toda transformação é conferida com um
> **ponto de prova**, e o log registra, por transformação aceita, a linha "Transformação
> EPSG:xxxx → EPSG:yyyy ok (prova ...)" com o ponto antes/depois. Em consequência, todos
> os campos de distância das saídas (`leg_dist`, `cum_dist`, `tour_dist`, `route_dist`, …)
> e os totais do painel estão **em metros** — os cálculos correm em EPSG:5880 (ou UTM
> SIRGAS da zona), mas as camadas de saída do TSP e do CVRP são **sempre gravadas em
> EPSG:4674** (SIRGAS 2000).

---

## Sumário dos Algoritmos

1. [`logis:vrp_cvrp`](#1-roteirização-de-veículos-capacitados--cvrp-logisvrp_cvrp) — Roteirização de Veículos Capacitados (CVRP via Clarke-Wright + 2-opt/Or-opt)
2. [`logis:vrp_tsp`](#2-caixeiro-viajante--tsp-logisvrp_tsp) — Caixeiro Viajante (TSP via Vizinho Mais Próximo + 2-opt/Or-opt)

---

## 1. Roteirização de Veículos Capacitados — CVRP (`logis:vrp_cvrp`)

### O que calcula
Resolve o Problema de Roteirização de Veículos Capacitados (*Capacitated Vehicle Routing Problem* - CVRP), construindo um conjunto de rotas otimizadas que iniciam e terminam em um depósito central para atender a um conjunto de pontos de demanda (clientes), respeitando a capacidade máxima de carga de cada veículo.

Matematicamente, minimiza a distância total acumulada por todas as rotas do plano de transporte:
$$\min Z = \sum_{r \in R} c(r)$$

Sujeito às restrições:
1. Toda rota $r \in R$ inicia e termina no nó de depósito $D$.
2. Cada ponto de demanda $i \in I$ é atendido exatamente uma vez por uma única rota.
3. A carga total transportada em qualquer rota não excede a capacidade máxima do veículo $C$:
   $$\sum_{i \in r} q_i \le C, \quad \forall r \in R$$

Onde:
- $I = \{1, 2, \dots, N\}$ é o conjunto de clientes/demandas com peso ou volume $q_i > 0$.
- $D$ (nó 0) é a localização do depósito central.
- $c(r)$ é a distância total da rota $r$, calculada sobre a malha viária (`QgsGraph`/Dijkstra) ou via distância euclidiana direta.
- $C$ é a capacidade do veículo (`CAPACITY`).

### Natureza Algorítmica e Backend OR-Tools
- **Heurística Nativa (Clarke-Wright + 2-opt / Or-opt):**
  - *Fase 1 — Construção de Economias:* Inicializa $N$ rotas individuais $(0 \to i \to 0)$. Para cada par de clientes $(i, j)$, calcula a economia obtida ao conectar $i$ e $j$ diretamente: $s_{ij} = d(0, i) + d(0, j) - d(i, j)$. Ordena $s_{ij}$ de forma decrescente e une iterativamente as rotas que contêm $i$ e $j$ em suas extremidades, desde que a soma das cargas da rota fundida não ultrapasse a capacidade $C$.
  - *Fase 2 — Busca Local Intra-Rota:* Se `IMPROVE=True`, aplica iterativamente as buscas locais **2-opt** (testando a inversão do subsegmento $R[i:j+1]$) e **Or-opt** (testando a remoção e inserção de blocos contíguos de 1, 2 e 3 clientes em outras posições da mesma rota) até atingir a convergência (nenhuma troca reduz a distância total).
- **Backend OR-Tools (Constraint Programming):**
  - Formula a instância de CVRP no módulo de roteirização do OR-Tools (`pywrapcp.RoutingModel`).
  - Define restrições de dimensão de capacidade (`AddDimensionWithVehicleCapacity`) e função de custo baseada na matriz OD.
  - Utiliza a busca `PATH_CHEAPEST_ARC` para inicialização e `GUIDED_LOCAL_SEARCH` com limite de 10 segundos para otimização metaheurística.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_DEPOT` | Camada de depósito (Pontos/Polígonos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial contendo o ponto ou polígono do depósito de partida e chegada das rotas. | *Obrigatório* |
| `INPUT_DEMAND` | Camada de demanda / clientes (Pontos/Polígonos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial contendo os clientes/pontos de entrega a serem atendidos. | *Obrigatório* |
| `FIELD_DEMAND` | Campo de peso/demanda (opcional, default=1.0) | `QgsProcessingParameterField` (`Numeric`) | Campo numérico da camada de demanda que define o peso ou volume entregue em cada nó. Se omitido ou nulo, assume $1,0$. | `None` (Opcional, assume $1,0$) |
| `CAPACITY` | Capacidade do veículo | `QgsProcessingParameterNumber` (`Double`) | Capacidade máxima de carga transportada por veículo em uma rota ($C > 0$). | `100.0` (min: `0.0001`) |
| `INPUT_NETWORK` | Camada de rede viária (Linhas) (opcional) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Malha viária para cálculo de distâncias e rotas reais via Dijkstra (`QgsGraph`). Se omitida, utiliza distância euclidiana direta. | `None` (Opcional) |
| `IMPROVE` | Aplicar busca local (2-opt e Or-opt) | `QgsProcessingParameterBoolean` | Se verdadeiro, aplica os algoritmos de refinamento de busca local (2-opt e Or-opt) em cada rota gerada. | `True` |
| `BACKEND` | Backend de otimização | `QgsProcessingParameterEnum` | Solver que resolve a instância: `0` — *Automático (OR-Tools quando disponível)*, `1` — *Python puro (heurística)*, `2` — *OR-Tools*. Todas as opções passam por `pick_backend` e caem na heurística Python quando o OR-Tools não está disponível; só a opção `1` evita importar a biblioteca. | `0` (Automático) |
| `OUTPUT_ROUTES` | Rotas geradas | `QgsProcessingParameterFeatureSink` | Camada vetorial de saída contendo as linhas das rotas geradas. | *Obrigatório* |
| `OUTPUT_STOPS` | Paradas por rota (opcional) | `QgsProcessingParameterFeatureSink` | Camada vetorial de saída contendo os pontos de parada ordenados. | `None` (Opcional) |

> [!NOTE]
> **O backend é escolhido no parâmetro `BACKEND`.** No modo padrão (`0 — Automático`) o OR-Tools é usado quando o pacote está instalado, com fallback silencioso para a heurística Python. Escolher `1 — Python puro (heurística)` força a heurística nativa e impede qualquer import do OR-Tools — é o modo a usar quando o QGIS fecha sozinho durante o cálculo. O backend efetivamente usado sai no campo `backend` da camada de rotas.

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_ROUTES` | Rotas geradas | `QgsFeatureSink` (Linhas) | Camada de linhas com a geometria das rotas (depósito $\to$ clientes $\to$ depósito) e atributos: `route_id` (identificador da rota, $1 \dots R$), `stop_count` (quantidade de clientes atendidos na rota), `route_load` (carga total transportada) e `route_dist` (distância total da rota). |
| `OUTPUT_STOPS` | Paradas por rota | `QgsFeatureSink` (Pontos/Polígonos) | Camada vetorial de demanda com os atributos originais acrescidos de: `route_id` (identificador da rota atribuída), `stop_seq` (posição sequencial da parada na rota, $1 \dots k$) e `cum_load` (carga acumulada no veículo após realizar a parada). |

### Referência Bibliográfica da Técnica
* Clarke, G., & Wright, J. W. (1964). *Scheduling of vehicles from a central depot to a number of delivery points*. Operations Research, 12(4), 568-581.
* Lin, S. (1965). *Computer solutions of the traveling salesman problem*. Bell System Technical Journal, 44(10), 2245-2269.
* Or, I. (1976). *Traveling salesman-type combinatorial problems and their relation to the logistics of regional blood banking*. PhD thesis, Northwestern University.
* Perron, L., & Furnon, V. (2019). *OR-Tools*. Google. https://developers.google.com/optimization/routing/cvrp

### Limite de Complexidade e Escala
- **Complexidade de Tempo (Heurística Nativa):** $\mathcal{O}(N^2 \log N)$ para a construção de economias de Clarke-Wright + $\mathcal{O}(R \cdot k^2)$ para as iterações de busca local 2-opt e Or-opt, onde $N$ é o número de pontos de demanda, $R$ o número de rotas e $k$ a quantidade de paradas da maior rota.
- **Complexidade de Espaço:** $\mathcal{O}(N^2)$ para a matriz de distâncias OD e vetor de economias.
- **Escala Testada:** Testado com sucesso para instâncias de até 1.000 pontos de demanda.

---

## 2. Caixeiro Viajante — TSP (`logis:vrp_tsp`)

### O que calcula
Resolve o Problema do Caixeiro Viajante (*Traveling Salesman Problem* - TSP), determinando a **sequência de visita de menor distância total** de um único veículo que parte de um ponto inicial e atende cada ponto da camada de visita exatamente uma vez.

O contrato do algoritmo prevê **dois casos**, decididos exclusivamente pela presença da camada de ponto final (`INPUT_END`):

**Caso 1 — Tour fechado (sem ponto final).** Quando `INPUT_END` é omitida, o veículo retorna ao ponto de partida ao final do atendimento, e o problema minimiza o circuito hamiltoniano:
$$\min Z = \sum_{k=1}^{N} d(\pi_{k-1}, \pi_k) + d(\pi_N, s)$$

**Caso 2 — Caminho aberto (com ponto final).** Quando `INPUT_END` é fornecida, o veículo encerra a jornada em um destino distinto da origem (garagem, aterro, transbordo, CD de destino), e o problema minimiza o caminho hamiltoniano de extremos fixos:
$$\min Z = \sum_{k=1}^{N} d(\pi_{k-1}, \pi_k) + d(\pi_N, e)$$

Onde:
- $s$ (nó 0) é o ponto inicial e $e$ (nó $N+1$, quando existir) é o ponto final, ambos fixos.
- $V = \{1, 2, \dots, N\}$ é o conjunto de pontos a visitar e $(\pi_1, \dots, \pi_N)$ é uma permutação de $V$, com $\pi_0 = s$.
- $d(u, v)$ é a distância entre os nós $u$ e $v$, calculada sobre a malha viária (`QgsGraph`/Dijkstra, matriz OD) quando `INPUT_NETWORK` é fornecida, ou via distância euclidiana direta caso contrário.

Os cálculos são realizados em CRS métrico: o CRS da camada de entrada quando suas unidades de mapa já forem metros, ou EPSG:5880 (SIRGAS 2000 / Brazil Polyconic) quando houver rede viária ou quando o CRS da camada de pontos não estiver em metros — com fallback para o UTM SIRGAS da zona (por exemplo, EPSG:31983 em São Paulo) se a transformação para EPSG:5880 falhar, com aviso no log. As camadas de saída, por sua vez, são sempre gravadas em EPSG:4674 (SIRGAS 2000); os atributos de distância permanecem em metros.

### Janela de construção do grafo
Quando `INPUT_NETWORK` é fornecida, o algoritmo **não constrói o grafo da camada inteira**: ele delimita antes uma janela de análise e só carrega no `QgsGraph` as feições viárias que caem nela. A janela é o retângulo envolvente de **todos** os pontos do problema (inicial, a visitar e final, já no CRS métrico de cálculo), dilatado em uma margem de $\max(3.000\ \text{m},\ diag)$, onde $diag$ é a diagonal desse retângulo envolvente — ou seja, a vizinhança dos pontos, e não o território todo da camada.

O motivo é de custo: reprojetar e triangular uma malha estadual ou nacional inteira para resolver um TSP de poucos pontos gasta memória e tempo proporcionais ao tamanho da camada, e não ao do problema — em redes grandes, o suficiente para derrubar o QGIS. Com a janela, o custo acompanha a extensão da nuvem de pontos. A janela escolhida, a contagem de feições dentro dela e o tamanho do grafo resultante (vértices e arestas) são impressos no log de execução do algoritmo.

A consequência a conhecer: um caminho que só existiria **saindo da janela** não é encontrado. Se algum ponto não se amarrar à malha recortada, ou se um par de pontos ficar sem caminho entre si dentro dela, a execução **para com erro** (ver a nota abaixo) em vez de devolver uma sequência silenciosamente contaminada — o remédio é usar uma camada de rede que cubra a região dos pontos com folga.

> [!NOTE]
> **Rede desconectada vira erro, não custo enorme.** Quando `INPUT_NETWORK` é fornecida, a amarração dos pontos e a conectividade da malha são validadas **antes** da otimização: ponto que não encontra vértice no grafo interrompe a execução com *"Não foi possível amarrar um ou mais pontos à rede viária."*, e par de pontos sem caminho entre si na matriz OD (custo infinito ou acima de $10^{18}$) interrompe com *"A rede viária possui N par(es) de pontos sem caminho entre si."*. Antes, esses casos entravam na otimização como custo enorme e contaminavam a sequência em silêncio.

### Natureza Algorítmica e Backend OR-Tools
- **Heurística Nativa (Vizinho Mais Próximo + 2-opt / Or-opt):**
  - *Fase 1 — Construção pelo Vizinho Mais Próximo:* Partindo de $s$, o algoritmo de Flood (1956) escolhe repetidamente o ponto ainda não visitado de menor distância ao ponto corrente (com desempate determinístico pelo menor índice), até esgotar o conjunto $V$. No caso aberto, o ponto final $e$ é excluído do conjunto de candidatos e anexado ao fim da sequência, de modo que nunca seja escolhido no meio do percurso.
  - *Fase 2 — Busca Local com Extremos Fixos:* Se `IMPROVE=True`, aplica alternadamente **2-opt** (inversão do subsegmento $\pi[i:j+1]$) e **Or-opt** (realocação de blocos contíguos de 1, 2 e 3 pontos para outra posição da sequência), repetindo o ciclo até a convergência (nenhuma iteração reduz a distância total além da tolerância de $10^{-9}$). Em ambas as buscas o **ponto inicial permanece fixo** na primeira posição e, no caso aberto, o **ponto final permanece fixo** na última (`fixed_end=True`) — as trocas só reordenam os pontos intermediários, preservando o contrato dos dois casos.
- **Backend OR-Tools (parâmetro `BACKEND`, com fallback automático):**
  - O parâmetro `BACKEND` escolhe quem resolve a instância: `0 — Automático (OR-Tools quando disponível)` (padrão), `1 — Python puro (heurística)` ou `2 — OR-Tools`. Em qualquer dos casos a decisão final passa por `pick_backend` (em `core.optim_backend`), que faz **fallback silencioso** para a heurística pura em Python quando o OR-Tools não está instalado, está quebrado ou está sob a trava de segurança — nunca há erro nem pergunta ao usuário por causa do backend.
  - A opção `1 — Python puro (heurística)` é a única que **não importa o OR-Tools em momento algum**: é o modo seguro quando o carregamento da biblioteca derruba o processo do QGIS (ver [Guia de Roteirização §11](../guias/roteirizacao.md#11-quando-o-qgis-fecha-sozinho-ao-calcular-a-rota)). As opções `0` e `2` pedem o OR-Tools e aceitam o fallback; diferem apenas na intenção declarada.
  - Com OR-Tools, a instância é formulada como um `pywrapcp.RoutingModel` de **um único veículo**, com depósito de partida $s$ no caso fechado e par início/fim $(s, e)$ no caso aberto. Usa `PATH_CHEAPEST_ARC` na construção e, quando `IMPROVE=True`, `GUIDED_LOCAL_SEARCH` com limite de 10 segundos (`_TIME_LIMIT_SECONDS`).
  - O backend efetivamente utilizado é registrado no campo `backend` da camada de rota (`ortools` ou `python`) e também na aba de log da execução.

### Trechos (`acesso` / `rota` / `retorno`) e taxa improdutiva
A sequência resolvida é dividida em **pernas** (trechos entre dois nós consecutivos), cada uma classificada por papel (`leg_role`):

- **`acesso`** — a primeira perna, do ponto inicial até o primeiro ponto a visitar; deslocamento improdutivo (*deadhead*), pois nenhum atendimento ocorre nela.
- **`rota`** — as pernas intermediárias, entre pontos a visitar; é a distância produtiva de serviço.
- **`retorno`** — a última perna: do último ponto visitado de volta ao ponto inicial (caso fechado) ou até o ponto final (caso aberto); também improdutiva.

As somas por papel obedecem à identidade:
$$\texttt{tour\_dist} = \texttt{access\_dist} + \texttt{service\_dist} + \texttt{return\_dist}$$

E a taxa de deslocamento improdutivo é:
$$\texttt{dead\_ratio} = \frac{\texttt{access\_dist} + \texttt{return\_dist}}{\texttt{tour\_dist}}$$

Com guarda de divisão por zero: `dead_ratio = 0.0` quando `tour_dist = 0.0`. Quando há apenas um ponto a visitar, a sequência tem só duas pernas (`acesso` e `retorno`), portanto `service_dist = 0` e `dead_ratio = 1` — o percurso é integralmente improdutivo.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_START` | Camada do ponto inicial | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial do local de partida. Utiliza a **primeira feição válida** (centroide, se polígono). | *Obrigatório* |
| `INPUT_POINTS` | Camada de pontos a visitar | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial com os pontos/polígonos a serem visitados exatamente uma vez. | *Obrigatório* |
| `INPUT_END` | Camada do ponto final (opcional; vazia = a rota fecha no ponto inicial) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial do local de chegada (primeira feição válida). **Presente:** caminho aberto. **Omitida:** tour fechado no ponto inicial. | `None` (Opcional) |
| `INPUT_NETWORK` | Camada de rede viária (Linhas) (opcional) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Malha viária para cálculo de distâncias e geometrias reais via Dijkstra (`QgsGraph`). Se omitida, utiliza distância euclidiana direta. | `None` (Opcional) |
| `IMPROVE` | Aplicar busca local (2-opt e Or-opt) | `QgsProcessingParameterBoolean` | Se verdadeiro, refina a sequência inicial com 2-opt e Or-opt de extremos fixos (e ativa a metaheurística `GUIDED_LOCAL_SEARCH` no backend OR-Tools). | `True` |
| `BACKEND` | Backend de otimização | `QgsProcessingParameterEnum` | Solver que resolve a instância: `0` — *Automático (OR-Tools quando disponível)*, `1` — *Python puro (heurística)*, `2` — *OR-Tools*. Todas as opções passam por `pick_backend` e caem na heurística Python quando o OR-Tools não está disponível; só a opção `1` evita importar a biblioteca. | `0` (Automático) |
| `OUTPUT_ORDER` | Ordem de visita | `QgsProcessingParameterFeatureSink` | Camada de pontos de saída com a sequência de visita. | *Obrigatório* |
| `OUTPUT_ROUTE` | Rota (trechos) | `QgsProcessingParameterFeatureSink` | Camada de linhas de saída com as pernas da rota. | `None` (Opcional) |

> [!NOTE]
> **O backend é escolhido no parâmetro `BACKEND`.** No modo padrão (`0 — Automático`) o OR-Tools é usado quando o pacote está instalado, com fallback silencioso para a heurística Python. Escolher `1 — Python puro (heurística)` força a heurística nativa e impede qualquer import do OR-Tools — é o modo a usar quando o QGIS fecha sozinho durante o cálculo. O backend efetivamente usado sai no campo `backend` da camada de rota.

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_ORDER` | Ordem de visita | `QgsFeatureSink` (Pontos) | Uma feição por nó da sequência resolvida (ponto inicial, pontos visitados e, no caso aberto, ponto final), com os campos originais da camada de visita acrescidos dos campos de sequência. Nas feições de ponto inicial e final os campos originais vêm nulos. |
| `OUTPUT_ROUTE` | Rota (trechos) | `QgsFeatureSink` (Linhas) | Uma feição por perna do percurso, com a geometria do caminho na rede (Dijkstra) quando há `INPUT_NETWORK`, ou o segmento reto entre os dois nós caso contrário (também usado como *fallback* quando o caminho da perna não pôde ser reconstruído na malha; o campo `leg_geom` registra qual dos dois casos ocorreu em cada perna). |

**Campos de `OUTPUT_ORDER` (Ordem de visita):**

| Campo | Tipo | Significado |
|---|---|---|
| *(campos originais)* | — | Atributos da camada `INPUT_POINTS` da feição visitada; nulos nas feições de ponto inicial e de ponto final. |
| `visit_seq` | Inteiro | Posição do nó na sequência de visita, $1 \dots N+1$ (ou $N+2$ no caso aberto). **É por este campo que se lê a ordem de visita** (ver nota abaixo). |
| `node_role` | Texto | Papel do nó: `inicio` (ponto de partida, sempre `visit_seq = 1`), `parada` (ponto a visitar) ou `fim` (ponto final, apenas no caso aberto). |
| `leg_role` | Texto | Papel da perna **que chega** a este nó: `acesso`, `rota` ou `retorno`. Vazio na feição de `inicio`, que não é destino de nenhuma perna. |
| `leg_dist` | Duplo | Distância da perna que chega a este nó, na unidade do CRS métrico de cálculo. Vale $0,0$ na feição de `inicio`. |
| `cum_dist` | Duplo | Distância acumulada desde o ponto inicial até este nó (soma dos `leg_dist` anteriores, inclusive). |

**Campos de `OUTPUT_ROUTE` (Rota — trechos):**

| Campo | Tipo | Significado |
|---|---|---|
| `leg_seq` | Inteiro | Número de ordem da perna no percurso, $1 \dots L$. |
| `from_seq` | Inteiro | `visit_seq` do nó de origem da perna. |
| `to_seq` | Inteiro | `visit_seq` do nó de destino da perna. Na última perna de um **tour fechado** vale `1`, explicitando o retorno ao ponto inicial. |
| `leg_role` | Texto | Papel da perna: `acesso` (primeira), `rota` (intermediárias) ou `retorno` (última). |
| `leg_dist` | Duplo | Distância desta perna. |
| `cum_dist` | Duplo | Distância acumulada do início do percurso até o fim desta perna. |
| `stop_count` | Inteiro | Quantidade de pontos a visitar atendidos no percurso ($N$). Repetido em todas as feições. |
| `tour_dist` | Duplo | Distância total do percurso. Repetido em todas as feições. |
| `access_dist` | Duplo | Soma das pernas de `acesso` (improdutivas). Repetido em todas as feições. |
| `service_dist` | Duplo | Soma das pernas de `rota` (produtivas/serviço). Repetido em todas as feições. |
| `return_dist` | Duplo | Soma das pernas de `retorno` (improdutivas). Repetido em todas as feições. |
| `dead_ratio` | Duplo | Taxa improdutiva $(\texttt{access\_dist} + \texttt{return\_dist}) / \texttt{tour\_dist}$, entre $0$ e $1$. Repetido em todas as feições. |
| `closed` | Inteiro | `1` quando o percurso é um tour fechado (sem ponto final) e `0` quando é um caminho aberto. Repetido em todas as feições. |
| `backend` | Texto | Backend efetivamente utilizado na otimização: `ortools` ou `python`. Repetido em todas as feições. |
| `dist_mode` | Texto | Modo de cálculo da distância: `rede` quando `INPUT_NETWORK` foi fornecida (Dijkstra sobre `QgsGraph`) e `euclidiana` caso contrário. Repetido em todas as feições. |
| `leg_geom` | Texto | Origem da geometria **desta** perna: `rede`, quando o caminho foi reconstruído sobre a malha, ou `reta`, quando é o segmento reto entre os dois nós. |

> [!NOTE]
> **Como ler a ordem de visita:** a sequência do percurso **não** está na ordem de armazenamento das feições nem em rótulos de mapa — ela é lida na **tabela de atributos da camada `Ordem de visita`, ordenando pelo campo `visit_seq`** (clique no cabeçalho da coluna). O nó com `visit_seq = 1` é sempre o ponto inicial (`node_role = inicio`); os demais seguem na ordem de atendimento, e o último é o retorno ao ponto inicial (tour fechado) ou o ponto final (`node_role = fim`, caminho aberto).

### Referência Bibliográfica da Técnica
* Flood, M. M. (1956). *The traveling-salesman problem*. Operations Research, 4(1), 61-75.
* Lin, S. (1965). *Computer solutions of the traveling salesman problem*. Bell System Technical Journal, 44(10), 2245-2269.
* Or, I. (1976). *Traveling salesman-type combinatorial problems and their relation to the logistics of regional blood banking*. PhD thesis, Northwestern University.
* Perron, L., & Furnon, V. (2019). *OR-Tools*. Google. https://developers.google.com/optimization/routing/tsp

### Limite de Complexidade e Escala
- **Complexidade de Tempo (Heurística Nativa):** $\mathcal{O}(N^2)$ para a construção pelo Vizinho Mais Próximo + $\mathcal{O}(N^2)$ por iteração de busca local 2-opt/Or-opt, onde $N$ é o número de pontos a visitar.
- **Complexidade de Espaço:** $\mathcal{O}(N^2)$ para a matriz de distâncias OD.
- **Escala Testada:** Testado com sucesso para instâncias de até 1.000 pontos.
