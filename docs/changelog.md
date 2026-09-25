# Histórico de Versões

Este documento registra as principais alterações e evoluções do plugin **logis** organizadas por versão.

## 0.6.3 - 2026-09-25

- **TSP e CVRP: transformação de SRC que não fazia nada** — no Windows/QGIS 4 os pontos continuavam em graus e o modo Rede falhava com "Forward transform … of bounding box failed"; agora toda transformação é conferida, com fallback para UTM SIRGAS da zona e diagnóstico (SRC, ponto de prova, versões do QGIS e do PROJ) no log.
- **Saídas do TSP e do CVRP em SIRGAS 2000 (EPSG:4674)** — antes saíam em EPSG:5880 e podiam não aparecer no mapa; as distâncias nos atributos continuam em metros.

## 0.6.2 - 2026-09-25

- **TSP e CVRP em modo Rede com pontos sem SRC** — pontos com SRC indefinido não eram reprojetados e o grafo falhava com "Forward transform … of bounding box failed"; agora o SRC é conferido, o log mostra origem e destino, e a mensagem final traz a causa do erro.

## 0.6.1 - 2026-09-25

- **Progresso e Log ao Vivo na Rede Viária** — barra de progresso e log ao vivo durante o download da rede viária (OSM e SNV) no painel Rede Viária, que antes deixava o QGIS congelado sem retorno.
- **Correção no TSP e CVRP** — o cálculo não iniciava (erro `QgsProcessingAlgRunnerTask(): argument 1 has unexpected type 'str'`) e o painel de Roteirização ficava travado com os botões desabilitados; agora qualquer falha mostra o erro no painel e restaura botões e barra.

## 0.6.0 - 2026-09-24

- **Rede Viária Municipal via GisBR** — integração com `gisbr:osm_network` quando o GisBR 0.11+ está instalado (com pipeline interno como fallback).
- **Linha de Fonte da Rede no Painel** — exibição da linha de fonte da rede viária no painel.
- **Listagem de Municípios via GisBR** — listagem de municípios via `gisbr:read_municipality`.
- **Correção no Código IBGE** — tratamento de códigos IBGE com sufixo `.0` que travavam o download.

## 0.5.0 - 2026-09-21

- **Execução Assíncrona no Gerenciador de Tarefas** — execução de TSP e CVRP fora da thread da UI pelo gerenciador de tarefas do QGIS.
- **Controles no Painel** — barra de progresso e botão Cancelar integrados ao painel de Roteirização.
- **Progresso por Etapa e Cancelamento Cooperativo** — acompanhamento de progresso por etapa (grafo, matriz OD, solver e saídas) e cancelamento cooperativo em ambos os backends.
- **Saídas Gravadas no GeoPackage** — gravação das camadas de resultado diretamente no GeoPackage da rede de entrada com nomes padronizados (`TSP-rede_…`/`TSP-euclidiana_…`/`CVRP-…`) e sufixo `_pontos`.
- **Relatório Consolidado** — inclusão da descrição da busca local, tempo de cálculo e unidade explicitada em metros no relatório de resultados.

## 0.4.0 - 2026-09-20

- **Seletor de Backend no CVRP** — parâmetro `BACKEND` no algoritmo `logis:vrp_cvrp` e seletor de backend de otimização na aba CVRP do painel de Roteirização.
- **Mudança de Comportamento no CVRP** — no modo "Automático", a roteirização CVRP agora utiliza OR-Tools por padrão quando disponível no ambiente.
- **Fallback Consistente do OR-Tools** — tratamento gracioso de falhas com fallback automático para heurísticas em Python puro em TSP e CVRP.
- **Rastro de Crashes no CVRP** — captura e exibição de rastro de diagnósticos e exceções durante a solução do CVRP.
- **Correção nos Textos do OR-Tools** — o diálogo de Dependências e a documentação não atribuem mais a localização de instalações ao OR-Tools: o pacote é apresentado apenas como backend de roteirização (TSP/CVRP), com a localização de instalações executada em Python puro por projeto.

## 0.3.0 - 2026-09-19

- **Rastro de Diagnóstico** — captura e exibição de rastro detalhado de diagnóstico para apoio à depuração em rotinas do plugin.
- **Trava do OR-Tools e Seletor de Backend** — introdução de trava de segurança do OR-Tools, seletor de backend de otimização na interface e opção de rearme.
- **Janela de Construção do Grafo** — melhorias e ajustes no cálculo e progresso durante a construção do grafo da rede viária.
- **Assinatura Barata de Cache** — otimização da validação de cache da matriz OD via assinatura simplificada e eficiente.
- **Tratamento de Geometrias Multipart** — suporte robusto ao processamento e conversão de feições multipartes em rotinas de rede.

## 0.2.0 - 2026-09-19

- **Painel Rede Viária** — painel acoplável **Rede Viária** (com entrada no menu `logis`) organizado em abas de município (OSM) e de estado (SNV/DNIT).
- **Algoritmos de Carga de Rede** — novos algoritmos `logis:load_osm_network` e `logis:load_snv_network` no grupo "Dados" da caixa de ferramentas do QGIS.
- **Seleção UF → Município** — lista UF → município para não precisar decorar código IBGE.
- **Cache Local de Downloads** — armazenamento automático dos downloads de redes em `QStandardPaths.CacheLocation/logis/` para evitar requisições repetidas.

## 0.1.12 - 2026-09-14

- **Modo de Cálculo de Distância no TSP** — adição do seletor "Modo de cálculo da distância" na aba TSP (linha reta por padrão, pela rede viária como opção).
- **Atributos de Trechos e Painel de Resultados** — novos campos `dist_mode` e `leg_geom` na camada de trechos e exibição do modo utilizado no painel de resultados.
- **Guardas de Segurança na Roteirização pela Rede** — inclusão de guardas de amarração à rede viária e de tratamento para pares inalcançáveis no cálculo de distância.

## 0.1.11 - 2026-09-13

- **Instalação do OR-Tools em um clique** — o Gerenciador de Dependências passa a instalar a biblioteca no Python do próprio QGIS, sem abrir terminal nem executar processo externo.
- **Detecção de ambiente** — o diálogo mostra sistema operacional, versão do Python, interpretador, disponibilidade do pip e restrições (PEP 668, Flatpak/Snap), e usa isso para decidir as opções do pip.
- **Correção do comando no Windows** — o comando exibido passa a apontar para o `python.exe` do QGIS em vez do `qgis-bin.exe`, que não executa o pip.

## 0.1.10 - 2026-09-10

- **Caixeiro Viajante (TSP)** — novo algoritmo `logis:vrp_tsp`, que recebe a camada de pontos a visitar, a camada do ponto inicial e, opcionalmente, a do ponto final, e devolve a ordem de visita na tabela de atributos (`visit_seq`) mais a camada de trechos, que separa os deslocamentos improdutivos de acesso e retorno dos trechos de rota.
- **Painel de Roteirização** — nova entrada **Roteirização** no menu `logis`, com o painel que executa o TSP e publica as camadas no projeto.
- **Aba CVRP no Painel de Roteirização** — o painel passa a ter duas abas, TSP e CVRP, com o seletor de rede viária compartilhado e o painel de resultados único no rodapé; a aba CVRP executa o `logis:vrp_cvrp`, publica as camadas de rotas e de paradas no projeto e resume a carga e a distância de cada rota.
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
