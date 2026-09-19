"""Módulo de dados de Unidades da Federação (UFs) do Brasil.

Fonte da tabela de UFs e códigos: IBGE (Instituto Brasileiro de Geografia e Estatística).
"""

UFS: tuple[tuple[str, str, str], ...] = (
    ("AC", "12", "Acre"),
    ("AL", "27", "Alagoas"),
    ("AM", "13", "Amazonas"),
    ("AP", "16", "Amapá"),
    ("BA", "29", "Bahia"),
    ("CE", "23", "Ceará"),
    ("DF", "53", "Distrito Federal"),
    ("ES", "32", "Espírito Santo"),
    ("GO", "52", "Goiás"),
    ("MA", "21", "Maranhão"),
    ("MG", "31", "Minas Gerais"),
    ("MS", "50", "Mato Grosso do Sul"),
    ("MT", "51", "Mato Grosso"),
    ("PA", "15", "Pará"),
    ("PB", "25", "Paraíba"),
    ("PE", "26", "Pernambuco"),
    ("PI", "22", "Piauí"),
    ("PR", "41", "Paraná"),
    ("RJ", "33", "Rio de Janeiro"),
    ("RN", "24", "Rio Grande do Norte"),
    ("RO", "11", "Rondônia"),
    ("RR", "14", "Roraima"),
    ("RS", "43", "Rio Grande do Sul"),
    ("SC", "42", "Santa Catarina"),
    ("SE", "28", "Sergipe"),
    ("SP", "35", "São Paulo"),
    ("TO", "17", "Tocantins"),
)

_MAPA_NOME: dict[str, str] = {item[0]: item[2] for item in UFS}
_MAPA_CODIGO: dict[str, str] = {item[0]: item[1] for item in UFS}


def siglas() -> list[str]:
    """Retorna a lista com as 27 siglas das UFs."""
    return [item[0] for item in UFS]


def nome_uf(sigla: str) -> str:
    """Retorna o nome da UF correspondente à sigla informada.

    Normaliza a sigla com .strip().upper().
    """
    key = sigla.strip().upper() if isinstance(sigla, str) else sigla
    if key not in _MAPA_NOME:
        raise ValueError(f"UF inválida: {sigla}")
    return _MAPA_NOME[key]


def codigo_uf(sigla: str) -> str:
    """Retorna o código IBGE de 2 dígitos da UF correspondente à sigla informada.

    Normaliza a sigla com .strip().upper().
    """
    key = sigla.strip().upper() if isinstance(sigla, str) else sigla
    if key not in _MAPA_CODIGO:
        raise ValueError(f"UF inválida: {sigla}")
    return _MAPA_CODIGO[key]
