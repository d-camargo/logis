# Sobre o logis

## Motivação

Análise logística — indicadores de rede, roteirização, localização de instalações — costuma exigir sair do QGIS: exportar a rede viária, montar um grafo em outra linguagem, rodar um solver externo, importar o resultado de volta como camada. O **logis** existe para eliminar essa costura. A proposta é que todo o fluxo — da rede viária tratada até a rota final ou o ponto ótimo para um CD — aconteça dentro do QGIS, usando bases públicas brasileiras (OSM, DNIT/SNV, IBGE/geobr) e sem depender de outra ferramenta ou stack para o núcleo do trabalho.

## Os três módulos e as três camadas

O recorte em três módulos — **Urbano**, **Regional** e **Especializado** (coleta de lixo, hoje) — segue a escala da rede que cada um analisa, não uma divisão arbitrária de funcionalidades. Uma rede viária municipal (OSM) e uma malha rodoviária nacional (SNV) têm volume de dados, granularidade e fontes de demanda diferentes o suficiente para justificar pipelines de construção de grafo separados. O módulo Especializado herda a rede do Urbano, mas muda o tipo de problema: em coleta de lixo a demanda está nas **ruas**, não nos pontos — por isso a roteirização ali é por arcos (CPP/RPP/CARP), não por nós (VRP/TSP) como nos outros dois.

Dentro de cada módulo, a mesma sequência de três camadas se repete — **Indicadores**, **Roteirização** e **Localização de instalações** — porque é a sequência natural de um projeto de logística: primeiro entender a rede e a demanda, depois decidir como servi-la (rotas), depois decidir onde posicionar a infraestrutura que sustenta essas rotas (CDs, hubs, garagens, ecopontos, estações de transbordo). Repetir a estrutura entre módulos, em vez de módulos com escopos distintos entre si, mantém previsível onde procurar cada funcionalidade.

## Zero dependências obrigatórias

O logis roda apenas com **PyQGIS + a biblioteca padrão do Python**. Essa restrição não é estética: instalar um pacote Python no ambiente do QGIS é frágil ou simplesmente impossível em boa parte das instalações reais — Flatpak isola o Python do sistema, no Windows depende de achar e usar o Python certo do OSGeo4W Shell, e em muitas máquinas o usuário não tem permissão para alterar o `sys.path` do QGIS. Um plugin que exige `pip install` para funcionar deixa de funcionar para uma fatia de usuários que o autor não controla.

Por isso, grafos e caminhos mínimos usam as classes nativas `QgsGraph`, `QgsGraphBuilder` e `QgsGraphAnalyzer`, e o processamento espacial se apoia em `processing.run()` com os providers `native:`/`qgis:` já embutidos no QGIS. A otimização — VRP, facility location, roteirização por arcos — é resolvida por padrão com **heurísticas clássicas em Python puro**: savings de Clarke-Wright, sweep, 2-opt/or-opt, Teitz-Bart para p-mediana, greedy para cobertura, matching guloso e Hierholzer para o problema do carteiro chinês. Essas heurísticas entregam soluções boas, não necessariamente ótimas, e isso é comunicado na interface em vez de escondido.

`pyarrow` e o `OR-Tools` são as únicas exceções, e ambas **opcionais**: o import de cada um é *lazy* e protegido, com fallback automático para o caminho em Python puro caso o pacote não esteja instalado ou a instalação falhe — inclusive quando o usuário tenta instalar o OR-Tools e o ambiente (Flatpak, falta de wheel binário, permissões) impede. Detalhes de como instalar o OR-Tools corretamente estão em [OR-Tools](ortools.md).

## Relação com o GisBR

O logis reaproveita a **lógica** de módulos do [GisBR](https://github.com/d-camargo/gisbr) — pipeline de rede OSM, conectores, cache de downloads, geografias e demografia — por cópia adaptada, não por dependência de import: o logis não importa o pacote `gisbr`. Quando o plugin GisBR está instalado no mesmo QGIS, chamar os algoritmos `gisbr:read_*` via `processing.run()` é o caminho preferencial; na ausência dele, as cópias adaptadas de downloader e conectores mantidas no próprio logis servem como fallback secundário, para que o plugin continue funcional sozinho.

## Estado e licença

O logis está na versão **0.1.5**, marcado como `experimental` no repositório oficial de plugins do QGIS. Nessa fase, API interna, nomes de algoritmos e resultados podem mudar entre versões sem aviso prévio de compatibilidade — é preciso habilitar plugins experimentais no Gerenciador de Complementos para instalá-lo (ver [Guia de Instalação](guias/instalacao.md)). A licença é **GPL-3.0**, herdada da lógica reaproveitada do GisBR.
