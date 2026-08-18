# Schema SNV — Sistema Rodoviário Nacional

- **Título:** Schema Real da Camada WFS SNV/DNIT
- **Origem:** DNIT (Departamento Nacional de Infraestrutura de Transportes) / GeoServer INDE
- **Vintage:** `snv_202507a` (Julho/2025)
- **Data de Consulta:** 2025-07-23

---

Este documento apresenta o resultado da investigação do schema de atributos e geometria da camada WFS `DNIT:snv_202507a` (SNV - Sistema Rodoviário Nacional, vintage Julho/2025), consultada a partir do GeoServer da Infraestrutura Nacional de Dados Espaciais (INDE) em `https://geoservicos.inde.gov.br/geoserver/DNIT/ows`.

## Informações Gerais da Camada
- **Endpoint WFS**: `https://geoservicos.inde.gov.br/geoserver/DNIT/ows`
- **FeatureType**: `DNIT:snv_202507a`
- **SRS Padrão**: `EPSG:4674` (SIRGAS 2000 / Geográfico)
- **Tipo de Geometria**: `gml:MultiLineString` (campo `the_geom`)

## Propriedades (Campos) do Schema

Abaixo estão detalhados os campos retornados pela requisição `DescribeFeatureType` do WFS:

| Campo | Tipo XML | Tipo Local | Descrição / Observações |
| :--- | :--- | :--- | :--- |
| `ogc_fid` | `xsd:int` | `int` | Chave primária gerada pelo GeoServer / OGC. |
| `id_trecho_` | `xsd:int` | `int` | Identificador interno único do trecho no SNV. |
| `vl_br` | `xsd:string` | `string` | Número identificador da BR (ex: `"040"`, `"116"`, `"381"`). |
| `sg_uf` | `xsd:string` | `string` | Sigla da Unidade Federativa do trecho (ex: `"MG"`, `"SP"`). Útil para filtros estaduais. |
| `nm_tipo_tr` | `xsd:string` | `string` | Nome descritivo do tipo de trecho. |
| `sg_tipo_tr` | `xsd:string` | `string` | Sigla do tipo de trecho. |
| `desc_coinc` | `xsd:string` | `string` | Descrição de coincidência física de trechos de rodovias. |
| `vl_codigo` | `xsd:string` | `string` | Código SNV estruturado do trecho (ex: `"116BRMG0110"`). |
| `ds_local_i` | `xsd:string` | `string` | Descrição textual do local de início do trecho (ex: referências geográficas ou limites municipais). |
| `ds_local_f` | `xsd:string` | `string` | Descrição textual do local de término do trecho. |
| `vl_km_inic` | `xsd:number` | `number` | Quilometragem (Km) inicial do trecho na rodovia (ponto de controle). |
| `vl_km_fina` | `xsd:number` | `number` | Quilometragem (Km) final do trecho na rodovia. |
| `vl_extensa` | `xsd:number` | `number` | Extensão física do trecho em quilômetros. |
| `ds_sup_fed` | `xsd:string` | `string` | Descrição da Superintendência Regional do DNIT responsável. |
| `ds_obra` | `xsd:string` | `string` | Descritivo de obras associadas ao trecho. |
| `ul` | `xsd:string` | `string` | Código/Sigla da Unidade Local (UL) do DNIT. |
| `ds_coinc` | `xsd:string` | `string` | Descrição da coincidência. |
| `ds_tipo_ad` | `xsd:string` | `string` | Descrição do tipo de administração do trecho. |
| `ds_ato_leg` | `xsd:string` | `string` | Ato legislativo ou decreto de criação/incorporação do trecho. |
| `est_coinc` | `xsd:string` | `string` | Estado do trecho coincidente. |
| `sup_est_co` | `xsd:string` | `string` | Superintendência do estado coincidente. |
| `ds_jurisdi` | `xsd:string` | `string` | Entidade sob cuja jurisdição o trecho se encontra (ex: `"Federal"`, `"Estadual"`). |
| `ds_superfi` | `xsd:string` | `string` | Tipo de superfície física do trecho (ex: `"Pavimentada"`, `"Duplicada"`, `"Implantada"`, `"Terra"`). Essencial para calcular velocidade e custos no grafo de transporte regional. |
| `ds_legenda` | `xsd:string` | `string` | Descrição textual da legenda de exibição cartográfica. |
| `sg_legenda` | `xsd:string` | `string` | Sigla da legenda. |
| `leg_multim` | `xsd:string` | `string` | Código para legenda multimodal. |
| `versao_snv` | `xsd:string` | `string` | Versão/Vintage do SNV (ex: `"202507a"`). |
| `id_versao` | `xsd:int` | `int` | ID interno da versão cadastrada no DNIT. |
| `marcador` | `xsd:string` | `string` | Marcador especial do trecho (se houver). |
| `the_geom` | `gml:MultiLineString` | `MultiLineString` | Geometria espacial do segmento da rodovia. |

## Relevância para o Módulo de Logística Regional do Plugin `logis`

1. **Filtro de Pavimentação (`ds_superfi`)**:
   Os indicadores regionais descritos no roadmap (`CLAUDE.md` §5.2) exigem calcular o percentual da malha pavimentada ou duplicada. O campo `ds_superfi` será o classificador direto para esse cálculo.
   
2. **Atributo de Custo (Extensão `vl_extensa`)**:
   Em vez de recalcular o comprimento das polilinhas em ambiente métrico (o que exige reprojeção cara de todas as feições), a extensão em quilômetros está declarada de forma tabulada no campo `vl_extensa`. Este valor pode ser usado diretamente como o peso padrão de distância no grafo de roteamento, acelerando o tempo de construção do `QgsGraph`.

3. **Recorte Regional por UF (`sg_uf`)**:
   A camada é nacional e pesada. O campo `sg_uf` permite aplicar um filtro CQL eficiente diretamente no request WFS (`CQL_FILTER="sg_uf = 'MG'"`), baixando apenas as rodovias da UF de interesse, minimizando o tráfego de rede e consumo de memória.
