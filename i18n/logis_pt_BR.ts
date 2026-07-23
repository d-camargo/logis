<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1">
<context>
    <name>FacilityLSCP</name>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="84"/>
        <source>Camada de demanda (Pontos/Polígonos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="91"/>
        <source>Campo de peso da demanda (opcional, default=1.0)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="100"/>
        <source>Camada de instalações candidatas (Pontos/Polígonos) (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="108"/>
        <source>Camada de rede viária (Linhas) (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="116"/>
        <source>Distância/Tempo máximo de cobertura (max_distance)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="125"/>
        <source>Instalações selecionadas</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="131"/>
        <source>Atribuição e cobertura de demandas</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="146"/>
        <source>Camada de demanda inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="149"/>
        <source>A distância máxima deve ser estritamente maior que zero.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="170"/>
        <source>Lendo pontos de demanda...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="195"/>
        <source>Nenhum ponto de demanda válido encontrado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="202"/>
        <source>Lendo instalações candidatas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="218"/>
        <source>Nenhuma instalação candidata válida encontrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="225"/>
        <source>Construindo o grafo e calculando a matriz OD na rede...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="230"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="236"/>
        <source>O grafo construído possui menos de 2 vértices.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="253"/>
        <source>Erro ao calcular a matriz OD: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="255"/>
        <source>Calculando matriz de distâncias euclidianas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="264"/>
        <source>Executando a otimização LSCP (Toregas et al.)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="274"/>
        <source>LSCP concluído. Instalações: {sel} | Totalmente Coberto: {cov} | Não cobertos: {unc}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="375"/>
        <source>Localização de Cobertura de Conjuntos (LSCP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="378"/>
        <source>Localização de Instalações</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_lscp.py" line="384"/>
        <source>Resolve o problema de localização de cobertura de conjuntos (LSCP) utilizando a heurística gulosa de Toregas et al. (1971).

Seleciona o menor número possível de instalações para cobrir todos os pontos de demanda dentro da distância/tempo máximo especificado (max_distance).

Parâmetros:
- Camada de demanda: feições de pontos ou polígonos representando a demanda.
- Campo de peso da demanda: campo numérico indicando a demanda de cada feição (opcional, default=1.0).
- Camada de instalações candidatas: instalações elegíveis (opcional, usa a camada de demanda se omitida).
- Camada de rede viária: rede viária para distâncias reais na rede (opcional, usa distância euclidiana se omitida).
- Distância/Tempo máximo de cobertura: raio ou tempo limite para considerar uma demanda coberta.

Saídas:
- Instalações selecionadas: camada de candidatos escolhidos com total de demanda e pontos cobertos.
- Atribuição e cobertura de demandas: camada de demanda com o status de cobertura (is_covered) e a instalação atribuída.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>FacilityMCLP</name>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="85"/>
        <source>Camada de demanda (Pontos/Polígonos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="92"/>
        <source>Campo de peso da demanda (opcional, default=1.0)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="101"/>
        <source>Camada de instalações candidatas (Pontos/Polígonos) (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="109"/>
        <source>Camada de rede viária (Linhas) (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="117"/>
        <source>Número máximo de instalações (p)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="126"/>
        <source>Distância/Tempo máximo de cobertura (max_distance)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="135"/>
        <source>Instalações selecionadas</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="141"/>
        <source>Atribuição e cobertura de demandas</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="157"/>
        <source>Camada de demanda inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="160"/>
        <source>A distância máxima deve ser estritamente maior que zero.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="181"/>
        <source>Lendo pontos de demanda...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="206"/>
        <source>Nenhum ponto de demanda válido encontrado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="213"/>
        <source>Lendo instalações candidatas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="229"/>
        <source>Nenhuma instalação candidata válida encontrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="232"/>
        <source>O número de instalações p ({p}) excede o número de candidatos ({cand}).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="243"/>
        <source>Construindo o grafo e calculando a matriz OD na rede...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="248"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="254"/>
        <source>O grafo construído possui menos de 2 vértices.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="271"/>
        <source>Erro ao calcular a matriz OD: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="273"/>
        <source>Calculando matriz de distâncias euclidianas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="282"/>
        <source>Executando a otimização MCLP (Church &amp; ReVelle)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="293"/>
        <source>MCLP concluído. Instalações: {sel} | Demanda Coberta: {cov:.2f}/{tot:.2f} ({ratio:.1%})</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="385"/>
        <source>Localização de Cobertura Máxima (MCLP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="388"/>
        <source>Localização de Instalações</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_mclp.py" line="394"/>
        <source>Resolve o problema de localização de cobertura máxima (MCLP) utilizando a heurística gulosa de Church &amp; ReVelle (1974).

Seleciona até p instalações candidatas que maximizem o peso da demanda atendida dentro da distância/tempo máximo especificado (max_distance).

Parâmetros:
- Camada de demanda: feições de pontos ou polígonos representando a demanda.
- Campo de peso da demanda: campo numérico indicando a demanda de cada feição (opcional, default=1.0).
- Camada de instalações candidatas: instalações elegíveis (opcional, usa a camada de demanda se omitida).
- Camada de rede viária: rede viária para distâncias reais na rede (opcional, usa distância euclidiana se omitida).
- Número máximo de instalações (p): quantidade máxima de instalações a selecionar.
- Distância/Tempo máximo de cobertura: raio ou tempo limite para considerar uma demanda coberta.

Saídas:
- Instalações selecionadas: camada de candidatos escolhidos com total de demanda e pontos cobertos.
- Atribuição e cobertura de demandas: camada de demanda com o status de cobertura (is_covered) e a instalação atribuída.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>FacilityPMedian</name>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="85"/>
        <source>Camada de demanda (Pontos/Polígonos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="92"/>
        <source>Campo de peso da demanda (opcional, default=1.0)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="101"/>
        <source>Camada de instalações candidatas (Pontos/Polígonos) (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="109"/>
        <source>Camada de rede viária (Linhas) (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="117"/>
        <source>Número de instalações (p)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="126"/>
        <source>Número máximo de iterações do Teitz-Bart</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="135"/>
        <source>Instalações selecionadas</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="141"/>
        <source>Atribuição de demandas</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="157"/>
        <source>Camada de demanda inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="178"/>
        <source>Lendo pontos de demanda...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="203"/>
        <source>Nenhum ponto de demanda válido encontrado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="210"/>
        <source>Lendo instalações candidatas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="226"/>
        <source>Nenhuma instalação candidata válida encontrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="229"/>
        <source>O número de instalações p ({p}) excede o número de candidatos ({cand}).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="240"/>
        <source>Construindo o grafo e calculando a matriz OD na rede...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="245"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="251"/>
        <source>O grafo construído possui menos de 2 vértices.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="268"/>
        <source>Erro ao calcular a matriz OD: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="270"/>
        <source>Calculando matriz de distâncias euclidianas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="279"/>
        <source>Executando a otimização p-Mediana (Teitz-Bart)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="290"/>
        <source>Localização concluída. Instalações selecionadas: {sel} | Custo Total: {cost:.2f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="372"/>
        <source>Localização p-Mediana (Teitz-Bart)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="375"/>
        <source>Localização de Instalações</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/facility_p_median.py" line="381"/>
        <source>Resolve o problema de localização p-mediana selecionando p instalações candidatas que minimizem a soma total das distâncias/custos ponderadas da demanda até a instalação mais próxima.

Parâmetros:
- Camada de demanda: feições de pontos ou polígonos representando a demanda.
- Campo de peso da demanda: campo numérico indicando a demanda de cada feição (opcional, default=1.0).
- Camada de instalações candidatas: instalações elegíveis (opcional, usa a camada de demanda se omitida).
- Camada de rede viária: rede viária para distâncias reais na rede (opcional, usa distância euclidiana se omitida).
- Número de instalações (p): quantidade de instalações a selecionar.
- Número máximo de iterações: limite de trocas locais no algoritmo Teitz-Bart.

Saídas:
- Instalações selecionadas: camada de candidatos escolhidos com totais de demanda e custo.
- Atribuição de demandas: camada de demanda com o ID da instalação atribuída e o custo de atendimento.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>LogisPlugin</name>
    <message>
        <location filename="../logis_plugin.py" line="39"/>
        <source>Dependências...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../logis_plugin.py" line="46"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../logis_plugin.py" line="53"/>
        <source>Indicadores Regionais</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../logis_plugin.py" line="60"/>
        <source>Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>LogisProvider</name>
    <message>
        <location filename="../provider.py" line="71"/>
        <source>logis — suporte a projetos de logística no Brasil</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>RegionalCriticalLinks</name>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="51"/>
        <source>Camada de malha rodoviária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="58"/>
        <source>Trechos com indicação de ponte/arco crítico</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="64"/>
        <source>Número de pontes/arcos críticos identificados</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="75"/>
        <source>Camada de malha rodoviária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="77"/>
        <source>Construindo o grafo a partir da malha rodoviária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="81"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="87"/>
        <source>O grafo construído está vazio.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="92"/>
        <source>Deduplicando arcos em arestas físicas únicas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="110"/>
        <source>Identificando pontes/arcos críticos ({n} arestas físicas)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="127"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="143"/>
        <source>Pontes/arcos críticos identificados: {n} de {total} trechos.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="159"/>
        <source>Pontes/Arcos Críticos da Malha Regional</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="162"/>
        <source>Indicadores Regionais</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_critical_links.py" line="168"/>
        <source>Identifica as pontes/arcos críticos (cut links) da malha rodoviária regional: trechos cuja remoção desconecta a rede, indicando ligações intermunicipais sem rota alternativa.

Parâmetros:
- Camada de malha rodoviária: feições de linha representando as rodovias.

Retorno:
- Camada de linhas com o campo 'is_critical_link' (booleano), uma feição por trecho físico único da malha.
- Número de pontes/arcos críticos identificados.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>RegionalDock</name>
    <message>
        <location filename="../gui/regional_dock.py" line="160"/>
        <source>logis — Indicadores Regionais</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="174"/>
        <source>&lt;b&gt;Indicadores Regionais&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="178"/>
        <source>Selecione as camadas e parâmetros abaixo para calcular os indicadores de densidade rodoviária regional e percentual de pavimentação.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="189"/>
        <source>Camada de rede regional (Linhas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="195"/>
        <source>Camada de área de referência (Polígonos - para Densidade):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="201"/>
        <source>População da área de referência (habitantes):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="208"/>
        <source>Calcular Densidade Rodoviária</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="214"/>
        <source>Calcular % Pavimentação</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="220"/>
        <source>Calcular Pontes/Arcos Críticos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="226"/>
        <source>Resultados dos Indicadores Regionais:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="383"/>
        <source>Aviso</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="383"/>
        <source>Por favor, selecione uma camada de rede regional.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="388"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro: Camada de rede regional não selecionada.&lt;/span&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="259"/>
        <source>Por favor, selecione uma camada de área de referência.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="264"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro: Camada de área de referência não selecionada.&lt;/span&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="394"/>
        <source>Erro</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="394"/>
        <source>QGIS Processing não está disponível no ambiente atual.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="399"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro: QGIS Processing não disponível.&lt;/span&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="279"/>
        <source>&lt;b&gt;=== CALCULANDO DENSIDADE RODOVIÁRIA REGIONAL ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="291"/>
        <source>-&gt; &lt;b&gt;Densidade por Área:&lt;/b&gt; {value:.4f} km/1.000 km²</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="295"/>
        <source>-&gt; &lt;b&gt;Densidade por Área:&lt;/b&gt; N/A</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="298"/>
        <source>-&gt; &lt;b&gt;Densidade por População:&lt;/b&gt; {value:.4f} km/10.000 hab.&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="302"/>
        <source>-&gt; &lt;b&gt;Densidade por População:&lt;/b&gt; N/A&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="305"/>
        <source>&lt;span style=&apos;color: #fc8181;&apos;&gt;Erro ao calcular densidade: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="428"/>
        <source>&lt;b&gt;=== CÁLCULO CONCLUÍDO ===&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="341"/>
        <source>&lt;b&gt;=== CALCULANDO PERCENTUAL DE PAVIMENTAÇÃO ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="352"/>
        <source>-&gt; &lt;b&gt;Percentual Pavimentada:&lt;/b&gt; {value:.2f}%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="356"/>
        <source>-&gt; &lt;b&gt;Percentual Pavimentada:&lt;/b&gt; N/A</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="359"/>
        <source>-&gt; &lt;b&gt;Percentual Duplicada:&lt;/b&gt; {value:.2f}%&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="363"/>
        <source>-&gt; &lt;b&gt;Percentual Duplicada:&lt;/b&gt; N/A&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="366"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro ao calcular pavimentação: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="403"/>
        <source>&lt;b&gt;=== CALCULANDO PONTES/ARCOS CRÍTICOS ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="417"/>
        <source>-&gt; &lt;b&gt;Pontes/Arcos Críticos:&lt;/b&gt; {n} de {total} trechos.&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/regional_dock.py" line="424"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro ao calcular pontes/arcos críticos: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>RegionalNetworkDensity</name>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="46"/>
        <source>Camada de malha rodoviária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="53"/>
        <source>Camada de área de referência (UF, mesorregião, etc.)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="60"/>
        <source>População da área de referência (hab.)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="68"/>
        <source>Densidade rodoviária por área (km/1.000 km²)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="74"/>
        <source>Densidade rodoviária por população (km/10.000 hab.)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="87"/>
        <source>Camada de malha rodoviária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="89"/>
        <source>Camada de área de referência inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="92"/>
        <source>O campo 'length' não foi encontrado na camada de malha rodoviária. Utilize a camada snv_links_{uf} gerada por core.network.snv_pipeline.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="104"/>
        <source>Somando a extensão total da malha rodoviária (campo 'length')...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="121"/>
        <source>Calculando a área total do polígono de referência...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="136"/>
        <source>A área calculada é de 0 km² ou negativa. Verifique a geometria de referência.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="146"/>
        <source>Extensão da Malha: {length:.2f} m | Área: {area:.4f} km² | População: {pop:.0f} hab.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="151"/>
        <source>Densidade por Área: {da:.4f} km/1.000 km² | Densidade por População: {dp:.4f} km/10.000 hab.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="168"/>
        <source>Densidade da Malha Rodoviária Regional</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="171"/>
        <source>Indicadores Regionais</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_network_density.py" line="177"/>
        <source>Calcula a densidade da malha rodoviária por área territorial (km/1.000 km²) e por população (km/10.000 hab.).

Parâmetros:
- Camada de malha rodoviária: feições de linha representando as rodovias.
- Camada de área de referência: feições de polígono definindo o território (UF, mesorregião, etc.).
- População da área de referência: número de habitantes do território.

Retornos:
- Densidade rodoviária por área (km/1.000 km²).
- Densidade rodoviária por população (km/10.000 hab.).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>RegionalPavementPercentage</name>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="42"/>
        <source>Camada de malha rodoviária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="49"/>
        <source>Campo que indica o tipo de superfície (ex: 'ds_superfi')</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="59"/>
        <source>Percentual de vias pavimentadas (%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="65"/>
        <source>Percentual de vias duplicadas (%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="77"/>
        <source>Camada de malha rodoviária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="84"/>
        <source>O campo '{field}' não foi encontrado na camada de malha rodoviária. Campos disponíveis: {fields}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="90"/>
        <source>O campo 'length' não foi encontrado na camada de malha rodoviária. Utilize a camada snv_links_{uf} gerada por core.network.snv_pipeline.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="103"/>
        <source>Somando as extensões da malha rodoviária (campo 'length')...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="124"/>
        <source>O comprimento total da malha é de 0 metros ou menor. Verifique as feições da camada de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="136"/>
        <source>Extensão Total: {total:.2f} m | Pavimentada: {paved:.2f} m | Duplicada: {dup:.2f} m</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="141"/>
        <source>Percentual Pavimentada: {p_paved:.2f}% | Percentual Duplicada: {p_dup:.2f}%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="158"/>
        <source>Percentual de Pavimentação e Duplicação</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="161"/>
        <source>Indicadores Regionais</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/regional_pavement_percentage.py" line="167"/>
        <source>Calcula o percentual da malha rodoviária regional que é pavimentada e o percentual que é duplicada.

Parâmetros:
- Camada de malha rodoviária: feições de linha representando as rodovias.
- Campo de superfície: o atributo que armazena a superfície física (ex: 'ds_superfi').

Retornos:
- Percentual da malha pavimentada (%).
- Percentual da malha duplicada (%).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanCargoRestriction</name>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="74"/>
        <source>Camada de rede viária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="81"/>
        <source>Expressão de restrição (retorna verdadeiro para trechos restritos). Se vazia, usa o filtro default por tipo de via (highway), largura e peso máximo, quando esses campos existirem na camada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="94"/>
        <source>Índice de restrição de circulação (%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="106"/>
        <source>Camada de rede viária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="112"/>
        <source>Usando expressão de restrição default: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="122"/>
        <source>Expressão de restrição inválida: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="134"/>
        <source>Calculando a extensão total e restrita da rede viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="154"/>
        <source>Erro ao avaliar a expressão de restrição: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="168"/>
        <source>O comprimento total da rede viária calculada é 0 m ou negativo. Verifique as geometrias.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="178"/>
        <source>Comprimento Total: {total:.2f} m | Comprimento Restrito: {restricted:.2f} m</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="183"/>
        <source>Índice de Acessibilidade de Carga: {index:.2f}%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="195"/>
        <source>Índice de Restrição de Circulação de Carga</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="198"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_cargo_restriction.py" line="204"/>
        <source>Calcula o índice de restrição de circulação para veículos de carga (acessibilidade de carga).
O índice representa o percentual da rede viária urbana que está livre de restrições de circulação.

Parâmetros:
- Camada de rede viária: feições de linha representando as vias.
- Expressão de restrição: expressão QGIS opcional que define quais trechos possuem restrições (ex: &quot;maxweight&quot; IS NOT NULL ou &quot;largura&quot; &lt; 3.0).

Retorno:
- Valor numérico (%) de 0.0 a 100.0, onde 100.0 indica que nenhuma via é restrita.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanDeliveryDistance</name>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="56"/>
        <source>Camada de rede viária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="63"/>
        <source>Camada de depósitos candidatos (Pontos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="70"/>
        <source>Camada de zonas/centroides (Pontos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="77"/>
        <source>Critério de custo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="77"/>
        <source>Distância</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="77"/>
        <source>Tempo de viagem</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="85"/>
        <source>Zonas com custo de entrega</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="99"/>
        <source>Camada de rede viária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="101"/>
        <source>Camada de depósitos inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="103"/>
        <source>Camada de zonas inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="112"/>
        <source>Lendo depósitos...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="122"/>
        <source>Nenhum depósito válido encontrado na camada de depósitos.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="127"/>
        <source>Lendo zonas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="138"/>
        <source>Nenhuma zona válida encontrada na camada de zonas.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="141"/>
        <source>Construindo o grafo a partir da rede viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="146"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="152"/>
        <source>O grafo construído possui menos de 2 vértices. Não é possível calcular as distâncias.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="163"/>
        <source>Não foi possível amarrar um ou mais depósitos à rede viária.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="165"/>
        <source>Não foi possível amarrar uma ou mais zonas à rede viária.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="168"/>
        <source>Calculando matriz de distâncias/tempos de viagem depósito-zona...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="176"/>
        <source>Erro ao calcular a matriz OD: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="193"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="201"/>
        <source>Custo de entrega ao depósito mais próximo calculado para {count} zona(s).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="212"/>
        <source>Distância de Entrega Urbana</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="215"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_delivery_distance.py" line="221"/>
        <source>Calcula a distância ou tempo de entrega ao depósito mais próximo para cada zona de demanda (centroide de setor) a partir de uma camada de depósitos candidatos, usando caminhos mínimos na rede viária.

Parâmetros:
- Camada de rede viária: feições de linha representando as vias.
- Camada de depósitos candidatos: feições de ponto representando os depósitos/centros de distribuição.
- Camada de zonas/centroides: feições de ponto representando as zonas de demanda/entregas.
- Critério de custo: define se o cálculo de custo de caminho mínimo é baseado em Distância ou Tempo de viagem.

Retorno:
- Cópia da camada de zonas com a coluna 'dist_entrega' (contendo a menor distância ou tempo de viagem até o depósito mais próximo).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanDemandDensity</name>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="47"/>
        <source>Código IBGE do município (7 dígitos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="53"/>
        <source>Campo de população (ou domicílios/empregos) na camada do censobr unida por gisbr:join_censo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="62"/>
        <source>Setores censitários com densidade de demanda</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="74"/>
        <source>Código do município é obrigatório.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="76"/>
        <source>Campo de população é obrigatório.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="78"/>
        <source>Obtendo setores censitários do município {}...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="87"/>
        <source>Campo de população '{field}' não encontrado. Campos disponíveis: {available}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="101"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="107"/>
        <source>Calculando densidade de demanda por setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="123"/>
        <source>Setor {fid}: {error}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="136"/>
        <source>Densidade de demanda calculada para {count} setor(es).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="145"/>
        <source>Densidade de Demanda Urbana</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="148"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_demand_density.py" line="154"/>
        <source>Calcula a densidade de demanda (população, domicílios ou empregos por km²) de cada setor censitário de um município, a partir dos setores + variáveis do censobr (gisbr:read_census_tract + gisbr:join_censo). Requer o plugin GisBR instalado.

Parâmetros:
- Código IBGE do município: código de 7 dígitos.
- Campo de população: nome do campo de população/domicílios/empregos na camada unida pelo censobr (varia conforme o dataset do censobr).

Retorno:
- Cópia dos setores censitários com o campo 'dens_demanda_hab_km2'.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanDock</name>
    <message>
        <location filename="../gui/urban_dock.py" line="161"/>
        <source>logis — Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="175"/>
        <source>&lt;b&gt;Indicadores Urbanos&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="179"/>
        <source>Selecione as camadas e clique no botão abaixo para calcular os indicadores de densidade, conectividade, circuidade e restrição de circulação de carga.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="190"/>
        <source>Camada de rede viária (Linhas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="196"/>
        <source>Camada de área de referência (Polígonos - para Densidade):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="202"/>
        <source>Calcular Indicadores</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="208"/>
        <source>Resultados dos Indicadores:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="218"/>
        <source>&lt;b&gt;Densidade de Demanda&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="222"/>
        <source>Código IBGE do município (7 dígitos):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="226"/>
        <source>Campo de população (setor + censobr, requer GisBR):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="230"/>
        <source>Calcular Densidade de Demanda</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="235"/>
        <source>&lt;b&gt;Acessibilidade Gravitacional&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="239"/>
        <source>Camada de origem (pontos/centroides):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="244"/>
        <source>Camada de destinos (POIs):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="249"/>
        <source>Campo de peso do destino (opcional, default 1):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="255"/>
        <source>Beta (decaimento por distância):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="262"/>
        <source>Calcular Acessibilidade Gravitacional</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="267"/>
        <source>&lt;b&gt;Centralidade de Intermediação (Betweenness)&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="271"/>
        <source>Número de amostras (pares OD):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="277"/>
        <source>Calcular Centralidade de Intermediação</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="282"/>
        <source>&lt;b&gt;Distância de Entrega&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="286"/>
        <source>Camada de depósitos candidatos (Pontos):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="291"/>
        <source>Camada de zonas/centroides (Pontos):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="296"/>
        <source>Critério de custo:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="298"/>
        <source>Distância</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="298"/>
        <source>Tempo de viagem</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="301"/>
        <source>Calcular Distância de Entrega</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="630"/>
        <source>Aviso</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="616"/>
        <source>Por favor, selecione uma camada de rede viária.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="323"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro: Camada de rede viária não selecionada.&lt;/span&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="640"/>
        <source>Erro</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="640"/>
        <source>QGIS Processing não está disponível no ambiente atual.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="334"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro: QGIS Processing não disponível.&lt;/span&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="338"/>
        <source>&lt;b&gt;=== INICIANDO CÁLCULO DOS INDICADORES ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="342"/>
        <source>&lt;i&gt;1) Densidade viária: Pulado (camada de área não selecionada)&lt;/i&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="344"/>
        <source>1) Calculando densidade viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="352"/>
        <source>   -&gt; &lt;b&gt;Densidade viária:&lt;/b&gt; {value:.4f} km/km²&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="356"/>
        <source>   -&gt; &lt;b&gt;Densidade viária:&lt;/b&gt; N/A (resultado vazio)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="358"/>
        <source>   -&gt; &lt;span style=&apos;color: #fc8181;&apos;&gt;Erro ao calcular densidade: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="363"/>
        <source>2) Calculando conectividade da rede...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="376"/>
        <source>   -&gt; &lt;b&gt;Número de nós (v):&lt;/b&gt; {v}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="377"/>
        <source>   -&gt; &lt;b&gt;Número de arestas (e):&lt;/b&gt; {e}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="379"/>
        <source>   -&gt; &lt;b&gt;Índice Alfa:&lt;/b&gt; {v:.4f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="381"/>
        <source>   -&gt; &lt;b&gt;Índice Beta:&lt;/b&gt; {v:.4f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="383"/>
        <source>   -&gt; &lt;b&gt;Índice Gama:&lt;/b&gt; {v:.4f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="385"/>
        <source>   -&gt; &lt;b&gt;Cruzamentos 4+ pernas:&lt;/b&gt; {v:.2f}%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="387"/>
        <source>   -&gt; &lt;b&gt;Becos sem saída:&lt;/b&gt; {v:.2f}%&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="389"/>
        <source>   -&gt; &lt;span style=&apos;color: #fc8181;&apos;&gt;Erro ao calcular conectividade: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="394"/>
        <source>3) Calculando circuidade média (amostragem)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="403"/>
        <source>   -&gt; &lt;b&gt;Circuidade média:&lt;/b&gt; {value:.4f}&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="407"/>
        <source>   -&gt; &lt;b&gt;Circuidade média:&lt;/b&gt; N/A (resultado vazio)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="409"/>
        <source>   -&gt; &lt;span style=&apos;color: #fc8181;&apos;&gt;Erro ao calcular circuidade: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="414"/>
        <source>4) Calculando acessibilidade/restrição de carga...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="422"/>
        <source>   -&gt; &lt;b&gt;Acessibilidade de carga:&lt;/b&gt; {value:.2f}%&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="426"/>
        <source>   -&gt; &lt;b&gt;Acessibilidade de carga:&lt;/b&gt; N/A (resultado vazio)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="428"/>
        <source>   -&gt; &lt;span style='color: #fc8181;'&gt;Erro ao calcular restrição: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="432"/>
        <source>&lt;b&gt;=== CÁLCULO CONCLUÍDO ===&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="444"/>
        <source>Por favor, informe o código IBGE do município.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="451"/>
        <source>Por favor, informe o campo de população.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="468"/>
        <source>&lt;b&gt;Calculando densidade de demanda...&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="479"/>
        <source>   -&gt; &lt;b&gt;Densidade de demanda:&lt;/b&gt; camada adicionada ao projeto com {count} setor(es).&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="483"/>
        <source>   -&gt; &lt;b&gt;Densidade de demanda:&lt;/b&gt; N/A (resultado vazio)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="485"/>
        <source>   -&gt; &lt;span style=&apos;color: #fc8181;&apos;&gt;Erro ao calcular densidade de demanda: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="508"/>
        <source>Por favor, selecione uma camada de origem.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="515"/>
        <source>Por favor, selecione uma camada de destinos.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="532"/>
        <source>&lt;b&gt;Calculando acessibilidade gravitacional...&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="548"/>
        <source>   -&gt; &lt;b&gt;Acessibilidade gravitacional:&lt;/b&gt; camada adicionada ao projeto com {count} origem(ns).&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="552"/>
        <source>   -&gt; &lt;b&gt;Acessibilidade gravitacional:&lt;/b&gt; N/A (resultado vazio)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="554"/>
        <source>   -&gt; &lt;span style=&apos;color: #fc8181;&apos;&gt;Erro ao calcular acessibilidade gravitacional: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="584"/>
        <source>&lt;b&gt;Calculando centralidade de intermediação...&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="595"/>
        <source>   -&gt; &lt;b&gt;Centralidade de intermediação:&lt;/b&gt; camada adicionada ao projeto com {count} aresta(s).&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="599"/>
        <source>   -&gt; &lt;b&gt;Centralidade de intermediação:&lt;/b&gt; N/A (resultado vazio)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="601"/>
        <source>   -&gt; &lt;span style='color: #fc8181;'&gt;Erro ao calcular centralidade de intermediação: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="623"/>
        <source>Por favor, selecione uma camada de depósitos candidatos.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="630"/>
        <source>Por favor, selecione uma camada de zonas/centroides.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="647"/>
        <source>&lt;b&gt;Calculando distância de entrega...&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="660"/>
        <source>   -&gt; &lt;b&gt;Distância de entrega:&lt;/b&gt; camada adicionada ao projeto com {count} zona(s).&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="664"/>
        <source>   -&gt; &lt;b&gt;Distância de entrega:&lt;/b&gt; N/A (resultado vazio)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/urban_dock.py" line="666"/>
        <source>   -&gt; &lt;span style='color: #fc8181;'&gt;Erro ao calcular distância de entrega: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanEdgeBetweenness</name>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="54"/>
        <source>Camada de rede viária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="61"/>
        <source>Número de amostras (pares OD)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="70"/>
        <source>Semente aleatória (opcional, para reprodutibilidade)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="77"/>
        <source>Arestas com centralidade de intermediação</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="93"/>
        <source>Camada de rede viária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="95"/>
        <source>Construindo o grafo a partir da rede viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="99"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="105"/>
        <source>O grafo construído está vazio.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="107"/>
        <source>Grafo construído: {v} vértices, {e} arestas.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="113"/>
        <source>Amostrando pares OD e calculando a centralidade de intermediação...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="129"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="144"/>
        <source>Centralidade de intermediação máxima observada: {max_score:.4f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="157"/>
        <source>Centralidade de Intermediação de Arestas (Betweenness)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="160"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_edge_betweenness.py" line="166"/>
        <source>Calcula a centralidade de intermediação (betweenness) aproximada de cada aresta de uma rede viária urbana, por amostragem de pares origem-destino e caminhos mínimos de Dijkstra.

Parâmetros:
- Camada de rede viária: feições de linha representando as vias.
- Número de amostras (pares OD): número de pares a amostrar (default 1000).
- Semente aleatória: opcional, para reprodutibilidade da amostragem.

Retorno:
- Camada de linhas com o campo 'betweenness' (0.0 a 1.0), uma feição por aresta do grafo.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanGravityAccessibility</name>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="58"/>
        <source>Camada de rede viária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="65"/>
        <source>Camada de origem (pontos/centroides)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="72"/>
        <source>Camada de destinos (POIs)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="79"/>
        <source>Campo de peso/atratividade do destino (opcional, default 1 para todos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="88"/>
        <source>Parâmetro de decaimento por distância (beta)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="97"/>
        <source>Origem com acessibilidade gravitacional</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="112"/>
        <source>Camada de rede viária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="114"/>
        <source>Camada de origem inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="116"/>
        <source>Camada de destinos inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="130"/>
        <source>Lendo origens...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="141"/>
        <source>Nenhuma origem válida encontrada na camada de origem.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="146"/>
        <source>Lendo destinos e pesos...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="160"/>
        <source>Nenhum destino válido encontrado na camada de destinos.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="163"/>
        <source>Construindo o grafo a partir da rede viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="168"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="174"/>
        <source>O grafo construído possui menos de 2 vértices. Não é possível calcular a acessibilidade.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="185"/>
        <source>Não foi possível amarrar uma ou mais origens à rede viária.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="187"/>
        <source>Não foi possível amarrar um ou mais destinos à rede viária.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="190"/>
        <source>Calculando matriz de distâncias origem-destino...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="197"/>
        <source>Erro ao calcular a matriz OD: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="214"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="222"/>
        <source>Acessibilidade gravitacional calculada para {count} origem(ns).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="233"/>
        <source>Acessibilidade Gravitacional Urbana</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="236"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_gravity_accessibility.py" line="242"/>
        <source>Calcula a acessibilidade gravitacional de cada origem (ex.: centroides de setor) a uma camada de destinos ponderados (ex.: POIs, comércio, empregos), usando caminhos mínimos sobre a rede viária urbana.

Parâmetros:
- Camada de rede viária: feições de linha representando as vias.
- Camada de origem: feições de ponto (ex.: centroides de setor, saída do indicador de densidade de demanda).
- Camada de destinos (POIs): feições de ponto com os destinos.
- Campo de peso/atratividade do destino: campo numérico opcional (default 1 para todos os destinos).
- Beta: parâmetro de decaimento por distância do modelo gravitacional (default 2.0).

Retorno:
- Cópia da camada de origem com o campo 'acess_gravit' (índice de acessibilidade gravitacional).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanMeanCircuity</name>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="48"/>
        <source>Camada de rede viária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="55"/>
        <source>Número de amostras (pares OD)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="64"/>
        <source>Distância euclidiana mínima (metros)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="73"/>
        <source>Circuidade média</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="86"/>
        <source>Camada de rede viária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="88"/>
        <source>Construindo o grafo a partir da rede viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="92"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="98"/>
        <source>O grafo construído possui menos de 2 vértices. Não é possível calcular a circuidade.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="102"/>
        <source>Grafo construído: {v} vértices, {e} arestas.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="108"/>
        <source>Amostrando pares de pontos para o cálculo da circuidade...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="165"/>
        <source>Não foi possível encontrar nenhum par de pontos válido que satisfaça a distância mínima de {min_dist} metros.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="172"/>
        <source>Calculando circuidade média com {count} amostras válidas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="183"/>
        <source>Circuidade média calculada: {circuity:.4f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="192"/>
        <source>Circuidade Média de Rede Viária Urbana</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="195"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_mean_circuity.py" line="201"/>
        <source>Calcula a circuidade média de uma rede viária urbana a partir de amostras de caminhos mínimos.

Parâmetros:
- Camada de rede viária: feições de linha representando as vias.
- Número de amostras (pares OD): número de caminhos a amostrar (default 1000).
- Distância euclidiana mínima: distância mínima em metros entre origem e destino (default 100m).

Retorno:
- Valor numérico contendo a circuidade média (distância rede / distância euclidiana).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanNetworkConnectivity</name>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="47"/>
        <source>Camada de rede viária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="54"/>
        <source>Número de nós (v)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="60"/>
        <source>Número de arestas (e)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="66"/>
        <source>Índice Alfa</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="72"/>
        <source>Índice Beta</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="78"/>
        <source>Índice Gama</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="84"/>
        <source>Percentual de interseções com grau 4 ou mais</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="90"/>
        <source>Percentual de becos sem saída</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="101"/>
        <source>Camada de rede viária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="103"/>
        <source>Construindo o grafo a partir da rede viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="108"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="113"/>
        <source>O grafo construído não possui vértices.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="116"/>
        <source>Calculando os graus dos nós...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="140"/>
        <source>Calculando os indicadores de conectividade...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="147"/>
        <source>Nós (v): {v} | Arestas (e): {e}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="150"/>
        <source>Índices: Alfa={alpha:.4f} | Beta={beta:.4f} | Gama={gamma:.4f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="155"/>
        <source>Interseções 4+ pernas: {pct_4:.2f}% | Becos sem saída: {pct_dead:.2f}%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="177"/>
        <source>Conectividade de Rede Viária Urbana</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="180"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_connectivity.py" line="186"/>
        <source>Calcula indicadores de conectividade para uma rede viária urbana a partir dos graus de seus nós.

Parâmetros:
- Camada de rede viária: feições de linha representando as vias.

Retornos:
- Número de nós (v)
- Número de arestas (e)
- Índice Alfa (0 a 1)
- Índice Beta (links por nó)
- Índice Gama (0 a 1)
- Percentual de interseções com grau 4 ou mais (cruzamentos de 4 pernas)
- Percentual de becos sem saída (grau 1)</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>UrbanNetworkDensity</name>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="42"/>
        <source>Camada de rede viária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="49"/>
        <source>Camada de área de referência (Polígonos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="56"/>
        <source>Densidade da rede viária (km/km²)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="68"/>
        <source>Camada de rede viária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="70"/>
        <source>Camada de área de referência inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="79"/>
        <source>Calculando a extensão total da rede viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="96"/>
        <source>Calculando a área total do polígono de referência...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="111"/>
        <source>A área calculada é de 0 km² ou negativa. Verifique a geometria de referência.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="121"/>
        <source>Comprimento da Rede: {length:.2f} m | Área: {area:.4f} km²</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="126"/>
        <source>Densidade Calculada: {density:.4f} km/km²</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="136"/>
        <source>Densidade de Rede Viária Urbana</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="139"/>
        <source>Indicadores Urbanos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/urban_network_density.py" line="145"/>
        <source>Calcula a densidade da rede viária em km de via por km² de área de referência.

Parâmetros:
- Camada de rede viária: feições de linha representando as vias.
- Camada de área de referência: feições de polígono definindo a área territorial.

Retorno:
- Valor numérico contendo a densidade em km/km².</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>VrpCvrp</name>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="92"/>
        <source>Camada de depósito (Pontos/Polígonos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="99"/>
        <source>Camada de demanda / clientes (Pontos/Polígonos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="106"/>
        <source>Campo de peso/demanda (opcional, default=1.0)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="115"/>
        <source>Capacidade do veículo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="124"/>
        <source>Camada de rede viária (Linhas) (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="132"/>
        <source>Aplicar busca local (2-opt e Or-opt)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="139"/>
        <source>Rotas geradas</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="145"/>
        <source>Paradas por rota (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="162"/>
        <source>Camada de depósito inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="164"/>
        <source>Camada de demanda inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="166"/>
        <source>A capacidade do veículo deve ser estritamente maior que zero.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="190"/>
        <source>Nenhum ponto de depósito válido encontrado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="199"/>
        <source>Lendo pontos de demanda...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="220"/>
        <source>A demanda do nó excede a capacidade máxima do veículo ({weight} &gt; {cap}).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="231"/>
        <source>Nenhum ponto de demanda válido encontrado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="238"/>
        <source>Construindo o grafo e calculando a matriz OD na rede...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="242"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="248"/>
        <source>O grafo construído possui menos de 2 vértices.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="261"/>
        <source>Erro ao calcular a matriz OD: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="263"/>
        <source>Calculando matriz de distâncias euclidianas...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="272"/>
        <source>Executando a otimização CVRP (Clarke-Wright + 2-opt/Or-opt)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="284"/>
        <source>Roteirização concluída. Rotas geradas: {count} | Distância Total: {dist:.2f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="355"/>
        <source>Roteirização de Veículos Capacitados (CVRP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="358"/>
        <source>Roteirização</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/vrp_cvrp.py" line="364"/>
        <source>Resolve o Problema de Roteirização de Veículos Capacitados (CVRP) a partir de uma camada de depósito e uma camada de pontos de demanda (clientes).

Constroi rotas que iniciam e terminam no depósito, respeitando a capacidade máxima do veículo, utilizando a heurística de economias de Clarke &amp; Wright (1964) e refinamento opcional por busca local 2-opt (Lin, 1965) e Or-opt (Or, 1976).

Parâmetros:
- Camada de depósito: feição de ponto/polígono representando o depósito de partida/chegada.
- Camada de demanda / clientes: feições de pontos ou polígonos com demandas a atender.
- Campo de peso/demanda: campo numérico da demanda de cada cliente (opcional, default=1.0).
- Capacidade do veículo: carga máxima transportada por cada veículo em uma rota.
- Camada de rede viária: rede viária para distâncias reais (opcional, usa distância euclidiana se omitida).
- Aplicar busca local: se verdadeiro, aplica 2-opt e Or-opt para otimização de cada rota.

Saídas:
- Rotas geradas: camada de linhas com a geometria das rotas e estatísticas de carga e distância.
- Paradas por rota: camada de pontos ordenada com atribuição de rota e carga acumulada.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteCarpRoute</name>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="105"/>
        <source>Camada de vias</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="112"/>
        <source>Campo de geração/demanda de resíduos (kg)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="121"/>
        <source>Campo de via obrigatória para coleta (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="129"/>
        <source>Campo de setor de coleta (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="137"/>
        <source>Capacidade do veículo (em toneladas ou kg)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="146"/>
        <source>Camada de ponto do depósito/aterro (exatamente 1 feição)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="153"/>
        <source>Tolerância de nó em metros (requer CRS métrico)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="162"/>
        <source>Vias com rota de coleta (CARP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="179"/>
        <source>Camada de vias inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="181"/>
        <source>A capacidade do veículo deve ser maior que zero.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="199"/>
        <source>Lendo trechos de via...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="254"/>
        <source>Demanda do trecho '{fid}' ({dem:.2f}) excede a capacidade do veículo ({cap:.2f}).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="273"/>
        <source>{count} trecho(s) com geometria inválida foram ignorados.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="280"/>
        <source>Nenhum trecho de via válido encontrado na camada de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="286"/>
        <source>Camada de depósito inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="296"/>
        <source>A camada de ponto do depósito deve conter exatamente 1 feição (encontradas {count}).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="320"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="331"/>
        <source>Setor '{sec}': nenhum trecho de coleta obrigatória. Ignorando setor.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="351"/>
        <source>Calculando rotas CARP para o setor '{sec}' ({req_count} trechos obrigatórios)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="365"/>
        <source>Erro ao calcular rotas CARP para o setor &apos;{sec}&apos;: {err}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="371"/>
        <source>Setor &apos;{sec}&apos;: {count} rota(s)/viagem(ns) gerada(s).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="391"/>
        <source>Setor &apos;{sec}&apos;, rota {idx}: carga {load:.2f} kg, {dh_km:.2f} km de deadhead.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="397"/>
        <source>Aviso: rota {idx} do setor &apos;{sec}&apos; usa menos de 50% da capacidade ({load:.2f} kg de {cap:.2f} kg).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="433"/>
        <source>Roteirização por Arcos Capacitada (CARP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="436"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_carp_route.py" line="442"/>
        <source>Calcula rotas de veículos capacitados para coleta de lixo por arcos usando o Problema de Roteirização por Arcos Capacitada (Capacitated Arc Routing Problem - CARP) com a heurística Path-Scanning (Golden et al., 1983).

Parâmetros:
- Camada de vias: feições de linha com a malha viária.
- Campo de demanda de resíduos (obrigatório): campo numérico com a geração em cada trecho, em kg.
- Campo de via obrigatória (opcional): campo indicando trechos com coleta obrigatória; se omitido, todos os trechos são obrigatórios.
- Campo de setor de coleta (opcional): se informado, resolve o CARP separadamente por setor.
- Capacidade do veículo: capacidade máxima de carga por veículo, em kg.
- Camada de depósito/aterro: feição de ponto com a localização do aterro/depósito/garagem (exatamente 1 feição). O depósito é snapado ao vértice de via mais próximo por distância euclidiana — aproximação heurística, não uma projeção exata sobre a rede.
- Tolerância de nó: distância em metros para conectar vértices das vias.

Um trecho isolado com demanda maior que a capacidade do veículo gera erro explícito em vez de ser dividido entre mais de uma viagem (sem split-delivery).

Retorno:
- Camada de linha com feições de vias e campos adicionais: 'route_id' (identificador da rota/viagem dentro do setor), 'route_visit_order' (ordem de visita na rota), 'route_sector_id' (setor de coleta), 'route_is_deadhead' (booleano indicando passagem duplicada/deslocamento deadhead), 'route_load_kg' (carga total da rota em kg) e 'route_distance_km' (distância total da rota em km).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteCollectionCoverage</name>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="70"/>
        <source>Camada de vias exigidas (faixa de frequência)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="77"/>
        <source>Campo de setor da camada de vias exigidas (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="85"/>
        <source>Camada de rota coberta (vias percorridas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="92"/>
        <source>Campo indicador de deadhead/conector (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="102"/>
        <source>Campo de setor da camada de rota coberta (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="110"/>
        <source>Rótulo de frequência de coleta</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="118"/>
        <source>Tabela de cobertura por setor</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="134"/>
        <source>Camada de vias exigidas inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="136"/>
        <source>Camada de rota coberta inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="154"/>
        <source>Calculando extensão exigida por setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="174"/>
        <source>Calculando extensão coberta por setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="206"/>
        <source>Nenhum trecho válido encontrado nas camadas de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="226"/>
        <source>Erro ao calcular a cobertura da coleta: {err}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="250"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="267"/>
        <source>Setor &apos;{sid}&apos;: {req:.2f} km exigidos | {cov:.2f} km cobertos | Cobertura: {pct}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="279"/>
        <source>Aviso: Setor &apos;{sid}&apos; possui cobertura baixa ({pct:.1f}% &lt; 80.0%).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="318"/>
        <source>Total geral: {req:.2f} km exigidos | {cov:.2f} km cobertos | Cobertura total: {pct}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="335"/>
        <source>Cobertura da Coleta de Resíduos por Setor</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="338"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_collection_coverage.py" line="344"/>
        <source>Calcula a extensão de via exigida (required_km), extensão efetivamente coberta por rotas de coleta (covered_km) e a taxa de cobertura (coverage_pct) por setor e no total acumulado.

Parâmetros:
- Camada de vias exigidas (faixa de frequência): feições de linha com as vias exigidas.
- Campo de setor da camada de vias exigidas (opcional): campo com o identificador do setor.
- Camada de rota coberta (vias percorridas): feições de linha (ex.: saídas de logis:waste_cpp_route, logis:waste_rpp_route ou logis:waste_carp_route).
- Campo indicador de deadhead/conector (opcional): campo booleano onde True indica trecho improdutivo (default: 'route_is_deadhead'). Trechos improdutivos são desconsiderados da cobertura.
- Campo de setor da camada de rota coberta (opcional): campo de setor na camada de rota.
- Rótulo de frequência de coleta: rótulo textual de frequência (ex.: 'Diária', '3x/semana').

Retorno:
- Tabela sem geometria com uma feição por setor: 'sector_id', 'frequency_label', 'required_km', 'covered_km' e 'coverage_pct'. Quando há mais de um setor, uma feição adicional com 'sector_id' nulo traz o total acumulado.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteCppRoute</name>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="91"/>
        <source>Camada de vias</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="98"/>
        <source>Campo de setor de coleta (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="106"/>
        <source>Tolerância de nó em metros (requer CRS métrico)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="115"/>
        <source>Vias com rota de coleta (CPP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="128"/>
        <source>Camada de vias inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="136"/>
        <source>Lendo trechos de via e agrupando por setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="184"/>
        <source>{count} trecho(s) com geometria inválida foram ignorados.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="191"/>
        <source>Nenhum trecho de via válido encontrado na camada de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="209"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="218"/>
        <source>Calculando rota CPP para o setor &apos;{sec}&apos; com {count} trecho(s)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="230"/>
        <source>Erro ao calcular rota CPP para o setor &apos;{sec}&apos;: {err}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="240"/>
        <source>Setor &apos;{sec}&apos;: {dup} trecho(s) duplicado(s) (deadhead), {km:.2f} km improdutivos.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="270"/>
        <source>Roteirização por Arcos (CPP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="273"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_cpp_route.py" line="279"/>
        <source>Calcula a sequência de percurso para coleta de lixo por arcos usando o Problema do Carteiro Chinês (Chinese Postman Problem - CPP).

Parâmetros:
- Camada de vias: feições de linha a serem percorridas.
- Campo de setor de coleta (opcional): se informado, o CPP é resolvido separadamente para cada setor de coleta; se omitido, toda a camada é tratada como um único setor.
- Tolerância de nó: distância em metros para conectar vértices das vias.

Retorno:
- Camada de linha com feições duplicadas nos trechos de deadhead e campos adicionais: 'route_visit_order' (posição sequencial no circuito), 'route_sector_id' (setor de coleta) e 'route_is_deadhead' (booleano indicando passagem duplicada/deadhead).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteDeadheadRatio</name>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="66"/>
        <source>Camada de rotas/vias de coleta</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="73"/>
        <source>Campo indicador de deadhead/improdutivo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="83"/>
        <source>Campo de identificação da rota/setor (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="91"/>
        <source>Razão de deadhead por rota</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="104"/>
        <source>Camada de rotas de coleta inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="108"/>
        <source>Campo indicador de deadhead inválido.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="116"/>
        <source>Lendo feições da camada e calculando comprimentos...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="140"/>
        <source>Nenhum trecho válido encontrado na camada de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="151"/>
        <source>Erro ao calcular a razão de deadhead: {err}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="171"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="186"/>
        <source>Rota '{rid}': {prod:.2f} km produtivos | {dh:.2f} km deadhead | Razão: {ratio}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="211"/>
        <source>Total acumulado de todas as rotas: {prod:.2f} km produtivos | {dh:.2f} km deadhead | Razão total: {ratio}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="238"/>
        <source>Razão de Deadhead por Rota</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="241"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_deadhead_ratio.py" line="247"/>
        <source>Calcula a extensão de deslocamento produtivo (coleta), improdutivo (deadhead/conector) e a razão de deadhead (deadhead_km / productive_km) para cada rota de coleta e no total.

Parâmetros:
- Camada de rotas/vias de coleta: feições de linha (ex.: saídas de logis:waste_cpp_route, logis:waste_rpp_route ou logis:waste_carp_route).
- Campo indicador de deadhead (obrigatório): campo booleano onde True indica trecho de deadhead/deslocamento improdutivo (default: 'route_is_deadhead').
- Campo de identificação da rota/setor (opcional): se informado, calcula a razão separadamente para cada rota/setor; se omitido, calcula para a camada inteira.

Retorno:
- Tabela sem geometria com uma feição por rota: 'route_id', 'productive_km' (extensão de coleta), 'deadhead_km' (extensão improdutiva) e 'deadhead_ratio' (razão deadhead_km / productive_km). Quando há mais de uma rota, uma feição adicional com 'route_id' nulo traz o total agregado de todas as rotas.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteDestinationDistance</name>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="74"/>
        <source>Camada de rede viária (Linhas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="81"/>
        <source>Camada de destinos de resíduos - aterro/transbordo/ecoponto (Pontos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="88"/>
        <source>Camada de setores/origens de coleta (Pontos ou Polígonos)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="95"/>
        <source>Critério de custo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="95"/>
        <source>Distância</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="95"/>
        <source>Tempo de viagem</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="103"/>
        <source>Setores de coleta com distância ao destino</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="117"/>
        <source>Camada de rede viária inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="119"/>
        <source>Camada de destinos de resíduos inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="121"/>
        <source>Camada de setores/origens inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="130"/>
        <source>Lendo pontos de destino (aterros/transbordos/ecopontos)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="140"/>
        <source>Nenhum ponto de destino válido encontrado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="145"/>
        <source>Lendo setores/origens de coleta...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="160"/>
        <source>Nenhum setor/origem de coleta válido encontrado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="163"/>
        <source>Construindo o grafo a partir da rede viária...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="168"/>
        <source>Erro ao construir o grafo: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="174"/>
        <source>O grafo construído possui menos de 2 vértices. Não é possível calcular as distâncias.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="185"/>
        <source>Não foi possível amarrar um ou mais pontos de destino à rede viária.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="187"/>
        <source>Não foi possível amarrar um ou mais setores/origens à rede viária.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="190"/>
        <source>Calculando matriz de distâncias/tempos de viagem destino-setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="198"/>
        <source>Erro ao calcular a matriz OD: {}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="215"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="223"/>
        <source>Distância ao destino de resíduos mais próximo calculada para {count} setor(es).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="234"/>
        <source>Distância ao Destino de Resíduos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="237"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_destination_distance.py" line="243"/>
        <source>Calcula a distância ou tempo de viagem ao ponto de destino de resíduos mais próximo (aterro sanitário, estação de transbordo, ecoponto) para cada setor ou centroide de coleta, utilizando caminhos mínimos na rede viária.

Parâmetros:
- Camada de rede viária: feições de linha representando as vias.
- Camada de destinos de resíduos: feições de ponto representando aterros, estações de transbordo ou ecopontos.
- Camada de setores/origens: feições de ponto ou polígono representando os setores de coleta.
- Critério de custo: define se o cálculo de custo de caminho mínimo é baseado em Distância ou Tempo de viagem.

Retorno:
- Cópia da camada de origens com a coluna 'dist_destino' (menor distância em km ou tempo em min até o destino mais próximo).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteDistricting</name>
    <message>
        <location filename="../algorithms/waste_districting.py" line="94"/>
        <source>Camada de vias</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="101"/>
        <source>Campo de carga (opcional, default=comprimento do trecho)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="110"/>
        <source>Número de setores de coleta desejado</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="119"/>
        <source>Tolerância de nó em metros (requer CRS métrico)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="128"/>
        <source>Máximo de iterações de rebalanceamento de fronteira</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="137"/>
        <source>Vias com setor de coleta atribuído</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="152"/>
        <source>Camada de vias inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="157"/>
        <source>Lendo trechos de via e construindo adjacência...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="192"/>
        <source>{count} trecho(s) com geometria inválida foram ignorados.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="199"/>
        <source>Nenhum trecho de via válido encontrado na camada de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="202"/>
        <source>O número de setores ({k}) não pode exceder o número de trechos válidos ({n}).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="209"/>
        <source>Selecionando sementes (farthest-first)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="213"/>
        <source>Crescendo setores a partir das sementes...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="216"/>
        <source>Rebalanceando trechos de fronteira...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="227"/>
        <source>Setorização concluída. Setores: {k} | carga mín={min:.2f} | carga máx={max:.2f} | carga média={avg:.2f}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="243"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="268"/>
        <source>Setorização de Coleta de Resíduos (Districting)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="271"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_districting.py" line="277"/>
        <source>Particiona os trechos de uma camada de vias em k setores de coleta contíguos e balanceados por carga (resíduos gerados ou, na ausência do campo, comprimento do trecho).

Usa a heurística de sementes farthest-first (Gonzalez, 1985), seguida de crescimento de regiões a partir das sementes e refinamento local por troca de trechos de fronteira para equilibrar a carga entre setores mantendo contiguidade. A solução é boa, não necessariamente ótima.

Parâmetros:
- Camada de vias: trechos de via (linhas) a setorizar.
- Campo de carga: campo numérico com a carga de cada trecho (opcional; se omitido, usa o comprimento do trecho como proxy de carga).
- Número de setores: quantidade desejada de setores de coleta (k &gt;= 2).
- Tolerância de nó: distância, em metros, usada para considerar dois vértices de extremidade como o mesmo nó da rede. Requer que a camada esteja em um CRS métrico.
- Máximo de iterações: limite de trocas locais de trechos de fronteira.

Saída:
- Camada de vias com o novo atributo 'collection_sector_id' (ID do setor de coleta).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteDock</name>
    <message>
        <location filename="../gui/waste_dock.py" line="172"/>
        <source>logis — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="189"/>
        <source>&lt;b&gt;Coleta de Lixo&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="193"/>
        <source>Painel para gestão, estimativa de geração, setorização e roteirização por arcos (coleta de lixo urbana).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="204"/>
        <source>&lt;b&gt;Estimativa de Geração&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="209"/>
        <source>Camada de setores censitérios (Polígonos):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="215"/>
        <source>Campo ID do setor (Setores):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="222"/>
        <source>Campo de população (Setores):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="346"/>
        <source>Camada de trechos de via (Linhas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="235"/>
        <source>Campo ID do setor (Vias):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="242"/>
        <source>Taxa per capita (kg/hab/dia):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="250"/>
        <source>Fração de cobertura (0.0 a 1.0):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="258"/>
        <source>Calcular Estimativa de Geração</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="264"/>
        <source>&lt;b&gt;Roteirização CPP&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="506"/>
        <source>Campo de setor de coleta (opcional):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="391"/>
        <source>Tolerância de nó (m):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="292"/>
        <source>Executar Roteirização CPP</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="298"/>
        <source>&lt;b&gt;Roteirização RPP&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="352"/>
        <source>Campo de via obrigatória (opcional):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="335"/>
        <source>Executar Roteirização RPP</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="341"/>
        <source>&lt;b&gt;Roteirização CARP&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="361"/>
        <source>Campo de demanda de resíduos (kg):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="368"/>
        <source>Camada de ponto do depósito/aterro (Pontos):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="374"/>
        <source>Capacidade do veículo:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="399"/>
        <source>Executar Roteirização CARP</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="405"/>
        <source>&lt;b&gt;Dimensionamento de Frota&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="475"/>
        <source>Camada de rotas de coleta (Linhas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="416"/>
        <source>Campo ID da rota:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="515"/>
        <source>Velocidade média de coleta (km/h):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="440"/>
        <source>Duração da jornada de trabalho (horas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="523"/>
        <source>Tempo de descarga por rota (horas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="531"/>
        <source>Tempo de deslocamento ao destino por rota (horas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="464"/>
        <source>Executar Dimensionamento de Frota</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="470"/>
        <source>&lt;b&gt;Equilíbrio entre Setores&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="481"/>
        <source>Campo de carga da rota (kg):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="488"/>
        <source>Campo de distância da rota em km (opcional):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="497"/>
        <source>Campo ID da rota (opcional):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="539"/>
        <source>Executar Equilíbrio entre Setores</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="545"/>
        <source>&lt;b&gt;Distância ao Destino&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="550"/>
        <source>Camada de rede viária (Linhas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="556"/>
        <source>Camada de destinos de resíduos (Pontos):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="562"/>
        <source>Camada de setores/origens de coleta (Pontos ou Polígonos):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="568"/>
        <source>Critério de custo:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="570"/>
        <source>Distância</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="570"/>
        <source>Tempo de viagem</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="574"/>
        <source>Executar Distância ao Destino</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="580"/>
        <source>&lt;b&gt;Cobertura por Frequência&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="585"/>
        <source>Camada de vias exigidas (faixa de frequência) (Linhas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="591"/>
        <source>Campo de setor da camada de vias exigidas (opcional):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="600"/>
        <source>Camada de rota coberta (Linhas):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="606"/>
        <source>Campo indicador de deadhead/conector (opcional):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="615"/>
        <source>Campo de setor da camada de rota coberta (opcional):</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="624"/>
        <source>Rótulo de frequência de coleta:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="629"/>
        <source>Executar Cobertura por Frequência</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="635"/>
        <source>Resultados:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1133"/>
        <source>Aviso</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="663"/>
        <source>Por favor, selecione todas as camadas e campos necessários para a estimativa de geração.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1138"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro: Parâmetros incompletos.&lt;/span&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1144"/>
        <source>Erro</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1144"/>
        <source>QGIS Processing não está disponível no ambiente atual.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1149"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro: QGIS Processing não disponível.&lt;/span&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="683"/>
        <source>&lt;b&gt;=== CALCULANDO ESTIMATIVA DE GERAÇÃO ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="703"/>
        <source>-&gt; &lt;b&gt;Estimativa calculada com sucesso!&lt;/b&gt; (Camada com {count} trechos viários)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="707"/>
        <source>-&gt; &lt;b&gt;Resultado da estimativa retornou vazio.&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="710"/>
        <source>&lt;span style=&apos;color: #fc8181;&apos;&gt;Erro ao calcular estimativa: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1184"/>
        <source>&lt;b&gt;=== CÁLCULO CONCLUÍDO ===&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="728"/>
        <source>Por favor, selecione a camada de vias para a roteirização CPP.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="748"/>
        <source>&lt;b&gt;=== EXECUTANDO ROTEIRIZAÇÃO CPP ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="765"/>
        <source>-&gt; &lt;b&gt;Roteirização CPP concluída com sucesso!&lt;/b&gt; (Camada com {count} trechos viários)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="903"/>
        <source>-&gt; &lt;b&gt;Resultado da roteirização retornou vazio.&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="772"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro ao executar roteirização CPP: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="910"/>
        <source>&lt;b&gt;=== ROTEIRIZAÇÃO CONCLUÍDA ===&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="791"/>
        <source>Por favor, selecione a camada de vias para a roteirização RPP.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="811"/>
        <source>&lt;b&gt;=== EXECUTANDO ROTEIRIZAÇÃO RPP ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="829"/>
        <source>-&gt; &lt;b&gt;Roteirização RPP concluída com sucesso!&lt;/b&gt; (Camada com {count} trechos viários)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="836"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro ao executar roteirização RPP: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="858"/>
        <source>Por favor, selecione a camada de vias, o campo de demanda e a camada do depósito para a roteirização CARP.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="878"/>
        <source>&lt;b&gt;=== EXECUTANDO ROTEIRIZAÇÃO CARP ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="899"/>
        <source>-&gt; &lt;b&gt;Roteirização CARP concluída com sucesso!&lt;/b&gt; (Camada com {count} trechos viários)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="906"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro ao executar roteirização CARP: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="928"/>
        <source>Por favor, selecione a camada de rotas e o campo ID da rota para o dimensionamento de frota.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="948"/>
        <source>&lt;b&gt;=== EXECUTANDO DIMENSIONAMENTO DE FROTA ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="969"/>
        <source>-&gt; &lt;b&gt;Dimensionamento de frota concluído com sucesso!&lt;/b&gt; (Camada com {count} registros)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="973"/>
        <source>-&gt; &lt;b&gt;Resultado do dimensionamento retornou vazio.&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="976"/>
        <source>&lt;span style=&apos;color: #fc8181;&apos;&gt;Erro ao executar dimensionamento de frota: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="980"/>
        <source>&lt;b&gt;=== DIMENSIONAMENTO CONCLUÍDO ===&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="999"/>
        <source>Por favor, selecione a camada de rotas e o campo de carga para a análise de equilíbrio.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1019"/>
        <source>&lt;b&gt;=== EXECUTANDO EQUILÍBRIO ENTRE SETORES ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1041"/>
        <source>-&gt; &lt;b&gt;Equilíbrio entre setores calculado com sucesso!&lt;/b&gt; (Camada com {count} registros)&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1045"/>
        <source>-&gt; &lt;b&gt;Resultado do equilíbrio retornou vazio.&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1048"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro ao executar equilíbrio entre setores: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1052"/>
        <source>&lt;b&gt;=== ANÁLISE CONCLUÍDA ===&lt;/b&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1067"/>
        <source>Por favor, selecione a rede viária, a camada de destinos e a camada de setores para o cálculo de distância ao destino.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1087"/>
        <source>&lt;b&gt;=== EXECUTANDO DISTÂNCIA AO DESTINO ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1105"/>
        <source>-&gt; &lt;b&gt;Distância ao destino calculada com sucesso!&lt;/b&gt; (Camada com {count} registro(s))&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1109"/>
        <source>-&gt; &lt;b&gt;Resultado da distância ao destino retornou vazio.&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1112"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro ao executar distância ao destino: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1133"/>
        <source>Por favor, selecione a camada de vias exigidas e a camada de rota coberta para o cálculo de cobertura por frequência.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1153"/>
        <source>&lt;b&gt;=== EXECUTANDO COBERTURA POR FREQUÊNCIA ===&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1173"/>
        <source>-&gt; &lt;b&gt;Cobertura por frequência calculada com sucesso!&lt;/b&gt; (Camada com {count} registro(s))&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1177"/>
        <source>-&gt; &lt;b&gt;Resultado da cobertura por frequência retornou vazio.&lt;/b&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../gui/waste_dock.py" line="1180"/>
        <source>&lt;span style='color: #fc8181;'&gt;Erro ao executar cobertura por frequência: {error}&lt;/span&gt;&lt;br&gt;</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteFleetSizing</name>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="69"/>
        <source>Camada de rotas de coleta (saída de logis:waste_carp_route)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="76"/>
        <source>Campo de identificação da rota</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="84"/>
        <source>Campo de setor de coleta (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="92"/>
        <source>Velocidade média de coleta (km/h)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="101"/>
        <source>Duração da jornada de trabalho diária (horas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="110"/>
        <source>Tempo fixo de descarga por rota (horas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="119"/>
        <source>Tempo fixo de deslocamento ao destino por rota (horas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="128"/>
        <source>Dimensionamento de frota por setor</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="145"/>
        <source>Camada de rotas de coleta inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="149"/>
        <source>Campo de identificação da rota inválido.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="157"/>
        <source>Lendo rotas e somando distâncias por setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="179"/>
        <source>Nenhuma rota válida encontrada na camada de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="199"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="210"/>
        <source>Dimensionando frota do setor &apos;{sec}&apos; ({count} rota(s))...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="225"/>
        <source>Erro ao dimensionar a frota do setor &apos;{sec}&apos;: {err}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="231"/>
        <source>Setor '{sec}': {fleet} veículo(s) necessário(s) | Utilização média: {util:.1f}% | Tempo total de rotas: {total:.2f} h</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="243"/>
        <source>Aviso: frota do setor '{sec}' com utilização média abaixo de 50% ({util:.1f}%) — possível sobredimensionamento.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="270"/>
        <source>Dimensionamento de Frota de Coleta</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="273"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_fleet_sizing.py" line="279"/>
        <source>Dimensiona a frota de veículos necessária para atender às rotas de coleta de resíduos sólidos durante a jornada de trabalho, aplicando o algoritmo First-Fit Decreasing (FFD) para o problema de empacotamento (Bin Packing).

Parâmetros:
- Camada de rotas de coleta: feições de linha, tipicamente a saída de logis:waste_carp_route.
- Campo de identificação da rota (obrigatório): agrupa feições pela rota/viagem ('route_id'); a distância de cada rota é a soma do comprimento das geometrias.
- Campo de setor de coleta (opcional): se informado, dimensiona a frota separadamente por setor ('route_sector_id'); se omitido, trata a camada inteira como um único setor.
- Velocidade média de coleta: velocidade operacional em km/h (default: 10 km/h).
- Duração da jornada: tempo máximo de trabalho por veículo em horas (default: 8 h).
- Tempo fixo de descarga: tempo gasto na descarga por rota em horas (default: 0.5 h).
- Tempo fixo de deslocamento: tempo de viagem ao aterro/depósito por rota em horas (default: 0.5 h).

Uma rota isolada cuja duração exceda a jornada de trabalho gera erro explícito em vez de ser dividida entre mais de um veículo (sem split).

Retorno:
- Tabela sem geometria com uma feição por setor: 'sector_id', 'fleet_size' (nº de veículos estimado), 'num_routes' (nº de rotas do setor), 'total_route_time_h' (soma das durações das rotas) e 'avg_utilization' (utilização média da frota, entre 0 e 1).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteGenerationEstimate</name>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="61"/>
        <source>Camada de setores (população)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="68"/>
        <source>Campo de identificação do setor</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="76"/>
        <source>Campo de população (habitantes)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="84"/>
        <source>Camada de vias (com setor já associado)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="91"/>
        <source>Campo de identificação do setor na camada de vias</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="99"/>
        <source>Geração per capita (kg/hab/dia)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="108"/>
        <source>Fração de cobertura da coleta (0 a 1)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="118"/>
        <source>Vias com estimativa de geração de resíduos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="135"/>
        <source>Camada de setores inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="137"/>
        <source>Camada de vias inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="141"/>
        <source>Campo de população '{field}' não encontrado na camada de setores.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="146"/>
        <source>Campo de identificação do setor '{field}' não encontrado na camada de setores.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="151"/>
        <source>Campo de identificação do setor '{field}' não encontrado na camada de vias.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="156"/>
        <source>Lendo população dos setores...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="168"/>
        <source>Agrupando trechos de via por setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="175"/>
        <source>Trecho {fid} sem setor associado — ignorado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="185"/>
        <source>Setor '{sector}' presente na camada de vias mas não encontrado na camada de setores — ignorado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="208"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="226"/>
        <source>Geração de resíduos estimada para {count} trecho(s) de via.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="237"/>
        <source>Estimativa de Geração de Resíduos Sólidos</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="240"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_generation_estimate.py" line="246"/>
        <source>Estima a geração de resíduos sólidos (em kg/dia) por trecho de via, a partir da população de cada setor e do rateio proporcional ao comprimento dos trechos de via associados a esse setor.

A camada de vias deve chegar com um campo de identificação do setor já preenchido (ex.: executando native:joinbylocation manualmente no QGIS antes deste algorithm, ou trazendo o campo de outra fonte) — este algorithm não faz nenhum spatial join.

Parâmetros:
- Camada de setores: feições de polígono representando os setores de coleta.
- Campo de identificação do setor (setores): identifica cada setor.
- Campo de população: população de cada setor.
- Camada de vias: feições de linha representando os trechos de via a coletar.
- Campo de identificação do setor (vias): associa cada trecho de via ao seu setor.
- Geração per capita: taxa de geração diária por habitante em kg (default: 0.9 kg/hab/dia).
- Fração de cobertura: fração da população do setor efetivamente coberta pela coleta (default: 1.0).

Retorno:
- Camada de vias com a nova coluna 'waste_kg_day', contendo a geração de resíduos rateada de cada trecho (kg/dia).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteRppRoute</name>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="111"/>
        <source>Camada de vias</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="118"/>
        <source>Campo de via obrigatória para coleta (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="126"/>
        <source>Campo de setor de coleta (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="134"/>
        <source>Tolerância de nó em metros (requer CRS métrico)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="143"/>
        <source>Vias com rota de coleta (RPP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="157"/>
        <source>Camada de vias inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="170"/>
        <source>Lendo trechos de via e agrupando por setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="224"/>
        <source>{count} trecho(s) com geometria inválida foram ignorados.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="231"/>
        <source>Nenhum trecho de via válido encontrado na camada de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="249"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="262"/>
        <source>Setor '{sec}': nenhum trecho de coleta obrigatória. Ignorando setor.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="271"/>
        <source>Calculando rota RPP para o setor '{sec}' ({req_count} obrigatórios de {tot_count} trechos)...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="316"/>
        <source>Erro ao calcular rota RPP para o setor &apos;{sec}&apos;: {err}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="327"/>
        <source>Setor '{sec}': RPP concluído com {steps} passo(s). {km:.2f} km de deadhead/deslocamento.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="354"/>
        <source>Roteirização por Arcos (RPP)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="357"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_rpp_route.py" line="363"/>
        <source>Calcula a sequência de percurso para coleta de lixo por arcos em um subconjunto de vias obrigatórias usando o Problema do Carteiro Rural (Rural Postman Problem - RPP).

Parâmetros:
- Camada de vias: feições de linha com a malha viária.
- Campo de via obrigatória (opcional): campo booleano/inteiro indicando trechos de coleta obrigatória; se omitido, todas as vias são consideradas obrigatórias (equivalente ao CPP).
- Campo de setor de coleta (opcional): se informado, o RPP é resolvido separadamente por setor.
- Tolerância de nó: distância em metros para conectar vértices das vias.

Retorno:
- Camada de linha com feições duplicadas na sequência de travessia e três campos adicionais: 'route_visit_order' (posição sequencial no circuito), 'route_sector_id' (setor de coleta) e 'route_is_connector' (booleano indicando via conetora).</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>WasteSectorBalance</name>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="72"/>
        <source>Camada de rotas de coleta (ex.: saída de logis:waste_carp_route)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="79"/>
        <source>Campo de carga da rota (kg)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="89"/>
        <source>Campo de distância da rota em km (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="99"/>
        <source>Campo de identificação da rota (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="108"/>
        <source>Campo de setor de coleta (opcional)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="117"/>
        <source>Velocidade média de coleta (km/h)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="127"/>
        <source>Tempo fixo de descarga por rota (horas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="136"/>
        <source>Tempo fixo de deslocamento ao destino por rota (horas)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="145"/>
        <source>Indicadores de equilíbrio entre rotas por setor</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="163"/>
        <source>Camada de rotas de coleta inválida.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="167"/>
        <source>Campo de carga da rota '{field}' não encontrado.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="189"/>
        <source>Agrupando feições e calculando cargas e distâncias de rotas por setor...</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="228"/>
        <source>Nenhuma rota válida encontrada na camada de entrada.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="257"/>
        <source>Não foi possível criar a camada de saída.</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="310"/>
        <source>Erro ao calcular equilíbrio do setor '{sec}': {err}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="319"/>
        <source>Setor '{sec}': {num} rota(s) | Carga média: {m_load:.2f} kg (σ={std_load:.2f}, CV={cv_load:.1f}%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="332"/>
        <source>Aviso: setor '{sec}' apresenta desbalanço de carga alto (CV={cv:.1f}% &gt; 20%).</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="339"/>
        <source>Setor '{sec}': Tempo médio: {m_time:.2f} h (σ={std_time:.2f}, CV={cv_time:.1f}%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="379"/>
        <source>Equilíbrio entre Setores/Rotas de Coleta</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="382"/>
        <source>Logística Especializada — Coleta de Lixo</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../algorithms/waste_sector_balance.py" line="388"/>
        <source>Avalia o equilíbrio (balanço) de carga e tempo operacional entre rotas/setores de coleta de resíduos sólidos, calculando média, desvio padrão, mínimo, máximo e coeficiente de variação (CV).

Parâmetros:
- Camada de rotas de coleta: feições com rotas/vias (ex.: saída de logis:waste_carp_route, com campos 'route_load_kg' e 'route_distance_km').
- Campo de carga da rota (obrigatório): campo numérico com a carga total da rota (kg).
- Campo de distância da rota (opcional): campo numérico com a distância em km; se omitido, utiliza a extensão das geometrias das rotas.
- Campo de identificação da rota (opcional): se informado, agrupa feições por rota.
- Campo de setor de coleta (opcional): se informado, calcula o equilíbrio separadamente para cada setor.
- Velocidade média de coleta: velocidade operacional em km/h (default: 10 km/h).
- Tempo fixo de descarga: tempo gasto na descarga por rota em horas (default: 0.0 h).
- Tempo fixo de deslocamento: tempo de viagem ao aterro/depósito em horas (default: 0.0 h).

Retorno:
- Tabela sem geometria com uma feição por setor: 'sector_id', 'num_routes', 'total_load_kg', 'mean_load_kg', 'std_dev_load_kg', 'min_load_kg', 'max_load_kg', 'cv_load', 'total_time_h', 'mean_time_h', 'std_dev_time_h', 'min_time_h', 'max_time_h' e 'cv_time'.</source>
        <translation type="unfinished"></translation>
    </message>
</context>
</TS>
