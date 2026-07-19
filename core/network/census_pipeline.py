# -*- coding: utf-8 -*-
"""Pipeline de setores censitários: setores + variáveis do censobr via GisBR.

Obtém a malha de setores censitários do município e junta variáveis do
censobr, reaproveitando os algoritmos `gisbr:read_census_tract` e
`gisbr:join_censo` do plugin GisBR (ver CLAUDE.md seção 3).

Restrição desta rodada (F2, 2ª rodada): sem fallback de censo sem GisBR.
`gisbr:join_censo` depende da lógica de `censobr` do GisBR, que não é
reimplementada aqui — se o GisBR não estiver instalado, `fetch_census_tracts`
levanta `RuntimeError` em vez de baixar/juntar os dados por conta própria.

Referência Bibliográfica da Técnica:
    IBGE (Instituto Brasileiro de Geografia e Estatística). (2011).
    Censo Demográfico 2010: Metodologia do Censo Demográfico. Rio de Janeiro: IBGE.

Limite de Complexidade:
    Complexidade de Tempo: O(N) onde N é o número de setores censitários do município.
    Complexidade de Espaço: O(N) para o armazenamento das feições.
    Testado com municípios de até 10.000 setores censitários.
"""

from qgis.core import QgsVectorLayer, QgsProject

from ..data_backend import has_gisbr


def fetch_census_tracts(code_muni, nome_muni=None, feedback=None):
    """Obtém os setores censitários do município, já com variáveis do censobr.

    Exige o plugin GisBR instalado e registrado no Processing (`has_gisbr()`).
    Encadeia `gisbr:read_census_tract` (geometria dos setores) com
    `gisbr:join_censo` (variáveis do censobr, ex.: população/domicílios).

    Args:
        code_muni (str/int): Código IBGE de 7 dígitos do município.
        nome_muni (str, optional): Nome do município, usado apenas em mensagens de log.
        feedback (QgsProcessingFeedback, optional): Canal de feedback de progresso/log.

    Returns:
        QgsVectorLayer: Camada de polígonos dos setores censitários com as
        variáveis do censobr unidas (nomes de campo dependem do dataset
        censobr padrão de `gisbr:join_censo`).

    Raises:
        RuntimeError: Se o GisBR não estiver instalado, ou se a leitura/junção falhar.
    """
    if not has_gisbr():
        raise RuntimeError(
            "GisBR não instalado — necessário para dados de setor censitário "
            "nesta versão do logis."
        )

    import processing

    code_muni = str(code_muni)

    def log(msg):
        if feedback is not None:
            feedback.pushInfo(msg)

    label = nome_muni or code_muni
    log(f"Censo: obtendo setores censitários via GisBR (município {label})")
    try:
        tracts = processing.run("gisbr:read_census_tract", {
            "CODE": code_muni,
            "SIMPLIFIED": False,
            "OUTPUT": "TEMPORARY_OUTPUT",
        })["OUTPUT"]
    except Exception as exc:
        raise RuntimeError(f"Falha ao ler setores censitários via GisBR: {exc}")

    log("Censo: unindo variáveis do censobr aos setores (gisbr:join_censo)")
    try:
        joined = processing.run("gisbr:join_censo", {
            "INPUT": tracts,
            "JOIN_FIELD": "code_tract",
            "PREFIX": "",
            "OUTPUT": "TEMPORARY_OUTPUT",
        })["OUTPUT"]
    except Exception as exc:
        raise RuntimeError(f"Falha ao unir variáveis do censobr via GisBR: {exc}")

    if isinstance(joined, str):
        layer = QgsProject.instance().mapLayer(joined) or QgsVectorLayer(
            joined, f"census_tracts_{code_muni}", "ogr"
        )
    else:
        layer = joined

    if layer is None or not layer.isValid():
        raise RuntimeError(
            f"Falha ao obter setores censitários com dados de censo para o município {code_muni}."
        )

    return layer
