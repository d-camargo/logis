# Algoritmos de Roteirização

Esta página documenta os **algoritmos de processamento** do grupo **Roteirização** (`logis:vrp_*`), projetados para a otimização de rotas de transporte de cargas e serviços pontuais (VRP/CVRP - *Vehicle Routing Problem*) sobre redes de transporte urbanas ou regionais.

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

## Sumário dos Algoritmos

1. [`logis:vrp_cvrp`](#1-roteirização-de-veículos-capacitados--cvrp-logisvrp_cvrp) — Roteirização de Veículos Capacitados (CVRP via Clarke-Wright + 2-opt/Or-opt)

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
| `OUTPUT_ROUTES` | Rotas geradas | `QgsProcessingParameterFeatureSink` | Camada vetorial de saída contendo as linhas das rotas geradas. | *Obrigatório* |
| `OUTPUT_STOPS` | Paradas por rota (opcional) | `QgsProcessingParameterFeatureSink` | Camada vetorial de saída contendo os pontos de parada ordenados. | `None` (Opcional) |

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
