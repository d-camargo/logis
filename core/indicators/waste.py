# -*- coding: utf-8 -*-
"""
Módulo de cálculo de indicadores de geração de resíduos sólidos (logística especializada).
"""
from typing import Any, Dict, List, Optional, Union


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


def compute_deadhead_ratio(
    lengths_km: List[float],
    deadhead_flags: List[bool],
    route_ids: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Calcula a extensão de deslocamento produtivo (coleta), improdutivo (deadhead/conector)
    e a razão de deadhead (deadhead_km / productive_km) para cada rota e no total acumulado.

    Fórmula:
        productive_km = soma(lengths_km onde deadhead_flags é False)
        deadhead_km = soma(lengths_km onde deadhead_flags é True)
        deadhead_ratio = deadhead_km / productive_km (se productive_km > 0, senão None)

    Referência Bibliográfica da Técnica:
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.
        Beltrami, E. J., & Bodin, L. D. (1974). Networks and vehicle routing for municipal
        waste collection. Networks, 4(1), 65-94.

    Limite de Complexidade:
        Complexidade de Tempo: O(N), onde N é o número de trechos (feições) em lengths_km.
        Complexidade de Espaço: O(N) para armazenar o agrupamento por rota.

    Args:
        lengths_km (List[float]): Comprimentos dos trechos de rota em km (não vazia, valores >= 0).
        deadhead_flags (List[bool]): Indicadores se cada trecho é deadhead (True) ou produtivo (False).
        route_ids (Optional[List[Any]]): Identificador da rota/setor para cada trecho. Se None,
            trata toda a entrada como pertencente a uma única rota (chave None).

    Returns:
        Dict[str, Any]: Dicionário com o resultado:
            - "routes" (Dict[Any, Dict[str, Optional[float]]]): Mapeamento de route_id para
              dicionário contendo "productive_km", "deadhead_km" e "deadhead_ratio".
            - "total" (Dict[str, Optional[float]]): Dicionário agregando todos os trechos com
              "productive_km", "deadhead_km" e "deadhead_ratio".

    Raises:
        ValueError: Se lengths_km for vazia ou contiver elementos com valor negativo ou tipo inválido;
            se deadhead_flags ou route_ids (quando fornecido) tiverem tamanho diferente de lengths_km.
    """
    if not isinstance(lengths_km, (list, tuple)) or not lengths_km:
        raise ValueError("A lista de comprimentos (lengths_km) não pode ser vazia.")

    if not isinstance(deadhead_flags, (list, tuple)) or len(deadhead_flags) != len(lengths_km):
        raise ValueError("A lista deadhead_flags deve ser fornecida e ter o mesmo tamanho de lengths_km.")

    if route_ids is not None:
        if not isinstance(route_ids, (list, tuple)) or len(route_ids) != len(lengths_km):
            raise ValueError("A lista route_ids deve ter o mesmo tamanho de lengths_km quando fornecida.")

    for length in lengths_km:
        if isinstance(length, bool) or not isinstance(length, (int, float)) or length < 0:
            raise ValueError("Todos os comprimentos em lengths_km devem ser números não-negativos.")

    effective_route_ids = route_ids if route_ids is not None else [None] * len(lengths_km)

    routes_data: Dict[Any, Dict[str, float]] = {}

    total_productive = 0.0
    total_deadhead = 0.0

    for length, is_dh, rid in zip(lengths_km, deadhead_flags, effective_route_ids):
        l_float = float(length)
        if rid not in routes_data:
            routes_data[rid] = {"productive_km": 0.0, "deadhead_km": 0.0}

        if is_dh:
            routes_data[rid]["deadhead_km"] += l_float
            total_deadhead += l_float
        else:
            routes_data[rid]["productive_km"] += l_float
            total_productive += l_float

    routes_result: Dict[Any, Dict[str, Optional[float]]] = {}
    for rid, data in routes_data.items():
        prod = data["productive_km"]
        dh = data["deadhead_km"]
        ratio = (dh / prod) if prod > 0 else None
        routes_result[rid] = {
            "productive_km": prod,
            "deadhead_km": dh,
            "deadhead_ratio": ratio
        }

    total_ratio = (total_deadhead / total_productive) if total_productive > 0 else None
    total_result: Dict[str, Optional[float]] = {
        "productive_km": total_productive,
        "deadhead_km": total_deadhead,
        "deadhead_ratio": total_ratio
    }

    return {
        "routes": routes_result,
        "total": total_result
    }


