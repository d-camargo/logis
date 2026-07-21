# -*- coding: utf-8 -*-
"""
Módulo de cálculo de indicadores de geração de resíduos sólidos (logística especializada).
"""
from typing import Dict, List, Union


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


def estimate_fleet_size(
    route_distances_km: List[float],
    avg_collection_speed_kmh: float,
    shift_duration_h: float,
    unload_time_h: float,
    travel_time_to_destination_h: float
) -> Dict[str, Union[int, float, List[List[int]]]]:
    """
    Estima a dimensão da frota de veículos necessária para realizar as rotas de coleta
    de resíduos de um setor durante uma jornada de trabalho, aplicando a heurística
    First-Fit Decreasing (FFD) para o problema de empacotamento (Bin Packing).

    Fórmula / Algoritmo:
        Duração de cada rota i (h):
            duração_i = (distância_i / velocidade_média) + tempo_descarga + tempo_deslocamento

        Empacotamento First-Fit Decreasing (FFD):
            1. Ordena as rotas por duração decrescente.
            2. Para cada rota, aloca no primeiro veículo cuja jornada acumulada mais
               a duração da rota não ultrapasse a duração máxima da jornada.
            3. Se nenhum veículo existente tiver capacidade restante suficiente, aloca um novo veículo.

        Utilização média:
            utilização = soma(durações) / (número_de_veículos * duração_jornada)

    Referência Bibliográfica da Técnica:
        Johnson, D. S. (1973). Near-optimal bin packing algorithms (Tese de Doutorado,
        Massachusetts Institute of Technology).

    Limite de Complexidade:
        Complexidade de Tempo: O(R log R), onde R é o número de rotas (ordenação domina).
        Complexidade de Espaço: O(R) para armazenar as durações e as atribuições de veículos.

    Args:
        route_distances_km (List[float]): Distâncias totais das rotas de coleta do setor em km (não vazia, valores >= 0).
        avg_collection_speed_kmh (float): Velocidade média operacional durante a coleta em km/h (estritamente > 0).
        shift_duration_h (float): Duração da jornada de trabalho diária em horas (estritamente > 0).
        unload_time_h (float): Tempo fixo de descarga por rota em horas (>= 0).
        travel_time_to_destination_h (float): Tempo fixo de deslocamento até o destino por rota em horas (>= 0).

    Returns:
        Dict[str, Union[int, float, List[List[int]]]]: Dicionário com os resultados:
            - "fleet_size" (int): Número total estimado de veículos necessários.
            - "vehicle_assignments" (List[List[int]]): Índices originais das rotas atribuídas a cada veículo.
            - "total_route_time_h" (float): Soma total do tempo de todas as rotas (em horas).
            - "avg_utilization" (float): Taxa média de utilização do tempo dos veículos (entre 0 e 1).

    Raises:
        ValueError: Se route_distances_km estiver vazia ou contiver valores inválidos/negativos;
            se avg_collection_speed_kmh <= 0 ou shift_duration_h <= 0;
            se unload_time_h < 0 ou travel_time_to_destination_h < 0;
            ou se alguma rota isolada tiver duração maior que shift_duration_h.
    """
    if isinstance(avg_collection_speed_kmh, bool) or not isinstance(avg_collection_speed_kmh, (int, float)) or avg_collection_speed_kmh <= 0:
        raise ValueError("A velocidade média de coleta (avg_collection_speed_kmh) deve ser estritamente maior que zero.")

    if isinstance(shift_duration_h, bool) or not isinstance(shift_duration_h, (int, float)) or shift_duration_h <= 0:
        raise ValueError("A duração da jornada (shift_duration_h) deve ser estritamente maior que zero.")

    if isinstance(unload_time_h, bool) or not isinstance(unload_time_h, (int, float)) or unload_time_h < 0:
        raise ValueError("O tempo de descarga (unload_time_h) não pode ser negativo.")

    if isinstance(travel_time_to_destination_h, bool) or not isinstance(travel_time_to_destination_h, (int, float)) or travel_time_to_destination_h < 0:
        raise ValueError("O tempo de deslocamento ao destino (travel_time_to_destination_h) não pode ser negativo.")

    if not isinstance(route_distances_km, list) or not route_distances_km:
        raise ValueError("A lista de distâncias de rotas (route_distances_km) não pode ser vazia.")

    durations = []
    for i, dist in enumerate(route_distances_km):
        if isinstance(dist, bool) or not isinstance(dist, (int, float)) or dist < 0:
            raise ValueError("Todas as distâncias de rota em route_distances_km devem ser números não-negativos.")

        dur_h = float(dist) / avg_collection_speed_kmh + unload_time_h + travel_time_to_destination_h
        if dur_h > shift_duration_h + 1e-9:
            raise ValueError(
                f"A rota {i} possui duração estimada ({dur_h:.2f} h) superior à duração máxima da jornada ({shift_duration_h:.2f} h)."
            )
        durations.append(dur_h)

    sorted_routes = sorted(enumerate(durations), key=lambda x: x[1], reverse=True)

    bins_used_time = []
    vehicle_assignments = []

    for orig_idx, dur_h in sorted_routes:
        placed = False
        for v_idx in range(len(bins_used_time)):
            if bins_used_time[v_idx] + dur_h <= shift_duration_h + 1e-9:
                bins_used_time[v_idx] += dur_h
                vehicle_assignments[v_idx].append(orig_idx)
                placed = True
                break
        if not placed:
            bins_used_time.append(dur_h)
            vehicle_assignments.append([orig_idx])

    fleet_size = len(bins_used_time)
    total_route_time_h = sum(durations)
    avg_utilization = total_route_time_h / (fleet_size * shift_duration_h)

    return {
        "fleet_size": fleet_size,
        "vehicle_assignments": vehicle_assignments,
        "total_route_time_h": total_route_time_h,
        "avg_utilization": avg_utilization
    }

