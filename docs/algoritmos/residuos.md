# Algoritmos de Coleta de Resíduos Sólidos

Esta página documenta os **10 algoritmos de processamento** do grupo **Logística Especializada — Coleta de Lixo** (`logis:waste_*`), destinados ao planejamento, setorização, roteirização por arcos, dimensionamento de frota e análise de indicadores operacionais de serviços de limpeza urbana e manejo de resíduos sólidos.

---

## Estrutura do Fluxo de Projeto

Os algoritmos do módulo especializado de coleta de resíduos estão organizados na sequência operacional completa do projeto:

1. **Geração de Resíduos** — Estimativa de volume/massa gerada por trecho de via a partir da demografia dos setores censitários.
2. **Setorização (*Districting*)** — Particionamento espacial em setores de coleta contíguos e equilibrados por carga.
3. **Roteirização por Arcos** — Otimização do percurso de varredura/coleta sobre os eixos viários (CPP para cobertura total, RPP para subconjuntos de vias e CARP para rotas capacitadas de veículos).
4. **Dimensionamento de Frota** — Alocação de viagens e definição da frota de veículos necessária via empacotamento em jornadas de trabalho (*First-Fit Decreasing*).
5. **Indicadores Operacionais** — Métricas de eficiência (razão de *deadhead*), equilíbrio de carga e tempo entre equipes, menor distância até aterros/estações de transbordo e taxa de cobertura do serviço.

---

## Sumário dos Algoritmos

### 1. Geração de Resíduos
1. [`logis:waste_generation_estimate`](#1-estimativa-de-geração-de-resíduos-sólidos-logiswaste_generation_estimate) — Estimativa de Geração de Resíduos Sólidos

### 2. Setorização
2. [`logis:waste_districting`](#2-setorização-de-coleta-de-resíduos--districting-logiswaste_districting) — Setorização de Coleta de Resíduos (*Districting*)

### 3. Roteirização por Arcos
3. [`logis:waste_cpp_route`](#3-roteirização-por-arcos--cpp-logiswaste_cpp_route) — Roteirização por Arcos (Chinese Postman Problem - CPP)
4. [`logis:waste_rpp_route`](#4-roteirização-por-arcos--rpp-logiswaste_rpp_route) — Roteirização por Arcos (Rural Postman Problem - RPP)
5. [`logis:waste_carp_route`](#5-roteirização-por-arcos-capacitada--carp-logiswaste_carp_route) — Roteirização por Arcos Capacitada (Capacitated Arc Routing Problem - CARP)

### 4. Dimensionamento de Frota
6. [`logis:waste_fleet_sizing`](#6-dimensionamento-de-frota-de-coleta-logiswaste_fleet_sizing) — Dimensionamento de Frota de Coleta

### 5. Indicadores Operacionais
7. [`logis:waste_deadhead_ratio`](#7-razão-de-deadhead-por-rota-logiswaste_deadhead_ratio) — Razão de Deadhead por Rota
8. [`logis:waste_sector_balance`](#8-equilíbrio-entre-setoresrotas-de-coleta-logiswaste_sector_balance) — Equilíbrio entre Setores/Rotas de Coleta
9. [`logis:waste_destination_distance`](#9-distância-ao-destino-de-resíduos-logiswaste_destination_distance) — Distância ao Destino de Resíduos
10. [`logis:waste_collection_coverage`](#10-cobertura-da-coleta-de-resíduos-por-setor-logiswaste_collection_coverage) — Cobertura da Coleta de Resíduos por Setor

---

## 1. Estimativa de Geração de Resíduos Sólidos (`logis:waste_generation_estimate`)

### O que calcula
Estima a geração diária de resíduos sólidos (em kg/dia) por trecho de via de coleta, a partir da população residente de cada setor de referência e do rateio proporcional ao comprimento das vias pertencentes àquele setor.

A geração total de resíduos no setor $G_s$ (em kg/dia) é calculada por:
$$G_s = P_s \cdot g \cdot c$$

Onde:
- $P_s$ é a população total residente no setor censitário ou de referência.
- $g$ é a taxa diária de geração per capita de resíduos em kg/hab/dia (`PER_CAPITA_KG_DAY`, padrão $0,9\text{ kg/hab/dia}$).
- $c$ é a fração de cobertura da coleta (`COVERAGE_FRACTION`, de $0,0$ a $1,0$).

A massa de resíduos gerada em cada trecho de via $i$ do setor $s$ ($g_i$) é alocada proporcionalmente ao seu comprimento físico $l_i$:
$$g_i = G_s \cdot \frac{l_i}{\sum_{j \in S_s} l_j}$$

> [!NOTE]
> A camada de vias de entrada deve conter um campo identificador do setor (`FIELD_STREET_SECTOR_ID`) associando previamente cada trecho ao seu respectivo setor.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_SECTORS` | Camada de setores (população) | `QgsProcessingParameterFeatureSource` (`TypeVectorPolygon`) | Polígonos de referência contendo a população (ex.: setores censitários IBGE). | *Obrigatório* |
| `FIELD_SECTOR_ID` | Campo de identificação do setor | `QgsProcessingParameterField` (`Any`) | Identificador único do setor na camada de polígonos. | *Obrigatório* |
| `FIELD_POPULATION` | Campo de população (habitantes) | `QgsProcessingParameterField` (`Numeric`) | Campo numérico com a população residente do setor. | *Obrigatório* |
| `INPUT_STREETS` | Camada de vias (com setor já associado) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Trechos de via contendo a geometria da malha de coleta. | *Obrigatório* |
| `FIELD_STREET_SECTOR_ID` | Campo de identificação do setor na camada de vias | `QgsProcessingParameterField` (`Any`) | Identificador do setor a que o trecho de via pertence. | *Obrigatório* |
| `PER_CAPITA_KG_DAY` | Geração per capita (kg/hab/dia) | `QgsProcessingParameterNumber` (`Double`) | Taxa diária de geração por habitante em kg. | `0.9` (min: `0.0001`) |
| `COVERAGE_FRACTION` | Fração de cobertura da coleta (0 a 1) | `QgsProcessingParameterNumber` (`Double`) | Proporção da população efetivamente atendida pelo serviço. | `1.0` (min: `0.0`, max: `1.0`) |
| `OUTPUT` | Vias com estimativa de geração de resíduos | `QgsProcessingParameterFeatureSink` | Camada de saída com trechos de via e nova coluna de geração. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Vias com estimativa de geração de resíduos | `QgsFeatureSink` (Linhas) | Camada de vias com os atributos originais acrescida do campo `waste_kg_day` (Real, kg/dia). |

### Referência Bibliográfica da Técnica
* Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). *Integrated Solid Waste Management: Engineering Principles and Management Issues*. McGraw-Hill.
* SNIS — Sistema Nacional de Informações sobre Saneamento (Faixa nacional média de $0,9$ a $1,0\text{ kg/hab/dia}$).
* Ghose, M. K., Dikshit, A. K., & Sharma, S. K. (2006). *A GIS based transportation model for solid waste disposal – A case study on Asansol municipality*. Waste Management, 26(11), 1287-1293.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(S + V)$, onde $S$ é a quantidade de setores e $V$ o número de trechos de via.
- **Complexidade de Espaço:** $\mathcal{O}(S + V)$ para o agrupamento em memória.
- **Escala Testada:** Execução instantânea para camadas de até 100.000 trechos de via.

---

## 2. Setorização de Coleta de Resíduos — *Districting* (`logis:waste_districting`)

### O que calcula
Particiona os trechos de via em $k$ setores de coleta contíguos e equilibrados em relação à carga total (massa de resíduos gerada em kg ou, na ausência do atributo, o comprimento acumulado dos trechos).

A heurística de setorização territorial opera em três etapas:
1. **Seleção de Sementes (*Farthest-First*):** Escolhe $k$ trechos de via iniciais como sementes dos setores utilizando a heurística de Gonzalez (1985), maximizando a menor distância topológica/espacial entre sementes.
2. **Crescimento de Regiões:** Expande os setores a partir das sementes sobre a estrutura do grafo de adjacência da malha.
3. **Rebalanceamento de Fronteiras:** Realiza um refinamento local através de trocas iterativas de trechos localizados na fronteira dos setores para minimizar a variância de carga mantendo rigorosamente a contiguidade territorial.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_STREETS` | Camada de vias | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Trechos de via a serem setorizados. | *Obrigatório* |
| `FIELD_LOAD` | Campo de carga (opcional) | `QgsProcessingParameterField` (`Numeric`) | Campo numérico com a carga do trecho (kg). Se omitido, usa o comprimento do trecho. | `None` (Opcional) |
| `NUM_SECTORS` | Número de setores de coleta desejado | `QgsProcessingParameterNumber` (`Integer`) | Quantidade desejada $k$ de setores de coleta ($k \ge 2$). | `2` (min: `2`) |
| `NODE_TOLERANCE` | Tolerância de nó em metros | `QgsProcessingParameterNumber` (`Double`) | Distância limite para considerar vértices como o mesmo nó no grafo (requer CRS métrico). | `0.01` (min: `0.0001`) |
| `MAX_ITERATIONS` | Máximo de iterações de rebalanceamento | `QgsProcessingParameterNumber` (`Integer`) | Limite de iterações para trocas de trechos de fronteira. | `50` (min: `1`) |
| `OUTPUT` | Vias com setor de coleta atribuído | `QgsProcessingParameterFeatureSink` | Camada de saída com o ID do setor atribuído. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Vias com setor de coleta atribuído | `QgsFeatureSink` (Linhas) | Camada de vias contendo os atributos originais mais o campo `collection_sector_id` (Inteiro, ID do setor de coleta). |

### Referência Bibliográfica da Técnica
* Gonzalez, T. F. (1985). *Clustering to minimize the maximum intercluster distance*. Theoretical Computer Science, 38, 293-306.
* Kalcsics, J., Nickel, S., & Schröder, M. (2005). *Towards a unified territorial design approach – Applications, algorithms and GIS integration*. Top, 13(1), 1-56.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(K \cdot E)$ para seleção de sementes + $\mathcal{O}(E \log E)$ para crescimento de regiões + $\mathcal{O}(I \cdot E)$ para o refinamento de fronteira, onde $E$ é o número de trechos, $K$ o número de setores e $I$ o limite de iterações.
- **Complexidade de Espaço:** $\mathcal{O}(E + V)$ para a estrutura de adjacência.
- **Escala Testada:** Testado com redes de até ~5.000 trechos de via.

---

## 3. Roteirização por Arcos — CPP (`logis:waste_cpp_route`)

### O que calcula
Determina o itinerário ótimo de coleta por arcos para varredura total em grafos não direcionados utilizando o **Problema do Carteiro Chinês** (*Chinese Postman Problem* - CPP). 

Garante que todas as vias da malha (ou de cada setor de coleta) sejam percorridas ao menos uma vez, minimizando a distância total de deslocamento improdutivo (*deadhead*):
1. **Identificação de Nós Ímpares:** Determina todos os nós da rede com grau topológico ímpar.
2. **Emparelhamento Mínimo:** Conecta os nós ímpares em pares através de caminhos mínimos de menor custo, duplicando os trechos necessários para tornar o grafo euleriano (onde todos os nós possuem grau par).
3. **Circuito Eulerianizado:** Constrói um circuito fechado euleriano contínuo utilizando o algoritmo de Hierholzer.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_STREETS` | Camada de vias | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Trechos de via a serem percorridos. | *Obrigatório* |
| `FIELD_COLLECTION_SECTOR` | Campo de setor de coleta (opcional) | `QgsProcessingParameterField` (`Any`) | Se informado, o CPP é resolvido separadamente por setor; se omitido, trata toda a camada como um setor único. | `None` (Opcional) |
| `NODE_TOLERANCE` | Tolerância de nó em metros | `QgsProcessingParameterNumber` (`Double`) | Distância em metros para agregação de nós da malha (requer CRS métrico). | `0.01` (min: `0.0001`) |
| `OUTPUT` | Vias com rota de coleta (CPP) | `QgsProcessingParameterFeatureSink` | Camada de saída com a sequência da rota e marcação de deadhead. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Vias com rota de coleta (CPP) | `QgsFeatureSink` (Linhas) | Camada de vias contendo feições duplicadas para passagens improdutivas e os campos: `route_visit_order` (Inteiro, ordem sequencial), `route_sector_id` (ID do setor) e `route_is_deadhead` (Booleano, `True` se for travessia duplicada/deadhead). |

### Referência Bibliográfica da Técnica
* Edmonds, J., & Johnson, E. L. (1973). *Matching, Euler tours and the Chinese postman*. Mathematical Programming, 5(1), 88-124.
* Hierholzer, C. (1873). *Über die Möglichkeit, einen Linienzug ohne Wiederholung und ohne Unterbrechung zu umfahren*. Mathematische Annalen, 6(1), 30-32.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(E \log V)$ para emparelhamento de nós ímpares + $\mathcal{O}(E)$ para construção do circuito de Hierholzer, onde $E$ é o número de trechos de via e $V$ o número de interseções.
- **Complexidade de Espaço:** $\mathcal{O}(E + V)$ para o multigrafo euleriano.
- **Escala Testada:** Testado com até ~5.000 trechos de via por setor.

---

## 4. Roteirização por Arcos — RPP (`logis:waste_rpp_route`)

### O que calcula
Resolve o **Problema do Carteiro Rural** (*Rural Postman Problem* - RPP) para calcular o itinerário de coleta quando apenas um **subconjunto específico de vias é de coleta obrigatória**, enquanto os demais trechos da malha podem ser utilizados livremente como conectores para deslocamento improdutivo (*deadhead*).

Etapas do algoritmo:
1. **Conexão de Componentes:** Identifica os componentes conectados formados pelos arcos obrigatórios e os interliga através de uma Árvore Geradora Mínima (MST) construída sobre caminhos mínimos na malha viária completa (Frederickson, 1979).
2. **Eulerianização:** Localiza os nós de grau ímpar no subgrafo estendido e aplica o emparelhamento perfeito de menor custo.
3. **Geração do Circuito:** Constrói o circuito euleriano sequencial contínuo (Hierholzer).

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_STREETS` | Camada de vias | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Malha viária completa contendo vias de coleta e vias de conexão. | *Obrigatório* |
| `FIELD_REQUIRED` | Campo de via obrigatória para coleta (opcional) | `QgsProcessingParameterField` (`Any`) | Campo booleano ou numérico (`1`/`True`) indicando coleta obrigatória no trecho. | `None` (Opcional, assume todas como obrigatórias) |
| `FIELD_COLLECTION_SECTOR` | Campo de setor de coleta (opcional) | `QgsProcessingParameterField` (`Any`) | Se informado, o RPP é resolvido separadamente por setor. | `None` (Opcional) |
| `NODE_TOLERANCE` | Tolerância de nó em metros | `QgsProcessingParameterNumber` (`Double`) | Distância em metros para união de vértices (requer CRS métrico). | `0.01` (min: `0.0001`) |
| `OUTPUT` | Vias com rota de coleta (RPP) | `QgsProcessingParameterFeatureSink` | Camada de saída com a rota RPP gerada. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Vias com rota de coleta (RPP) | `QgsFeatureSink` (Linhas) | Camada vetorial com os trechos percorridos e os campos: `route_visit_order` (Inteiro, ordem de visita), `route_sector_id` (ID do setor) e `route_is_connector` (Booleano, `True` se for trecho conector sem coleta). |

### Referência Bibliográfica da Técnica
* Frederickson, G. N. (1979). *Approximation algorithms for some postman problems*. Journal of the ACM, 26(3), 538-554.
* Edmonds, J., & Johnson, E. L. (1973). *Matching, Euler tours and the Chinese postman*. Mathematical Programming, 5(1), 88-124.
* Hierholzer, C. (1873). *Über die Möglichkeit, einen Linienzug ohne Wiederholung und ohne Unterbrechung zu umfahren*. Mathematische Annalen, 6(1), 30-32.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(C^2 \log V)$ para conexão de componentes via MST + $\mathcal{O}(K^2 \log V)$ para emparelhamento de nós ímpares + $\mathcal{O}(E)$ para a travessia euleriana, onde $C$ é o número de componentes obrigatórios, $K$ o número de nós ímpares e $V$ o total de cruzamentos.
- **Complexidade de Espaço:** $\mathcal{O}(E + V)$.
- **Escala Testada:** Testado com até ~5.000 trechos de via por setor.

---

## 5. Roteirização por Arcos Capacitada — CARP (`logis:waste_carp_route`)

### O que calcula
Resolve o **Problema de Roteirização por Arcos Capacitada** (*Capacitated Arc Routing Problem* - CARP), determinando rotas para uma frota de caminhões de lixo com limitação rígida de capacidade que partem e retornam a um depósito, garagem ou estação de transbordo.

Utiliza a heurística **Path-Scanning** (Golden et al., 1983):
1. **Snap do Depósito:** Associa a localização do depósito ao nó mais próximo do grafo viário.
2. **Construção de Viagens:** Inicializa uma nova rota no depósito. Seleciona iterativamente o próximo trecho obrigatório não atendido que minimiza a distância de deslocamento a partir do nó atual, respeitando a capacidade máxima do veículo:
   $$\sum_{i \in \text{rota}} q_i \le Q_{\text{veículo}}$$
3. **Retorno ao Depósito:** Quando nenhum trecho obrigatório adicional pode ser atendido sem estourar a capacidade $Q_{\text{veículo}}$, a rota fecha retornando ao depósito e uma nova viagem é iniciada.

> [!WARNING]
> Se um trecho obrigatório individual possuir demanda maior que a capacidade do veículo ($q_i > Q_{\text{veículo}}$), o algoritmo interrompe a execução e lança uma exceção explícita (sem suporte a *split-delivery*).

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_STREETS` | Camada de vias | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Trechos da malha viária. | *Obrigatório* |
| `FIELD_DEMAND` | Campo de geração/demanda de resíduos (kg) | `QgsProcessingParameterField` (`Numeric`) | Campo numérico com a geração de resíduos do trecho (em kg). | *Obrigatório* |
| `FIELD_REQUIRED` | Campo de via obrigatória para coleta (opcional) | `QgsProcessingParameterField` (`Any`) | Indica trechos com coleta obrigatória. | `None` (Opcional) |
| `FIELD_COLLECTION_SECTOR` | Campo de setor de coleta (opcional) | `QgsProcessingParameterField` (`Any`) | Resolve o CARP separadamente por setor. | `None` (Opcional) |
| `CAPACITY` | Capacidade do veículo | `QgsProcessingParameterNumber` (`Double`) | Capacidade máxima de carga por veículo ($Q_{\text{veículo}}$, em kg ou toneladas). | `10.0` (min: `0.0001`) |
| `INPUT_DEPOT` | Camada de ponto do depósito/aterro | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`) | Ponto único representando a garagem/aterro/transbordo. | *Obrigatório* (1 feição) |
| `NODE_TOLERANCE` | Tolerância de nó em metros | `QgsProcessingParameterNumber` (`Double`) | Tolerância para conexão de nós (requer CRS métrico). | `0.01` (min: `0.0001`) |
| `OUTPUT` | Vias com rota de coleta (CARP) | `QgsProcessingParameterFeatureSink` | Camada de saída com as rotas capacitadas. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Vias com rota de coleta (CARP) | `QgsFeatureSink` (Linhas) | Camada com atributos estendidos: `route_id` (ID da viagem/rota), `route_visit_order` (ordem na rota), `route_sector_id` (ID do setor), `route_is_deadhead` (Booleano, `True` para travessias improdutivas), `route_load_kg` (carga total transportada) e `route_distance_km` (extensão total da viagem em km). |

### Referência Bibliográfica da Técnica
* Golden, B. L., DeArmon, J. S., & Baker, E. K. (1983). *Computational experiments with algorithms for a class of routing problems*. Computers & Operations Research, 10(1), 47-59.
* Edmonds, J., & Johnson, E. L. (1973). *Matching, Euler tours and the Chinese postman*. Mathematical Programming, 5(1), 88-124.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(R^2 \cdot E \log V)$, onde $R$ é o número de trechos de via obrigatórios do setor, $E$ o total de vias e $V$ o número de nós.
- **Complexidade de Espaço:** $\mathcal{O}(E + V)$ para o grafo.
- **Escala Testada:** Testado com até ~500 trechos de via obrigatórios por setor.

---

## 6. Dimensionamento de Frota de Coleta (`logis:waste_fleet_sizing`)

### O que calcula
Estima a quantidade mínima de veículos de coleta necessários para cumprir todas as rotas/viagens de um setor durante a jornada de trabalho diária, aplicando a heurística **First-Fit Decreasing (FFD)** para o Problema de Empacotamento (*Bin Packing Problem*).

A duração total $T_r$ (em horas) de cada rota $r$ é dada por:
$$T_r = \frac{d_r}{v} + t_{\text{descarga}} + t_{\text{deslocamento}}$$

Onde:
- $d_r$ é a extensão total da rota (em km).
- $v$ é a velocidade média operacional de coleta (`AVG_SPEED`, em km/h).
- $t_{\text{descarga}}$ é o tempo fixo de descarga por viagem (`UNLOAD_TIME`, em horas).
- $t_{\text{deslocamento}}$ é o tempo fixo de viagem de ida e volta ao destino (`TRAVEL_TIME`, em horas).

Em seguida, as rotas são ordenadas por duração decrescente e alocadas aos veículos sequencialmente de forma que o tempo total acumulado em cada caminhão não exceda a jornada de trabalho $H$ (`SHIFT_DURATION`):
$$\sum_{r \in \text{veículo } k} T_r \le H$$

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_ROUTES` | Camada de rotas de coleta | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada de linhas contendo as rotas (ex.: saída do CARP). | *Obrigatório* |
| `FIELD_ROUTE_ID` | Campo de identificação da rota | `QgsProcessingParameterField` (`Any`) | Campo que agrupa os segmentos por viagem/rota (`route_id`). | *Obrigatório* |
| `FIELD_COLLECTION_SECTOR` | Campo de setor de coleta (opcional) | `QgsProcessingParameterField` (`Any`) | Se informado, dimensiona a frota separadamente por setor. | `None` (Opcional) |
| `AVG_SPEED` | Velocidade média de coleta (km/h) | `QgsProcessingParameterNumber` (`Double`) | Velocidade operacional média durante o recolhimento. | `10.0` (min: `0.0001`) |
| `SHIFT_DURATION` | Duração da jornada de trabalho diária (horas) | `QgsProcessingParameterNumber` (`Double`) | Tempo máximo de trabalho diário por veículo ($H$). | `8.0` (min: `0.0001`) |
| `UNLOAD_TIME` | Tempo fixo de descarga por rota (horas) | `QgsProcessingParameterNumber` (`Double`) | Tempo operacional no aterro/estação de transbordo. | `0.5` (min: `0.0`) |
| `TRAVEL_TIME` | Tempo fixo de deslocamento ao destino por rota (horas) | `QgsProcessingParameterNumber` (`Double`) | Tempo de viagem de ida/volta entre o setor e o destino. | `0.5` (min: `0.0`) |
| `OUTPUT` | Dimensionamento de frota por setor | `QgsProcessingParameterFeatureSink` | Tabela de saída com os resultados de frota por setor. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Dimensionamento de frota por setor | `QgsFeatureSink` (Sem Geometria) | Tabela contendo uma linha por setor com os campos: `sector_id`, `fleet_size` (nº de veículos estimados), `num_routes` (nº de rotas), `total_route_time_h` (tempo total de rota em horas) e `avg_utilization` (utilização média da frota, $0,0$ a $1,0$). |

### Referência Bibliográfica da Técnica
* Johnson, D. S. (1973). *Near-optimal bin packing algorithms* (Tese de Doutorado, Massachusetts Institute of Technology).

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(R \log R)$, onde $R$ é a quantidade de rotas de coleta (dominado pela ordenação FFD).
- **Complexidade de Espaço:** $\mathcal{O}(R)$ para armazenamento das viagens e veículos.
- **Escala Testada:** Testado para instâncias com centenas de rotas por setor.

---

## 7. Razão de Deadhead por Rota (`logis:waste_deadhead_ratio`)

### O que calcula
Mede a eficiência espacial do plano de roteirização calculando a extensão percorrida em modo **produtivo** ($d_{\text{prod}}$, vias onde há efetiva coleta de resíduos), a extensão **improdutiva** ($d_{\text{deadhead}}$, deslocamentos, conectores ou passagens repetidas) e a **Razão de Deadhead**:

$$\text{Deadhead Ratio} = \frac{d_{\text{deadhead}}}{d_{\text{prod}}}$$

Valores mais baixos indicam rotas mais eficientes; valores elevados indicam excesso de trajetos improdutivos de deslocamento.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_ROUTES` | Camada de rotas/vias de coleta | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada de linhas com os itinerários (saída de CPP, RPP ou CARP). | *Obrigatório* |
| `FIELD_DEADHEAD` | Campo indicador de deadhead/improdutivo | `QgsProcessingParameterField` (`Boolean`) | Campo booleano onde `True` indica segmento improdutivo. | `route_is_deadhead` |
| `FIELD_ROUTE_ID` | Campo de identificação da rota/setor (opcional) | `QgsProcessingParameterField` (`Any`) | Se informado, calcula a razão por rota/setor; se omitido, calcula para a camada toda. | `None` (Opcional) |
| `OUTPUT` | Razão de deadhead por rota | `QgsProcessingParameterFeatureSink` | Tabela de saída com os indicadores por rota e total. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Razão de deadhead por rota | `QgsFeatureSink` (Sem Geometria) | Tabela sem geometria com os campos: `route_id` (identificador da rota ou `Total`), `productive_km` (extensão produtiva em km), `deadhead_km` (extensão improdutiva em km) e `deadhead_ratio` (razão $d_{\text{deadhead}} / d_{\text{prod}}$). |

### Referência Bibliográfica da Técnica
* Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). *Integrated Solid Waste Management: Engineering Principles and Management Issues*. McGraw-Hill.
* Beltrami, E. J., & Bodin, L. D. (1974). *Networks and vehicle routing for municipal waste collection*. Networks, 4(1), 65-94.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(N)$, onde $N$ é o número de feições/trechos na camada de entrada.
- **Complexidade de Espaço:** $\mathcal{O}(N)$ para agregação em memória.
- **Escala Testada:** Processamento instantâneo para dezenas de milhares de trechos.

---

## 8. Equilíbrio entre Setores/Rotas de Coleta (`logis:waste_sector_balance`)

### O que calcula
Avalia o nível de equilíbrio (balanço operacional) de carga (em kg) e tempo total de serviço (em horas) entre as diversas rotas ou setores de coleta da cidade.

Para cada grupo de rotas, calcula estatísticas descritivas completas:
- **Carga:** Total ($\sum q$), Média ($\mu_q$), Desvio Padrão ($\sigma_q$), Mínimo, Máximo e Coeficiente de Variação ($CV_q = \sigma_q / \mu_q$).
- **Tempo:** Total ($\sum T$), Média ($\mu_T$), Desvio Padrão ($\sigma_T$), Mínimo, Máximo e Coeficiente de Variação ($CV_T = \sigma_T / \mu_T$).

> [!NOTE]
> Um coeficiente de variação de carga $CV_q > 0,20$ (20%) sinaliza desbalanço significativo entre as rotas, sugerindo a necessidade de rebalanceamento territorial.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_ROUTES` | Camada de rotas de coleta | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada de linhas com as rotas de coleta (ex.: saída do CARP). | *Obrigatório* |
| `FIELD_LOAD` | Campo de carga da rota (kg) | `QgsProcessingParameterField` (`Numeric`) | Campo com a carga da rota em kg. | `route_load_kg` |
| `FIELD_DISTANCE` | Campo de distância da rota em km (opcional) | `QgsProcessingParameterField` (`Numeric`) | Distância da rota em km (se omitido, usa a extensão geométrica). | `route_distance_km` |
| `FIELD_ROUTE_ID` | Campo de identificação da rota (opcional) | `QgsProcessingParameterField` (`Any`) | Identificador único de rota/viagem. | `route_id` |
| `FIELD_COLLECTION_SECTOR` | Campo de setor de coleta (opcional) | `QgsProcessingParameterField` (`Any`) | Identificador do setor de coleta. | `route_sector_id` |
| `AVG_SPEED` | Velocidade média de coleta (km/h) | `QgsProcessingParameterNumber` (`Double`) | Velocidade de operação. | `10.0` |
| `UNLOAD_TIME` | Tempo fixo de descarga por rota (horas) | `QgsProcessingParameterNumber` (`Double`) | Tempo gasto na descarga por rota. | `0.0` |
| `TRAVEL_TIME` | Tempo fixo de deslocamento ao destino por rota (horas) | `QgsProcessingParameterNumber` (`Double`) | Tempo de viagem até o destino por rota. | `0.0` |
| `OUTPUT` | Indicadores de equilíbrio entre rotas por setor | `QgsProcessingParameterFeatureSink` | Tabela de saída com estatísticas de equilíbrio. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Indicadores de equilíbrio entre rotas por setor | `QgsFeatureSink` (Sem Geometria) | Tabela contendo: `sector_id`, `num_routes`, `total_load_kg`, `mean_load_kg`, `std_dev_load_kg`, `min_load_kg`, `max_load_kg`, `cv_load`, `total_time_h`, `mean_time_h`, `std_dev_time_h`, `min_time_h`, `max_time_h` e `cv_time`. |

### Referência Bibliográfica da Técnica
* Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). *Integrated Solid Waste Management: Engineering Principles and Management Issues*. McGraw-Hill.
* Kim, B. I., Kim, S., & Sahoo, S. (2006). *Waste collection vehicle routing with time windows*. Computers & Operations Research, 33(12), 3624-3642.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(N)$, onde $N$ é a quantidade de feições na camada.
- **Complexidade de Espaço:** $\mathcal{O}(R)$, onde $R$ é o número de rotas agrupadas.
- **Escala Testada:** Testado para milhares de rotas em ambientes urbanos.

---

## 9. Distância ao Destino de Resíduos (`logis:waste_destination_distance`)

### O que calcula
Calcula a menor distância (em km) ou o menor tempo de viagem (em minutos) entre cada setor/origem de coleta e a instalação de destino de resíduos mais próxima (aterro sanitário, estação de transbordo ou ecoponto), utilizando caminhos mínimos sobre o grafo da rede viária (`QgsGraph`).

Fluxo de cálculo:
1. Reprojetar temporariamente destinos e origens para CRS projetado métrico Polyconic (EPSG:5880).
2. Construir o grafo viário unificado e determinar a matriz OD por Dijkstra multi-origem a partir das instalações de destino.
3. Determinar o custo mínimo até o destino mais próximo para cada setor $i$:
   $$c_i = \min_{j \in D} d_{ij}$$

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de rede viária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Malha viária para cálculo dos caminhos mínimos. | *Obrigatório* |
| `INPUT_DESTINATIONS` | Camada de destinos de resíduos (Pontos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`) | Localização dos aterros, transbordos ou ecopontos. | *Obrigatório* |
| `INPUT_SECTORS` | Camada de setores/origens de coleta | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`, `TypeVectorPolygon`) | Origens ou centroides dos setores de coleta. | *Obrigatório* |
| `CRITERION` | Critério de custo | `QgsProcessingParameterEnum` | Métrica a minimizar: `Distância` (0) ou `Tempo de viagem` (1). | `Distância` (0) |
| `OUTPUT` | Setores de coleta com distância ao destino | `QgsProcessingParameterFeatureSink` | Camada de setores com o custo ao destino. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Setores de coleta com distância ao destino | `QgsFeatureSink` (Pontos/Polígonos) | Cópia da camada de setores de origem com a nova coluna `dist_destino` (Real, menor distância em km ou tempo em min ao destino mais próximo). |

### Referência Bibliográfica da Técnica
* Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). *Integrated Solid Waste Management: Engineering Principles and Management Issues*. McGraw-Hill.
* Daskin, M. S. (1995). *Network and Discrete Location: Models, Algorithms, and Applications*. John Wiley & Sons.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(D \cdot (E + V \log V))$ para o Dijkstra multi-origem a partir dos $D$ destinos + $\mathcal{O}(D \cdot S)$ para busca do mínimo para os $S$ setores.
- **Complexidade de Espaço:** $\mathcal{O}(V + E)$ para o grafo + $\mathcal{O}(D \cdot S)$ para a matriz OD.
- **Escala Testada:** Testado para redes urbanas com até 50.000 arestas.

---

## 10. Cobertura da Coleta de Resíduos por Setor (`logis:waste_collection_coverage`)

### O que calcula
Calcula a extensão de vias com exigência de coleta ($L_{\text{exigida}}$), a extensão de vias efetivamente percorrida e atendida por rotas de coleta ($L_{\text{coberta}}$) e a **taxa de cobertura de coleta** por setor e no total acumulado:

$$\text{Taxa de Cobertura (\%)} = \frac{L_{\text{coberta}}}{L_{\text{exigida}}} \times 100$$

> [!NOTE]
> Trechos classificados como improdutivos (*deadhead*) nas rotas percorridas são desconsiderados do cálculo de $L_{\text{coberta}}$. Se a taxa de cobertura de um setor for inferior a 80,0%, o algoritmo gera um alerta explicativo no log de execução.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_REQUIRED_ROADS` | Camada de vias exigidas (faixa de frequência) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Malha de vias que exigem atendimento de coleta. | *Obrigatório* |
| `FIELD_REQUIRED_SECTOR` | Campo de setor da camada de vias exigidas | `QgsProcessingParameterField` (`Any`) | Identificador do setor nas vias exigidas. | `None` (Opcional) |
| `INPUT_COVERED_ROUTES` | Camada de rota coberta (vias percorridas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Malha com as rotas efetivamente percorridas. | *Obrigatório* |
| `FIELD_COVERED_DEADHEAD` | Campo indicador de deadhead/conector | `QgsProcessingParameterField` (`Boolean`) | Campo booleano onde `True` desconsidera o trecho por ser deadhead. | `route_is_deadhead` |
| `FIELD_COVERED_SECTOR` | Campo de setor da camada de rota coberta | `QgsProcessingParameterField` (`Any`) | Identificador do setor nas rotas cobertas. | `None` (Opcional) |
| `FREQUENCY_LABEL` | Rótulo de frequência de coleta | `QgsProcessingParameterString` | Rótulo de frequência do serviço (ex.: `"Diária"`, `"3x/semana"`). | `"Diária"` |
| `OUTPUT` | Tabela de cobertura por setor | `QgsProcessingParameterFeatureSink` | Tabela de saída com os indicadores de cobertura. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Tabela de cobertura por setor | `QgsFeatureSink` (Sem Geometria) | Tabela sem geometria contendo: `sector_id` (ID do setor ou `Total`), `frequency_label` (rótulo da frequência), `required_km` (extensão exigida em km), `covered_km` (extensão coberta em km) e `coverage_pct` (porcentagem de cobertura, de $0,0$ a $1,0$). |

### Referência Bibliográfica da Técnica
* Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). *The location of emergency service facilities*. Operations Research, 19(6), 1363-1373.
* Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). *Integrated Solid Waste Management: Engineering Principles and Management Issues*. McGraw-Hill.

### Limite de Complexidade e Escala
- **Complexidade de Tempo:** $\mathcal{O}(N)$, onde $N$ é o número total de trechos nas camadas de vias exigidas e rotas cobertas.
- **Complexidade de Espaço:** $\mathcal{O}(S)$, onde $S$ é o número de setores de coleta.
- **Escala Testada:** Testado para dezenas de milhares de trechos de via.
