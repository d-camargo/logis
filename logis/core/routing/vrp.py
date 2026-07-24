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
"""VRP pure-Python heuristics module for the logis plugin.

Provides pure Python implementations for Capacitated Vehicle Routing Problem (CVRP):
- Clarke & Wright savings algorithm for initial route construction.
- 2-opt local search heuristic for single-route improvement.

References:
    - Clarke, G., & Wright, J. W. (1964). Scheduling of vehicles from a central depot
      to a number of delivery points. Operations Research, 12(4), 568-581.
    - Lin, S. (1965). Computer solutions of the traveling salesman problem.
      Bell System Technical Journal, 44(10), 2245-2269.

Complexity/Scale limits:
    - Clarke-Wright: O(N^2 log N), space O(N^2), tested up to 1,000 demand nodes.
    - 2-opt: O(k^2) per swap iteration (k customers in route), tested up to 500 stops per route.
"""
import math
from typing import List, Tuple, Optional

try:
    from ..optim_backend import pick_backend
except ImportError:
    from core.optim_backend import pick_backend

_TIME_LIMIT_SECONDS: int = 10


def _validate_matrix_and_depot(
    distance_matrix: List[List[float]],
    depot: int = 0
) -> int:
    """Validates distance matrix and depot index.

    Returns:
        int: Number of nodes in the matrix.
    """
    if not distance_matrix or not distance_matrix[0]:
        raise ValueError("A matriz de distâncias (distance_matrix) não pode ser vazia.")

    num_nodes = len(distance_matrix)
    for row_idx, row in enumerate(distance_matrix):
        if len(row) != num_nodes:
            raise ValueError(
                f"A matriz de distâncias deve ser quadrada. A linha {row_idx} possui "
                f"comprimento {len(row)}, esperado {num_nodes}."
            )
        for col_idx, val in enumerate(row):
            if val < 0:
                raise ValueError(
                    f"Distância negativa encontrada na posição ({row_idx}, {col_idx}): {val}."
                )

    if not (0 <= depot < num_nodes):
        raise ValueError(
            f"Índice de depósito inválido: {depot}. Deve estar entre 0 e {num_nodes - 1}."
        )

    return num_nodes


def _validate_demands(
    demands: List[float],
    capacity: float,
    num_nodes: int,
    depot: int = 0
) -> None:
    """Validates demands vector and vehicle capacity against matrix size and depot."""
    if len(demands) != num_nodes:
        raise ValueError(
            f"O número de demandas ({len(demands)}) deve ser igual ao tamanho da matriz ({num_nodes})."
        )

    for i, d in enumerate(demands):
        if d < 0:
            raise ValueError(f"Demanda negativa encontrada no nó {i}: {d}.")

    if capacity <= 0:
        raise ValueError("A capacidade do veículo deve ser estritamente maior que zero.")

    for i, d in enumerate(demands):
        if i != depot and d > capacity:
            raise ValueError(
                f"A demanda do nó {i} ({d}) excede a capacidade máxima do veículo ({capacity})."
            )


def _validate_route(
    route: List[int],
    num_nodes: int
) -> None:
    """Validates route customer indices."""
    for idx, node in enumerate(route):
        if not isinstance(node, int) or not (0 <= node < num_nodes):
            raise ValueError(
                f"Nó inválido na rota no índice {idx}: {node}. Deve ser um inteiro entre 0 e {num_nodes - 1}."
            )


def compute_route_distance(
    route: List[int],
    distance_matrix: List[List[float]],
    depot: int = 0
) -> float:
    """Calculates total distance of a route starting and ending at depot."""
    if not route:
        return 0.0
    dist = distance_matrix[depot][route[0]]
    for i in range(len(route) - 1):
        dist += distance_matrix[route[i]][route[i + 1]]
    dist += distance_matrix[route[-1]][depot]
    return dist


def clarke_wright_savings(
    distance_matrix: List[List[float]],
    demands: List[float],
    capacity: float,
    depot: int = 0
) -> Tuple[List[List[int]], float, List[float]]:
    """Constructs initial VRP routes using the Clarke & Wright savings algorithm.

    Referência Bibliográfica da Técnica:
        Clarke, G., & Wright, J. W. (1964). Scheduling of vehicles from a central depot
        to a number of delivery points. Operations Research, 12(4), 568-581.

    Limite de Complexidade:
        Complexidade de Tempo: O(N^2 log N) onde N é o número de nós.
        Complexidade de Espaço: O(N^2) para lista de economias.
        Testado com até 1.000 nós de demanda.

    Args:
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        demands (List[float]): Vetor N com a demanda de cada nó (demanda do depósito deve ser 0).
        capacity (float): Capacidade máxima do veículo (capacidade > 0).
        depot (int): Índice do nó de depósito (padrão: 0).

    Returns:
        Tuple[List[List[int]], float, List[float]]:
            - routes (List[List[int]]): Lista de rotas (cada rota é uma lista de índices de clientes).
            - total_distance (float): Soma das distâncias de todas as rotas.
            - route_loads (List[float]): Carga total transportada em cada rota.

    Raises:
        ValueError: Se entradas forem inválidas ou demanda exceder capacidade.
    """
    num_nodes = _validate_matrix_and_depot(distance_matrix, depot)
    _validate_demands(demands, capacity, num_nodes, depot)

    # Customers to route (ignoring depot and nodes with 0 demand if any)
    customers = [i for i in range(num_nodes) if i != depot and demands[i] > 0]

    if not customers:
        return [], 0.0, []

    # Initial routes: one route per customer
    routes: List[List[int]] = [[c] for c in customers]
    route_loads: List[float] = [demands[c] for c in customers]

    # Node to route index mapping
    node_to_route = {c: idx for idx, c in enumerate(customers)}

    # Calculate savings s_ij = d(0, i) + d(0, j) - d(i, j)
    savings = []
    for i_idx, i in enumerate(customers):
        for j in customers[i_idx + 1:]:
            s = distance_matrix[depot][i] + distance_matrix[depot][j] - distance_matrix[i][j]
            savings.append((s, i, j))

    savings.sort(key=lambda x: x[0], reverse=True)

    # Merge routes based on savings
    for s, i, j in savings:
        r_i = node_to_route[i]
        r_j = node_to_route[j]

        if r_i == r_j:
            continue

        route1 = routes[r_i]
        route2 = routes[r_j]

        if route_loads[r_i] + route_loads[r_j] > capacity:
            continue

        # Check endpoints
        if route1[-1] == i and route2[0] == j:
            merged = route1 + route2
        elif route1[0] == i and route2[0] == j:
            merged = route1[::-1] + route2
        elif route1[-1] == i and route2[-1] == j:
            merged = route1 + route2[::-1]
        elif route1[0] == i and route2[-1] == j:
            merged = route2 + route1
        else:
            continue

        # Update merged route
        routes[r_i] = merged
        route_loads[r_i] += route_loads[r_j]

        # Update node mappings
        for node in route2:
            node_to_route[node] = r_i

        # Mark r_j as empty
        routes[r_j] = []
        route_loads[r_j] = 0.0

    # Filter non-empty routes
    final_routes = [r for r in routes if r]
    final_loads = [sum(demands[c] for c in r) for r in final_routes]
    total_dist = sum(compute_route_distance(r, distance_matrix, depot) for r in final_routes)

    return final_routes, total_dist, final_loads


def two_opt(
    route: List[int],
    distance_matrix: List[List[float]],
    depot: int = 0
) -> Tuple[List[int], float]:
    """Applies the 2-opt local search heuristic to improve a single VRP route.

    The depot remains fixed at both endpoints (start and end) of the route.
    Iteratively reverses subsegments of the route if the reversal reduces total distance.

    Fórmula da Troca 2-opt:
        Dada uma rota de clientes R = [r_0, r_1, ..., r_{k-1}] com depósito D nas extremidades,
        avalia a inversão do subsegmento R[i:j+1] -> R[i:j+1][::-1] para 0 <= i < j < k.

    Referência Bibliográfica da Técnica:
        Lin, S. (1965). Computer solutions of the traveling salesman problem.
        Bell System Technical Journal, 44(10), 2245-2269.

    Limite de Complexidade:
        Complexidade de Tempo: O(k^2) por iteração de troca (onde k é o número de clientes na rota).
        Complexidade de Espaço: O(k) para a rota resultante.
        Testado com rotas de até 500 paradas.

    Args:
        route (List[int]): Lista de índices de clientes na rota (sem incluir o depósito nas pontas).
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        depot (int): Índice do nó de depósito (padrão: 0).

    Returns:
        Tuple[List[int], float]:
            - best_route (List[int]): Lista otimizada de índices de clientes.
            - best_distance (float): Distância total da rota otimizada (incluindo ida/volta ao depósito).

    Raises:
        ValueError: Se a matriz não for quadrada, contiver valores negativos, ou se índices forem inválidos.
    """
    num_nodes = _validate_matrix_and_depot(distance_matrix, depot)
    _validate_route(route, num_nodes)

    best_route = list(route)
    best_dist = compute_route_distance(best_route, distance_matrix, depot)

    if len(best_route) <= 1:
        return best_route, best_dist

    improved = True
    while improved:
        improved = False
        n = len(best_route)
        for i in range(n - 1):
            for j in range(i + 1, n):
                new_route = best_route[:i] + best_route[i:j + 1][::-1] + best_route[j + 1:]
                new_dist = compute_route_distance(new_route, distance_matrix, depot)
                if new_dist < best_dist - 1e-9:
                    best_route = new_route
                    best_dist = new_dist
                    improved = True
                    break
            if improved:
                break

    return best_route, best_dist


def or_opt(
    route: List[int],
    distance_matrix: List[List[float]],
    depot: int = 0,
    segment_lengths: Tuple[int, ...] = (1, 2, 3)
) -> Tuple[List[int], float]:
    """Applies the Or-opt local search heuristic to improve a single VRP route.

    Relocates contiguous segments of customers (of lengths specified in segment_lengths)
    to other positions within the same route. The depot remains fixed at both endpoints.

    Fórmula da Realocação Or-opt:
        Dada uma rota de clientes R = [r_0, r_1, ..., r_{k-1}], para cada tamanho de segmento
        L em segment_lengths, remove um subsegmento R[i:i+L] de comprimento L e o insere
        em outra posição j na rota resultante.

    Referência Bibliográfica da Técnica:
        Or, I. (1976). Traveling salesman-type combinatorial problems and their
        relation to the logistics of regional blood banking. PhD thesis, Northwestern University.

    Limite de Complexidade:
        Complexidade de Tempo: O(k^2) por iteração de realocação (onde k é o número de clientes na rota).
        Complexidade de Espaço: O(k) para a rota resultante.
        Testado com rotas de até 500 paradas.

    Args:
        route (List[int]): Lista de índices de clientes na rota (sem incluir o depósito nas pontas).
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        depot (int): Índice do nó de depósito (padrão: 0).
        segment_lengths (Tuple[int, ...]): Tamanhos de segmentos consecutivos a realocar (padrão: (1, 2, 3)).

    Returns:
        Tuple[List[int], float]:
            - best_route (List[int]): Lista otimizada de índices de clientes.
            - best_distance (float): Distância total da rota otimizada (incluindo ida/volta ao depósito).

    Raises:
        ValueError: Se a matriz não for quadrada, contiver valores negativos, ou se índices forem inválidos.
    """
    num_nodes = _validate_matrix_and_depot(distance_matrix, depot)
    _validate_route(route, num_nodes)

    best_route = list(route)
    best_dist = compute_route_distance(best_route, distance_matrix, depot)

    if len(best_route) <= 1:
        return best_route, best_dist

    improved = True
    while improved:
        improved = False
        n = len(best_route)
        for length in segment_lengths:
            if length <= 0 or length > n:
                continue
            for i in range(n - length + 1):
                segment = best_route[i:i + length]
                rem_route = best_route[:i] + best_route[i + length:]
                for j in range(len(rem_route) + 1):
                    if j == i:
                        continue
                    new_route = rem_route[:j] + segment + rem_route[j:]
                    new_dist = compute_route_distance(new_route, distance_matrix, depot)
                    if new_dist < best_dist - 1e-9:
                        best_route = new_route
                        best_dist = new_dist
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break

    return best_route, best_dist


def solve_cvrp(
    distance_matrix: List[List[float]],
    demands: List[float],
    capacity: float,
    depot: int = 0,
    improve: bool = True,
    backend: str = "python"
) -> Tuple[List[List[int]], float, List[float]]:
    """Solves the Capacitated Vehicle Routing Problem (CVRP) using Savings and local search heuristics.

    Combines Clarke & Wright savings algorithm for initial route construction with
    2-opt and Or-opt local search heuristics applied iteratively to each route
    when improve is True.

    Referência Bibliográfica da Técnica:
        - Clarke, G., & Wright, J. W. (1964). Scheduling of vehicles from a central depot
          to a number of delivery points. Operations Research, 12(4), 568-581.
        - Lin, S. (1965). Computer solutions of the traveling salesman problem.
          Bell System Technical Journal, 44(10), 2245-2269.
        - Or, I. (1976). Traveling salesman-type combinatorial problems and their
          relation to the logistics of regional blood banking. PhD thesis, Northwestern University.

    Limite de Complexidade:
        Complexidade de Tempo: O(N^2 log N) para a construção + O(R * k^2) para a fase de melhoria,
        onde N é o número de nós, R é o número de rotas e k é o tamanho da maior rota.
        Complexidade de Espaço: O(N^2) para matriz/economias.
        Testado com até 1.000 nós de demanda.

    Args:
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        demands (List[float]): Vetor N com a demanda de cada nó (demanda do depósito deve ser 0).
        capacity (float): Capacidade máxima do veículo (capacidade > 0).
        depot (int): Índice do nó de depósito (padrão: 0).
        improve (bool): Se True, aplica 2-opt e Or-opt até convergência em cada rota (padrão: True).
        backend (str): Backend de otimização, `"python"` (heurística Clarke-Wright + 2-opt/Or-opt,
            padrão) ou `"ortools"` (delega para `solve_cvrp_ortools`). Se `"ortools"` for pedido mas
            o OR-Tools não estiver instalado, cai silenciosamente para `"python"` com um aviso de
            log (ver `core.optim_backend.pick_backend`).

    Returns:
        Tuple[List[List[int]], float, List[float]]:
            - routes (List[List[int]]): Lista de rotas (cada rota é uma lista de índices de clientes).
            - total_distance (float): Soma das distâncias de todas as rotas.
            - route_loads (List[float]): Carga total transportada em cada rota.

    Raises:
        ValueError: Se entradas forem inválidas ou demanda exceder capacidade.
    """
    resolved = pick_backend(backend)
    if resolved == "ortools":
        return solve_cvrp_ortools(
            distance_matrix, demands, capacity, depot=depot, improve=improve
        )

    routes, _, route_loads = clarke_wright_savings(
        distance_matrix, demands, capacity, depot=depot
    )

    if improve and routes:
        improved_routes = []
        for route in routes:
            curr_route = route
            curr_dist = compute_route_distance(curr_route, distance_matrix, depot)
            while True:
                curr_route, _ = two_opt(curr_route, distance_matrix, depot)
                curr_route, _ = or_opt(curr_route, distance_matrix, depot)
                new_dist = compute_route_distance(curr_route, distance_matrix, depot)
                if new_dist >= curr_dist - 1e-9:
                    break
                curr_dist = new_dist
            improved_routes.append(curr_route)
        routes = improved_routes
        route_loads = [sum(demands[c] for c in r) for r in routes]

    total_distance = sum(
        compute_route_distance(r, distance_matrix, depot) for r in routes
    )

    return routes, total_distance, route_loads


def solve_cvrp_ortools(
    distance_matrix: List[List[float]],
    demands: List[float],
    capacity: float,
    depot: int = 0,
    improve: bool = True
) -> Tuple[List[List[int]], float, List[float]]:
    """Solves the Capacitated Vehicle Routing Problem (CVRP) using Google OR-Tools.

    Uses OR-Tools Constraint Programming (CP-SAT/Routing) solver as an optimization backend.
    Applies PATH_CHEAPEST_ARC for initial solution construction and, when improve is True,
    GUIDED_LOCAL_SEARCH metaheuristic with a time limit of _TIME_LIMIT_SECONDS seconds.

    Referência Bibliográfica da Técnica:
        Perron, L., & Furnon, V. (2019). OR-Tools. Google.
        https://developers.google.com/optimization/routing/cvrp

    Limite de Complexidade:
        Constraint Programming / Busca Local via Google OR-Tools.
        Testado com até 1.000 nós de demanda.
        Limite de tempo interno: _TIME_LIMIT_SECONDS segundos quando improve=True.

    Args:
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        demands (List[float]): Vetor N com a demanda de cada nó (demanda do depósito deve ser 0).
        capacity (float): Capacidade máxima do veículo (capacidade > 0).
        depot (int): Índice do nó de depósito (padrão: 0).
        improve (bool): Se True, ativa a metaheurística GUIDED_LOCAL_SEARCH (padrão: True).

    Returns:
        Tuple[List[List[int]], float, List[float]]:
            - routes (List[List[int]]): Lista de rotas (cada rota é uma lista de índices de clientes).
            - total_distance (float): Soma das distâncias de todas as rotas.
            - route_loads (List[float]): Carga total transportada em cada rota.

    Raises:
        ValueError: Se entradas forem inválidas ou demanda exceder capacidade.
        RuntimeError: Se o OR-Tools não estiver instalado ou se nenhuma solução for encontrada.
    """
    num_nodes = _validate_matrix_and_depot(distance_matrix, depot)
    _validate_demands(demands, capacity, num_nodes, depot)

    customers = [i for i in range(num_nodes) if i != depot and demands[i] > 0]
    if not customers:
        return [], 0.0, []

    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except ImportError as e:
        raise RuntimeError(
            "O backend OR-Tools não está instalado ou disponível no ambiente. "
            "Instale-o via core/ortools_installer.py ou utilize a heurística pura em Python."
        ) from e

    num_vehicles = min(len(customers), max(1, math.ceil(sum(demands) / capacity)) + 2)

    manager = pywrapcp.RoutingIndexManager(num_nodes, num_vehicles, depot)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(round(distance_matrix[from_node][to_node] * 1000.0))

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return int(round(demands[from_node] * 1000.0))

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

    cap_int = int(round(capacity * 1000.0))
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        [cap_int] * num_vehicles,  # vehicle maximum capacities
        True,  # start cumul to zero
        "Capacity"
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    if improve:
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = _TIME_LIMIT_SECONDS

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        raise RuntimeError("OR-Tools não encontrou solução para a instância de CVRP.")

    routes: List[List[int]] = []
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route: List[int] = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != depot:
                route.append(node)
            index = solution.Value(routing.NextVar(index))
        if route:
            routes.append(route)

    route_loads = [sum(demands[c] for c in r) for r in routes]
    total_distance = sum(compute_route_distance(r, distance_matrix, depot) for r in routes)

    return routes, total_distance, route_loads


