# Guia de Roteirização

Este guia percorre, passo a passo, o uso do painel **logis — Roteirização**: como
preparar as camadas de entrada, como preencher as **duas abas** do painel — **TSP**, a
rota de Caixeiro Viajante de um único veículo, e **CVRP**, a roteirização de uma frota
com capacidade a partir de um depósito — e como ler os resultados de cada uma.

Os botões do painel são apenas orquestradores: chamam os algoritmos `logis:vrp_tsp` e
`logis:vrp_cvrp` do Processing e escrevem o retorno no painel de resultados. A
referência técnica dos algoritmos (parâmetros, fórmulas, complexidade, bibliografia)
está em [Algoritmos de Roteirização](../algoritmos/roteirizacao.md); aqui o foco é o uso
do painel.

---

## 1. Preparar as camadas de entrada

O painel **não baixa dados**: ele consome camadas já carregadas no projeto. São quatro
insumos possíveis na aba **TSP** — a camada de rede viária, por ficar no topo do painel,
vale também para a aba **CVRP**, cujos insumos estão na
[seção 7](#7-roteirizar-uma-frota-com-capacidade-aba-cvrp).

| Insumo | Obrigatória? | Papel |
|---|---|---|
| **Camada do ponto inicial (Pontos)** | Sim | O algoritmo usa a **primeira feição válida** da camada; o ideal é uma camada com uma única feição (garagem, CD, depósito). |
| **Camada de pontos a visitar (Pontos)** | Sim | Cada feição é uma parada visitada exatamente uma vez. Os atributos originais são preservados na saída. |
| **Camada do ponto final (Pontos)** | Não | Se vazia, a rota **fecha no ponto inicial** (tour fechado). Se preenchida, a rota termina nesse ponto (caminho aberto — garagem diferente, aterro, transbordo, CD de destino). Também usa a primeira feição válida. |
| **Camada de rede viária (Linhas)** | Não | Com rede, as distâncias são reais (Dijkstra sobre `QgsGraph`, matriz OD) e os trechos da saída seguem a geometria das ruas; sem rede, tudo é **distância euclidiana** e os trechos são segmentos retos. A rede pode ser a `osm_links_<code_muni>` do pipeline OSM — ver o [Guia de Logística Urbana](urbano.md#1-obter-a-rede-viária-osm-do-município). |

> **CRS de cálculo.** O cálculo é feito em CRS métrico. Quando há rede viária, ou quando
> a camada de pontos está em coordenadas geográficas, o algoritmo reprojeta para
> **EPSG:5880** (SIRGAS 2000 / Brazil Polyconic); quando a camada de pontos já está em
> CRS projetado e não há rede, usa o CRS dela. As distâncias das saídas estão na unidade
> desse CRS de cálculo (metros).

---

## 2. Abrir o painel

**Complementos → logis → Roteirização**. O painel abre ancorado à direita da janela do
QGIS; se for fechado, reabra pela mesma entrada de menu (ou por **Ver → Painéis**).

O painel tem **duas abas**: **TSP** (um único veículo, sem capacidade) e **CVRP** (frota
com capacidade a partir de um depósito). O seletor **Camada de rede viária (Linhas -
opcional)** fica **no topo do painel, fora das abas**, e vale para as duas; o painel
**Resultados da Roteirização**, logo abaixo das abas, também é compartilhado e é limpo a
cada execução, seja de qual aba for.

---

## 3. Passo a passo da aba TSP

Os controles aparecem nesta ordem:

1. **Camada do ponto inicial (Pontos)** — obrigatória.
2. **Camada de pontos a visitar (Pontos)** — obrigatória.
3. **Camada do ponto final (Pontos - opcional, vazio fecha no ponto inicial)** — o
   seletor aceita entrada vazia.
4. **Camada de rede viária (Linhas - opcional)** — no topo do painel, fora das abas;
   também aceita vazia.
5. **Aplicar busca local (2-opt e Or-opt)** — caixa marcada por padrão; refina a
   sequência inicial do Vizinho Mais Próximo. Desmarcar entrega a rota bruta do Vizinho
   Mais Próximo, mais rápida e pior.
6. Botão **Calcular Rota (TSP)**.

O painel **limpa** os resultados a cada execução. As duas camadas de saída (**Ordem de
visita** e **Rota (trechos)**) são criadas **em memória** e adicionadas automaticamente
ao projeto — salve-as em disco antes de fechar o projeto.

Ponto inicial e pontos a visitar são obrigatórios: sem eles, o painel abre um aviso e
não executa. O backend OR-Tools é usado automaticamente quando instalado, com fallback
silencioso para a heurística Python — o backend efetivamente usado aparece no resultado.

---

## 4. Ler o painel de resultados do TSP

| Linha do painel | Campo de origem | Significado |
|---|---|---|
| **Pontos visitados** | `stop_count` | Quantidade de pontos da camada de visita atendidos no percurso. |
| **Distância total do tour** | `tour_dist` | Distância total do percurso, do ponto inicial ao encerramento (retorno ou ponto final). |
| **Custo de acesso** | `access_dist` | Distância da perna do ponto inicial até o primeiro ponto a visitar — deslocamento improdutivo. |
| **Custo de retorno** | `return_dist` | Distância da perna final, de volta ao ponto inicial (tour fechado) ou até o ponto final (caminho aberto) — também improdutiva. |
| **Razão de deadhead (dead_ratio)** | `dead_ratio` | Fração do percurso que é deslocamento improdutivo, entre 0 e 1. |
| **Fechamento** | `closed` | "Sim (fecha no ponto inicial)" ou "Não (termina no ponto final)". |
| **Backend de otimização** | `backend` | `ortools` quando o OR-Tools resolveu a instância, ou `python` quando caiu no fallback da heurística nativa. |

---

## 5. Ler a camada Ordem de visita

A sequência de visita **não** está na ordem de armazenamento das feições: abra a tabela
de atributos da camada **Ordem de visita** e ordene pelo campo **`visit_seq`** (clique
no cabeçalho da coluna).

| Campo | Significado |
|---|---|
| *(campos originais)* | Atributos da camada de pontos a visitar; nulos nas feições de ponto inicial e de ponto final. |
| `visit_seq` | Posição do nó na sequência de visita. |
| `node_role` | Papel do nó: `inicio`, `parada` ou `fim`. |
| `leg_role` | Papel da perna que **chega** a este nó (`acesso`, `rota` ou `retorno`); vazio na feição de `inicio`. |
| `leg_dist` | Distância da perna que chega a este nó. |
| `cum_dist` | Distância acumulada desde o ponto inicial até este nó. |

---

## 6. Quanto do percurso foi deslocamento improdutivo

### Os três papéis de `leg_role`

Na camada **Rota (trechos)**, cada perna do percurso é classificada em um de três
papéis:

- **`acesso`** — a primeira perna, do ponto inicial ao primeiro ponto a visitar.
- **`rota`** — as pernas intermediárias, entre pontos a visitar — distância produtiva.
- **`retorno`** — a última perna, de volta ao ponto inicial (tour fechado) ou até o
  ponto final (caminho aberto).

`acesso` e `retorno` são o deslocamento improdutivo (*deadhead*): nenhum atendimento
ocorre nessas pernas.

### Como estilizar por `leg_role`

Para ver o improdutivo no mapa, clique com o botão direito na camada **Rota
(trechos)** → **Propriedades → Simbologia** → mude **Símbolo Único** para
**Categorizado** → em *Valor*, escolha o campo **`leg_role`** → **Classificar**. Dê às
classes `acesso` e `retorno` uma cor/tracejado distintos de `rota`, para que o
deslocamento improdutivo salte no mapa.

### Como somar

Os campos `access_dist`, `service_dist`, `return_dist`, `tour_dist`, `dead_ratio`,
`stop_count`, `closed` e `backend` já vêm **repetidos em todas as feições** com o total
do percurso — não é preciso somar nada à mão; basta abrir a tabela de atributos e ler
qualquer feição.

A soma manual dos `leg_dist` das feições com `leg_role` em (`acesso`, `retorno`) — por
exemplo com a calculadora de campo ou pelo resumo estatístico com o filtro
`"leg_role" IN ('acesso','retorno')` — dá exatamente `access_dist + return_dist`.

### A identidade que fecha as contas

$$\texttt{tour\_dist} = \texttt{access\_dist} + \texttt{service\_dist} + \texttt{return\_dist}$$

$$\texttt{dead\_ratio} = \frac{\texttt{access\_dist} + \texttt{return\_dist}}{\texttt{tour\_dist}}$$

`dead_ratio` fica entre 0 e 1. Quanto mais perto de 0, mais do percurso é atendimento;
perto de 1, o veículo gasta o percurso se deslocando sem atender. `dead_ratio` alto
sugere ponto inicial mal localizado em relação à nuvem de paradas — gancho para
[localização de instalações](../algoritmos/localizacao.md).

### Os demais campos da camada Rota (trechos)

| Campo | Significado |
|---|---|
| `leg_seq` | Número de ordem da perna no percurso. |
| `from_seq` | `visit_seq` do nó de origem da perna. |
| `to_seq` | `visit_seq` do nó de destino da perna. Na última perna de um tour fechado vale `1`, explicitando o retorno ao ponto inicial. |
| `leg_role` | `acesso`, `rota` ou `retorno`. |
| `leg_dist` | Distância desta perna. |
| `cum_dist` | Distância acumulada do início do percurso até o fim desta perna. |

---

## 7. Roteirizar uma frota com capacidade (aba CVRP)

### Quando usar CVRP em vez de TSP

A aba **TSP** sequencia as visitas de **um único veículo**, sem capacidade: toda parada
entra no mesmo percurso, custe o que custar em carga. A aba **CVRP** parte de uma
**frota de veículos idênticos**, cada um com uma capacidade máxima, e reparte os
clientes em **várias rotas** — cada rota sai do depósito, atende um subconjunto de
clientes cuja soma de demandas cabe no veículo, e volta ao depósito.

O número de rotas **não é um parâmetro**: ele é resultado do cálculo, e depende da carga
total, da capacidade informada e da distribuição geográfica dos clientes.

Regra prática: se um veículo só dá conta de tudo e o que interessa é a **ordem de
visita**, use a aba TSP; se há uma **capacidade a respeitar** (toneladas, m³, caixas,
contêineres, vagas) e a operação vai se dividir em vários veículos ou várias viagens,
use a aba CVRP.

### Os insumos da aba CVRP

| Insumo | Obrigatório? | Papel |
|---|---|---|
| **Camada de depósito (Pontos)** | Sim | Ponto de partida e de chegada de **todas** as rotas. O algoritmo usa a **primeira feição válida** da camada; o ideal é uma camada com uma única feição (CD, garagem, transbordo). |
| **Camada de demanda / clientes (Pontos)** | Sim | Cada feição é um cliente atendido exatamente uma vez, por uma única rota. Os atributos originais são preservados na saída. |
| **Campo de peso/demanda (opcional, default = 1,0)** | Não | Campo numérico com a carga de cada cliente. Deixado vazio — ou nulo/não numérico na feição —, a demanda vale **1,0**, e a capacidade passa a contar **paradas por rota**. Valor negativo é tratado como zero. |
| **Capacidade do veículo** | Sim | Carga máxima de um veículo em uma rota; vem preenchida com **100,0** e precisa ser maior que zero. Tem que estar na **mesma unidade** do campo de peso. |
| **Camada de rede viária (Linhas)** | Não | O seletor do **topo do painel**, compartilhado com a aba TSP: com rede, as distâncias são reais (Dijkstra sobre `QgsGraph`, matriz OD); sem rede, são **euclidianas**. Vale aqui a mesma nota de CRS de cálculo da [seção 1](#1-preparar-as-camadas-de-entrada). |
| **Aplicar busca local (2-opt e Or-opt)** | Não | Caixa marcada por padrão; refina cada rota construída pelas economias de Clarke-Wright. Desmarcar entrega as rotas brutas, mais rápido e pior. |

### Passo a passo do preenchimento

1. **Camada de rede viária (Linhas - opcional)** — no topo do painel, antes de abrir a
   aba; vale para as duas abas.
2. Abra a aba **CVRP**.
3. **Camada de depósito (Pontos)** — obrigatória.
4. **Camada de demanda / clientes (Pontos)** — obrigatória.
5. **Campo de peso/demanda (opcional, default = 1,0)** — o seletor aceita campo vazio, e
   a lista de campos acompanha a camada de demanda escolhida no passo anterior.
6. **Capacidade do veículo** — na mesma unidade do campo de peso.
7. **Aplicar busca local (2-opt e Or-opt)** — marcada por padrão.
8. Botão **Executar Roteirização (CVRP)**.

Depósito e demanda são obrigatórios: sem eles, o painel abre um aviso e não executa. As
duas camadas de saída (**Rotas geradas** e **Paradas por rota**) são criadas **em
memória** e adicionadas automaticamente ao projeto — salve-as em disco antes de fechar o
projeto.

### Ler o painel de resultados do CVRP

O painel abre com quatro totais e, em seguida, uma linha por rota:

| Linha do painel | Campo de origem | Significado |
|---|---|---|
| **Rotas geradas** | contagem de `route_id` | Quantos veículos/viagens o plano exige. |
| **Paradas atendidas** | soma de `stop_count` | Total de clientes atendidos, somando todas as rotas. |
| **Carga total** | soma de `route_load` | Soma das demandas atendidas, na unidade do campo de peso (ou o número de paradas, quando o campo fica vazio). |
| **Distância total** | soma de `route_dist` | Quilometragem do plano inteiro, na unidade do CRS de cálculo (metros). |
| **Rota N: k paradas \| carga L \| distância D** | `route_id`, `stop_count`, `route_load`, `route_dist` | Uma linha por rota gerada — é por aqui que se vê o **equilíbrio da frota**: rotas com carga muito abaixo da capacidade, ou uma rota muito mais longa que as demais. |

### Ler as camadas de saída

**Rotas geradas** (linhas) — uma feição por rota, com a geometria do percurso depósito →
clientes → depósito:

| Campo | Significado |
|---|---|
| `route_id` | Identificador da rota, de 1 até o número de rotas. |
| `stop_count` | Quantidade de clientes atendidos nessa rota. |
| `route_load` | Carga total transportada na rota — comparar com a capacidade informada mostra a folga do veículo. |
| `route_dist` | Distância total da rota, ida e volta ao depósito. |

**Paradas por rota** (pontos) — uma feição por cliente, com os atributos originais da
camada de demanda acrescidos de:

| Campo | Significado |
|---|---|
| `route_id` | Rota à qual o cliente foi atribuído — bom campo para uma simbologia **Categorizada**, que pinta cada rota de uma cor. |
| `stop_seq` | Posição da parada dentro da rota, de 1 até `stop_count`. |
| `cum_load` | Carga acumulada no veículo **depois** de atender esta parada; na última parada da rota, iguala o `route_load`. |

> **A sequência de visita está na tabela de atributos.** Como no TSP, a ordem de
> armazenamento das feições não é a ordem de atendimento: abra a tabela de atributos de
> **Paradas por rota** e ordene por **`route_id`** e depois por **`stop_seq`** (clique
> nos cabeçalhos das colunas) para ler o roteiro de cada veículo, parada a parada.

A referência técnica do algoritmo — formulação, economias de Clarke-Wright, backend
OR-Tools, complexidade e bibliografia — está em
[Algoritmos de Roteirização](../algoritmos/roteirizacao.md) §1.

---

## 8. Limitações

- A aba TSP é um **TSP de um único veículo**: não há capacidade, janela de tempo nem
  frota. Para frota com capacidade, use a aba **CVRP**
  ([`logis:vrp_cvrp`](../algoritmos/roteirizacao.md)).
- **Solução boa, não ótima**: heurística Vizinho Mais Próximo + 2-opt/Or-opt (ou
  OR-Tools com limite de 10 segundos). Escala testada: até 1.000 pontos; o custo cresce
  com o quadrado do número de pontos (matriz de distâncias N×N).
- Sem rede viária, as distâncias são **euclidianas** e subestimam o percurso real.
- Com rede viária, os pontos são **aproximados (snap)** ao vértice mais próximo do
  grafo; par inalcançável na rede cai no **segmento reto** entre os dois nós como
  *fallback*.
- Ponto inicial e ponto final usam apenas a **primeira feição válida** da camada —
  feições extras são ignoradas em silêncio.
- Feições de geometria vazia na camada de pontos a visitar são puladas; polígonos
  entram pelo **centroide**.
- Camadas de saída em **memória**: perdem-se ao fechar o projeto sem salvar.
- **CVRP — demanda maior que a capacidade**: nenhum cliente pode ter demanda maior que a
  capacidade do veículo; nesse caso o algoritmo **recusa a execução** com a mensagem "A
  demanda do nó excede a capacidade máxima do veículo". Não há entrega fracionada: ou o
  cliente cabe em um veículo, ou a instância é inviável.
- **CVRP — frota homogênea e sem janela de tempo**: todos os veículos têm a mesma
  capacidade, não há limite de jornada, tempo de serviço, janela de atendimento nem
  número máximo de veículos.
- **CVRP — solução boa, não ótima**: heurística de economias de Clarke-Wright + 2-opt/
  Or-opt, em Python puro. Escala testada: até 1.000 pontos de demanda.

---

## 9. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Por favor, selecione a camada do ponto inicial." | Nenhuma camada escolhida no seletor de ponto inicial. |
| "Por favor, selecione a camada de pontos a visitar." | Nenhuma camada escolhida no seletor de pontos a visitar. |
| "QGIS Processing não está disponível no ambiente atual." | O painel foi instanciado fora de uma sessão do QGIS Desktop. |
| "A camada de pontos a visitar está vazia." | Nenhuma feição com geometria válida na camada de pontos a visitar. |
| "Nenhum ponto final válido encontrado na camada fornecida." | A camada de ponto final foi selecionada, mas nenhuma feição nela tem geometria válida. |
| Trechos retos na saída apesar de haver rede selecionada | Par de nós inalcançável na rede (fallback para o segmento reto), ou pontos longe demais da malha viária. |
| A rota muda de uma execução para outra com OR-Tools instalado | A metaheurística `GUIDED_LOCAL_SEARCH` roda até o limite de 10 segundos; pequenas variações de tempo podem mudar o resultado entre rodadas. |
