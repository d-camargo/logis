# Fontes de Dados

Esta página registra a procedência dos dados que o **logis** consome: o que o plugin
busca hoje, por qual protocolo e sob qual licença — e o que ainda está previsto, mas não
implementado.

A distinção importa na prática: só as fontes da primeira seção têm código que as lê. As
da última seção descrevem o rumo do módulo Regional e não podem ser chamadas ainda.

---

## 1. Fonte declarada em `core/sources.py`

O catálogo declarativo `logis/core/sources.py` (lista `SOURCES`) contém **uma** fonte
nesta versão. É o registro que o pipeline regional consulta para montar a requisição
WFS.

| ID | Órgão | Eixo | Protocolo | Licença | Vintage | Módulo |
|---|---|---|---|---|---|---|
| `dnit_snv` | DNIT — Departamento Nacional de Infraestrutura de Transportes | Transportes (rodovias federais) | WFS | Pública | `snv_202507a` (Jul/2025) | Regional |

**Detalhamento**

- **Endpoint:** `https://geoservicos.inde.gov.br/geoserver/DNIT/ows` (GeoServer da INDE)
- **FeatureType:** `DNIT:snv_202507a`
- **SRS:** `EPSG:4674` (SIRGAS 2000)
- **Como é consumida:** `core/network/snv_pipeline.py` → `build_snv_state_network(uf, gpkg)`,
  que aplica o filtro CQL `sg_uf = '<UF>'`, deriva os atributos de custo
  (`length`, `speed`, `travel_time`) a partir da superfície (`ds_superfi`) e grava
  `snv_links_<UF>` / `snv_nodes_<UF>` em GeoPackage.
- **Usada por:** `logis:regional_network_density`, `logis:regional_pavement_percentage`,
  `logis:regional_critical_links`.
- **Atributos:** a lista completa dos campos originais está em
  [Schema SNV](schema-snv.md).

---

## 2. Fontes consumidas diretamente pelo código

Estas fontes não passam por `SOURCES` — são acessadas por conectores e pipelines
específicos.

| Fonte | Órgão | Protocolo | Licença | Onde é lida | Módulo |
|---|---|---|---|---|---|
| Rede viária OSM | OpenStreetMap Foundation / comunidade | Overpass API (HTTP) | ODbL | `core/connectors/osm.py` → `fetch_overpass_json()` | Urbano, Coleta de Lixo |
| Malha municipal geobr | IPEA (`geobr`) | GeoPackage por download (ou `gisbr:read_municipality`) | Pública | `core/network/osm_pipeline.py`, `core/downloader.py` | Urbano, Coleta de Lixo |
| Setores censitários + censobr | IBGE (via plugin GisBR) | `processing.run()` no provider `gisbr` | Pública | `core/network/census_pipeline.py` | Urbano, Coleta de Lixo |

**Rede viária OSM.** O endpoint é `https://overpass-api.de/api/interpreter`, consultado
por *bounding box* com *User-Agent* próprio e repetição em caso de falha. O
`osm_pipeline` converte a resposta em camadas de links e nós, recorta pelo polígono do
município e deriva `length`, `speed` (por `highway=*`) e `travel_time`. O dado é
dinâmico: cada consulta traz o estado atual do mapeamento comunitário.

**Malha municipal geobr.** Serve para recortar a rede OSM pelo limite do município.
Quando o plugin [GisBR](https://github.com/d-camargo/gisbr) está instalado, o polígono
vem de `gisbr:read_municipality` — é o caminho preferencial. Sem GisBR, o
`osm_pipeline` baixa direto
`https://www.ipea.gov.br/geobr/data_gpkg/municipality/2020/<UF>municipality_2020_simplified.gpkg`,
com a cadeia de *mirrors* do `core/downloader.py` (releases `ipeaGIT/geobr` v1.7.0 no
GitHub) e cache em disco em `QStandardPaths.CacheLocation` → `.../logis/`.

**Setores censitários e censobr.** `fetch_census_tracts()` encadeia
`gisbr:read_census_tract` (geometria dos setores) e `gisbr:join_censo` (variáveis do
censobr, p. ex. população e domicílios). **Esta fonte exige o GisBR instalado**: sem ele
a função levanta `RuntimeError`, sem fallback próprio nesta versão. É a origem dos dados
de demanda usados por `logis:urban_demand_density`,
`logis:urban_gravity_accessibility` e pela estimativa de geração de resíduos.

---

## 3. Fontes previstas, ainda não implementadas

O escopo de dados do módulo Regional (§4 das regras do projeto) prevê as fontes abaixo.
Nenhuma delas está declarada em `SOURCES` nem tem conector no código desta versão — a
tabela existe para registrar o rumo, não para ser chamada.

| Fonte prevista | Órgão | Protocolo previsto | Para quê |
|---|---|---|---|
| Declaração de rede ferroviária | ANTT | WFS / download | Intermodalidade e distância ao terminal ferroviário |
| Hidrovias e instalações portuárias | ANTAQ | WFS / download | Acessibilidade a portos e terminais hidroviários |
| Aeroportos | ANAC / `geobr` | Download | Distância da sede municipal ao aeroporto mais próximo |
| População e PIB municipal | IBGE / SIDRA | API JSON (`urllib`) | Acessibilidade gravitacional a mercados, centro de gravidade da demanda |
| Malha rodoviária estadual (piloto MG, DER-MG) | IDE-Sisema / MG | WFS | Complemento estadual ao SNV |

O conector WFS genérico (`core/connectors/wfs.py`) já existe e é o ponto de entrada
natural para as fontes servidas por WFS quando elas forem acrescentadas a
`core/sources.py`.

---

## Convenções comuns

- **CRS de entrega:** todas as camadas saem em SIRGAS 2000 / `EPSG:4674`; a reprojeção
  para CRS métrico acontece apenas nos cálculos intermediários de distância e tempo.
- **Cache:** downloads e respostas de WFS/Overpass são guardados em
  `QStandardPaths.CacheLocation` → `.../logis/`. Os pipelines aceitam `force=True` para
  ignorar o cache e buscar de novo.
- **Licenças:** o uso do OSM exige atribuição nos termos da ODbL; as bases federais
  (DNIT, IBGE, IPEA) são de dados abertos, com atribuição ao órgão de origem.
