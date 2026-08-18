# Guia de Coleta de Lixo

Este guia percorre, passo a passo, o fluxo completo do painel **logis — Coleta de
Lixo**: como preparar as camadas de entrada e como usar as quatro abas do painel
(*Geração*, *Roteirização*, *Frota*, *Indicadores*), que estão dispostas exatamente na
ordem metodológica de um projeto de coleta — estimar quanto se gera, dividir a cidade em
setores, traçar o itinerário sobre as ruas, dimensionar a frota e, por fim, medir o
resultado.

Todos os botões do painel são apenas orquestradores: cada um chama um algoritmo
`logis:waste_*` do Processing e escreve o retorno no painel de resultados. A referência
técnica de cada algoritmo (parâmetros, fórmulas, complexidade, bibliografia) está em
[Algoritmos de Coleta de Resíduos](../algoritmos/residuos.md); aqui o foco é o uso do
painel.

> A coleta domiciliar porta a porta é um problema de **roteirização por arcos** — a
> demanda está nas ruas, não em pontos. Por isso o módulo gira em torno de CPP, RPP e
> CARP. A coleta ponto a ponto (contêineres, PEVs, coleta seletiva com pontos de
> entrega) é um problema por **nós** e fica na
> [roteirização por nós](../algoritmos/roteirizacao.md); a escolha de onde ficam
> ecopontos e estações de transbordo é
> [localização de instalações](../algoritmos/localizacao.md).

---

## 1. Preparar as camadas de entrada

O painel **não baixa dados**: ele consome camadas já carregadas no projeto. Para um
projeto completo você precisa de três insumos.

| Insumo | De onde vem |
|---|---|
| **Rede viária do município** (linhas) | Pipeline OSM do módulo Urbano — ver o [Guia de Logística Urbana](urbano.md#1-obter-a-rede-viária-osm-do-município). É a mesma camada `osm_links_<code_muni>`, com `length`, `speed` e `travel_time`. |
| **Setores censitários com população** (polígonos) | `gisbr:read_census_tract` + `gisbr:join_censo`, com o plugin GisBR instalado. |
| **Ponto do depósito/aterro/transbordo** (pontos) | Camada com **uma única feição**, digitalizada ou importada — exigida pela roteirização CARP. |

Além disso, cada trecho de via precisa saber a que setor censitário pertence: a aba
*Geração* espera um **campo de setor já presente na camada de vias**. Se a rede OSM
ainda não tiver esse campo, faça antes um `native:joinbylocation` (ou
`native:joinattributesbylocation`) entre as vias e os setores censitários.

> **CRS métrico.** Todas as etapas que constroem grafo (setorização, CPP, RPP, CARP)
> usam a *tolerância de nó em metros* para decidir se dois vértices são o mesmo
> cruzamento. Trabalhe com as camadas reprojetadas para um CRS métrico (UTM da zona ou
> EPSG:5880) — em EPSG:4674 a tolerância seria interpretada em graus e a rede se
> desmontaria em componentes soltos.

---

## 2. Abrir o painel

**Complementos → logis → Coleta de Lixo**. O painel abre ancorado à direita da janela do
QGIS; se for fechado, reabra pela mesma entrada de menu (ou por **Ver → Painéis**).

---

## 3. O painel de resultados

No rodapé, fora das abas, fica a área **Resultados** — somente leitura, em fonte
monoespaçada, compartilhada pelas quatro abas. Cada botão **limpa o painel** antes de
executar e escreve ali um bloco delimitado (`=== EXECUTANDO … ===` … `=== CONCLUÍDO
===`); erros aparecem em vermelho, com a mensagem do algoritmo. Ou seja: o painel mostra
sempre **a última execução**, não o histórico da sessão — se quiser comparar rodadas,
copie o texto antes de clicar de novo.

Diferentemente do painel Urbano, **não há seletor de rede compartilhado**: cada seção
tem os seus próprios seletores de camada e de campo, porque as etapas consomem saídas
umas das outras (as vias com geração alimentam a setorização, as vias setorizadas
alimentam a roteirização, as rotas alimentam a frota e os indicadores).

Todas as saídas são criadas em **memória** e adicionadas automaticamente ao projeto — as
de rota são camadas de linha; as de frota, equilíbrio, deadhead e cobertura são tabelas
sem geometria. Salve-as em disco antes de fechar o projeto, sobretudo as que servem de
entrada para a etapa seguinte.

---

## 4. Aba **Geração** — quanto se gera e como dividir a cidade

### 4.1 Estimativa de geração

Cruza a população dos setores censitários com a malha viária e distribui a massa gerada
pelos trechos, proporcionalmente ao comprimento de cada um.

- **Camada de setores censitários (Polígonos)**, **Campo ID do setor (Setores)** e
  **Campo de população (Setores)** — de onde vem a população.
- **Camada de trechos de via (Linhas)** e **Campo ID do setor (Vias)** — a malha a
  coletar e o campo que a liga aos setores (o do `joinbylocation` do passo 1).
- **Taxa per capita (kg/hab/dia)** — o parâmetro que define a escala de todo o projeto.
  Padrão `0,9`, dentro da faixa nacional do SNIS (≈ 0,9 a 1,0 kg/hab/dia). **Use o valor
  local sempre que existir**: a massa total, o número de viagens e o tamanho da frota
  são proporcionais a ele — trocar `0,9` por `1,2` encarece a operação em um terço, sem
  que nada mais mude no modelo.
- **Fração de cobertura (0.0 a 1.0)** — a parcela da população efetivamente atendida
  pelo serviço. Padrão `1,0` (cobertura universal). Use um valor menor para representar
  áreas sem coleta regular, ou para simular a implantação gradual do serviço.

O botão **Calcular Estimativa de Geração** adiciona ao projeto as vias com o campo
`waste_kg_day`.

### 4.2 Setorização

Particiona as vias em setores de coleta contíguos e equilibrados por carga.

- **Camada de trechos de via (Linhas)** — normalmente a saída de 4.1.
- **Campo de carga (opcional)** — aponte para `waste_kg_day`. **Se deixar vazio, o
  balanceamento passa a ser feito pelo comprimento dos trechos**, e não pela massa
  coletada: aceitável como aproximação em cidades homogêneas, ruim onde a densidade
  populacional varia muito.
- **Número de setores de coleta desejado** — o *k* da partição (mínimo `2`, padrão `2`).
  Na prática, é o número de equipes/turnos que se pretende operar; se você não sabe
  ainda, rode com uma estimativa, veja o resultado do dimensionamento de frota (aba
  *Frota*) e volte para ajustar.
- **Tolerância de nó (m)** — padrão `0,01` m. Aumente apenas se a malha tiver
  extremidades que não se tocam exatamente; valores altos demais fundem cruzamentos
  distintos.
- **Máximo de iterações de rebalanceamento** — padrão `50`. Mais iterações aparam melhor
  a diferença de carga entre setores, ao custo de tempo.

O botão **Executar Setorização** adiciona ao projeto as vias com o campo
`collection_sector_id`.

---

## 5. Aba **Roteirização** — o itinerário sobre as ruas

### 5.1 Como escolher entre CPP, RPP e CARP

As três seções resolvem o mesmo tipo de problema — percorrer **arestas**, não pontos —,
mas respondem a perguntas diferentes. Decida por duas questões, nesta ordem:

**Primeira: todas as vias da camada precisam ser coletadas?**

- **Sim, todas** → **CPP** (*Chinese Postman Problem*). É o caso da varredura completa de
  um setor: o algoritmo garante que cada trecho seja percorrido ao menos uma vez e
  minimiza a repetição improdutiva.
- **Não, só um subconjunto** → **RPP** (*Rural Postman Problem*). É o caso quando parte
  da malha existe apenas para o caminhão se deslocar — vias de outro setor, marginais,
  trechos sem domicílio, ou a coleta de uma frequência específica (só a rota de
  3x/semana). As vias não obrigatórias continuam disponíveis como **conector**.

**Segunda: o caminhão enche antes de terminar?**

- **Não, ou a capacidade não é a questão** → fique com CPP ou RPP. Ambos produzem **um
  circuito por setor**, sem limite de carga e sem depósito: são modelos de *cobertura*,
  bons para medir a extensão a percorrer e o deadhead mínimo do setor.
- **Sim** → **CARP** (*Capacitated Arc Routing Problem*). É o único dos três que conhece
  **capacidade do veículo** e **depósito**: ele quebra a coleta em várias viagens, cada
  uma partindo e voltando ao depósito quando a carga acumulada atinge o limite. É o que
  produz o `route_id` que a aba *Frota* consome.

Na prática, um projeto completo costuma usar **CPP ou RPP para dimensionar o setor** (e
conferir se a setorização ficou razoável) e **CARP para produzir as rotas operacionais**.
Se um único trecho tiver demanda maior que a capacidade do veículo, o CARP **falha com
erro explícito** — não existe entrega fracionada; reduza o trecho ou aumente a
capacidade.

### 5.2 Roteirização CPP

- **Camada de trechos de via (Linhas)** — a malha a varrer.
- **Campo de setor de coleta (opcional)** — aponte para `collection_sector_id` para
  resolver **um circuito por setor**. Vazio, a camada inteira é tratada como um setor
  único.
- **Tolerância de nó (m)** — padrão `0,01` m, como em 4.2.

Saída: vias com `route_visit_order`, `route_sector_id` e `route_is_deadhead` — as
passagens improdutivas aparecem como feições duplicadas marcadas com `True`.

### 5.3 Roteirização RPP

Mesmos campos do CPP, mais um:

- **Campo de via obrigatória (opcional)** — campo booleano ou numérico (`1`/`True`) que
  marca os trechos com coleta obrigatória. **Deixando vazio, todas as vias são tratadas
  como obrigatórias** e o resultado equivale ao CPP — o campo é justamente o que
  distingue os dois.

Saída: vias com `route_visit_order`, `route_sector_id` e `route_is_connector` (`True`
nos trechos percorridos sem coleta).

### 5.4 Roteirização CARP

- **Camada de trechos de via (Linhas)** e **Campo de demanda de resíduos (kg)** —
  obrigatório; aponte para `waste_kg_day`.
- **Campo de via obrigatória (opcional)** — como no RPP.
- **Camada de ponto do depósito/aterro (Pontos)** — obrigatória, com **uma feição**. É o
  ponto de partida e de retorno de cada viagem.
- **Capacidade do veículo** — padrão `10,0`. **Na mesma unidade do campo de demanda**: se
  a demanda está em kg (caso de `waste_kg_day`), um caminhão de 10 t é `10000`, não
  `10`. Esse parâmetro define quantas viagens saem por setor — capacidade menor gera mais
  viagens, mais idas ao aterro e mais deadhead.
- **Campo de setor de coleta (opcional)** e **Tolerância de nó (m)** — como no CPP.

Saída: vias com `route_id`, `route_visit_order`, `route_sector_id`,
`route_is_deadhead`, `route_load_kg` e `route_distance_km`.

---

## 6. Aba **Frota** — quantos caminhões

Empacota as rotas em jornadas de trabalho: calcula a duração de cada rota, ordena por
duração decrescente e aloca a veículos sem estourar o turno.

- **Camada de rotas de coleta (Linhas)** e **Campo ID da rota** — obrigatórios;
  tipicamente a saída do CARP e o campo `route_id`.
- **Campo de setor de coleta (opcional)** — `route_sector_id`, para dimensionar a frota
  setor a setor em vez de para a cidade inteira.
- **Velocidade média de coleta (km/h)** — padrão `10,0`. É a velocidade **durante o
  recolhimento**, com paradas — não a velocidade de tráfego da via. Valores realistas de
  coleta porta a porta ficam bem abaixo dos 20 km/h.
- **Duração da jornada de trabalho (horas)** — padrão `8,0`. É o teto por veículo: a
  soma das rotas alocadas a um caminhão nunca ultrapassa esse valor. É o parâmetro mais
  sensível do dimensionamento — encolher a jornada de 8 h para 6 h pode adicionar um
  caminhão inteiro ao setor.
- **Tempo de descarga por rota (horas)** — padrão `0,5`. Tempo parado no aterro ou
  transbordo, por viagem.
- **Tempo de deslocamento ao destino por rota (horas)** — padrão `0,5`. Ida e volta entre
  o setor e o destino, por viagem. Some os dois: cada viagem custa 1 h de tempo
  improdutivo antes mesmo de coletar — é por isso que capacidade de veículo e distância
  ao aterro pesam tanto no total.

O botão **Executar Dimensionamento de Frota** adiciona uma tabela com `sector_id`,
`fleet_size`, `num_routes`, `total_route_time_h` e `avg_utilization`.

---

## 7. Aba **Indicadores** — medir o resultado

### 7.1 Razão de deadhead

- **Camada de rotas/vias de coleta (Linhas)** e **Campo indicador de
  deadhead/improdutivo** — obrigatórios; use `route_is_deadhead` da saída do CPP ou do
  CARP.
- **Campo de identificação da rota/setor (opcional)** — quebra o resultado por rota; sem
  ele, sai só o total.

Saída: tabela com `route_id`, `productive_km`, `deadhead_km` e `deadhead_ratio`.

### 7.2 Equilíbrio entre setores

- **Camada de rotas de coleta (Linhas)** e **Campo de carga da rota (kg)** —
  obrigatórios (`route_load_kg`).
- **Campo de distância da rota em km (opcional)** — `route_distance_km`; sem ele, o
  tempo é derivado da geometria.
- **Campo ID da rota (opcional)** e **Campo de setor de coleta (opcional)** — o
  agrupamento da estatística.
- **Velocidade média de coleta (km/h)** (padrão `10,0`), **Tempo de descarga por rota
  (horas)** e **Tempo de deslocamento ao destino por rota (horas)** — os dois últimos com
  padrão `0,0` aqui, ao contrário da aba *Frota*. Para que os tempos das duas abas sejam
  comparáveis, **repita os mesmos valores** que você usou no dimensionamento.

Saída: tabela com média, desvio-padrão, mínimo, máximo e coeficiente de variação de
carga e de tempo por setor.

### 7.3 Distância ao destino

- **Camada de rede viária (Linhas)**, **Camada de destinos de resíduos (Pontos)** e
  **Camada de setores/origens de coleta (Pontos ou Polígonos)** — obrigatórias.
- **Critério de custo** — *Distância* (km) ou *Tempo de viagem* (min).

Saída: a camada de setores com o campo `dist_destino`, referente ao destino **mais
próximo** de cada setor.

### 7.4 Cobertura por frequência

Compara o que **deveria** ser coletado com o que a rota de fato cobre.

- **Camada de vias exigidas (faixa de frequência) (Linhas)** — o subconjunto da malha
  que exige atendimento naquela frequência.
- **Camada de rota coberta (Linhas)** — a rota gerada (CPP, RPP ou CARP).
- **Campo indicador de deadhead/conector (opcional)** — `route_is_deadhead` ou
  `route_is_connector`: os trechos marcados são **descontados** da extensão coberta,
  porque foram percorridos sem coletar.
- **Campos de setor** das duas camadas (opcionais) — para o cálculo por setor.
- **Rótulo de frequência de coleta** — texto livre, padrão `Diária`. Só rotula a saída;
  use-o para distinguir as tabelas de cada faixa (`Diária`, `3x/semana`) ao rodar o
  cálculo mais de uma vez.

Saída: tabela com `sector_id`, `frequency_label`, `required_km`, `covered_km` e
`coverage_pct`.

---

## 8. Como interpretar cada indicador

| Indicador | Unidade | Leitura |
|---|---|---|
| **`waste_kg_day`** (camada) | kg/dia | Massa gerada por trecho de via. É a superfície de demanda do projeto: onde a rota rende mais tonelada por quilômetro. Depende linearmente da taxa per capita — mudar o parâmetro reescala o mapa inteiro, sem alterar o padrão espacial. |
| **`collection_sector_id`** (camada) | ID | O setor de coleta atribuído a cada trecho. Confira visualmente **contiguidade** (setor sem ilhas soltas) e **compacidade** (setor sem tentáculos): setores mal formados encarecem o deslocamento mesmo quando a carga está equilibrada. |
| **`route_visit_order`** (camada) | sequência | A ordem em que o caminhão percorre os trechos. Serve para exportar o roteiro da equipe e para animar/conferir o itinerário. |
| **`route_is_deadhead`** / **`route_is_connector`** (camada) | booleano | Marca o trecho percorrido **sem coletar**. Mapeados juntos, mostram onde o itinerário desperdiça quilometragem — quase sempre em becos sem saída e em barreiras da malha. |
| **`route_load_kg`** / **`route_distance_km`** (camada) | kg / km | Carga e extensão de cada viagem do CARP. Carga muito abaixo da capacidade em várias viagens indica capacidade mal informada ou setor pequeno demais para o veículo. |
| **`fleet_size`** | nº de veículos | Quantos caminhões o setor exige na jornada informada. É o número que fecha o projeto — leia sempre junto de `avg_utilization`. |
| **`avg_utilization`** | 0,0 a 1,0 | Fração média da jornada efetivamente usada. Perto de `1,0`, frota bem aproveitada e sem folga para imprevisto; valores baixos (ex.: `0,4`) denunciam um caminhão a mais que o necessário — sinal de que vale refazer a setorização com menos setores, ou rever a capacidade do veículo. |
| **`total_route_time_h`** | horas | Tempo total de rota do setor. Dividido pela jornada, dá o piso teórico da frota; a diferença para o `fleet_size` é a perda do empacotamento (rotas que não cabem juntas). |
| **`deadhead_ratio`** | razão | Km improdutivos ÷ km produtivos. Quanto menor, melhor. Valores altos apontam para setor mal desenhado, excesso de becos sem saída, ou distância grande demais ao aterro — compare entre setores antes de comparar com referências externas, porque o valor depende da malha. |
| **`cv_load`** / **`cv_time`** | coeficiente de variação | Dispersão da carga e do tempo entre as rotas do setor. Perto de `0`, equipes com serviço equivalente; valores altos significam que alguém termina cedo e alguém vira o turno — é o gatilho para voltar à setorização (4.2) e aumentar as iterações de rebalanceamento. |
| **`dist_destino`** (camada) | km ou min | Custo até o aterro/transbordo mais próximo, na unidade do critério escolhido. Os setores no topo dessa lista são os que mais ganham com uma **estação de transbordo** — o dimensionamento de onde colocá-la é [localização de instalações](../algoritmos/localizacao.md). |
| **`coverage_pct`** | % | Extensão coberta ÷ extensão exigida. `100` significa serviço completo naquela frequência; abaixo de **80%** o algoritmo já emite alerta no log do Processing. Leia sempre junto do `frequency_label`: cobertura de 100% na faixa diária nada diz sobre a faixa de 3x/semana. |

---

## 9. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Por favor, selecione todas as camadas e campos necessários para a estimativa de geração." | Falta uma das cinco entradas obrigatórias da aba *Geração* — inclusive o campo de setor **na camada de vias**. |
| "Por favor, selecione a camada de vias, o campo de demanda e a camada do depósito para a roteirização CARP." | O CARP exige demanda **e** depósito; os demais campos são opcionais. |
| "QGIS Processing não está disponível no ambiente atual." | O painel foi instanciado fora de uma sessão do QGIS Desktop. |
| O RPP devolve o mesmo resultado do CPP | **Campo de via obrigatória** vazio — sem ele todas as vias são obrigatórias. |
| Erro do CARP sobre demanda maior que a capacidade | Um trecho isolado gera mais que o caminhão comporta. Não há entrega fracionada: subdivida o trecho ou aumente a capacidade. |
| Frota absurdamente grande, ou `avg_utilization` muito baixa | Capacidade do veículo em unidade diferente da do campo de demanda (t contra kg), ou velocidade média de coleta irreal. |
| Rota fragmentada, com setores desconexos | Tolerância de nó incompatível com a malha, ou camada em EPSG:4674 em vez de CRS métrico. |
| A cobertura fica muito abaixo de 100% sem motivo aparente | Campo de deadhead/conector não informado (trechos improdutivos contando como cobertos, e não o contrário), ou campos de setor de setores diferentes nas duas camadas. |
| O painel de resultados perdeu a rodada anterior | Comportamento normal: cada botão limpa o painel antes de executar. |
