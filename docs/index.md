# logis

*Um complemento (plugin) do QGIS para apoiar projetos de logística no Brasil.*

O **logis** leva para dentro do QGIS o ferramental de análise de redes, roteirização e localização de instalações aplicado à realidade brasileira, usando bases públicas nacionais (OSM, DNIT/SNV, IBGE/geobr) e operando inteiramente dentro do ambiente do QGIS.

## Os três módulos

| Módulo | Escopo | Rede base |
|---|---|---|
| **Logística Urbana** | Cidade / município | Rede viária OSM tratada (pipeline derivado do GisBR) |
| **Logística Regional** | Estado / país | Bases nacionais (DNIT/SNV, geobr) + bases estaduais (ex.: IDE-Sisema/MG) |
| **Logística Especializada** | Serviços urbanos com roteirização por arcos — caso inicial: coleta de lixo | Rede urbana do módulo Urbano |

## As três camadas

Cada módulo entrega três camadas de funcionalidade:

1. **Indicadores** — métricas calculadas sobre a rede e sobre dados demográficos/econômicos.
2. **Roteirização** — VRP/TSP (por nós) e Arc Routing (por arestas, no módulo especializado).
3. **Localização de instalações** (*facility location*) — p-mediana, p-centro, cobertura máxima (MCLP) e cobertura de conjuntos (LSCP), para posicionar CDs, hubs, garagens, ecopontos e estações de transbordo.

## Zero dependências obrigatórias

O logis roda apenas com **PyQGIS + a biblioteca padrão do Python**. Nada de `networkx`, `igraph` ou `OSMnx`: grafos e caminhos mínimos usam as classes nativas `QgsGraph`, `QgsGraphBuilder` e `QgsGraphAnalyzer`, e as heurísticas de otimização (Clarke-Wright savings, sweep, 2-opt/or-opt, Teitz-Bart, matching guloso, Hierholzer) são implementadas em Python puro.

Duas bibliotecas externas são aceitas como **opcionais** — o plugin funciona normalmente sem elas:

- `pyarrow` — fallback de leitura de Parquet quando o driver GDAL correspondente não estiver disponível.
- `OR-Tools` — backend opcional de otimização, com import *lazy* e fallback automático para a heurística em Python puro.

Os dados são entregues em SIRGAS 2000 / EPSG:4674, com reprojeção para CRS métrico apenas nos cálculos intermediários de distância e tempo.

## Estado do projeto

| | |
|---|---|
| **Versão** | 0.1.5 |
| **Estado** | `experimental` |
| **Licença** | GPL-3.0 |
| **QGIS** | 3.16 ou superior (compatível com Qt6 / QGIS 4) |

Por ser marcado como `experimental`, é preciso habilitar a exibição de plugins experimentais no Gerenciador de Complementos do QGIS para vê-lo e instalá-lo — o [Guia de Instalação](guias/instalacao.md) detalha o procedimento.

## Por onde começar

| Seção | O que você encontra |
|---|---|
| [**Instalação**](guias/instalacao.md) | Como instalar o plugin no QGIS e, opcionalmente, habilitar o backend OR-Tools. |
| [**Guias**](guias/urbano.md) | Fluxos de trabalho ponta a ponta: [Logística Urbana](guias/urbano.md), [Logística Regional](guias/regional.md) e [Coleta de Lixo](guias/residuos.md). |
| [**Algoritmos**](algoritmos/index.md) | Referência técnica das rotinas: [Visão geral](algoritmos/index.md), [Indicadores Urbanos](algoritmos/urbano.md), [Indicadores Regionais](algoritmos/regional.md), [Roteirização](algoritmos/roteirizacao.md), [Localização de Instalações](algoritmos/localizacao.md) e [Coleta de Resíduos](algoritmos/residuos.md). |

---

Para a motivação e o contexto do projeto, veja [Sobre o logis](sobre.md). Para a procedência das bases de dados usadas, veja a [Referência de Fontes de Dados](referencia/fontes_dados.md).
