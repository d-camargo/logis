# Algoritmos de Dados (download de rede)

Esta página documenta os **2 algoritmos de processamento** do grupo **Dados**
(`logis:load_osm_network` e `logis:load_snv_network`), que baixam e pré-processam as
redes viárias que todos os demais grupos de algoritmos consomem: a rede urbana OSM
(indicadores urbanos, coleta de lixo) e a malha federal SNV/DNIT (indicadores
regionais).

São o caminho scriptável do painel **logis — Rede Viária**, que orquestra os mesmos
dois algoritmos por trás dos botões **Baixar arcos e nós (OSM)** e **Baixar arcos e nós
(SNV)**. Para o uso pelo painel, consulte o
[Guia da Rede Viária](../guias/rede_viaria.md); aqui o foco é a referência técnica de
parâmetros, saídas, cache e complexidade.

---

## Sumário dos Algoritmos

1. [`logis:load_osm_network`](#1-baixar-rede-viária-urbana-osm-município-logisload_osm_network) — Baixar Rede Viária Urbana (OSM, Município)
2. [`logis:load_snv_network`](#2-baixar-rede-viária-federal-snvdnit-uf-logisload_snv_network) — Baixar Rede Viária Federal (SNV/DNIT, UF)

---

## 1. Baixar Rede Viária Urbana (OSM, Município) (`logis:load_osm_network`)

### O que faz

Baixa e processa a rede viária urbana de um município brasileiro a partir dos dados do
OpenStreetMap, via Overpass API (`core.network.osm_pipeline.build_osm_municipal_network()`):

1. resolve o polígono do município (`gisbr:read_municipality` quando o GisBR está
   instalado; senão, download direto do GeoPackage municipal do geobr);
2. consulta a Overpass API pelo *bbox* do polígono resolvido;
3. monta a camada de trechos com os atributos de custo (`length`, `speed`,
   `travel_time`) a partir das tags OSM;
4. recorta a camada de trechos pelo polígono do município (`native:clip`);
5. deduplica os nós de extremidade dos trechos recortados.

Se o código IBGE não tiver exatamente 7 dígitos, o algoritmo falha antes de qualquer
requisição de rede com a mensagem *"Código IBGE do município deve possuir exatamente 7
dígitos."*. Se o polígono do município não puder ser resolvido, ou se a Overpass não
devolver nenhum trecho com tag `highway` dentro do *bbox*, o algoritmo lança
`QgsProcessingException` com a mensagem de erro do pipeline.

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_CODE_MUNI` | Código IBGE do município (7 dígitos) | `QgsProcessingParameterString` | Código IBGE numérico de 7 dígitos do município. Validado no início da execução. | *Obrigatório* |
| `INPUT_NOME_MUNI` | Nome do município (opcional) | `QgsProcessingParameterString` | Nome do município, repassado ao pipeline para auxiliar na identificação/log. | `""` (Opcional) |
| `FORCE` | Forçar novo download (ignorar cache) | `QgsProcessingParameterBoolean` | Se verdadeiro, ignora o cache local e faz nova requisição Overpass. | `False` |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_LINKS` | Arcos (rede viária) | `QgsProcessingParameterFeatureSink` (Linhas) | Trechos de vias recortados pelo polígono do município, com os campos `way_id`, `highway`, `name`, `oneway`, `length`, `speed`, `travel_time`. |
| `OUTPUT_NODES` | Nós (rede viária) | `QgsProcessingParameterFeatureSink` (Pontos) | Interseções e extremidades dos arcos, deduplicadas. |

### Cache

- GeoPackage persistente: `<cache>/osm_<código>.gpkg`, com as camadas
  `osm_links` e `osm_nodes`.
- Resposta bruta da Overpass: `<cache>/osm_overpass_<código>.json`.
- `<cache>` é `downloader.cache_dir()`, isto é, `QStandardPaths.CacheLocation` →
  `.../logis/`.
- Com `FORCE=False`, se o arquivo de cache da Overpass já existir, ele é reutilizado e
  nenhuma nova consulta é feita. Com `FORCE=True`, a consulta Overpass é refeita e o
  cache é sobrescrito.

### Limite de complexidade

Complexidade de Tempo: O(V + E) para construção e filtragem do grafo OSM.
Complexidade de Espaço: O(V + E) para armazenamento de nós (V) e arcos (E).
Testado com redes municipais de até 100.000 arcos e nós.

### Referência Bibliográfica da Técnica

* OpenStreetMap contributors (2024). *Planet dump* [Data file from Overpass API].
* Haklay, M., & Weber, P. (2008). *OpenStreetMap: User-generated street maps*. IEEE
  Pervasive Computing, 7(4), 12-18.

---

## 2. Baixar Rede Viária Federal (SNV/DNIT, UF) (`logis:load_snv_network`)

### O que faz

Baixa e processa a rede viária federal de uma UF a partir do SNV/DNIT
(`core.network.snv_pipeline.build_snv_state_network()`):

1. consulta o WFS da fonte declarativa `dnit_snv` (vintage `snv_202507a`, na INDE) com
   filtro CQL `sg_uf = '<UF>'`;
2. monta a camada de trechos com os atributos de custo (`length`, `speed`,
   `travel_time`), derivados da superfície física (`ds_superfi`);
3. extrai e deduplica os nós de extremidade dos trechos.

Se a sigla informada não constar em `logis/core/ufs.py`, o algoritmo falha antes de
qualquer requisição de rede com a mensagem *"UF inválida: \<UF\>"*. Se o WFS não
devolver dados válidos para a UF, o algoritmo lança `QgsProcessingException` com a
mensagem de erro do pipeline (por padrão, *"O SNV não devolveu dados para a UF
\<UF\>."*).

### Parâmetros de Entrada

| Identificador | Nome na UI | Tipo QGIS | Descrição | Valor Default |
|---|---|---|---|---|
| `INPUT_UF` | Sigla da UF (2 letras) | `QgsProcessingParameterString` | Sigla de 2 letras da UF (ex.: `MG`, `SP`, `RJ`), validada contra `logis/core/ufs.py`. | *Obrigatório* |
| `FORCE` | Forçar novo download (ignorar cache) | `QgsProcessingParameterBoolean` | Se verdadeiro, ignora o cache local (GeoPackage e GeoJSON) e faz nova requisição WFS. | `False` |

### Saídas e Resultados Gerados

| Identificador | Nome na UI | Tipo | Descrição |
|---|---|---|---|
| `OUTPUT_LINKS` | Arcos (rede viária) | `QgsProcessingParameterFeatureSink` (Linhas) | Trechos de rodovias federais/estaduais da UF, com os campos `id_trecho`, `vl_codigo`, `vl_br`, `sg_uf`, `ds_superfi`, `ds_jurisdi`, `oneway`, `length`, `speed`, `travel_time`. |
| `OUTPUT_NODES` | Nós (rede viária) | `QgsProcessingParameterFeatureSink` (Pontos) | Interseções e extremidades dos arcos, deduplicadas. |

### Cache

- GeoPackage persistente: `<cache>/snv_<UF>.gpkg`, com as camadas `snv_links_<UF>` e
  `snv_nodes_<UF>`.
- Resposta bruta do WFS: `<cache>/snv_<UF>.geojson`.
- `<cache>` é `downloader.cache_dir()`, isto é, `QStandardPaths.CacheLocation` →
  `.../logis/`.
- Com `FORCE=False`, se o GeoPackage já contiver as duas camadas, elas são devolvidas
  sem nova consulta ao WFS (`"cached": True` no metadado do pipeline). Sem o
  GeoPackage completo, o pipeline tenta o GeoJSON bruto em cache antes de consultar o
  WFS de novo. Com `FORCE=True`, ambos os caches são ignorados e a consulta WFS é
  refeita.

### Limite de complexidade

Complexidade de Tempo: O(N) onde N é o número de trechos de rodovias na UF.
Complexidade de Espaço: O(N) para armazenamento de links e nós.
Testado com malhas regionais de UFs de grande porte.

### Referência Bibliográfica da Técnica

* DNIT (Departamento Nacional de Infraestrutura de Transportes). (2025). *Sistema
  Rodoviário Nacional (SRN/SNV) - Especificações Técnicas*. Brasília: DNIT.

---

## Exemplos de Uso via Console Python (`processing.run`)

### Exemplo 1: Baixar a Rede Viária Urbana OSM de um Município

```python
import processing

resultado = processing.run("logis:load_osm_network", {
    'INPUT_CODE_MUNI': '3166600',
    'INPUT_NOME_MUNI': 'Serra da Saudade',
    'FORCE': False,
    'OUTPUT_LINKS': 'TEMPORARY_OUTPUT',
    'OUTPUT_NODES': 'TEMPORARY_OUTPUT'
})

camada_arcos = resultado['OUTPUT_LINKS']
```

### Exemplo 2: Baixar a Malha Rodoviária Federal SNV/DNIT de uma UF

```python
import processing

resultado = processing.run("logis:load_snv_network", {
    'INPUT_UF': 'MG',
    'FORCE': False,
    'OUTPUT_LINKS': 'TEMPORARY_OUTPUT',
    'OUTPUT_NODES': 'TEMPORARY_OUTPUT'
})

camada_arcos = resultado['OUTPUT_LINKS']
```

As camadas de saída são entregues em **EPSG:4674** (SIRGAS 2000), na mesma convenção de
CRS descrita em [Algoritmos de Processamento](index.md#convenção-de-crs-sistemas-de-referência-de-coordenadas).
