# Algoritmos Urbanos

Esta página documenta os **8 algoritmos de processamento** do grupo **Indicadores Urbanos** (`logis:urban_*`), destinados a análises de estrutura viária, acessibilidade, densidade de demanda, restrição de circulação e custos de entrega em escala municipal.

---

## Sumário dos Algoritmos

1. [`logis:urban_network_density`](#1-densidade-de-rede-viária-urbana-logisurban_network_density) — Densidade de Rede Viária Urbana (km/km²)
2. [`logis:urban_network_connectivity`](#2-conectividade-de-rede-viária-urbana-logisurban_network_connectivity) — Conectividade de Rede Viária Urbana (Índices $\alpha, \beta, \gamma$, $4+$ pernas e becos)
3. [`logis:urban_mean_circuity`](#3-circuidade-média-de-rede-viária-urbana-logisurban_mean_circuity) — Circuidade Média de Rede Viária Urbana
4. [`logis:urban_cargo_restriction`](#4-índice-de-restrição-de-circulação-de-carga-logisurban_cargo_restriction) — Índice de Restrição de Circulação de Carga
5. [`logis:urban_demand_density`](#5-densidade-de-demanda-urbana-logisurban_demand_density) — Densidade de Demanda Urbana por Setor Censitário
6. [`logis:urban_gravity_accessibility`](#6-acessibilidade-gravitacional-urbana-logisurban_gravity_accessibility) — Acessibilidade Gravitacional Urbana a POIs
7. [`logis:urban_edge_betweenness`](#7-centralidade-de-intermediação-de-arestas-logisurban_edge_betweenness) — Centralidade de Intermediação de Arestas (*Edge Betweenness*)
8. [`logis:urban_delivery_distance`](#8-distância-de-entrega-urbana-logisurban_delivery_distance) — Distância/Tempo de Entrega ao Depósito Mais Próximo

---

## 1. Densidade de Rede Viária Urbana (`logis:urban_network_density`)

### O que calcula
Calcula a densidade da rede viária em quilômetros de via por quilômetro quadrado de área de referência ($\text{km/km}^2$). O cálculo é realizado dividindo o comprimento total acumulado de todos os trechos de linha da rede viária ($\text{km}$) pela área geodésica do polígono de referência ($\text{km}^2$).

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de rede viária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial de linhas representando os eixos das vias urbanas. | *Obrigatório* |
| `INPUT_AREA` | Camada de área de referência (Polígonos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPolygon`) | Camada vetorial de polígonos definindo o limite territorial (ex.: município, bairro ou setor). | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Densidade da rede viária (km/km²) | `QgsProcessingOutputNumber` (Real) | Valor numérico contendo a densidade de rede calculada ($\text{km/km}^2$). |

### Referência Bibliográfica da Técnica
* Handy, S. L., & Clifton, K. J. (2001). *Evaluating neighborhood accessibility: Possibilities and limitations*. Journal of Transportation and Statistics, 4(2/3), 67-78.

---

## 2. Conectividade de Rede Viária Urbana (`logis:urban_network_connectivity`)

### O que calcula
Avalia a conectividade topológica e estrutural de uma rede viária urbana a partir dos conceitos clássicos da Teoria dos Grafos. A partir do cálculo dos graus de cada nó da malha (número de conexões físicas por vértice), determina:
- **Índice Alfa ($\alpha$):** Razão entre o número real de circuitos presentes e o número máximo de circuitos independentes possíveis ($0,0$ a $1,0$).
- **Índice Beta ($\beta$):** Razão entre o número de arestas e o número de nós ($e/v$), indicando a densidade de ligações.
- **Índice Gama ($\gamma$):** Razão entre o número de arestas presentes e o número máximo de arestas teoricamente possíveis ($0,0$ a $1,0$).
- **Percentual de interseções $4+$ pernas:** Proporção de nós com grau físico $\ge 4$ sobre o total de cruzamentos (grau $\ge 3$).
- **Percentual de becos sem saída:** Proporção de nós de terminação (grau $1$) sobre o total de nós da malha.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de rede viária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial de linhas representando a malha viária urbana. | *Obrigatório* |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `NUM_NODES` | Número de nós (v) | `QgsProcessingOutputNumber` (Inteiro) | Quantidade total de vértices/cruzamentos identificados na malha. |
| `NUM_EDGES` | Número de arestas (e) | `QgsProcessingOutputNumber` (Inteiro) | Quantidade total de segmentos/arestas únicos do grafo. |
| `ALPHA` | Índice Alfa | `QgsProcessingOutputNumber` (Real) | Valor do índice $\alpha$ ($0,0$ a $1,0$). |
| `BETA` | Índice Beta | `QgsProcessingOutputNumber` (Real) | Valor do índice $\beta$ (arestas por nó). |
| `GAMMA` | Índice Gama | `QgsProcessingOutputNumber` (Real) | Valor do índice $\gamma$ ($0,0$ a $1,0$). |
| `PCT_4_WAY` | Percentual de interseções com grau 4 ou mais | `QgsProcessingOutputNumber` (Real) | Porcentagem ($\%$) de cruzamentos com 4 ou mais conexões. |
| `PCT_DEAD_ENDS` | Percentual de becos sem saída | `QgsProcessingOutputNumber` (Real) | Porcentagem ($\%$) de nós de grau 1 (ruas sem saída). |

### Referência Bibliográfica da Técnica
* Rodrigue, J. P., Comtois, C., & Slack, B. (2013). *The geography of transport systems*. Routledge.

---

## 3. Circuidade Média de Rede Viária Urbana (`logis:urban_mean_circuity`)

### O que calcula
Estima o fator de circuidade médio da rede viária urbana, definido como a razão entre a distância real percorrida na malha (menor caminho via algoritmo de Dijkstra) e a distância euclidiana (em linha reta) entre pares de pontos origem-destino:
$$\text{Circuidade} = \frac{d_{\text{rede}}}{d_{\text{euclidiana}}}$$
O algoritmo sorteia aleatoriamente amostras de pares OD sobre os nós da rede que respeitem a distância euclidiana mínima configurada.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de rede viária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial de linhas da rede viária. | *Obrigatório* |
| `NUM_SAMPLES` | Número de amostras (pares OD) | `QgsProcessingParameterNumber` (`Integer`) | Quantidade de pares origem-destino a serem amostrados via Dijkstra. | `1000` (min: `1`) |
| `MIN_DISTANCE` | Distância euclidiana mínima (metros) | `QgsProcessingParameterNumber` (`Double`) | Distância em linha reta mínima exigida entre a origem e o destino. | `100.0` (min: `0.0`) |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Circuidade média | `QgsProcessingOutputNumber` (Real) | Valor médio adimensionado ($\ge 1,0$). Valores próximos de $1,0$ indicam malhas ortogonais/eficientes; valores mais altos indicam desvios severos. |

### Referência Bibliográfica da Técnica
* Giacomin, C., & Levinson, D. (2015). *Road network circuity in metro areas*. Environment and Planning B: Planning and Design, 42(6), 1040-1053.

---

## 4. Índice de Restrição de Circulação de Carga (`logis:urban_cargo_restriction`)

### O que calcula
Calcula o índice de acessibilidade e restrição de circulação para veículos de carga no ambiente urbano. O indicador expressa a porcentagem da extensão total da rede viária que permanece livre de impedimentos de tráfego pesado:
$$\text{Índice} = \frac{\text{Comprimento Livre (m)}}{\text{Comprimento Total (m)}} \times 100$$
Se a expressão de restrição não for customizada pelo usuário, o algoritmo aplica automaticamente regras padrão com base nas etiquetas do OSM (`highway` $\in$ `pedestrian`, `footway`, `path`, `steps`, `cycleway`, `bridleway`, `corridor`), bem como restrições físicas de largura (`width < 3.0m`) e peso bruto total (`maxweight < 3.5t`), quando tais atributos existirem na camada.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de rede viária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial contendo os trechos de vias urbanas. | *Obrigatório* |
| `RESTRICTION_EXPRESSION` | Expressão de restrição | `QgsProcessingParameterExpression` | Expressão QGIS customizada que avalia como `VERDADEIRO` para trechos com restrição de carga. Se omitida, utiliza a expressão default por tipo de via, largura e peso. | `''` (Vazio) |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Índice de restrição de circulação (%) | `QgsProcessingOutputNumber` (Real) | Percentual ($0,0\%$ a $100,0\%$) de vias liberadas para veículos de carga na malha. |

### Referência Bibliográfica da Técnica
* Dablanc, L. (2007). *Goods transport in large European cities: Difficult to organize, difficult to modernize*. Transportation Research Part A: Policy and Practice, 41(3), 280-290.

---

## 5. Densidade de Demanda Urbana (`logis:urban_demand_density`)

### O que calcula
Calcula a densidade espacial de demanda (população, domicílios ou postos de trabalho por $\text{km}^2$) para cada setor censitário de um município brasileiro. O algoritmo obtém a malha oficial de setores censitários (via integração com `gisbr:read_census_tract` / `gisbr:join_censo`) e computa a razão entre a variável quantitativa de demanda e a área geodésica do setor em $\text{km}^2$.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_CODE_MUNI` | Código IBGE do município (7 dígitos) | `QgsProcessingParameterString` | Código numérico oficial do município no IBGE (ex.: `3106200` para Belo Horizonte). | *Obrigatório* |
| `FIELD_POPULATION` | Campo de população | `QgsProcessingParameterString` | Nome da coluna contendo a contagem de população/domicílios na camada do censobr. | *Obrigatório* |
| `OUTPUT` | Setores censitários com densidade de demanda | `QgsProcessingParameterFeatureSink` (Polígonos) | Camada de saída para gravar os polígonos dos setores com a nova coluna. | `[Criar camada temporária]` |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Camada de Saída (Polígonos) | `QgsProcessingOutputVectorLayer` | Cópia dos setores censitários do município acrescida do atributo:<br>• **`dens_demanda_hab_km2`** (`Double`): Densidade de demanda por setor ($\text{hab/km}^2$). |

### Referência Bibliográfica da Técnica
* Bertaud, A. (2004). *The spatial organization of cities: Deliberate outcome or unforeseen consequence?* Institute of Urban and Regional Development, UC Berkeley.

---

## 6. Acessibilidade Gravitacional Urbana (`logis:urban_gravity_accessibility`)

### O que calcula
Calcula o índice de acessibilidade gravitacional (Modelo de Hansen) de cada ponto de origem (ex.: centroides de setores censitários ou pontos de demanda) até um conjunto de pontos de destino (POIs, instalações comerciais, equipamentos urbanos), ponderados por sua atratividade/peso:
$$A_i = \sum_{j=1}^{D} \frac{W_j}{d_{ij}^\beta}$$
onde:
- $W_j$ é o peso/atratividade do destino $j$.
- $d_{ij}$ é a distância de caminho mínimo na rede viária entre a origem $i$ e o destino $j$ (calculada via Dijkstra multi-origem sobre `QgsGraph` com suporte a cache em disco).
- $\beta$ é o fator de decaimento por distância.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de rede viária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial de linhas da rede viária urbana. | *Obrigatório* |
| `INPUT_ORIGINS` | Camada de origem (pontos/centroides) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`) | Camada de pontos representando os locais de origem da demanda. | *Obrigatório* |
| `INPUT_DESTINATIONS` | Camada de destinos (POIs) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`) | Camada de pontos representando os destinos / equipamentos de interesse. | *Obrigatório* |
| `FIELD_WEIGHT` | Campo de peso/atratividade do destino | `QgsProcessingParameterField` (Numérico) | Campo numérico da camada de destinos especificando o peso/atratividade $W_j$. Se omitido, atribui $1,0$ a todos os destinos. | `None` (Opcional) |
| `BETA` | Parâmetro de decaimento por distância (beta) | `QgsProcessingParameterNumber` (`Double`) | Expoente de impedância por distância ($\beta$). | `2.0` (min: `0.0001`) |
| `OUTPUT` | Origem com acessibilidade gravitacional | `QgsProcessingParameterFeatureSink` (Pontos) | Camada de destino para salvar os pontos de origem com a nova métrica. | `[Criar camada temporária]` |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Camada de Saída (Pontos) | `QgsProcessingOutputVectorLayer` | Cópia da camada de pontos de origem acrescida do atributo:<br>• **`acess_gravit`** (`Double`): Escore acumulado de acessibilidade gravitacional da origem. |

### Referência Bibliográfica da Técnica
* Hansen, W. G. (1959). *How accessibility shapes land use*. Journal of the American Institute of Planners, 25(2), 73-76.

---

## 7. Centralidade de Intermediação de Arestas (`logis:urban_edge_betweenness`)

### O que calcula
Estima a centralidade de intermediação (*edge betweenness centrality*) das arestas da rede viária urbana através de amostragem estocástica de pares origem-destino (OD). A centralidade de intermediação mede a frequência com que um segmento de via é atravessado pelos caminhos mínimos que conectam diferentes pares de pontos na cidade:
$$C_B(e) = \sum_{s \neq t} \frac{\sigma_{st}(e)}{\sigma_{st}}$$
Para viabilizar a execução em malhas urbanas de grande porte em Python puro, o algoritmo amostra $S$ pares OD aleatórios, calcula as árvores de menores caminhos e atribui a cada aresta o número de travessias normalizado no intervalo $[0,0; 1,0]$.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de rede viária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada de linhas da rede viária urbana. | *Obrigatório* |
| `NUM_SAMPLES` | Número de amostras (pares OD) | `QgsProcessingParameterNumber` (`Integer`) | Quantidade de pares OD sorteados para amostragem do algoritmo. | `1000` (min: `1`) |
| `SEED` | Semente aleatória | `QgsProcessingParameterNumber` (`Integer`) | Semente do gerador aleatório para reprodução exata dos resultados. | `None` (Opcional) |
| `OUTPUT` | Arestas com centralidade de intermediação | `QgsProcessingParameterFeatureSink` (Linhas) | Camada de saída para gravação das arestas do grafo com o escore. | `[Criar camada temporária]` |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Camada de Saída (Linhas) | `QgsProcessingOutputVectorLayer` | Camada de linhas contendo uma feição por aresta do grafo e o atributo:<br>• **`betweenness`** (`Double`): Escore de centralidade de intermediação normalizado ($0,0$ a $1,0$). |

### Referência Bibliográfica da Técnica
* Freeman, L. C. (1977). *A set of measures of centrality based on betweenness*. Sociometry, 40(1), 35-41.
* Brandes, U., & Pich, C. (2007). *Centrality estimation in large networks*. International Journal of Bifurcation and Chaos, 17(7), 2303-2318.

---

## 8. Distância de Entrega Urbana (`logis:urban_delivery_distance`)

### O que calcula
Calcula o custo mínimo (em distância física ou em tempo de viagem) de atendimento para cada zona de demanda/entrega (pontos ou centroides de setores) até o centro de distribuição ou depósito candidato mais próximo na malha viária urbana:
$$\text{Custo}_i = \min_{d \in \text{Depósitos}} \{ \text{CustoCaminho}(d, i) \}$$
O cálculo utiliza a matriz OD pré-calculada por Dijkstra multi-origem (com cache em disco em `QStandardPaths.CacheLocation`) a partir das localizações dos depósitos amarradas ao grafo viário.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de rede viária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial de linhas da rede viária urbana. | *Obrigatório* |
| `INPUT_DEPOTS` | Camada de depósitos candidatos (Pontos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`) | Camada de pontos representando os depósitos ou centros de distribuição. | *Obrigatório* |
| `INPUT_ZONES` | Camada de zonas/centroides (Pontos) | `QgsProcessingParameterFeatureSource` (`TypeVectorPoint`) | Camada de pontos representando as zonas de demanda de entrega. | *Obrigatório* |
| `CRITERION` | Critério de custo | `QgsProcessingParameterEnum` | Critério para avaliação dos custos de caminho mínimo na rede:<br>• `0`: **Distância** (metros)<br>• `1`: **Tempo de viagem** (segundos/minutos) | `0` (Distância) |
| `OUTPUT` | Zonas com custo de entrega | `QgsProcessingParameterFeatureSink` (Pontos) | Camada de saída com as zonas calculadas. | `[Criar camada temporária]` |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Camada de Saída (Pontos) | `QgsProcessingOutputVectorLayer` | Cópia das feições da camada de zonas acrescida do atributo:<br>• **`dist_entrega`** (`Double`): Menor distância ($\text{m}$) ou tempo de viagem ($\text{s/min}$) até o depósito candidato mais próximo. |

### Referência Bibliográfica da Técnica
* Daskin, M. S. (1995). *Network and Discrete Location: Models, Algorithms, and Applications*. John Wiley & Sons.
