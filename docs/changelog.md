# Histórico de Versões

Este documento registra as principais alterações e evoluções do plugin **logis** organizadas por versão.

## 0.1.5

- **Ajuste Dinâmico de Dependências (OR-Tools)**: Atualização na estratégia de verificação e instalação do backend OR-Tools, adequando a trava de dependências (`numpy`, `pandas`, `typing_extensions`) ao ambiente Python ativo no QGIS.
- **Governança e Limpeza do Repositório**: Consolidação da documentação de regras em `GEMINI.md` e remoção de arquivos temporários de planejamento do repositório público.

## 0.1.4

- **Ajustes de Interface Urbana**: Refinamento no leiaute em abas do painel de Logística Urbana.
- **Atualização da Documentação**: Expansão e sincronização dos manuais e guias de uso da documentação.

## 0.1.3

- **Organização do Painel Urbano**: Estruturação dos controles e parâmetros do dock de Logística Urbana em abas temáticas para otimizar o fluxo de trabalho.

## 0.1.2

- **Usabilidade da Interface**: Adição de barras de rolagem (`QScrollArea`) e navegação por abas nos painéis acopláveis (*dock widgets*) dos módulos.

## 0.1.1

- **Compatibilidade Qt6 e QGIS 4**: Adaptações na camada de compatibilidade `core/qgis_compat.py` e escopagem de enums (`Qt.DockWidgetArea`, `QgsProcessing.SourceType`, etc.) para garantir execução compatível tanto com QGIS 3 quanto com QGIS 4.

## 0.1.0

- **Lançamento Inicial**:
  - **Módulo Urbano**: Leitura e tratamento de redes OSM, construção de grafos `QgsGraph`, matrizes OD com cache em disco e indicadores de rede, demografia e acessibilidade.
  - **Módulo Regional**: Leitura da malha SNV (DNIT) e IDEs estaduais, com suporte a indicadores de acessibilidade regional.
  - **Roteirização por Nós (VRP)**: Roteirização CVRP com heurística Clarke-Wright savings, refinamento 2-opt e backend opcional OR-Tools.
  - **Módulo de Coleta de Resíduos**: Estimativa de geração de resíduos, setorização de coleta, roteirização por arcos (CPP, RPP, CARP), dimensionamento de frota e indicadores operacionais.
  - **Localização de Instalações**: Algoritmos para p-mediana (Teitz-Bart), MCLP e LSCP.
  - **Infraestrutura**: Suporte a internacionalização (PT-BR/EN), arquitetura de Processing Provider e empacotamento com `qgis-plugin-ci`.
