# -*- coding: utf-8 -*-
"""
/***************************************************************************
 logis
                                 A QGIS plugin
 Complemento do QGIS para apoiar projetos de logística no Brasil
                               -------------------
        begin                : 2026-07-20
        copyright            : (C) 2026 by Diego Camargo
        license              : GPL-3.0
 ***************************************************************************/
"""
"""Facility location heuristics module for the logis plugin.

Provides pure Python implementations for facility location optimization:
- p-median problem (Teitz-Bart heuristic / 1-interchange local search)
- p-center problem (greedy + 1-interchange minimax local search heuristic)
- Maximum Coverage Location Problem (MCLP, Church & ReVelle greedy heuristic)
- Location Set Covering Problem (LSCP, Toregas greedy set cover heuristic)

References:
    - Teitz, M. B., & Bart, P. (1968). Heuristic methods for estimating the
      generalized vertex median of a weighted graph. Operations Research, 16(5), 955-961.
    - Church, R., & ReVelle, C. (1974). The maximal covering location problem.
      Papers of the Regional Science Association, 32(1), 101-118.
    - Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). The location of
      emergency service facilities. Operations Research, 19(6), 1363-1373.
    - Daskin, M. S. (2013). Network and discrete location: models, algorithms,
      and applications. John Wiley & Sons.

Complexity/Scale limits:
    - Tested scale: up to 1,000 demand nodes and 500 candidate locations.
    - Time complexity:
        * p-median: O(p * N * M + max_iter * p * (M - p) * N) where N is demand points,
          M is candidate sites, and p is chosen facilities.
        * MCLP: O(p * M * N).
        * LSCP: O(M * N * min(M, N)).
    - Space complexity: O(N * M) for cost matrix evaluation.
"""

from typing import List, Tuple, Optional


def _validate_inputs(
    cost_matrix: List[List[float]],
    demand_weights: List[float],
    candidate_indices: Optional[List[int]] = None
) -> Tuple[int, int, List[int]]:
    """Validates cost matrix, demand weights, and candidate indices.

    Returns:
        Tuple[int, int, List[int]]: (num_demands, num_candidates, candidate_list)
    """
    if not cost_matrix or not cost_matrix[0]:
        raise ValueError("A matriz de custos (cost_matrix) não pode ser vazia.")

    num_demands = len(cost_matrix)
    num_candidates = len(cost_matrix[0])

    for row_idx, row in enumerate(cost_matrix):
        if len(row) != num_candidates:
            raise ValueError(
                f"A matriz de custos deve ser retangular. A linha {row_idx} possui "
                f"comprimento {len(row)}, esperado {num_candidates}."
            )
        for col_idx, val in enumerate(row):
            if val < 0:
                raise ValueError(
                    f"Custo negativo encontrado na posição ({row_idx}, {col_idx}): {val}."
                )

    if len(demand_weights) != num_demands:
        raise ValueError(
            f"O número de pesos de demanda ({len(demand_weights)}) deve ser igual ao "
            f"número de linhas da matriz de custos ({num_demands})."
        )

    for w_idx, w in enumerate(demand_weights):
        if w < 0:
            raise ValueError(f"Peso de demanda negativo encontrado no índice {w_idx}: {w}.")

    if candidate_indices is None:
        candidates = list(range(num_candidates))
    else:
        if not candidate_indices:
            raise ValueError("A lista de candidatos (candidate_indices) não pode ser vazia.")
        candidates = list(dict.fromkeys(candidate_indices))
        for c in candidates:
            if not (0 <= c < num_candidates):
                raise ValueError(f"Índice de candidato inválido: {c}. Deve estar entre 0 e {num_candidates - 1}.")

    return num_demands, num_candidates, candidates


def solve_p_median(
    cost_matrix: List[List[float]],
    demand_weights: List[float],
    p: int,
    candidate_indices: Optional[List[int]] = None,
    max_iter: int = 100
) -> Tuple[List[int], float, List[int]]:
    """Solves the p-median facility location problem using the Teitz-Bart heuristic.

    Minimizes total weighted cost from demand points to their nearest facility.

    Fórmula do Custo Total:
        Custo = sum(demand_weights[i] * min_{j in S} cost_matrix[i][j])

    Referência Bibliográfica da Técnica:
        Teitz, M. B., & Bart, P. (1968). Heuristic methods for estimating the
        generalized vertex median of a weighted graph. Operations Research, 16(5), 955-961.

    Limite de Complexidade:
        Complexidade de Tempo: O(p * N * M + max_iter * p * (M - p) * N)
        Complexidade de Espaço: O(N + M)
        Testado com até 1.000 pontos de demanda e 500 candidatos.

    Args:
        cost_matrix (List[List[float]]): Matriz N x M de custos/distâncias (N demandas, M candidatos).
        demand_weights (List[float]): Lista de N pesos/demandas associados a cada ponto.
        p (int): Número de instalações a serem localizadas (1 <= p <= M).
        candidate_indices (Optional[List[int]]): Subconjunto de índices de colunas candidatas a considerar.
        max_iter (int): Número máximo de iterações do método Teitz-Bart (padrão: 100).

    Returns:
        Tuple[List[int], float, List[int]]:
            - selected_facilities (List[int]): Lista de índices de colunas das instalações escolhidas (tamanho p).
            - total_cost (float): Custo total ponderado da solução final.
            - assignments (List[int]): Instalação atribuída a cada demanda i (índice da coluna).

    Raises:
        ValueError: Se entradas forem inválidas ou p for fora dos limites.
    """
    num_demands, num_candidates, candidates = _validate_inputs(
        cost_matrix, demand_weights, candidate_indices
    )

    if p <= 0:
        raise ValueError("O número de instalações (p) deve ser maior ou igual a 1.")
    if p > len(candidates):
        raise ValueError(
            f"O número de instalações (p={p}) não pode exceder o número de candidatos disponíveis ({len(candidates)})."
        )

    # 1. Greedy construction to get a good initial set of p facilities
    selected = []
    candidates_set = set(candidates)

    for _ in range(p):
        best_candidate = None
        best_cost = float("inf")

        for c in candidates_set - set(selected):
            temp_facilities = selected + [c]
            cost = sum(
                demand_weights[i] * min(cost_matrix[i][f] for f in temp_facilities)
                for i in range(num_demands)
            )
            if cost < best_cost:
                best_cost = cost
                best_candidate = c

        if best_candidate is not None:
            selected.append(best_candidate)

    def compute_total_cost(facilities: List[int]) -> float:
        return sum(
            demand_weights[i] * min(cost_matrix[i][f] for f in facilities)
            for i in range(num_demands)
        )

    current_cost = compute_total_cost(selected)

    # 2. Teitz-Bart 1-interchange local search
    iteration = 0
    improved = True

    while improved and iteration < max_iter:
        improved = False
        iteration += 1

        for idx, current_f in enumerate(selected):
            best_swap_candidate = None
            best_swap_cost = current_cost

            unselected_candidates = [c for c in candidates if c not in selected]
            for cand in unselected_candidates:
                test_facilities = list(selected)
                test_facilities[idx] = cand
                test_cost = compute_total_cost(test_facilities)

                if test_cost < best_swap_cost - 1e-9:
                    best_swap_cost = test_cost
                    best_swap_candidate = cand

            if best_swap_candidate is not None:
                selected[idx] = best_swap_candidate
                current_cost = best_swap_cost
                improved = True
                break

    selected.sort()
    assignments = [
        min(selected, key=lambda f: cost_matrix[i][f])
        for i in range(num_demands)
    ]

    return selected, current_cost, assignments


def solve_p_center(
    cost_matrix: List[List[float]],
    demand_weights: Optional[List[float]] = None,
    p: int = 1,
    candidate_indices: Optional[List[int]] = None,
    max_iter: int = 100
) -> Tuple[List[int], float, List[int]]:
    """Solves the p-center facility location problem using a greedy + 1-interchange local search heuristic.

    Minimizes the maximum weighted cost (minimax) from any demand point to its nearest facility.

    Fórmula do Custo Máximo:
        Custo Máximo = max_{i} (demand_weights[i] * min_{j in S} cost_matrix[i][j])

    Referência Bibliográfica da Técnica:
        - Hakimi, S. L. (1964). Optimum locations of switching centers and the absolute centers
          and medians of a graph. Operations Research, 12(3), 450-459.
        - Daskin, M. S. (2013). Network and discrete location: models, algorithms,
          and applications. John Wiley & Sons.

    Limite de Complexidade:
        Complexidade de Tempo: O(p * N * M + max_iter * p * (M - p) * N)
        Complexidade de Espaço: O(N + M)
        Testado com até 1.000 pontos de demanda e 500 candidatos.

    Args:
        cost_matrix (List[List[float]]): Matriz N x M de custos/distâncias (N demandas, M candidatos).
        demand_weights (Optional[List[float]]): Lista de N pesos associados a cada ponto de demanda.
            Se None, assume peso 1.0 para todos os pontos.
        p (int): Número de instalações a serem localizadas (1 <= p <= M).
        candidate_indices (Optional[List[int]]): Subconjunto de índices de colunas candidatas a considerar.
        max_iter (int): Número máximo de iterações do refinamento por troca local (padrão: 100).

    Returns:
        Tuple[List[int], float, List[int]]:
            - selected_facilities (List[int]): Lista de índices de colunas das instalações escolhidas (tamanho p).
            - max_cost (float): Custo máximo ponderado da solução final (minimax).
            - assignments (List[int]): Instalação atribuída a cada demanda i (índice da coluna).

    Raises:
        ValueError: Se entradas forem inválidas ou p for fora dos limites.
    """
    if demand_weights is None:
        demand_weights = [1.0] * len(cost_matrix)

    num_demands, num_candidates, candidates = _validate_inputs(
        cost_matrix, demand_weights, candidate_indices
    )

    if p <= 0:
        raise ValueError("O número de instalações (p) deve ser maior ou igual a 1.")
    if p > len(candidates):
        raise ValueError(
            f"O número de instalações (p={p}) não pode exceder o número de candidatos disponíveis ({len(candidates)})."
        )

    def eval_solution(facilities: List[int]) -> Tuple[float, float]:
        max_c = 0.0
        sum_c = 0.0
        for i in range(num_demands):
            min_d = min(cost_matrix[i][f] for f in facilities)
            w_cost = demand_weights[i] * min_d
            if w_cost > max_c:
                max_c = w_cost
            sum_c += w_cost
        return max_c, sum_c

    # 1. Greedy construction phase
    selected = []
    candidates_set = set(candidates)

    for _ in range(p):
        best_candidate = None
        best_eval = (float("inf"), float("inf"))

        for c in candidates_set - set(selected):
            temp_facilities = selected + [c]
            curr_eval = eval_solution(temp_facilities)
            if curr_eval < best_eval:
                best_eval = curr_eval
                best_candidate = c

        if best_candidate is not None:
            selected.append(best_candidate)

    current_max_cost, current_sum_cost = eval_solution(selected)

    # 2. 1-interchange local search
    iteration = 0
    improved = True

    while improved and iteration < max_iter:
        improved = False
        iteration += 1

        for idx, current_f in enumerate(selected):
            best_swap_candidate = None
            best_swap_eval = (current_max_cost, current_sum_cost)

            unselected_candidates = [c for c in candidates if c not in selected]
            for cand in unselected_candidates:
                test_facilities = list(selected)
                test_facilities[idx] = cand
                test_eval = eval_solution(test_facilities)

                if test_eval[0] < best_swap_eval[0] - 1e-9 or (
                    abs(test_eval[0] - best_swap_eval[0]) <= 1e-9 and test_eval[1] < best_swap_eval[1] - 1e-9
                ):
                    best_swap_eval = test_eval
                    best_swap_candidate = cand

            if best_swap_candidate is not None:
                selected[idx] = best_swap_candidate
                current_max_cost, current_sum_cost = best_swap_eval
                improved = True
                break

    selected.sort()
    assignments = [
        min(selected, key=lambda f: cost_matrix[i][f])
        for i in range(num_demands)
    ]

    return selected, current_max_cost, assignments


def solve_mclp(
    cost_matrix: List[List[float]],
    demand_weights: List[float],
    p: int,
    max_distance: float,
    candidate_indices: Optional[List[int]] = None
) -> Tuple[List[int], float, float, float, List[bool]]:
    """Solves the Maximum Coverage Location Problem (MCLP) using Church & ReVelle's greedy heuristic.

    Maximizes total covered demand weight within a maximum service distance (max_distance).

    Referência Bibliográfica da Técnica:
        Church, R., & ReVelle, C. (1974). The maximal covering location problem.
        Papers of the Regional Science Association, 32(1), 101-118.

    Limite de Complexidade:
        Complexidade de Tempo: O(p * M * N)
        Complexidade de Espaço: O(N * M)
        Testado com até 1.000 pontos de demanda e 500 candidatos.

    Args:
        cost_matrix (List[List[float]]): Matriz N x M de custos/distâncias.
        demand_weights (List[float]): Pesos/demandas associados a cada ponto.
        p (int): Número máximo de instalações a serem localizadas (p >= 1).
        max_distance (float): Distância/tempo máximo para considerar um ponto de demanda coberto.
        candidate_indices (Optional[List[int]]): Subconjunto de candidatos.

    Returns:
        Tuple[List[int], float, float, float, List[bool]]:
            - selected_facilities (List[int]): Lista dos índices de colunas das instalações escolhidas.
            - covered_demand (float): Soma dos pesos da demanda coberta.
            - total_demand (float): Soma total dos pesos de demanda.
            - coverage_ratio (float): Proporção da demanda coberta (covered_demand / total_demand).
            - covered_mask (List[bool]): Máscara indicando se cada demanda i está coberta.

    Raises:
        ValueError: Se parâmetros forem inválidos ou max_distance <= 0.
    """
    num_demands, num_candidates, candidates = _validate_inputs(
        cost_matrix, demand_weights, candidate_indices
    )

    if p <= 0:
        raise ValueError("O número de instalações (p) deve ser maior ou igual a 1.")
    if max_distance <= 0:
        raise ValueError("A distância máxima (max_distance) deve ser estritamente maior que zero.")

    total_demand = sum(demand_weights)
    if total_demand == 0:
        return [], 0.0, 0.0, 0.0, [False] * num_demands

    p = min(p, len(candidates))

    # Coverage matrix: covers[i][j] is True if cost_matrix[i][j] <= max_distance
    covers = [
        [cost_matrix[i][j] <= max_distance for j in range(num_candidates)]
        for i in range(num_demands)
    ]

    selected = []
    covered_set = set()

    for _ in range(p):
        best_cand = None
        best_gain = -1.0

        for c in candidates:
            if c in selected:
                continue
            gain = sum(
                demand_weights[i]
                for i in range(num_demands)
                if i not in covered_set and covers[i][c]
            )
            if gain > best_gain:
                best_gain = gain
                best_cand = c

        if best_cand is None or best_gain <= 0:
            break

        selected.append(best_cand)
        for i in range(num_demands):
            if covers[i][best_cand]:
                covered_set.add(i)

    selected.sort()
    covered_mask = [i in covered_set for i in range(num_demands)]
    covered_demand = sum(demand_weights[i] for i in covered_set)
    coverage_ratio = covered_demand / total_demand if total_demand > 0 else 0.0

    return selected, covered_demand, total_demand, coverage_ratio, covered_mask


def solve_lscp(
    cost_matrix: List[List[float]],
    max_distance: float,
    candidate_indices: Optional[List[int]] = None,
    demand_weights: Optional[List[float]] = None
) -> Tuple[List[int], bool, List[int]]:
    """Solves the Location Set Covering Problem (LSCP) using a greedy set covering heuristic.

    Finds the minimum number of facilities required to cover all demand points within max_distance.

    Referência Bibliográfica da Técnica:
        Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). The location of
        emergency service facilities. Operations Research, 19(6), 1363-1373.

    Limite de Complexidade:
        Complexidade de Tempo: O(M * N * min(M, N))
        Complexidade de Espaço: O(N * M)
        Testado com até 1.000 pontos de demanda e 500 candidatos.

    Args:
        cost_matrix (List[List[float]]): Matriz N x M de custos/distâncias.
        max_distance (float): Distância/tempo máximo para considerar uma demanda coberta.
        candidate_indices (Optional[List[int]]): Subconjunto de candidatos.
        demand_weights (Optional[List[float]]): Pesos opcionais para desempate/priorização de cobertura.

    Returns:
        Tuple[List[int], bool, List[int]]:
            - selected_facilities (List[int]): Lista dos índices de colunas das instalações escolhidas.
            - is_fully_covered (bool): True se 100% das demandas foram cobertas, False caso contrário.
            - uncovered_indices (List[int]): Lista de índices de demandas não cobertas.

    Raises:
        ValueError: Se entradas forem inválidas ou max_distance <= 0.
    """
    if demand_weights is None:
        demand_weights = [1.0] * len(cost_matrix)

    num_demands, num_candidates, candidates = _validate_inputs(
        cost_matrix, demand_weights, candidate_indices
    )

    if max_distance <= 0:
        raise ValueError("A distância máxima (max_distance) deve ser estritamente maior que zero.")

    covers = [
        [cost_matrix[i][j] <= max_distance for j in range(num_candidates)]
        for i in range(num_demands)
    ]

    uncovered = set(range(num_demands))
    selected = []

    while uncovered:
        best_cand = None
        best_gain = -1.0

        for c in candidates:
            if c in selected:
                continue
            gain = sum(demand_weights[i] for i in uncovered if covers[i][c])
            if gain > best_gain:
                best_gain = gain
                best_cand = c

        if best_cand is None or best_gain <= 0:
            break

        selected.append(best_cand)
        uncovered -= {i for i in uncovered if covers[i][best_cand]}

    selected.sort()
    is_fully_covered = len(uncovered) == 0
    uncovered_indices = sorted(list(uncovered))

    return selected, is_fully_covered, uncovered_indices
