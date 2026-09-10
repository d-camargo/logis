# Guia de Roteirização

Este guia percorre, passo a passo, o uso do painel **logis — Roteirização**: como
preparar as camadas de entrada, como preencher o painel e como ler os resultados de uma
rota de Caixeiro Viajante (TSP) para um único veículo.

O botão do painel é apenas um orquestrador: ele chama o algoritmo `logis:vrp_tsp` do
Processing e escreve o retorno no painel de resultados. A referência técnica do
algoritmo (parâmetros, fórmulas, complexidade, bibliografia) está em
[Algoritmos de Roteirização](../algoritmos/roteirizacao.md); aqui o foco é o uso do
painel.

---

## 1. Preparar as camadas de entrada

O painel **não baixa dados**: ele consome camadas já carregadas no projeto. São quatro
insumos possíveis.

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

---

## 3. Passo a passo do painel

Os controles aparecem nesta ordem:

1. **Camada do ponto inicial (Pontos)** — obrigatória.
2. **Camada de pontos a visitar (Pontos)** — obrigatória.
3. **Camada do ponto final (Pontos - opcional, vazio fecha no ponto inicial)** — o
   seletor aceita entrada vazia.
4. **Camada de rede viária (Linhas - opcional)** — também aceita vazia.
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

## 4. Ler o painel de resultados

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

## 7. Limitações

- É um **TSP de um único veículo**: não há capacidade, janela de tempo nem frota. Para
  frota com capacidade, use o CVRP
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

---

## 8. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Por favor, selecione a camada do ponto inicial." | Nenhuma camada escolhida no seletor de ponto inicial. |
| "Por favor, selecione a camada de pontos a visitar." | Nenhuma camada escolhida no seletor de pontos a visitar. |
| "QGIS Processing não está disponível no ambiente atual." | O painel foi instanciado fora de uma sessão do QGIS Desktop. |
| "A camada de pontos a visitar está vazia." | Nenhuma feição com geometria válida na camada de pontos a visitar. |
| "Nenhum ponto final válido encontrado na camada fornecida." | A camada de ponto final foi selecionada, mas nenhuma feição nela tem geometria válida. |
| Trechos retos na saída apesar de haver rede selecionada | Par de nós inalcançável na rede (fallback para o segmento reto), ou pontos longe demais da malha viária. |
| A rota muda de uma execução para outra com OR-Tools instalado | A metaheurística `GUIDED_LOCAL_SEARCH` roda até o limite de 10 segundos; pequenas variações de tempo podem mudar o resultado entre rodadas. |
