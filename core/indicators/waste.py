# -*- coding: utf-8 -*-
"""
Módulo de cálculo de indicadores de geração de resíduos sólidos (logística especializada).
"""
from typing import List, Union


def sector_waste_generation(
    population: Union[int, float],
    per_capita_kg_day: float = 0.9,
    coverage_fraction: float = 1.0
) -> float:
    """
    Estima a geração total de resíduos sólidos (em kg/dia) de um setor de coleta,
    a partir da população do setor, da taxa de geração per capita e da fração
    da população efetivamente coberta pelo serviço de coleta.

    Fórmula:
        Geração (kg/dia) = População * Geração per capita (kg/hab/dia) * Fração de cobertura

    Referência Bibliográfica da Técnica:
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.
        SNIS - Sistema Nacional de Informações sobre Saneamento (faixa nacional ~0,9-1,0 kg/hab/dia).

    Limite de Complexidade:
        Complexidade de Tempo: O(1)
        Complexidade de Espaço: O(1)

    Args:
        population (Union[int, float]): População do setor (deve ser >= 0).
        per_capita_kg_day (float): Taxa de geração per capita em kg/hab/dia (deve ser > 0). Default: 0.9.
        coverage_fraction (float): Fração da população coberta pela coleta, entre 0 e 1. Default: 1.0.

    Returns:
        float: Geração total estimada do setor em kg/dia.

    Raises:
        ValueError: Se population < 0, per_capita_kg_day <= 0 ou coverage_fraction fora de [0, 1].
    """
    if population < 0:
        raise ValueError("A população (population) não pode ser negativa.")
    if per_capita_kg_day <= 0:
        raise ValueError("A taxa per capita (per_capita_kg_day) deve ser estritamente maior que zero.")
    if coverage_fraction < 0 or coverage_fraction > 1:
        raise ValueError("A fração de cobertura (coverage_fraction) deve estar entre 0 e 1.")

    return float(population) * per_capita_kg_day * coverage_fraction


def allocate_generation_by_street_length(
    total_generation_kg: float,
    street_lengths_m: List[float]
) -> List[float]:
    """
    Rateia a geração total de resíduos de um setor (kg/dia) entre os trechos de via
    do setor, proporcionalmente ao comprimento de cada trecho.

    Fórmula:
        Geração_trecho_i (kg/dia) = Geração_total * (comprimento_i / soma(comprimentos))

    Referência Bibliográfica da Técnica:
        Ghose, M. K., Dikshit, A. K., & Sharma, S. K. (2006). A GIS based transportation
        model for solid waste disposal – A case study on Asansol municipality.
        Waste Management, 26(11), 1287-1293.

    Limite de Complexidade:
        Complexidade de Tempo: O(N) onde N é o número de trechos de via do setor.
        Complexidade de Espaço: O(N) para a lista de retorno.

    Args:
        total_generation_kg (float): Geração total do setor em kg/dia (deve ser >= 0).
        street_lengths_m (List[float]): Comprimento de cada trecho de via do setor, em metros.
            Não pode ser vazia; cada valor deve ser estritamente maior que zero.

    Returns:
        List[float]: Geração rateada (kg/dia) de cada trecho, na mesma ordem de `street_lengths_m`.
        A soma dos valores retornados é igual a `total_generation_kg` (dentro de tolerância de
        ponto flutuante).

    Raises:
        ValueError: Se total_generation_kg < 0, se street_lengths_m estiver vazia (setor sem
            vias onde alocar a geração) ou se contiver comprimento <= 0.
    """
    if total_generation_kg < 0:
        raise ValueError("A geração total (total_generation_kg) não pode ser negativa.")
    if not street_lengths_m:
        raise ValueError(
            "A lista de comprimentos de via (street_lengths_m) não pode ser vazia "
            "(o setor não possui vias onde alocar a geração)."
        )
    for length in street_lengths_m:
        if length <= 0:
            raise ValueError("Os comprimentos de via (street_lengths_m) devem ser estritamente maiores que zero.")

    total_length = sum(street_lengths_m)
    return [total_generation_kg * (length / total_length) for length in street_lengths_m]
