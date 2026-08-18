# Algoritmos Regionais

Esta página documenta os **3 algoritmos de processamento** do grupo **Indicadores Regionais** (`logis:regional_*`), destinados ao diagnóstico da infraestrutura rodoviária e identificação de trechos críticos em escala estadual ou nacional.

Os algoritmos deste grupo dependem diretamente do pré-processamento da malha rodoviária oficial do **Sistema Nacional de Viação (SNV/DNIT)**, integrada via `core.network.snv_pipeline` (`dnit_snv`), ou de bases rodoviárias estaduais (ex.: DER-MG via IDE-Sisema).

---

## Sumário dos Algoritmos

1. [`logis:regional_network_density`](#1-densidade-da-malha-rodoviária-regional-logisregional_network_density) — Densidade da Malha Rodoviária Regional (km/1.000 km² e km/10.000 hab.)
2. [`logis:regional_pavement_percentage`](#2-percentual-de-pavimentação-e-duplicação-logisregional_pavement_percentage) — Percentual de Pavimentação e Duplicação (malha rodoviária)
3. [`logis:regional_critical_links`](#3-pontes-e-arcos-críticos-da-malha-regional-logisregional_critical_links) — Pontes e Arcos Críticos (Cut Links) da Malha Regional

---

## Dependência da Malha SNV / DNIT

Os algoritmos de indicadores regionais utilizam como infraestrutura primária a malha rodoviária tratada do **SNV / DNIT** (vintage `snv_202507a`), gerada pelo pipeline `core.network.snv_pipeline` (`snv_links_{uf}`).

Essa malha fornece os atributos estruturantes necessários para a execução dos algoritmos:
- **`length` (Real, metros):** Extensão física do segmento rodoviário em metros (calculada no pipeline a partir do campo oficial `vl_extensa` do DNIT).
- **`ds_superfi` (Texto):** Tipo de superfície física do trecho (ex.: `"Pavimentada"`, `"Duplicada"`, `"Implantada"`, `"Terra"`).
- **Grafo físico (`QgsGraph`):** Conectividade topológica construída por `core.network.graph_builder.build_graph()`.

---

## 1. Densidade da Malha Rodoviária Regional (`logis:regional_network_density`)

### O que calcula
Calcula a densidade da malha rodoviária regional sob duas perspectivas complementares:
1. **Densidade territorial ($\text{km}/1.000\text{ km}^2$):** Razão entre a extensão total das rodovias (em $\text{km}$) e a área do território de referência (em $1.000\text{ km}^2$).
   $$\text{Densidade por Área} = \frac{\text{Extensão Total (km)}}{\text{Área Total (km}^2\text{)}} \times 1.000$$
2. **Densidade demográfica ($\text{km}/10.000\text{ hab.}$):** Razão entre a extensão total das rodovias (em $\text{km}$) e a população residente do território (em $10.000\text{ hab.}$):
   $$\text{Densidade por População} = \frac{\text{Extensão Total (km)}}{\text{População (hab.)}} \times 10.000$$

A extensão total é obtida pela soma do campo `length` (em metros) de todos os trechos da malha rodoviária. A área do polígono de referência é calculada utilizando a elipsoide do CRS da camada (`QgsDistanceArea`).

### Dependência da Malha SNV / DNIT
Exige a camada de malha rodoviária pré-processada contendo obrigatoriamente a coluna `length` (em metros), fornecida pelas camadas `snv_links_{uf}` geradas pelo `core.network.snv_pipeline`.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de malha rodoviária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial de linhas representando os trechos rodoviários (ex.: `snv_links_MG`). | *Obrigatório* |
| `INPUT_AREA` | Camada de área de referência (UF, mesorregião, etc.) | `QgsProcessingParameterFeatureSource` (`TypeVectorPolygon`) | Camada vetorial de polígonos definindo o limite territorial de análise (ex.: UF ou mesorregião). | *Obrigatório* |
| `INPUT_POPULATION` | População da área de referência (hab.) | `QgsProcessingParameterNumber` (`Double`) | População total do território analisado (número de habitantes). | *Obrigatório* (min: $0,0000001$) |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_DENSITY_AREA` | Densidade rodoviária por área (km/1.000 km²) | `QgsProcessingOutputNumber` (Real) | Valor numérico da densidade territorial ($\text{km}/1.000\text{ km}^2$). |
| `OUTPUT_DENSITY_POP` | Densidade rodoviária por população (km/10.000 hab.) | `QgsProcessingOutputNumber` (Real) | Valor numérico da densidade demográfica ($\text{km}/10.000\text{ hab.}$). |

### Referência Bibliográfica da Técnica
* Handy, S. L., & Clifton, K. J. (2001). *Evaluating neighborhood accessibility: Possibilities and limitations*. Journal of Transportation and Statistics, 4(2/3), 67-78.

---

## 2. Percentual de Pavimentação e Duplicação (`logis:regional_pavement_percentage`)

### O que calcula
Calcula as proporções acumuladas da malha rodoviária regional que se encontram pavimentadas e que se encontram duplicadas:
- **Percentual de Pavimentação ($\%$):**
  $$\text{Percentual Pavimentada} = \frac{\text{Extensão Pavimentada (m)}}{\text{Extensão Total (m)}} \times 100$$
- **Percentual de Duplicação ($\%$):**
  $$\text{Percentual Duplicada} = \frac{\text{Extensão Duplicada (m)}}{\text{Extensão Total (m)}} \times 100$$

O algoritmo analisa o atributo de superfície física da rodovia (`FIELD_SURFACE`, padrão `ds_superfi`). Trechos cuja descrição contenha a palavra `"duplicada"` são computados tanto como pavimentados quanto como duplicados; trechos contendo `"pavimentada"` são computados como pavimentados.

### Dependência da Malha SNV / DNIT
Utiliza o campo `length` (extensão em metros) e o atributo de superfície física `ds_superfi` (originário da base oficial WFS `DNIT:snv_202507a`), pré-processados pelo `core.network.snv_pipeline`.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de malha rodoviária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial de linhas da malha rodoviária regional. | *Obrigatório* |
| `FIELD_SURFACE` | Campo que indica o tipo de superfície (ex: 'ds_superfi') | `QgsProcessingParameterField` (`Any`) | Atributo que especifica a superfície física do trecho. | `'ds_superfi'` (Opcional) |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_PCT_PAVED` | Percentual de vias pavimentadas (%) | `QgsProcessingOutputNumber` (Real) | Porcentagem acumulada da extensão de vias pavimentadas ($0,0\%$ a $100,0\%$). |
| `OUTPUT_PCT_DUP` | Percentual de vias duplicadas (%) | `QgsProcessingOutputNumber` (Real) | Porcentagem acumulada da extensão de vias duplicadas ($0,0\%$ a $100,0\%$). |

### Referência Bibliográfica da Técnica
* Confederação Nacional do Transporte. (2024). *Pesquisa CNT de Rodovias*. CNT, Brasília.

---

## 3. Pontes e Arcos Críticos da Malha Regional (`logis:regional_critical_links`)

### O que calcula
Identifica os **pontes/arcos críticos** (*cut links* ou *bridges*) da malha rodoviária regional — trechos rodoviários cuja interrupção ou remoção desconecta o grafo da rede, aumentando o número de componentes conexos.

A técnica permite identificar ligações intermunicipais ou pontes vulneráveis que não possuem rotas alternativas na malha rodoviária:
1. Constrói o `QgsGraph` a partir das feições de linha via `core.network.graph_builder.build_graph()`.
2. Deduplica os arcos direcionados do `QgsGraph` em arestas físicas únicas não ordenadas $(u, v)$.
3. Aplica a busca em profundidade (DFS) baseada no **Algoritmo de Tarjan** para encontrar todas as pontes do grafo em tempo linear $O(V + E)$.
4. Exporta uma camada vetorial de linhas contendo uma feição por aresta física única e a coluna booleana `is_critical_link`.

### Dependência da Malha SNV / DNIT
Funciona sobre o grafo construído a partir das camadas de rede regional (SNV/DNIT via `snv_pipeline` ou conectores estaduais como DER-MG/IDE-Sisema), identificando pontos únicos de falha na infraestrutura de transporte de carga.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_NETWORK` | Camada de malha rodoviária (Linhas) | `QgsProcessingParameterFeatureSource` (`TypeVectorLine`) | Camada vetorial de linhas representando a malha rodoviária regional. | *Obrigatório* |
| `OUTPUT` | Trechos com indicação de ponte/arco crítico | `QgsProcessingParameterFeatureSink` (Linhas) | Camada vetorial de saída para gravar os trechos físicos com o atributo booleano. | `[Criar camada temporária]` |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT` | Camada de Saída (Linhas) | `QgsProcessingOutputVectorLayer` | Camada de linhas com feições deduplicadas contendo o atributo:<br>• **`is_critical_link`** (`Boolean`): `True` se a aresta é uma ponte/arco crítico sem rota alternativa, `False` caso contrário. |
| `OUTPUT_NUM_CRITICAL_LINKS` | Número de pontes/arcos críticos identificados | `QgsProcessingOutputNumber` (Inteiro) | Quantidade total de pontes/arcos críticos mapeados na rede. |

### Referência Bibliográfica da Técnica
* Tarjan, R. E. (1974). *A note on finding the bridges of a graph*. Information Processing Letters, 2(6), 160-161.
