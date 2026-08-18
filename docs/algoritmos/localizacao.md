# Algoritmos de Localização de Instalações (*Facility Location*)

Esta página documenta os **3 algoritmos de processamento** do grupo **Localização de Instalações** (`logis:facility_*`), projetados para resolver problemas estratégicos de alocação e localização de facilidades (como centros de distribuição, hubs logísticos, garagens, ecopontos, estações de transbordo e pontos de apoio) sobre redes de transporte urbanas ou regionais.

---

## Natureza Algorítmica: Heurísticas Nativas vs. Backend OR-Tools

Por diretriz arquitetural do plugin **logis**, todos os algoritmos do grupo de localização possuem implementações nativas em **Python puro sem dependências externas obrigatórias**. 

### 1. Heurísticas em Python Puro (Padrão Obligatório)
Os algoritmos utilizam heurísticas clássicas da literatura de Pesquisa Operacional e Logística:
- **p-Mediana:** Heurística construtiva gulosa seguida por busca local de troca (*1-interchange local search*) de Teitz-Bart.
- **Cobertura Máxima (MCLP):** Heurística gulosa de adição sucessiva (*Greedy Add*) de Church & ReVelle.
- **Cobertura de Conjuntos (LSCP):** Heurística gulosa de cobertura de conjuntos (*Greedy Set Cover*) de Toregas et al.

> [!NOTE]
> **Soluções Boas vs. Soluções Ótimas:** As heurísticas nativas garantem que o plugin funcione em qualquer ambiente Python/PyQGIS e entregam **soluções de alta qualidade (boas), mas não garantidamente ótimas**. Para a vasta maioria das aplicações de planejamento territorial, os resultados heurísticos são extremamente próximos do ótimo global e obtidos em tempos de computação extremamente reduzidos.

### 2. Backend Opcional de Otimização Exata (Google OR-Tools)
Quando o pacote opcional **Google OR-Tools** está instalado e ativo no ambiente Python do QGIS, os algoritmos podem delegar a resolução para os resolvedores matemáticos exatos de Programação Inteira Mista (MIP / MILP - *Mixed-Integer Linear Programming*):
- **Formulação Exata:** O problema é formulado matematicamente com variáveis de decisão binárias, função objetivo linear e restrições lineares de alocação e capacidade.
- **Ótimo Comprovado:** O solver (CBC ou SCIP via OR-Tools `MPSolver`) encontra a **solução exata/ótima comprovada** com limite de erro (*mip gap*) configurável.
- **Fallback Automático e Transparente:** A verificação da disponibilidade do OR-Tools é *lazy* e protegida. Se o OR-Tools não estiver instalado, falhar ou não conseguir resolver a instância, o `logis` executa um *fallback* automático imediato para a heurística pura em Python, garantindo que o usuário receba uma solução válida sem interrupção do fluxo de trabalho.

---

## Sumário dos Algoritmos

1. [`logis:facility_p_median`](#1-localização-p-mediana-logisfacility_p_median) — Localização p-Mediana (Teitz-Bart)
2. [`logis:facility_mclp`](#2-localização-de-cobertura-máxima--mclp-logisfacility_mclp) — Localização de Cobertura Máxima (MCLP)
3. [`logis:facility_lscp`](#3-localização-de-cobertura-de-conjuntos--lscp-logisfacility_lscp) — Localização de Cobertura de Conjuntos (LSCP)

---

## 1. Localização p-Mediana (`logis:facility_p_median`)

### O que calcula
Resolve o problema clássico da $p$-mediana, selecionando exatamente $p$ instalações entre um conjunto de candidatos disponíveis com o objetivo de **minimizar a soma total dos custos/distâncias ponderados da demanda até a instalação selecionada mais próxima**.

Matematicamente, minimiza a função objetivo:
$$Z = \sum_{i \in I} w_i \cdot \min_{j \in S} d_{ij}$$

Onde:
- $I$ é o conjunto de pontos de demanda.
- $w_i$ é o peso ou volume de demanda associado ao ponto $i$.
- $S \subset J$ é o conjunto de $p$ instalações selecionadas entre os candidatos $J$.
- $d_{ij}$ é a distância ou tempo de viagem entre a demanda $i$ e o candidato $j$ (calculado via rede viária por `QgsGraph`/Dijkstra ou via distância euclidiana direta).

### Natureza Algorítmica e Backend OR-Tools
- **Heurística Nátiva (Teitz-Bart):** Inicializa a solução com uma fase construtiva gulosa para escolher os $p$ candidatos iniciais. Em seguida, executa a busca local *1-interchange* de Teitz-Bart (1968), testando iterativamente a substituição de cada instalação selecionada por candidatos não selecionados. Se a troca reduzir o custo total ponderado $Z$, a mudança é aceita. O processo se repete até que nenhuma troca unitária melhore o custo ou até atingir o limite `MAX_ITER`.
- **Backend OR-Tools (Exato):** Formula o modelo de Programação Inteira Mista (MILP):
  $$\min \sum_{i \in I} \sum_{j \in J} w_i d_{ij} x_{ij} \quad \text{sujeito a} \quad \sum_{j \in J} x_{ij} = 1, \quad x_{ij} \le y_j, \quad \sum_{j \in J} y_j = p, \quad x_{ij}, y_j \in \{0, 1\}$$
  Solução obtida via `MPSolver` garantindo o ótimo global absoluto.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_DEMAND` | Camada de demanda (Pontos/Polígonos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial contendo a localização geográfica dos pontos ou polígonos de demanda. | *Obrigatório* |
| `FIELD_WEIGHT` | Campo de peso da demanda (opcional, default=1.0) | `QgsProcessingParameterField` (`Numeric`) | Atributo numérico da camada de demanda que especifica o peso/volume (ex.: população, domicílios, toneladas). | `None` (assume peso $1,0$) |
| `INPUT_CANDIDATES` | Camada de instalações candidatas (Pontos/Polígonos) (opcional) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial com os locais elegíveis para instalação. Se omitida, assume os próprios pontos de demanda como candidatos. | `None` (Opcional) |
| `INPUT_NETWORK` | Camada de rede viária (Linhas) (opcional) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Malha viária para cálculo de distâncias/tempos reais na rede via Dijkstra. Se omitida, utiliza distâncias euclidianas diretas. | `None` (Opcional) |
| `P_FACILITIES` | Número de instalações (p) | `QgsProcessingParameterNumber` (`Integer`) | Quantidade exata $p$ de instalações a serem selecionadas ($p \ge 1$). | `1` (min: `1`) |
| `MAX_ITER` | Número máximo de iterações do Teitz-Bart | `QgsProcessingParameterNumber` (`Integer`) | Limite máximo de iterações do refinamento por trocas locais no algoritmo Teitz-Bart. | `100` (min: `1`) |
| `OUTPUT_FACILITIES` | Instalações selecionadas | `QgsProcessingParameterFeatureSink` | Camada vetorial de saída com as $p$ instalações escolhidas. | *Obrigatório* |
| `OUTPUT_ASSIGNMENTS` | Atribuição de demandas | `QgsProcessingParameterFeatureSink` | Camada vetorial de saída de demanda com a identificação da instalação atribuída e o custo individual. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_FACILITIES` | Instalações selecionadas | `QgsFeatureSink` (Pontos/Polígonos) | Camada das instalações escolhidas contendo os atributos adicionais: `facility_id` (ID do candidato), `assigned_count` (nº de demandas atendidas), `assigned_demand_sum` (soma ponderada da demanda atendida) e `total_weighted_cost` (custo ponderado acumulado da instalação). |
| `OUTPUT_ASSIGNMENTS` | Atribuição de demandas | `QgsFeatureSink` (Pontos/Polígonos) | Camada de demanda contendo os atributos adicionais: `assigned_facility_id` (ID da instalação atribuída), `cost_to_facility` (distância/tempo até a instalação) e `weighted_cost` (custo ponderado do ponto $w_i \cdot d_{ij}$). |

### Referência Bibliográfica da Técnica
* Teitz, M. B., & Bart, P. (1968). *Heuristic methods for estimating the generalized vertex median of a weighted graph*. Operations Research, 16(5), 955-961.
* Daskin, M. S. (2013). *Network and discrete location: models, algorithms, and applications*. John Wiley & Sons.

### Limite de Complexidade e Escala
- **Complexidade de Tempo (Heurística Teitz-Bart):** $\mathcal{O}(p \cdot N \cdot M + \text{max\_iter} \cdot p \cdot (M - p) \cdot N)$, onde $N$ é o número de pontos de demanda e $M$ o número de candidatos.
- **Complexidade de Espaço:** $\mathcal{O}(N \cdot M)$ para armazenamento da matriz de distâncias OD.
- **Escala Testada:** Testado com sucesso para instâncias de até 1.000 pontos de demanda e 500 instalações candidatas.

---

## 2. Localização de Cobertura Máxima — MCLP (`logis:facility_mclp`)

### O que calcula
Resolve o problema de localização de cobertura máxima (*Maximal Covering Location Problem* - MCLP), selecionando **até $p$ instalações candidatas de modo a maximizar a demanda total atendida dentro de um limite máximo de distância ou tempo de viagem** (`MAX_DISTANCE`).

Matematicamente, maximiza a demanda coberta:
$$Z = \sum_{i \in I} w_i \cdot y_i$$

Onde:
- $y_i = 1$ se o ponto de demanda $i$ estiver a uma distância $\le S_{\text{max}}$ (`MAX_DISTANCE`) de pelo menos uma instalação selecionada $j \in S$; $y_i = 0$ caso contrário.
- $S \subset J$ com $|S| \le p$.

### Natureza Algorítmica e Backend OR-Tools
- **Heurística Nativa (Church & ReVelle Greedy Add):** Constrói a solução iterativamente adicionando, a cada passo, o candidato a instalação $j$ que proporciona o maior ganho marginal de demanda ponderada ainda não coberta. O processo se encerra ao atingir $p$ instalações ou quando todos os pontos de demanda estiverem cobertos.
- **Backend OR-Tools (Exato):** Formula o modelo de otimização de cobertura em Programação Inteira Binária:
  $$\max \sum_{i \in I} w_i y_i \quad \text{sujeito a} \quad y_i \le \sum_{j \in N_i} x_j, \quad \sum_{j \in J} x_j \le p, \quad x_j, y_i \in \{0, 1\}$$
  Onde $N_i = \{j \in J \mid d_{ij} \le S_{\text{max}}\}$.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_DEMAND` | Camada de demanda (Pontos/Polígonos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial representando a demanda espacial. | *Obrigatório* |
| `FIELD_WEIGHT` | Campo de peso da demanda (opcional, default=1.0) | `QgsProcessingParameterField` (`Numeric`) | Campo com os pesos de demanda (população, carga, etc.). | `None` (assume peso $1,0$) |
| `INPUT_CANDIDATES` | Camada de instalações candidatas (Pontos/Polígonos) (opcional) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Locais elegíveis para instalação. | `None` (assume a camada de demanda) |
| `INPUT_NETWORK` | Camada de rede viária (Linhas) (opcional) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Malha viária para cálculo de distâncias na rede. | `None` (distância euclidiana) |
| `P_FACILITIES` | Número máximo de instalações (p) | `QgsProcessingParameterNumber` (`Integer`) | Quantidade máxima $p$ de instalações a selecionar. | `1` (min: `1`) |
| `MAX_DISTANCE` | Distância/Tempo máximo de cobertura (max_distance) | `QgsProcessingParameterNumber` (`Double`) | Raio ou tempo limite $S_{\text{max}}$ para considerar a demanda coberta (em metros ou minutos). | `1000.0` (min: `0.0001`) |
| `OUTPUT_FACILITIES` | Instalações selecionadas | `QgsProcessingParameterFeatureSink` | Camada vetorial com as instalações escolhidas. | *Obrigatório* |
| `OUTPUT_ASSIGNMENTS` | Atribuição e cobertura de demandas | `QgsProcessingParameterFeatureSink` | Camada de demanda indicando o status de cobertura individual. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_FACILITIES` | Instalações selecionadas | `QgsFeatureSink` (Pontos/Polígonos) | Camada das instalações selecionadas contendo: `facility_id` (ID da instalação), `covered_count` (quantidade de pontos cobertos por esta instalação) e `covered_demand_sum` (soma do peso da demanda coberta). |
| `OUTPUT_ASSIGNMENTS` | Atribuição e cobertura de demandas | `QgsFeatureSink` (Pontos/Polígonos) | Camada de demanda contendo: `is_covered` ($1$ se coberto, $0$ se não coberto), `assigned_facility_id` (ID da instalação cobridora mais próxima), `cost_to_facility` (distância/tempo até a instalação) e `weighted_cost` (custo ponderado). |

### Referência Bibliográfica da Técnica
* Church, R., & ReVelle, C. (1974). *The maximal covering location problem*. Papers of the Regional Science Association, 32(1), 101-118.
* Daskin, M. S. (2013). *Network and discrete location: models, algorithms, and applications*. John Wiley & Sons.

### Limite de Complexidade e Escala
- **Complexidade de Tempo (Heurística Gulosa):** $\mathcal{O}(p \cdot M \cdot N)$, onde $N$ é o número de demandas e $M$ o de candidatos.
- **Complexidade de Espaço:** $\mathcal{O}(N \cdot M)$ para matriz de distâncias e tabela booleana de cobertura.
- **Escala Testada:** Testado com até 1.000 pontos de demanda e 500 candidatos.

---

## 3. Localização de Cobertura de Conjuntos — LSCP (`logis:facility_lscp`)

### O que calcula
Resolve o problema de localização de cobertura de conjuntos (*Location Set Covering Problem* - LSCP), determinando o **número mínimo absoluto de instalações necessárias para cobrir 100% dos pontos de demanda dentro de uma distância ou tempo máximo especificado** (`MAX_DISTANCE`).

Diferente do MCLP (onde o número de instalações $p$ é fixado pelo usuário), o LSCP trata $p$ como uma variável de decisão a ser minimizada:
$$\min Z = \sum_{j \in J} x_j$$

Sujeito à garantia de que toda demanda $i \in I$ esteja coberta:
$$\sum_{j \in N_i} x_j \ge 1, \quad \forall i \in I$$

Onde $N_i = \{j \in J \mid d_{ij} \le S_{\text{max}}\}$.

### Natureza Algorítmica e Backend OR-Tools
- **Heurística Nativa (Toregas Greedy Set Cover):** Utiliza um algoritmo guloso de cobertura de conjuntos. Em cada iteração, seleciona a instalação $j$ que cobre a maior quantidade acumulada de peso de demanda ainda não coberta. O processo continua recursivamente até que todas as demandas possíveis estejam atendidas ($100\%$ de cobertura) ou até que não restem candidatos que possam cobrir as demandas remanescentes.
- **Backend OR-Tools (Exato):** Resolve a Programação Inteira Binária original do Set Cover de Toregas et al. (1971) através do `MPSolver`, identificando a quantidade mínima global comprovada de instalações para cobertura total.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_DEMAND` | Camada de demanda (Pontos/Polígonos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Camada vetorial contendo os pontos de demanda. | *Obrigatório* |
| `FIELD_WEIGHT` | Campo de peso da demanda (opcional, default=1.0) | `QgsProcessingParameterField` (`Numeric`) | Campo de peso da demanda usado para priorização em empates. | `None` (assume peso $1,0$) |
| `INPUT_CANDIDATES` | Camada de instalações candidatas (Pontos/Polígonos) (opcional) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Instalações elegíveis para seleção. | `None` (assume a camada de demanda) |
| `INPUT_NETWORK` | Camada de rede viária (Linhas) (opcional) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Rede viária para medição de distâncias/tempos reais. | `None` (distância euclidiana) |
| `MAX_DISTANCE` | Distância/Tempo máximo de cobertura (max_distance) | `QgsProcessingParameterNumber` (`Double`) | Raio ou tempo limite $S_{\text{max}}$ exigido para cobertura. | `1000.0` (min: `0.0001`) |
| `OUTPUT_FACILITIES` | Instalações selecionadas | `QgsProcessingParameterFeatureSink` | Camada vetorial com a quantidade mínima de instalações selecionadas. | *Obrigatório* |
| `OUTPUT_ASSIGNMENTS` | Atribuição e cobertura de demandas | `QgsProcessingParameterFeatureSink` | Camada de demanda com a indicação de cobertura e alocação. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_FACILITIES` | Instalações selecionadas | `QgsFeatureSink` (Pontos/Polígonos) | Camada das instalações selecionadas com: `facility_id` (ID da instalação), `covered_count` (quantidade de demandas atendidas) e `covered_demand_sum` (soma da demanda coberta). |
| `OUTPUT_ASSIGNMENTS` | Atribuição e cobertura de demandas | `QgsFeatureSink` (Pontos/Polígonos) | Camada de demanda com: `is_covered` ($1$ se coberto, $0$ se isolado/não coberto), `assigned_facility_id` (ID da instalação cobridora), `cost_to_facility` (distância até a instalação) e `weighted_cost` (custo ponderado). |

### Referência Bibliográfica da Técnica
* Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). *The location of emergency service facilities*. Operations Research, 19(6), 1363-1373.
* Daskin, M. S. (2013). *Network and discrete location: models, algorithms, and applications*. John Wiley & Sons.

### Limite de Complexidade e Escala
- **Complexidade de Tempo (Heurística Set Cover):** $\mathcal{O}(M \cdot N \cdot \min(M, N))$, onde $N$ é a demanda e $M$ os candidatos.
- **Complexidade de Espaço:** $\mathcal{O}(N \cdot M)$.
- **Escala Testada:** Testado para instâncias com até 1.000 pontos de demanda e 500 candidatos.
