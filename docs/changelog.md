# Histórico de Versões

Este documento registra as principais alterações e evoluções do plugin **logis** organizadas por versão.

## 0.1.10 - 2026-09-10

- **Caixeiro Viajante (TSP)** — novo algoritmo `logis:vrp_tsp`, que recebe a camada de pontos a visitar, a camada do ponto inicial e, opcionalmente, a do ponto final, e devolve a ordem de visita na tabela de atributos (`visit_seq`) mais a camada de trechos, que separa os deslocamentos improdutivos de acesso e retorno dos trechos de rota.
- **Painel de Roteirização** — nova entrada **Roteirização** no menu `logis`, com o painel que executa o TSP e publica as camadas no projeto.
- **Ação de Documentação na Interface**: Novo item "Documentação" no menu do plugin para abrir a documentação oficial no navegador.
- **Integração de Changelog no Empacotamento**: Configuração de `changelog_path` em `.qgis-plugin-ci` e injeção do changelog no `metadata.txt`.
- **Testes de Empacotamento**: Adição da suíte `test_packaging.py` para validação de changelog, metadata e links de documentação.

## 0.1.9 - 2026-08-26

- **Enums Escopados em Todo o Pacote**: os 40 acessos remanescentes a enums não escopados — `QgsFeatureSink`, `QgsProcessingParameterField`, `QgsVectorLayerDirector` e `QNetworkReply` — passam a usar o namespace completo (`QgsFeatureSink.Flag.FastInsert`, `QgsProcessingParameterField.DataType.*`, `QgsVectorLayerDirector.Direction.*` e `QNetworkReply.NetworkError.*`), requisito do PyQt6/QGIS 4; sem mudança de comportamento no QGIS 3.
- **Guarda Automatizada de Compatibilidade**: `test_qt6_compat.py` passa a reprovar essas quatro famílias de enum, de modo que a forma antiga não volte em código novo.

## 0.1.8 - 2026-08-22

- **Instalação de Dependências por Comando**: O Gerenciador de Dependências deixa de executar o `pip` diretamente via subprocesso e passa a gerar e exibir o comando exato formatado para o interpretador do QGIS, com cópia em um clique para execução no terminal.
- **Conformidade de Segurança e Subprocessos**: Remoção completa de chamadas ao módulo `subprocess` no repositório do plugin para eliminar riscos de execução arbitrária e alertas em scanners de segurança de plugins do QGIS.

## 0.1.7 - 2026-08-22

- **Amostragem Determinística**: O gerador `logis.core.sampling.DeterministicRandom` (SplitMix64 em Python puro) substitui o `random` da biblioteca padrão, tornando a circuidade média e a centralidade de intermediação reprodutíveis para a mesma camada e os mesmos parâmetros.
- **Chave de Cache em SHA-256**: A assinatura do cache da matriz OD passa de MD5 para SHA-256; os arquivos de cache gravados por versões anteriores deixam de ser encontrados e são recalculados na primeira execução.
- **Instalador do OR-Tools Endurecido**: As versões de dependência são validadas antes de entrar na linha de comando do `pip`, e o comando é conferido antes de ser executado.

## 0.1.6 - 2026-08-22

- **Interface Sem Diálogos Modais**: Transição de `.exec()` para `.show()` na caixa de diálogo de dependências para compatibilidade total com PyQt6/QGIS 4 e remoção de chamadas modais/bloqueantes.
- **Conformidade e Regras de Segurança**: Atualização em `test_plugin.py` e `test_security_scan.py` para reforçar a varredura contra chamadas `exec()` em todo o repositório.

## 0.1.5 - 2026-08-05

- **Ajuste Dinâmico de Dependências (OR-Tools)**: Atualização na estratégia de verificação e instalação do backend OR-Tools, adequando a trava de dependências (`numpy`, `pandas`, `typing_extensions`) ao ambiente Python ativo no QGIS.
- **Governança e Limpeza do Repositório**: Consolidação da documentação de regras em `GEMINI.md` e remoção de arquivos temporários de planejamento do repositório público.

## 0.1.4 - 2026-07-30

- **Ajustes de Interface Urbana**: Refinamento no leiaute em abas do painel de Logística Urbana.
- **Atualização da Documentação**: Expansão e sincronização dos manuais e guias de uso da documentação.

## 0.1.3 - 2026-07-30

- **Organização do Painel Urbano**: Estruturação dos controles e parâmetros do dock de Logística Urbana em abas temáticas para otimizar o fluxo de trabalho.

## 0.1.2 - 2026-07-29

- **Usabilidade da Interface**: Adição de barras de rolagem (`QScrollArea`) e navegação por abas nos painéis acopláveis (*dock widgets*) dos módulos.

## 0.1.1 - 2026-07-29

- **Compatibilidade Qt6 e QGIS 4**: Adaptações na camada de compatibilidade `core/qgis_compat.py` e escopagem de enums (`Qt.DockWidgetArea`, `QgsProcessing.SourceType`, etc.) para garantir execução compatível tanto com QGIS 3 quanto com QGIS 4.

## 0.1.0 - 2026-07-23

- **Lançamento Inicial**:
  - **Módulo Urbano**: Leitura e tratamento de redes OSM, construção de grafos `QgsGraph`, matrizes OD com cache em disco e indicadores de rede, demografia e acessibilidade.
  - **Módulo Regional**: Leitura da malha SNV (DNIT) e IDEs estaduais, com suporte a indicadores de acessibilidade regional.
  - **Roteirização por Nós (VRP)**: Roteirização CVRP com heurística Clarke-Wright savings, refinamento 2-opt e backend opcional OR-Tools.
  - **Módulo de Coleta de Resíduos**: Estimativa de geração de resíduos, setorização de coleta, roteirização por arcos (CPP, RPP, CARP), dimensionamento de frota e indicadores operacionais.
  - **Localização de Instalações**: Algoritmos para p-mediana (Teitz-Bart), MCLP e LSCP.
  - **Infraestrutura**: Suporte a internacionalização (PT-BR/EN), arquitetura de Processing Provider e empacotamento com `qgis-plugin-ci`.
