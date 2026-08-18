# Guia de Logística Urbana

Este guia percorre, passo a passo, o fluxo completo do painel **logis — Indicadores
Urbanos**: como obter a rede viária do município, como usar as três abas do painel
(*Rede*, *Demanda*, *Carga*) e como ler cada indicador produzido.

Todos os botões do painel são apenas orquestradores: cada um chama um algoritmo
`logis:urban_*` do Processing e escreve o retorno no painel de resultados. A referência
técnica de cada algoritmo (parâmetros, complexidade, bibliografia) está em
[Algoritmos Urbanos](../algoritmos/urbano.md); aqui o foco é o uso do painel.

---

## 1. Obter a rede viária OSM do município

O painel **não baixa a rede**: ele consome uma camada de linhas já carregada no
projeto. O módulo Urbano trabalha sobre a rede viária do OpenStreetMap tratada pelo
pipeline `core.network.osm_pipeline`, que faz Overpass → recorte pelo polígono
municipal → GeoPackage.

No **Console Python** do QGIS:

```python
from logis.core.network.osm_pipeline import build_osm_municipal_network

resultado = build_osm_municipal_network(
    "3166600",              # code_muni — código IBGE de 7 dígitos
    "Serra da Saudade",     # nome do município (usado para resolver o polígono)
    "/caminho/para/rede.gpkg",
)
print(resultado["metadata"])
```

O que o pipeline faz e entrega:

| Etapa | Resultado |
|---|---|
| Resolve o polígono do município | Usa `gisbr:read_municipality` quando o GisBR está instalado |
| Consulta a Overpass API pelo *bbox* | Resposta JSON cacheada em `osm_overpass_<code_muni>.json`, ao lado do GPKG |
| Monta a camada de links e recorta pelo município | `osm_links_<code_muni>` (LineString, EPSG:4674) |
| Deduplica os nós de extremidade | `osm_nodes_<code_muni>` (Point, EPSG:4674) |

A camada de links já vem com os atributos de custo que os algoritmos usam:

| Campo | Conteúdo |
|---|---|
| `way_id` | Identificador do *way* no OSM |
| `highway` | Classe da via (`residential`, `primary`, `footway`, …) |
| `name` | Nome da via, quando existir no OSM |
| `oneway` | Sentido de circulação (`yes`, `no`, `-1`) |
| `length` | Comprimento do trecho, em **metros** |
| `speed` | Velocidade estimada pela classe `highway`, em km/h |
| `travel_time` | Tempo de percurso do trecho, em **segundos** (`length` ÷ `speed`) |

> A resposta da Overpass é reaproveitada do cache em execuções seguintes. Para forçar
> uma nova consulta (rede desatualizada, download truncado), chame a função com
> `force=True`.

Depois de gerado o GPKG, arraste `osm_links_<code_muni>` para o projeto — é essa camada
que o painel vai consumir. O script `tools/pilot_urbano_mg.py` mostra o mesmo fluxo
encadeado com o construtor de grafo e a matriz OD, fora do QGIS Desktop.

---

## 2. Abrir o painel

**Complementos → logis → Indicadores Urbanos**. O painel abre ancorado à direita da
janela do QGIS; se for fechado, reabra pela mesma entrada de menu (ou por **Ver →
Painéis**).

---

## 3. O seletor de rede e o painel de resultados

Dois elementos ficam **fora das abas**, porque valem para todas elas:

- **Camada de rede viária (Linhas)** — no topo, logo abaixo do título. O seletor lista
  apenas camadas de linha do projeto e é **compartilhado pelas três abas**: escolher a
  rede uma vez basta para todos os cálculos. Se nenhuma camada estiver selecionada,
  qualquer botão que dependa da rede abre um aviso e não executa nada.
- **Resultados dos Indicadores** — no rodapé, uma área de texto somente leitura, em
  fonte monoespaçada. Cada botão **acrescenta** suas linhas ao final; erros aparecem em
  vermelho, com a mensagem do algoritmo. O painel só é **limpo** pelo botão *Calcular
  Indicadores* da aba *Rede* — os demais botões preservam o histórico da sessão, o que
  permite comparar rodadas com parâmetros diferentes.

As saídas que são camadas (`betweenness`, densidade de demanda, acessibilidade
gravitacional e distância de entrega) são criadas em **memória** e adicionadas
automaticamente ao projeto; o painel apenas informa quantas feições vieram. Salve-as em
disco antes de fechar o projeto.

---

## 4. Aba **Rede** — estrutura da malha

### 4.1 Os três indicadores de estrutura

1. Selecione, em **Camada de área de referência (Polígonos)**, o recorte que serve de
   denominador para a densidade (o polígono do município, setores censitários ou um
   hexgrid).
2. Clique em **Calcular Indicadores**. O painel roda três algoritmos em sequência:

| Ordem | Algoritmo | Observação |
|---|---|---|
| 1 | `logis:urban_network_density` | **Pulado** se nenhuma camada de área estiver selecionada — o painel registra "Pulado" e segue |
| 2 | `logis:urban_network_connectivity` | Não precisa de área |
| 3 | `logis:urban_mean_circuity` | Roda com parâmetros fixos: 1.000 pares amostrados e distância mínima de 100 m entre origem e destino |

Um erro em um dos três não interrompe os outros: a falha é escrita no painel e a
sequência continua.

### 4.2 Centralidade de intermediação (*betweenness*)

Calculada à parte, no bloco seguinte da mesma aba, porque produz uma camada e é a
operação mais cara do painel.

- **Número de amostras (pares OD)** — quantos pares origem-destino são sorteados para
  aproximar a centralidade. O padrão é `1000`. O custo cresce linearmente com esse
  número (um Dijkstra por origem amostrada): aumente com parcimônia em redes grandes.
- **Semente da amostragem (opcional, 0 = aleatório)** — controla o sorteio dos pares.
  Com o valor `0`, o campo mostra **"Aleatória"** e nenhuma semente é passada ao
  algoritmo: cada execução sorteia pares diferentes e os valores mudam de uma rodada
  para outra. Com **qualquer valor maior que zero**, a amostragem passa a ser
  **reprodutível** — a mesma rede com a mesma semente e o mesmo número de amostras
  devolve exatamente os mesmos valores. Use uma semente fixa sempre que o resultado
  for entrar em um relatório, ou quando quiser comparar dois cenários de rede sem que a
  diferença venha do sorteio.

O botão **Calcular Centralidade de Intermediação** adiciona ao projeto uma cópia da
rede com o campo `betweenness`.

---

## 5. Aba **Demanda** — onde estão as pessoas e os destinos

### 5.1 Densidade de demanda

Precisa de dois campos e **do plugin GisBR instalado** — os setores censitários e a
população vêm de `gisbr:read_census_tract` + `gisbr:join_censo`:

- **Código IBGE do município (7 dígitos)** — o mesmo `code_muni` usado no passo 1.
- **Campo de população** — o nome do campo populacional da tabela do censo unida aos
  setores (ex.: `V0001`).

O botão adiciona ao projeto os setores censitários com o campo
`dens_demanda_hab_km2`.

### 5.2 Acessibilidade gravitacional

- **Camada de origem (pontos/centroides)** — de onde se mede o acesso (centroides de
  setor, por exemplo).
- **Camada de destinos (POIs)** — comércio, equipamentos, oportunidades.
- **Campo de peso do destino (opcional, default 1)** — a lista de campos acompanha a
  camada de destinos escolhida. Sem peso, todos os destinos valem 1.
- **Beta (decaimento por distância)** — expoente da fricção de distância, entre
  `0,0001` e `10`, padrão `2,0`. O escore de cada origem é
  Σ (peso*j* ÷ distância*ij*^beta): **beta maior penaliza mais o destino distante**
  (acesso mais "local"), beta menor achata a penalização e aproxima o resultado de uma
  soma dos pesos.

A saída é a camada de origens com o campo `acess_gravit`.

---

## 6. Aba **Carga** — circulação e custo de entrega

### 6.1 Restrição de circulação de carga

- **Expressão de restrição (opcional)** — uma expressão QGIS que devolve verdadeiro
  para os trechos **restritos** ao caminhão, por exemplo
  `"highway" = 'residential' OR "maxweight" < 3.5`.
- **Deixando o campo vazio**, o algoritmo monta uma expressão padrão a partir dos campos
  existentes na camada: sempre marca as classes incompatíveis com carga (`pedestrian`,
  `footway`, `path`, `steps`, `cycleway`, `bridleway`, `corridor`) e acrescenta
  `width < 3,0 m` e `maxweight < 3,5 t` **quando esses campos existirem**. A expressão
  efetivamente usada é registrada no log do Processing.

O painel devolve um percentual — a fração da rede, **ponderada por extensão**, que está
**livre** de restrição.

### 6.2 Distância de entrega

- **Camada de depósitos candidatos (Pontos)** — os CDs/bases avaliados.
- **Camada de zonas/centroides (Pontos)** — os pontos de demanda a atender.
- **Critério de custo** — *Distância* ou *Tempo de viagem*; define se o caminho mínimo
  usa o campo `length` ou o campo `travel_time` da rede.

A saída é a camada de zonas com o campo `dist_entrega`, contendo o custo até o
**depósito mais próximo** de cada zona.

---

## 7. Como interpretar cada indicador

| Indicador | Unidade | Leitura |
|---|---|---|
| **Densidade viária** | km/km² | Quanto de via existe por área. Valores altos indicam malha densa e capilar (mais opções de rota, quadras menores); valores baixos, malha esparsa e dependente de poucos eixos. Só é comparável entre cidades se o recorte de área for equivalente. |
| **Número de nós (v) / arestas (e)** | contagem | Tamanho do grafo. Servem de referência de porte e de sanidade: uma queda brusca em relação à camada original indica geometrias inválidas ou rede desconectada. |
| **Índice Alfa** | 0 a 1 | Razão entre circuitos existentes e circuitos possíveis. Perto de 0, rede quase arborescente (poucos caminhos alternativos); quanto maior, mais malha em anel — melhor para redundância de rotas. |
| **Índice Beta** | e/v | Arestas por nó. Abaixo de 1, estrutura de árvore; em torno de 1, rede com poucos circuitos; acima de 1, rede reticulada. |
| **Índice Gama** | 0 a 1 | Fração das conexões possíveis que de fato existem. Quanto mais alto, mais conectada a malha. |
| **Cruzamentos 4+ pernas** | % | Proporção de interseções com quatro ou mais aproximações — assinatura de malha em grelha, que favorece o desvio e a distribuição do tráfego de carga. |
| **Becos sem saída** | % | Proporção de nós de grau 1. Alto em tecidos de condomínio/loteamento fechado: encarece a coleta e a entrega porta a porta, porque obriga a entrar e voltar pelo mesmo trecho. |
| **Circuidade média** | razão ≥ 1 | Distância pela rede ÷ distância em linha reta, média de 1.000 pares sorteados. `1,0` seria o ideal inalcançável; valores próximos de `1,2`–`1,3` indicam malha eficiente, e valores altos denunciam barreiras (rio, ferrovia, relevo) ou malha muito recortada. |
| **`betweenness`** (camada) | escore relativo | Quantas rotas mínimas da amostra passam por cada trecho. Os valores mais altos marcam os **eixos críticos**: gargalos cujo bloqueio desorganiza a circulação, e candidatos naturais a corredor de carga. Compare valores **dentro da mesma rodada** — a escala depende do número de amostras. |
| **`dens_demanda_hab_km2`** (camada) | hab/km² | Densidade populacional por setor censitário. É a superfície de demanda: onde adensar entregas e onde a rota rende mais paradas por quilômetro. |
| **`acess_gravit`** (camada) | escore relativo | Oportunidades acessíveis a partir de cada origem, descontadas pela distância. Sem unidade física — serve para **ranquear e mapear** origens bem e mal servidas, sempre com o mesmo beta e o mesmo conjunto de destinos. |
| **Acessibilidade de carga** | % (0 a 100) | Percentual da extensão da rede **livre** de restrição. `100` significa que nenhum trecho foi marcado como restrito; quanto menor, maior a parcela da malha vedada ao veículo considerado — leia sempre junto da expressão usada, porque o valor é definido por ela. |
| **`dist_entrega`** (camada) | metros ou segundos | Custo até o depósito mais próximo, na unidade do critério escolhido (metros para *Distância*, segundos para *Tempo de viagem*). O máximo e a média sobre as zonas medem a qualidade de um arranjo de depósitos; o mapa do campo mostra as zonas mal atendidas, que é onde entra a [localização de instalações](../algoritmos/localizacao.md). |

---

## 8. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Por favor, selecione uma camada de rede viária." | Nenhuma camada de linha no projeto, ou nenhuma escolhida no seletor do topo. |
| "1) Densidade viária: Pulado" | Nenhuma camada de área de referência selecionada na aba *Rede*. |
| "QGIS Processing não está disponível no ambiente atual." | O painel foi instanciado fora de uma sessão do QGIS Desktop. |
| Erro no cálculo de densidade de demanda | Plugin GisBR ausente, código IBGE incorreto ou nome de campo de população inexistente na tabela do censo. |
| A centralidade muda a cada execução | Semente em `0` ("Aleatória") — fixe um valor maior que zero para reproduzir o resultado. |
| Expressão de restrição inválida | Nome de campo inexistente na camada de rede; confira os campos disponíveis na tabela de atributos. |
