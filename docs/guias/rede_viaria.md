# Guia da Rede Viária (baixar dados)

Este guia percorre o painel **logis — Rede Viária**: o único painel do plugin que
**baixa** dados. Os painéis Urbano, Regional e Coleta de Lixo apenas **consomem**
camadas de rede já carregadas no projeto — quem as traz para dentro do QGIS é este
painel.

Os dois botões de download são orquestradores: cada um chama um algoritmo do
Processing (`logis:load_osm_network` para a aba Município, `logis:load_snv_network`
para a aba Estado) e escreve o retorno na área de resultados. A referência técnica de
cada algoritmo (parâmetros, cache, complexidade, bibliografia) está em
[Dados (download de rede)](../algoritmos/dados.md); aqui o foco é o uso do painel.

---

## 1. Abrir o painel

**Complementos → logis → Rede Viária**. O painel abre ancorado à direita da janela do
QGIS; se for fechado, reabra pela mesma entrada de menu (ou por **Ver → Painéis**). O
conteúdo fica dentro de uma área rolável, como os demais painéis do plugin.

---

## 2. O que vale para as duas abas

Logo abaixo do título, o próprio painel avisa: *"O painel baixa arcos e nós direto para
o projeto. O QGIS pode ficar sem resposta durante o download."* Isso descreve um
comportamento real, não um bug:

- A execução do download é **síncrona**. Enquanto ela roda, o cursor vira ampulheta e
  os três botões (**Listar municípios da UF**, **Baixar arcos e nós (OSM)**, **Baixar
  arcos e nós (SNV)**) ficam desabilitados.
- A janela do QGIS pode parecer travada até o download terminar — **é esperado, não
  feche o QGIS**. Municípios grandes e UFs extensas podem levar minutos.
- A área **Resultados**, no rodapé, é somente leitura, em fonte monoespaçada. Ela
  **acumula** as linhas de cada execução — nunca é limpa automaticamente — e mostra
  erros em vermelho, com a mensagem do algoritmo.
- O checkbox **Forçar novo download (ignorar cache)** existe nas duas abas e repete a
  consulta remota ignorando o que já estiver em cache local.

---

## 3. Aba Município (OSM)

1. Escolha a **UF** na lista.
2. Clique em **Listar municípios da UF**. Isso baixa a malha municipal do geobr (IBGE
   2020) e preenche a lista **Município** com `Nome (código)`, ordenada por nome. A
   primeira chamada para uma UF baixa o GeoPackage da malha municipal; as chamadas
   seguintes, para a mesma UF, vêm do cache.
3. Escolha o município na lista. O campo **Código IBGE (7 dígitos)** é preenchido
   sozinho a partir da seleção. Se você já souber o código, pode digitá-lo direto nesse
   campo — a listagem por UF é só uma conveniência, não um pré-requisito.
4. Marque **Forçar novo download (ignorar cache)** se quiser refazer a consulta
   Overpass em vez de reaproveitar o cache local.
5. Clique em **Baixar arcos e nós (OSM)**.

Por baixo, o algoritmo `logis:load_osm_network` (via
`core.network.osm_pipeline.build_osm_municipal_network()`):

- resolve o polígono do município — usando `gisbr:read_municipality` quando o plugin
  GisBR está instalado, ou baixando o GeoPackage do geobr diretamente quando não está;
- consulta a Overpass API pelo *bbox* do polígono;
- recorta o resultado pelo polígono do município;
- deduplica os nós de extremidade dos trechos recortados.

O resultado são duas camadas adicionadas ao projeto: **Arcos OSM — \<município\>** (arcos)
e **Nós OSM — \<município\>** (nós), onde \<município\> é o nome escolhido na lista — ou o
código IBGE digitado, quando o download foi feito sem passar pela listagem. Ambas entram
como camadas **temporárias** — salve-as em disco antes de fechar o projeto, se quiser
mantê-las.

A camada de arcos já vem com os campos de custo que os demais algoritmos usam:

| Campo | Conteúdo |
|---|---|
| `way_id` | Identificador do *way* no OSM |
| `highway` | Classe da via (`residential`, `primary`, `footway`, …) |
| `name` | Nome da via, quando existir no OSM |
| `oneway` | Sentido de circulação (`yes`, `no`, `-1`) |
| `length` | Comprimento do trecho, em **metros** |
| `speed` | Velocidade estimada pela classe `highway`, em km/h |
| `travel_time` | Tempo de percurso do trecho, em **segundos** (`length` ÷ `speed`) |

É essa camada de arcos que os painéis **Urbano** e **Coleta de Lixo** consomem.

---

## 4. Aba Estado (SNV/DNIT)

1. Escolha a **UF**.
2. Marque **Forçar novo download (ignorar cache)**, se necessário.
3. Clique em **Baixar arcos e nós (SNV)**.

Por baixo, o algoritmo `logis:load_snv_network` (via
`core.network.snv_pipeline.build_snv_state_network()`) consulta o WFS do DNIT (vintage
`snv_202507a`, servido na INDE) com filtro CQL `sg_uf = '<UF>'`, deriva os atributos de
custo a partir da superfície do trecho e adiciona ao projeto as camadas **Arcos SNV — \<UF\>**
e **Nós SNV — \<UF\>**, também como camadas temporárias.

A camada de arcos traz estes campos principais (significados copiados do
[Guia de Logística Regional](regional.md)):

| Campo | Conteúdo |
|---|---|
| `id_trecho` | Identificador do trecho na base do DNIT |
| `vl_codigo` | Código SNV do trecho |
| `vl_br` | Número da BR |
| `sg_uf` | Sigla da UF |
| `ds_superfi` | Superfície física (`Pavimentada`, `Duplicada`, `Implantada`, `Terra`, …) |
| `oneway` | Sentido de circulação — a malha SNV é tratada como bidirecional (`no`) |
| `length` | Extensão do trecho, em **metros** (do campo oficial `vl_extensa`, em km) |
| `speed` | Velocidade estimada pela superfície, em km/h (de 30 em leito natural a 110 em pista duplicada) |
| `travel_time` | Tempo de percurso do trecho, em **segundos** (`length` ÷ `speed`) |

É essa camada de arcos que o painel **Regional** consome.

---

## 5. Onde ficam o cache e o GeoPackage

O cache do plugin fica em `QStandardPaths.CacheLocation` → `.../logis/` (mesma
convenção descrita em [Fontes de Dados](../referencia/fontes_dados.md)). Nessa pasta os
algoritmos gravam:

- por município: `osm_<código>.gpkg` (as camadas persistentes de arcos e nós) e
  `osm_overpass_<código>.json` (a resposta bruta da consulta à Overpass);
- por UF: `snv_<UF>.gpkg` (arcos e nós) e `snv_<UF>.geojson` (a resposta bruta do WFS).

Vale entender a diferença prática entre o que aparece no projeto e o que fica em disco:
as camadas adicionadas ao mapa são de **memória** (`TEMPORARY_OUTPUT`) — salvar o
projeto não as preserva, e elas somem ao fechar o QGIS. O **GeoPackage no cache é a
cópia persistente**: para manter o resultado, exporte as camadas do mapa para disco ou
carregue de volta o GeoPackage do cache. O efeito na velocidade da segunda execução
também difere entre as abas: no **SNV**, se o GPKG do cache já tiver as duas camadas,
o pipeline as devolve direto dele, sem nova consulta ao WFS — praticamente instantâneo.
No **OSM**, o pipeline não lê o GPKG de volta: ele reaproveita a resposta bruta em
`osm_overpass_<código>.json` e refaz o processamento (recorte pelo polígono,
extração dos nós, gravação no GPKG) — bem mais rápido que baixar de novo da Overpass,
mas não instantâneo.

Limpar a pasta de cache obriga a um novo download na próxima execução. O checkbox
**Forçar novo download** é o jeito de atualizar um dado que ficou velho (vintage do SNV
mudou, mapeamento OSM mudou) ou de consertar um download que ficou truncado.

---

## 6. Solução de problemas

| Sintoma | Causa provável |
|---|---|
| Erro de Overpass na área de resultados | A Overpass API está fora do ar ou sobrecarregada — é um serviço público com limite de uso; tente de novo mais tarde. Um município grande também pode estourar o tempo limite da consulta. |
| "nao foi possivel resolver o municipio" | Código IBGE inexistente ou digitado errado, falha no plugin GisBR, ou geobr inacessível para o fallback direto. |
| "OSM: nenhum way com highway encontrado no bbox" / nenhuma via encontrada | O *bbox* do município não retornou vias mapeadas com a tag `highway` no OpenStreetMap. |
| O SNV não devolve dados para a UF | O WFS da INDE está fora do ar, ou a UF não tem trecho federal registrado no vintage `snv_202507a`. O erro chega ao painel com a mensagem do algoritmo. |
| "Falha ao listar municípios de \<UF\>" | Sem conexão à internet, ou o servidor do IPEA (geobr) está fora do ar ao listar municípios. Saída: digite o **Código IBGE (7 dígitos)** à mão — o download da rede OSM não depende da listagem. |
| "Código IBGE do município deve possuir 7 dígitos." | O campo **Código IBGE** está vazio, incompleto ou com caracteres que não são dígitos. |
| QGIS aparentemente travado durante o download | Comportamento esperado da execução síncrona — ver seção 2. |
