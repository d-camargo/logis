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


def compute_route_balance(
    route_loads_kg: List[float],
    route_distances_km: Optional[List[float]] = None,
    avg_collection_speed_kmh: Optional[float] = None,
    unload_time_h: float = 0.0,
    travel_time_to_destination_h: float = 0.0
) -> Dict[str, Any]:
    """
    Calcula os indicadores de equilíbrio (balanço) entre rotas de coleta de resíduos,
    avaliando a média, o desvio padrão, o coeficiente de variação (CV) e os valores
    mínimo/máximo para carga (kg) e, opcionalmente, tempo de operação (h).

    Fórmula / Algoritmo:
        Desvio Padrão Populacional (σ):
            σ = sqrt( sum((x_i - μ)^2) / N )

        Coeficiente de Variação (CV):
            CV = σ / μ  (se μ > 0, senão 0.0)

        Tempo da Rota i (h):
            tempo_i = (distância_i / velocidade_média) + tempo_descarga + tempo_deslocamento

    Referência Bibliográfica da Técnica:
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.
        Kim, B. I., Kim, S., & Sahoo, S. (2006). Waste collection vehicle routing with
        time windows. Computers & Operations Research, 33(12), 3624-3642.

    Limite de Complexidade:
        Complexidade de Tempo: O(R), onde R é o número de rotas.
        Complexidade de Espaço: O(R) para armazenar os desvios por rota.

    Args:
        route_loads_kg (List[float]): Cargas totais de cada rota em kg (não vazia, valores >= 0).
        route_distances_km (Optional[List[float]]): Distâncias totais de cada rota em km.
            Se fornecida, deve ter o mesmo tamanho de `route_loads_kg` (valores >= 0).
        avg_collection_speed_kmh (Optional[float]): Velocidade média operacional durante a coleta
            em km/h (estritamente > 0). Obrigatório se `route_distances_km` for fornecida.
        unload_time_h (float): Tempo fixo de descarga por rota em horas (>= 0). Default: 0.0.
        travel_time_to_destination_h (float): Tempo fixo de deslocamento até o destino em horas (>= 0). Default: 0.0.

    Returns:
        Dict[str, Any]: Dicionário com os indicadores de equilíbrio:
            - "num_routes" (int): Número total de rotas avaliadas.
            - "load" (Dict[str, float]): Estatísticas de carga em kg:
                "total_kg", "mean_kg", "std_dev_kg", "min_kg", "max_kg", "cv".
            - "time" (Optional[Dict[str, float]]): Estatísticas de tempo em horas (ou None se
                distâncias/velocidade não forem fornecidas):
                "total_h", "mean_h", "std_dev_h", "min_h", "max_h", "cv".
            - "route_details" (List[Dict[str, Any]]): Lista com detalhes e desvios por rota.

    Raises:
        ValueError: Se route_loads_kg for vazia ou contiver valores inválidos/negativos;
            se route_distances_km tiver tamanho incompatível ou valores negativos;
            se route_distances_km for fornecida mas avg_collection_speed_kmh for None ou <= 0;
            se unload_time_h ou travel_time_to_destination_h forem negativos.
    """
    if not isinstance(route_loads_kg, (list, tuple)) or not route_loads_kg:
        raise ValueError("A lista de cargas por rota (route_loads_kg) não pode ser vazia.")

    for i, load in enumerate(route_loads_kg):
        if isinstance(load, bool) or not isinstance(load, (int, float)) or load < 0:
            raise ValueError(f"A carga da rota {i} em route_loads_kg deve ser um número não-negativo.")

    if isinstance(unload_time_h, bool) or not isinstance(unload_time_h, (int, float)) or unload_time_h < 0:
        raise ValueError("O tempo de descarga (unload_time_h) não pode ser negativo.")

    if isinstance(travel_time_to_destination_h, bool) or not isinstance(travel_time_to_destination_h, (int, float)) or travel_time_to_destination_h < 0:
        raise ValueError("O tempo de deslocamento ao destino (travel_time_to_destination_h) não pode ser negativo.")

    has_distances = route_distances_km is not None
    if has_distances:
        if not isinstance(route_distances_km, (list, tuple)) or len(route_distances_km) != len(route_loads_kg):
            raise ValueError("A lista route_distances_km deve ter o mesmo tamanho de route_loads_kg quando fornecida.")
        for i, dist in enumerate(route_distances_km):
            if isinstance(dist, bool) or not isinstance(dist, (int, float)) or dist < 0:
                raise ValueError(f"A distância da rota {i} em route_distances_km deve ser um número não-negativo.")

        if isinstance(avg_collection_speed_kmh, bool) or not isinstance(avg_collection_speed_kmh, (int, float)) or avg_collection_speed_kmh <= 0:
            raise ValueError("A velocidade média de coleta (avg_collection_speed_kmh) deve ser estritamente maior que zero quando route_distances_km for fornecida.")

    num_routes = len(route_loads_kg)
    loads = [float(x) for x in route_loads_kg]
    total_load = sum(loads)
    mean_load = total_load / num_routes
    var_load = sum((x - mean_load) ** 2 for x in loads) / num_routes
    std_load = var_load ** 0.5
    min_load = min(loads)
    max_load = max(loads)
    cv_load = (std_load / mean_load) if mean_load > 0 else 0.0

    load_stats = {
        "total_kg": total_load,
        "mean_kg": mean_load,
        "std_dev_kg": std_load,
        "min_kg": min_load,
        "max_kg": max_load,
        "cv": cv_load
    }

    time_stats = None
    times = None
    if has_distances:
        times = [
            (float(dist) / float(avg_collection_speed_kmh)) + float(unload_time_h) + float(travel_time_to_destination_h)
            for dist in route_distances_km
        ]
        total_time = sum(times)
        mean_time = total_time / num_routes
        var_time = sum((t - mean_time) ** 2 for t in times) / num_routes
        std_time = var_time ** 0.5
        min_time = min(times)
        max_time = max(times)
        cv_time = (std_time / mean_time) if mean_time > 0 else 0.0

        time_stats = {
            "total_h": total_time,
            "mean_h": mean_time,
            "std_dev_h": std_time,
            "min_h": min_time,
            "max_h": max_time,
            "cv": cv_time
        }

    route_details = []
    for i in range(num_routes):
        detail = {
            "route_index": i,
            "load_kg": loads[i],
            "load_dev_kg": loads[i] - mean_load
        }
        if times is not None:
            detail["time_h"] = times[i]
            detail["time_dev_h"] = times[i] - mean_time
        route_details.append(detail)

    return {
        "num_routes": num_routes,
        "load": load_stats,
        "time": time_stats,
        "route_details": route_details
    }


def waste_destination_distance(
    od_matrix: List[List[Union[int, float]]]
) -> List[float]:
    """
    Calcula a menor distância ou tempo de viagem até o ponto de destino de resíduos
    (aterro sanitário, estação de transbordo ou ecoponto) mais próximo para cada setor/origem
    de coleta, a partir de uma matriz OD (Origem-Destino).

    Fórmula:
        Custo_j = Min(od_matrix[i][j]) para todo destino i

    Referência Bibliográfica da Técnica:
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.
        Daskin, M. S. (1995). Network and Discrete Location: Models, Algorithms, and Applications.
        John Wiley & Sons.

    Limite de Complexidade:
        Complexidade de Tempo: O(D * S) onde D é o número de destinos e S é o número de setores/origens.
        Complexidade de Espaço: O(S) para a lista de distâncias/custos de retorno.

    Args:
        od_matrix (List[List[Union[int, float]]]): Matriz onde a linha i representa o destino i
            e a coluna j representa o custo para a origem/setor j.

    Returns:
        List[float]: Lista contendo a menor distância ou tempo até o destino mais próximo para cada setor/origem.

    Raises:
        ValueError: Se a matriz OD for vazia, com linhas inconsistentes ou valores negativos.
        TypeError: Se od_matrix ou seus elementos não forem do tipo correto.
    """
    if od_matrix is None:
        raise TypeError("A matriz OD (od_matrix) não pode ser None.")
    if not isinstance(od_matrix, list):
        raise TypeError("A matriz OD (od_matrix) deve ser uma lista de listas.")
    if len(od_matrix) == 0:
        raise ValueError("A matriz OD (od_matrix) não pode ser vazia (deve conter pelo menos um destino).")

    num_zones = None
    for idx, row in enumerate(od_matrix):
        if not isinstance(row, list):
            raise TypeError(f"A linha {idx} da matriz OD deve ser uma lista.")
        if len(row) == 0:
            raise ValueError(f"A linha {idx} da matriz OD não pode ser vazia.")
        if num_zones is None:
            num_zones = len(row)
        elif len(row) != num_zones:
            raise ValueError("As linhas da matriz OD devem ter tamanhos consistentes (mesmo número de origens).")

        for val in row:
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise TypeError("Os valores da matriz OD devem ser numéricos.")
            if val < 0:
                raise ValueError("Os custos na matriz OD não podem ser negativos.")

    costs = []
    for j in range(num_zones):
        min_cost = min(od_matrix[i][j] for i in range(len(od_matrix)))
        costs.append(float(min_cost))

    return costs


def compute_collection_coverage(
    required_km: List[float],
    covered_km: List[float],
    sector_ids: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Calcula a extensão de via exigida (required_km), extensão efetivamente coberta (covered_km)
    e a taxa de cobertura (coverage_pct = covered_km / required_km, capada em 1.0) por setor
    e no total acumulado.

    Fórmula:
        coverage_pct = min(1.0, covered_km / required_km) (se required_km > 0, senão None)

    Nota de Decisão:
        A cobertura percentual é capada em 1.0 (100%) por setor e no total. Embora uma rota
        possa realizar múltiplas passadas em um mesmo trecho (gerando covered_km > required_km),
        o indicador mede a cobertura de extensão distinta da malha exigida, e não a intensidade de passadas.

    Referência Bibliográfica da Técnica:
        Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). The location of emergency
        service facilities. Operations Research, 19(6), 1363-1373.
        Tchobanoglous, G., Theisen, H., & Vigil, S. A. (1993). Integrated Solid Waste
        Management: Engineering Principles and Management Issues. McGraw-Hill.

    Limite de Complexidade:
        Complexidade de Tempo: O(N), onde N é o número de entradas em required_km.
        Complexidade de Espaço: O(N) para o agrupamento por setor.

    Args:
        required_km (List[float]): Lista de extensão de via exigida em km por setor (não vazia, valores >= 0).
        covered_km (List[float]): Lista de extensão efetivamente coberta em km por setor (mesmo tamanho, valores >= 0).
        sector_ids (Optional[List[Any]]): Identificador do setor para cada entrada. Se None, trata a entrada
            como um único grupo/setor (chave None).

    Returns:
        Dict[str, Any]: Dicionário com os resultados:
            - "by_sector" (Dict[Any, Dict[str, Optional[float]]]): Mapeamento de sector_id para dicionário
              contendo "required_km", "covered_km" e "coverage_pct".
            - "total" (Dict[str, Optional[float]]): Dicionário agregando todos os setores com
              "required_km", "covered_km" e "coverage_pct".

    Raises:
        ValueError: Se required_km for vazia ou contiver elementos com valor negativo ou tipo inválido;
            se covered_km não tiver o mesmo tamanho de required_km ou contiver valores inválidos/negativos;
            se sector_ids for fornecida e não tiver o mesmo tamanho de required_km.
    """
    if not isinstance(required_km, (list, tuple)) or not required_km:
        raise ValueError("A lista de extensão exigida (required_km) não pode ser vazia.")

    if not isinstance(covered_km, (list, tuple)) or len(covered_km) != len(required_km):
        raise ValueError("A lista covered_km deve ser fornecida e ter o mesmo tamanho de required_km.")

    if sector_ids is not None:
        if not isinstance(sector_ids, (list, tuple)) or len(sector_ids) != len(required_km):
            raise ValueError("A lista sector_ids deve ter o mesmo tamanho de required_km quando fornecida.")

    for req in required_km:
        if isinstance(req, bool) or not isinstance(req, (int, float)) or req < 0:
            raise ValueError("Todos os valores em required_km devem ser números não-negativos.")

    for cov in covered_km:
        if isinstance(cov, bool) or not isinstance(cov, (int, float)) or cov < 0:
            raise ValueError("Todos os valores em covered_km devem ser números não-negativos.")

    effective_sector_ids = sector_ids if sector_ids is not None else [None] * len(required_km)

    by_sector_raw: Dict[Any, Dict[str, float]] = {}

    for req, cov, sid in zip(required_km, covered_km, effective_sector_ids):
        req_f = float(req)
        cov_f = float(cov)
        if sid not in by_sector_raw:
            by_sector_raw[sid] = {"required_km": 0.0, "covered_km": 0.0}
        by_sector_raw[sid]["required_km"] += req_f
        by_sector_raw[sid]["covered_km"] += cov_f

    by_sector: Dict[Any, Dict[str, Optional[float]]] = {}
    for sid, data in by_sector_raw.items():
        r = data["required_km"]
        c = data["covered_km"]
        pct = min(1.0, c / r) if r > 0 else None
        by_sector[sid] = {
            "required_km": r,
            "covered_km": c,
            "coverage_pct": pct
        }

    tot_req = sum(data["required_km"] for data in by_sector_raw.values())
    tot_cov = sum(data["covered_km"] for data in by_sector_raw.values())
    tot_pct = min(1.0, tot_cov / tot_req) if tot_req > 0 else None

    total: Dict[str, Optional[float]] = {
        "required_km": tot_req,
        "covered_km": tot_cov,
        "coverage_pct": tot_pct
    }

    return {
        "by_sector": by_sector,
        "total": total
    }





