# Guia de Logística Regional

Este guia percorre, passo a passo, o fluxo completo do painel **logis — Indicadores
Regionais**: como obter a malha rodoviária do SNV/DNIT, como definir o escopo da
análise (UF ou recorte menor), como executar os três indicadores regionais e como ler
cada resultado.

Todos os botões do painel são apenas orquestradores: cada um chama um algoritmo
`logis:regional_*` do Processing e escreve o retorno no painel de resultados. A
referência técnica de cada algoritmo (parâmetros, complexidade, bibliografia) está em
[Algoritmos Regionais](../algoritmos/regional.md); aqui o foco é o uso do painel.

---

## 1. Obter a malha rodoviária SNV/DNIT

O painel **não baixa a malha**: ele consome uma camada de linhas já carregada no
projeto. O módulo Regional trabalha sobre a malha rodoviária federal do **SNV/DNIT**
(vintage `snv_202507a`, servida por WFS na INDE) tratada pelo pipeline
`core.network.snv_pipeline`, que faz WFS filtrado por UF → atributos de custo →
GeoPackage.

No **Console Python** do QGIS:

```python
from logis.core.network.snv_pipeline import build_snv_state_network

resultado = build_snv_state_network(
    "MG",                              # sigla da UF
    "/caminho/para/rede_regional.gpkg",
)
print(resultado["metadata"])
```

O que o pipeline faz e entrega:

| Etapa | Resultado |
|---|---|
| Consulta o WFS do DNIT com filtro CQL `sg_uf = '<UF>'` | Resposta cacheada em `snv_<UF>.geojson`, ao lado do GPKG |
| Monta a camada de trechos com atributos de custo | `snv_links_<UF>` (LineString, EPSG:4674) |
| Deduplica os nós de extremidade | `snv_nodes_<UF>` (Point, EPSG:4674) |

A camada de links já vem com os atributos que os algoritmos usam:

| Campo | Conteúdo |
|---|---|
| `id_trecho` | Identificador do trecho na base do DNIT |
| `vl_codigo` | Código SNV do trecho |
| `vl_br` | Número da BR |
| `sg_uf` | Sigla da UF |
| `ds_superfi` | Superfície física (`Pavimentada`, `Duplicada`, `Implantada`, `Terra`, …) |
| `ds_jurisdi` | Jurisdição do trecho (federal, estadual coincidente, …) |
| `oneway` | Sentido de circulação — a malha SNV é tratada como bidirecional (`no`) |
| `length` | Extensão do trecho, em **metros** (do campo oficial `vl_extensa`, em km) |
| `speed` | Velocidade estimada pela superfície, em km/h (de 30 em leito natural a 110 em pista duplicada) |
| `travel_time` | Tempo de percurso do trecho, em **segundos** (`length` ÷ `speed`) |

> A resposta do WFS é reaproveitada do cache em execuções seguintes; se o GeoPackage já
> contiver as duas camadas, elas são devolvidas sem nova consulta (o `metadata` traz
> `"cached": True`). Para forçar um novo download (vintage atualizado, arquivo
> truncado), chame a função com `force=True`.

Depois de gerado o GPKG, arraste `snv_links_<UF>` para o projeto — é essa camada que o
painel vai consumir. O script `tools/pilot_regional_mg.py` mostra o mesmo fluxo
encadeado com o construtor de grafo e a matriz OD, fora do QGIS Desktop.

Bases rodoviárias estaduais (piloto: DER-MG via IDE-Sisema) servem à mesma finalidade,
desde que a camada carregada tenha os campos `length` e `ds_superfi`. As fontes
declaradas estão em [Fontes de Dados](../referencia/fontes_dados.md), e a lista completa
de atributos originais do SNV, em [Schema SNV](../referencia/schema-snv.md).

---

## 2. Definir o escopo da análise

O escopo é definido em **dois lugares que precisam concordar entre si**:

- **A malha** — o pipeline baixa uma UF por vez (`sg_uf = '<UF>'`). Para uma região com
  mais de um estado, gere um GPKG por UF e mescle as camadas de links
  (`native:mergevectorlayers`).
- **A área de referência** — o polígono que entra no cálculo de densidade (limite da
  UF, mesorregião, região de planejamento).

> **Atenção:** o indicador de densidade **soma a extensão de toda a camada de rede**
> selecionada, sem recortá-la pelo polígono de referência. Para analisar um recorte
> menor que a UF — uma mesorregião, por exemplo —, recorte antes a malha pelo polígono
> (`native:clip`) e use a camada recortada no seletor de rede; caso contrário a
> extensão do estado inteiro será dividida pela área da mesorregião.

Os outros dois indicadores (pavimentação e arcos críticos) não usam polígono: eles
descrevem exatamente a camada de rede que estiver selecionada.

---

## 3. Abrir o painel

**Complementos → logis → Indicadores Regionais**. O painel abre ancorado à direita da
janela do QGIS; se for fechado, reabra pela mesma entrada de menu (ou por **Ver →
Painéis**). O conteúdo fica dentro de uma área rolável — em telas baixas, role até o
fim para chegar aos botões e ao painel de resultados.

---

## 4. Os seletores e o painel de resultados

Diferente do painel Urbano, o Regional não tem abas: os três seletores e os três botões
ficam empilhados na mesma coluna.

- **Camada de rede regional (Linhas)** — o seletor lista apenas camadas de linha do
  projeto e é **compartilhado pelos três botões**. Se nenhuma camada estiver
  selecionada, qualquer botão abre um aviso, registra o erro e não executa nada.
- **Camada de área de referência (Polígonos — para Densidade)** — só é usada pelo botão
  de densidade. Sem ela, o cálculo de densidade **não roda** (o painel avisa); os outros
  dois botões ignoram esse seletor.
- **População da área de referência (habitantes)** — campo numérico inteiro, de `1` a
  `2.000.000.000`, com valor inicial `21.000.000` (ordem de grandeza da população de
  MG). **Troque esse valor pela população do seu recorte** — ele não é lido de nenhuma
  camada, e o padrão só existe para o painel abrir preenchido.
- **Resultados dos Indicadores Regionais** — no rodapé, uma área de texto somente
  leitura, em fonte monoespaçada. Erros aparecem em vermelho, com a mensagem do
  algoritmo. Aqui **cada botão limpa o painel antes de escrever**: só o resultado da
  última execução fica visível, então copie os números que quiser comparar antes de
  rodar o próximo indicador.

A única saída que é camada (os trechos com `is_critical_link`) é criada em **memória** e
adicionada automaticamente ao projeto; o painel apenas informa quantos trechos foram
marcados. Salve-a em disco antes de fechar o projeto.

---

## 5. Densidade rodoviária regional

1. Selecione a rede em **Camada de rede regional**.
2. Selecione o recorte territorial em **Camada de área de referência** — a área é
   medida sobre a elipsoide do CRS da camada, somando **todas** as feições do polígono.
3. Informe a **população** do mesmo recorte.
4. Clique em **Calcular Densidade Rodoviária** (`logis:regional_network_density`).

O painel devolve dois números:

- **Densidade por Área**, em km/1.000 km²;
- **Densidade por População**, em km/10.000 hab.

---

## 6. Percentual de pavimentação e duplicação

Clique em **Calcular % Pavimentação** (`logis:regional_pavement_percentage`). Basta a
camada de rede.

O algoritmo classifica cada trecho pelo texto do campo de superfície e pondera **pela
extensão** (`length`): trechos cuja descrição contém `"duplicada"` entram nos dois
percentuais; os que contêm `"pavimentada"`, só no de pavimentação.

> O painel chama o algoritmo com o campo de superfície fixo em **`ds_superfi`**, que é o
> nome usado pelo `snv_pipeline`. Se a sua malha (uma base estadual, por exemplo) nomeia
> a superfície de outra forma, renomeie o campo para `ds_superfi` ou rode o algoritmo
> direto pela **Caixa de Ferramentas de Processamento**, onde o parâmetro *Campo que
> indica o tipo de superfície* é editável.

---

## 7. Pontes e arcos críticos

Clique em **Calcular Pontes/Arcos Críticos** (`logis:regional_critical_links`). Também
basta a camada de rede — é a operação mais cara do painel, porque constrói o grafo da
malha antes de analisá-lo.

O algoritmo monta o `QgsGraph`, deduplica os arcos em arestas físicas únicas e aplica o
algoritmo de Tarjan para achar as pontes do grafo. O painel informa quantos trechos são
críticos de um total, e adiciona ao projeto uma camada de linhas com o campo booleano
`is_critical_link` — filtre por `"is_critical_link" = true` para ver só os trechos
críticos.

---

## 8. Como interpretar cada indicador

| Indicador | Unidade | Leitura |
|---|---|---|
| **Densidade por Área** | km/1.000 km² | Quanto de rodovia existe por território. Mede a capilaridade da malha: valores baixos indicam grandes vazios rodoviários, onde o frete depende de poucos eixos e de longos acessos. Só é comparável entre recortes quando a malha usada é a mesma (só federal, ou federal + estadual). |
| **Densidade por População** | km/10.000 hab. | Quanto de rodovia existe por habitante. Alta densidade demográfica de malha aparece em regiões extensas e pouco povoadas — é o inverso da leitura anterior, e as duas juntas separam "território vazio" de "território mal servido". |
| **Percentual Pavimentada** | % (0 a 100) | Fração da extensão da malha com pista pavimentada (inclui a duplicada). É o indicador de qualidade mais direto: trecho não pavimentado impõe restrição de velocidade, de carga e de sazonalidade (chuva) ao caminhão. |
| **Percentual Duplicada** | % (0 a 100) | Fração da extensão em pista dupla — o subconjunto de alta capacidade da malha. Costuma ser pequeno e concentrado nos eixos troncais; leia junto com o mapa, porque o valor agregado esconde onde a duplicação está. |
| **`is_critical_link`** (camada) | booleano | Trecho cuja remoção **desconecta** o grafo: não existe rota alternativa dentro da malha analisada. São os pontos únicos de falha — pontes, travessias, ligações intermunicipais isoladas — e os candidatos naturais a prioridade de manutenção e a plano de contingência. O total marcado depende do recorte: quanto mais amputada a malha na borda do recorte, mais trechos aparecem como críticos por artefato de corte. |

---

## 9. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Por favor, selecione uma camada de rede regional." | Nenhuma camada de linha no projeto, ou nenhuma escolhida no seletor de rede. |
| "Por favor, selecione uma camada de área de referência." | O botão de densidade foi acionado sem polígono selecionado. |
| "QGIS Processing não está disponível no ambiente atual." | O painel foi instanciado fora de uma sessão do QGIS Desktop. |
| "O campo 'length' não foi encontrado na camada de malha rodoviária." | A camada não veio do `snv_pipeline`. Use `snv_links_<UF>` ou acrescente um campo `length` em metros. |
| "O campo 'ds_superfi' não foi encontrado…" | Malha de outra origem, com nome diferente para a superfície — renomeie o campo ou rode o algoritmo pela Caixa de Ferramentas (ver seção 6). |
| "A área calculada é de 0 km² ou negativa." | Polígono de referência com geometria vazia ou inválida. |
| Densidade absurdamente alta | Malha da UF inteira contra o polígono de um recorte menor — recorte a rede antes (ver seção 2). |
| "O grafo construído está vazio." | Camada de rede sem feições válidas, ou geometrias que não são linhas. |
| O resultado anterior sumiu do painel | Comportamento esperado: cada botão limpa a área de resultados antes de escrever. |
