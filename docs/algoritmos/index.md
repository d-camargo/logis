# Algoritmos de Processamento

O plugin **logis** expõe todas as suas funcionalidades analíticas e de otimização como **algoritmos nativos do QGIS Processing**. Isso permite que qualquer função do plugin seja executada através da interface gráfica (Caixa de Ferramentas / Processing Toolbox), em scripts via Console Python ou integrada em modelos do Modelador Gráfico do QGIS.

---

## Como o Provider `logis` aparece no QGIS

Ao carregar o plugin `logis` no QGIS, o provedor de processamento **`logis`** é registrado automaticamente na **Caixa de Ferramentas de Processamento** (Processing Toolbox, atalho `Ctrl+Alt+T`).

O provedor aparece sob o nome **`logis — suporte a projetos de logística no Brasil`** (identificador `logis`), organizado nos seguintes 5 grupos funcionais:

1. **Indicadores Urbanos** — métricas de estrutura viária, acessibilidade, densidade e restrição de carga na escala municipal.
2. **Indicadores Regionais** — densidade rodoviária, percentual de pavimentação/duplicação e pontes/arcos críticos na malha estadual/nacional.
3. **Localização de Instalações** — modelos de otimização para alocação de facilidades ($p$-mediana, MCLP, LSCP).
4. **Roteirização** — problemas de roteirização de veículos por nós (CVRP).
5. **Logística Especializada — Coleta de Lixo** — estimativa de geração, setorização, roteirização por arcos (CPP, RPP, CARP), dimensionamento de frota e indicadores operacionais de resíduos sólidos.

---

## Execução via Console Python (`processing.run`)

Todos os algoritmos do `logis` seguem o padrão `logis:<id_do_algoritmo>` e podem ser invocados programmaticamente no Console Python do QGIS ou em scripts externos.

### Exemplo 1: Cálculo de Densidade de Rede Viária Urbana

```python
import processing

# Executa a densidade viária urbana sobre setores censitários
resultado = processing.run("logis:urban_network_density", {
    'INPUT_NETWORK': '/caminho/para/rede_urbana.gpkg|layername=rede_links',
    'INPUT_ZONES': '/caminho/para/setores.gpkg|layername=setores',
    'OUTPUT_ZONES': 'memory:densidade_urbana'
})

# Camada resultante disponível em resultado['OUTPUT_ZONES']
camada_saida = resultado['OUTPUT_ZONES']
```

### Exemplo 2: Localização p-Mediana (Teitz-Bart)

```python
import processing

resultado = processing.run("logis:facility_p_median", {
    'INPUT_DEMAND': 'memory:setores_demanda',
    'DEMAND_FIELD': 'populacao',
    'INPUT_CANDIDATES': 'memory:candidatos_cd',
    'INPUT_NETWORK': 'memory:rede_links',
    'NUM_FACILITIES': 3,
    'OUTPUT_FACILITIES': 'memory:hubs_selecionados',
    'OUTPUT_ASSIGNMENT': 'memory:alocacao_demanda'
})
```

---

## Convenção de CRS (Sistemas de Referência de Coordenadas)

Para garantir precisão em cálculos espaciais de distância, área e tempo de viagem, o plugin `logis` adota uma convenção rigorosa de CRS:

1. **Camadas de Entrada e Saída (EPSG:4674 - SIRGAS 2000):**
   - As camadas geográficas de entrada são esperadas em **EPSG:4674** (SIRGAS 2000 em coordenadas geográficas) ou reprojetadas automaticamente no carregamento.
   - As camadas geradas pelos algoritmos são entregues no padrão geográfico **EPSG:4674**.

2. **Cálculos Internos em CRS Métrico:**
   - Todo cálculo de comprimento de via (m/km), área de setor ($m^2$/$km^2$), velocidade, tempo de viagem e matriz de distâncias (Dijkstra) é realizado automaticamente em um **CRS projetado métrico** adequado.
   - O algoritmo detecta o CRS métrico apropriado com base na localização geográfica dos dados (UTM da zona correspondente ou Policônica EPSG:5880 para análises nacionais/estaduais).
   - O resultado geométrico final é convertido de volta para **EPSG:4674** antes de ser salvo na camada de saída.

---

## Catálogo de Algoritmos (25 Algoritmos)

A tabela abaixo lista os 25 algoritmos registrados no provedor `logis`, classificados por grupo, com link para a página explicativa da família de algoritmos:

| ID do Algoritmo | Grupo no Processing | Descrição | Família |
|---|---|---|---|
| `logis:urban_network_density` | Indicadores Urbanos | Calcula a densidade de rede viária (km de via / km²) por setor censitário ou grade. | [Logística Urbana](urbano.md) |
| `logis:urban_network_connectivity` | Indicadores Urbanos | Avalia a conectividade da malha urbana (índices α, β, γ, % de interseções e becos). | [Logística Urbana](urbano.md) |
| `logis:urban_mean_circuity` | Indicadores Urbanos | Calcula a circuidade média da rede viária urbana (razão distância na rede / euclidiana). | [Logística Urbana](urbano.md) |
| `logis:urban_cargo_restriction` | Indicadores Urbanos | Avalia o índice de restrição de circulação de veículos de carga na malha viária urbana. | [Logística Urbana](urbano.md) |
| `logis:urban_demand_density` | Indicadores Urbanos | Calcula a densidade de demanda urbana (população ou domicílios / km²) por setor. | [Logística Urbana](urbano.md) |
| `logis:urban_gravity_accessibility` | Indicadores Urbanos | Calcula o índice de acessibilidade gravitacional da demanda em relação a POIs. | [Logística Urbana](urbano.md) |
| `logis:urban_edge_betweenness` | Indicadores Urbanos | Estima a centralidade de intermediação de arestas (betweenness) por amostragem de pares OD. | [Logística Urbana](urbano.md) |
| `logis:urban_delivery_distance` | Indicadores Urbanos | Calcula a distância e tempo médio de entrega das zonas até depósitos mais próximos. | [Logística Urbana](urbano.md) |
| `logis:regional_network_density` | Indicadores Regionais | Calcula a densidade da malha rodoviária regional por município ou estado. | [Logística Regional](regional.md) |
| `logis:regional_pavement_percentage` | Indicadores Regionais | Calcula o percentual de pavimentação e duplicação da malha rodoviária regional. | [Logística Regional](regional.md) |
| `logis:regional_critical_links` | Indicadores Regionais | Identifica pontes e arcos críticos (cut links) na rede rodoviária regional. | [Logística Regional](regional.md) |
| `logis:facility_p_median` | Localização de Instalações | Resolve a localização p-mediana minimizando a distância ponderada pela demanda. | [Localização de Instalações](localizacao.md) |
| `logis:facility_mclp` | Localização de Instalações | Resolve a localização de cobertura máxima (MCLP) dado um raio limite e número de hubs. | [Localização de Instalações](localizacao.md) |
| `logis:facility_lscp` | Localização de Instalações | Resolve a cobertura de conjuntos (LSCP) determinando a menor quantidade de instalações. | [Localização de Instalações](localizacao.md) |
| `logis:vrp_cvrp` | Roteirização | Resolve a Roteirização de Veículos Capacitados por nós (CVRP via Clarke-Wright + 2-opt). | [Roteirização](roteirizacao.md) |
| `logis:waste_generation_estimate` | Logística Especializada — Coleta de Lixo | Estima a geração de resíduos sólidos (kg/dia ou t/dia) por trecho de via. | [Coleta de Resíduos](residuos.md) |
| `logis:waste_districting` | Logística Especializada — Coleta de Lixo | Realiza a setorização espacial (districting) balanceada para coleta de resíduos sólidos. | [Coleta de Resíduos](residuos.md) |
| `logis:waste_cpp_route` | Logística Especializada — Coleta de Lixo | Roteirização por arcos não direcionados para todas as vias (Chinese Postman Problem - CPP). | [Coleta de Resíduos](residuos.md) |
| `logis:waste_rpp_route` | Logística Especializada — Coleta de Lixo | Roteirização por arcos para subconjunto de vias requeridas (Rural Postman Problem - RPP). | [Coleta de Resíduos](residuos.md) |
| `logis:waste_carp_route` | Logística Especializada — Coleta de Lixo | Roteirização por arcos capacitada com frota de caminhões (Capacitated Arc Routing - CARP). | [Coleta de Resíduos](residuos.md) |
| `logis:waste_fleet_sizing` | Logística Especializada — Coleta de Lixo | Dimensiona a frota de veículos e quantidade de viagens necessárias para a coleta. | [Coleta de Resíduos](residuos.md) |
| `logis:waste_deadhead_ratio` | Logística Especializada — Coleta de Lixo | Calcula a razão de deadhead (km improdutivos / km produtivos) por rota de coleta. | [Coleta de Resíduos](residuos.md) |
| `logis:waste_sector_balance` | Logística Especializada — Coleta de Lixo | Avalia o equilíbrio e desvio relativo de carga (t) e tempo entre setores/rotas de coleta. | [Coleta de Resíduos](residuos.md) |
| `logis:waste_destination_distance` | Logística Especializada — Coleta de Lixo | Calcula a distância e tempo de viagem dos setores até destinos (aterro/transbordo). | [Coleta de Resíduos](residuos.md) |
| `logis:waste_collection_coverage` | Logística Especializada — Coleta de Lixo | Calcula o percentual e extensão de vias cobertas por frequência de coleta de resíduos. | [Coleta de Resíduos](residuos.md) |

---

> **Nota:** Para detalhes sobre parâmetros, entradas e saídas de cada algoritmo específico, consulte a página da respectiva família de algoritmos.
