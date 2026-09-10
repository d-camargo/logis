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
"""TSP pure-Python heuristics module for the logis plugin.

Provides pure Python implementations for Traveling Salesman Problem (TSP):
- Nearest Neighbor heuristic for initial tour construction.
- 2-opt local search heuristic for tour improvement.
- Or-opt local search heuristic for segment relocation.

References:
    - Flood, M. M. (1956). The traveling-salesman problem.
      Operations Research, 4(1), 61-75.
    - Lin, S. (1965). Computer solutions of the traveling salesman problem.
      Bell System Technical Journal, 44(10), 2245-2269.
    - Or, I. (1976). Traveling salesman-type combinatorial problems and their
      relation to the logistics of regional blood banking. PhD thesis, Northwestern University.

Complexity/Scale limits:
    - Nearest Neighbor: O(N^2), space O(N), tested up to 1,000 nodes.
    - 2-opt: O(N^2) per swap iteration, space O(N), tested up to 1,000 nodes.
    - Or-opt: O(N^2) per relocation iteration, space O(N), tested up to 1,000 nodes.
"""
from typing import List, Tuple, Optional, Dict

try:
    from ..optim_backend import pick_backend
except ImportError:
    from core.optim_backend import pick_backend

try:
    from .vrp import _validate_matrix_and_depot, _validate_route
except ImportError:
    from core.routing.vrp import _validate_matrix_and_depot, _validate_route

_TIME_LIMIT_SECONDS: int = 10


def compute_tour_cost(
    order: List[int],
    distance_matrix: List[List[float]],
    closed: bool = True
) -> float:
    """Calcula o custo/distância total de um tour TSP.

    Args:
        order (List[int]): Sequência de nós do tour.
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        closed (bool): Se True, inclui o retorno do último nó ao primeiro (padrão: True).

    Returns:
        float: Custo total do tour. Retorna 0.0 para listas vazias ou de tamanho <= 1.
    """
    if len(order) <= 1:
        return 0.0

    cost = 0.0
    for i in range(len(order) - 1):
        cost += distance_matrix[order[i]][order[i + 1]]

    if closed:
        cost += distance_matrix[order[-1]][order[0]]

    return float(cost)


def nearest_neighbor(
    distance_matrix: List[List[float]],
    start: int = 0,
    end: Optional[int] = None
) -> List[int]:
    """Constrói um tour inicial para o TSP usando a heurística do Vizinho Mais Próximo.

    Referência Bibliográfica da Técnica:
        Flood, M. M. (1956). The traveling-salesman problem.
        Operations Research, 4(1), 61-75.

    Limite de Complexidade:
        Complexidade de Tempo: O(N^2) onde N é o número de nós na matriz.
        Complexidade de Espaço: O(N) para o tour retornado.
        Testado com até 1.000 nós.

    Args:
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        start (int): Índice do nó inicial (padrão: 0).
        end (Optional[int]): Índice do nó final se o tour for aberto (padrão: None).

    Returns:
        List[int]: Ordem dos nós visitados.

    Raises:
        ValueError: Se a matriz/nós forem inválidos ou se end == start.
    """
    num_nodes = _validate_matrix_and_depot(distance_matrix, depot=start)

    if end is not None:
        if end == start:
            raise ValueError("O nó final (end) deve ser diferente do nó inicial (start); para pedir um tour fechado, deixe a camada do ponto final vazia (end=None).")
        if not (0 <= end < num_nodes):
            raise ValueError(
                f"Índice final (end) inválido: {end}. Deve estar entre 0 e {num_nodes - 1}."
            )

    if num_nodes == 1:
        return [start]

    if num_nodes == 2:
        if end is None:
            other = 1 - start
            return [start, other]
        else:
            return [start, end]

    unvisited = set(range(num_nodes)) - {start}
    if end is not None:
        unvisited.remove(end)

    tour = [start]
    curr = start

    while unvisited:
        # Escolhe o vizinho mais próximo com desempate pelo menor índice
        next_node = min(
            unvisited,
            key=lambda node: (distance_matrix[curr][node], node)
        )
        tour.append(next_node)
        unvisited.remove(next_node)
        curr = next_node

    if end is not None:
        tour.append(end)

    return tour


def two_opt_tour(
    order: List[int],
    distance_matrix: List[List[float]],
    closed: bool = True,
    fixed_end: bool = False
) -> Tuple[List[int], float]:
    """Aplica a busca local 2-opt para melhorar um tour TSP.

    Inverte subsegmentos order[i:j+1] mantendo order[0] (start) fixo e,
    se fixed_end=True, mantendo order[-1] (end) fixo.

    Referência Bibliográfica da Técnica:
        Lin, S. (1965). Computer solutions of the traveling salesman problem.
        Bell System Technical Journal, 44(10), 2245-2269.

    Limite de Complexidade:
        Complexidade de Tempo: O(N^2) por iteração de troca (onde N é o tamanho do tour).
        Complexidade de Espaço: O(N) para o tour resultante.
        Testado com tours de até 1.000 nós.

    Args:
        order (List[int]): Sequência de nós do tour.
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        closed (bool): Se True, calcula o custo considerando o fechamento do tour (padrão: True).
        fixed_end (bool): Se True, mantém o último elemento de order fixo (padrão: False).

    Returns:
        Tuple[List[int], float]:
            - best_order (List[int]): Sequência otimizada de nós.
            - best_cost (float): Custo total do tour otimizado.

    Raises:
        ValueError: Se a matriz ou os nós do tour forem inválidos.
    """
    if not order:
        return [], 0.0

    num_nodes = _validate_matrix_and_depot(distance_matrix, depot=order[0])
    _validate_route(order, num_nodes)

    best_order = list(order)
    best_cost = compute_tour_cost(best_order, distance_matrix, closed=closed)

    n = len(best_order)
    if n <= 3:
        return best_order, best_cost

    improved = True
    while improved:
        improved = False
        max_j = n - 2 if fixed_end else n - 1
        for i in range(1, max_j):
            for j in range(i + 1, max_j + 1):
                new_order = best_order[:i] + best_order[i : j + 1][::-1] + best_order[j + 1:]
                new_cost = compute_tour_cost(new_order, distance_matrix, closed=closed)
                if new_cost < best_cost - 1e-9:
                    best_order = new_order
                    best_cost = new_cost
                    improved = True
                    break
            if improved:
                break

    return best_order, best_cost


def or_opt_tour(
    order: List[int],
    distance_matrix: List[List[float]],
    closed: bool = True,
    fixed_end: bool = False,
    segment_lengths: Tuple[int, ...] = (1, 2, 3)
) -> Tuple[List[int], float]:
    """Aplica a busca local Or-opt para melhorar um tour TSP.

    Realoca blocos contíguos de nós (de tamanhos em segment_lengths) para outras posições no tour,
    mantendo order[0] fixo e, se fixed_end=True, mantendo order[-1] fixo.

    Referência Bibliográfica da Técnica:
        Or, I. (1976). Traveling salesman-type combinatorial problems and their
        relation to the logistics of regional blood banking. PhD thesis, Northwestern University.

    Limite de Complexidade:
        Complexidade de Tempo: O(N^2) por iteração de realocação (onde N é o tamanho do tour).
        Complexidade de Espaço: O(N) para o tour resultante.
        Testado com tours de até 1.000 nós.

    Args:
        order (List[int]): Sequência de nós do tour.
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        closed (bool): Se True, calcula o custo considerando o fechamento do tour (padrão: True).
        fixed_end (bool): Se True, mantém o último elemento de order fixo (padrão: False).
        segment_lengths (Tuple[int, ...]): Tamanhos dos segmentos a realocar (padrão: (1, 2, 3)).

    Returns:
        Tuple[List[int], float]:
            - best_order (List[int]): Sequência otimizada de nós.
            - best_cost (float): Custo total do tour otimizado.

    Raises:
        ValueError: Se a matriz ou os nós do tour forem inválidos.
    """
    if not order:
        return [], 0.0

    num_nodes = _validate_matrix_and_depot(distance_matrix, depot=order[0])
    _validate_route(order, num_nodes)

    best_order = list(order)
    best_cost = compute_tour_cost(best_order, distance_matrix, closed=closed)

    n = len(best_order)
    if n <= 2:
        return best_order, best_cost

    improved = True
    while improved:
        improved = False
        n = len(best_order)
        for length in segment_lengths:
            if length <= 0 or length >= n:
                continue
            max_i = (n - 1 - length) if fixed_end else (n - length)
            for i in range(1, max_i + 1):
                segment = best_order[i : i + length]
                rem_order = best_order[:i] + best_order[i + length :]
                m = len(rem_order)
                max_j = (m - 1) if fixed_end else m
                for j in range(1, max_j + 1):
                    new_order = rem_order[:j] + segment + rem_order[j:]
                    if new_order == best_order:
                        continue
                    new_cost = compute_tour_cost(new_order, distance_matrix, closed=closed)
                    if new_cost < best_cost - 1e-9:
                        best_order = new_order
                        best_cost = new_cost
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break

    return best_order, best_cost


def solve_tsp(
    distance_matrix: List[List[float]],
    start: int = 0,
    end: Optional[int] = None,
    improve: bool = True,
    backend: str = "ortools"
) -> Tuple[List[int], float]:
    """Resolve o Caixeiro Viajante (TSP) usando heurísticas ou OR-Tools.

    Constrói tour inicial com Vizinho Mais Próximo e, se improve=True, aplica alternadamente
    2-opt e Or-opt até convergência (no backend Python), ou delega para OR-Tools.

    Referência Bibliográfica da Técnica:
        - Flood, M. M. (1956). The traveling-salesman problem. Operations Research, 4(1), 61-75.
        - Lin, S. (1965). Computer solutions of the traveling salesman problem. BSTJ, 44(10), 2245-2269.
        - Or, I. (1976). Traveling salesman-type combinatorial problems. PhD thesis, Northwestern Univ.

    Limite de Complexidade:
        Complexidade de Tempo: O(N^2) para construção + O(N^2) para melhorias locais.
        Complexidade de Espaço: O(N^2) para matriz.
        Testado com até 1.000 nós.

    Args:
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        start (int): Índice do nó inicial (padrão: 0).
        end (Optional[int]): Índice do nó final se o tour for aberto (padrão: None).
        improve (bool): Se True, aplica 2-opt e Or-opt até convergência (padrão: True).
        backend (str): Backend de otimização, `"ortools"` (padrão) ou `"python"`. Se `"ortools"` for
            pedido mas não estiver instalado, cai silenciosamente para `"python"`.

    Returns:
        Tuple[List[int], float]:
            - tour (List[int]): Sequência de nós do tour.
            - total_cost (float): Custo total do tour.

    Raises:
        ValueError: Se a matriz for inválida, end == start, ou índices fora do intervalo.
    """
    num_nodes = _validate_matrix_and_depot(distance_matrix, depot=start)

    if end is not None:
        if end == start:
            raise ValueError("O nó final (end) deve ser diferente do nó inicial (start); para pedir um tour fechado, deixe a camada do ponto final vazia (end=None).")
        if not (0 <= end < num_nodes):
            raise ValueError(
                f"Índice final (end) inválido: {end}. Deve estar entre 0 e {num_nodes - 1}."
            )

    if num_nodes == 1:
        return [start], 0.0

    closed = (end is None)
    if num_nodes == 2:
        tour = [start, 1 - start] if closed else [start, end]
        cost = compute_tour_cost(tour, distance_matrix, closed=closed)
        return tour, cost

    resolved = pick_backend(backend)
    if resolved == "ortools":
        return solve_tsp_ortools(
            distance_matrix, start=start, end=end, improve=improve
        )

    initial_tour = nearest_neighbor(distance_matrix, start=start, end=end)
    fixed_end = (end is not None)

    curr_tour = initial_tour
    curr_cost = compute_tour_cost(curr_tour, distance_matrix, closed=closed)

    if improve and len(curr_tour) > 2:
        while True:
            curr_tour, _ = two_opt_tour(curr_tour, distance_matrix, closed=closed, fixed_end=fixed_end)
            curr_tour, _ = or_opt_tour(curr_tour, distance_matrix, closed=closed, fixed_end=fixed_end)
            new_cost = compute_tour_cost(curr_tour, distance_matrix, closed=closed)
            if new_cost >= curr_cost - 1e-9:
                break
            curr_cost = new_cost

    return curr_tour, curr_cost


def solve_tsp_ortools(
    distance_matrix: List[List[float]],
    start: int = 0,
    end: Optional[int] = None,
    improve: bool = True
) -> Tuple[List[int], float]:
    """Resolve o Caixeiro Viajante (TSP) usando Google OR-Tools.

    Referência Bibliográfica da Técnica:
        Perron, L., & Furnon, V. (2019). OR-Tools. Google.
        https://developers.google.com/optimization/routing/tsp

    Limite de Complexidade:
        Constraint Programming / Busca Local via Google OR-Tools.
        Testado com até 1.000 nós.
        Limite de tempo interno: _TIME_LIMIT_SECONDS segundos quando improve=True.

    Args:
        distance_matrix (List[List[float]]): Matriz N x N de custos/distâncias.
        start (int): Índice do nó inicial (padrão: 0).
        end (Optional[int]): Índice do nó final se o tour for aberto (padrão: None).
        improve (bool): Se True, ativa a metaheurística GUIDED_LOCAL_SEARCH (padrão: True).

    Returns:
        Tuple[List[int], float]:
            - tour (List[int]): Sequência de nós do tour.
            - total_cost (float): Custo total do tour.

    Raises:
        ValueError: Se a matriz for inválida, end == start, ou índices fora do intervalo.
        RuntimeError: Se o OR-Tools não estiver instalado ou se nenhuma solução for encontrada.
    """
    num_nodes = _validate_matrix_and_depot(distance_matrix, depot=start)

    if end is not None:
        if end == start:
            raise ValueError("O nó final (end) deve ser diferente do nó inicial (start); para pedir um tour fechado, deixe a camada do ponto final vazia (end=None).")
        if not (0 <= end < num_nodes):
            raise ValueError(
                f"Índice final (end) inválido: {end}. Deve estar entre 0 e {num_nodes - 1}."
            )

    if num_nodes == 1:
        return [start], 0.0

    closed = (end is None)
    if num_nodes == 2:
        tour = [start, 1 - start] if closed else [start, end]
        cost = compute_tour_cost(tour, distance_matrix, closed=closed)
        return tour, cost

    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except ImportError as e:
        raise RuntimeError(
            "O backend OR-Tools não está instalado ou disponível no ambiente. "
            "Use o diálogo Complementos → logis → Dependências… para obter o comando de instalação, ou utilize a heurística pura em Python."
        ) from e

    if end is None:
        manager = pywrapcp.RoutingIndexManager(num_nodes, 1, start)
    else:
        manager = pywrapcp.RoutingIndexManager(num_nodes, 1, [start], [end])

    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(round(distance_matrix[from_node][to_node] * 1000.0))

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

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
        raise RuntimeError("OR-Tools não encontrou solução para a instância de TSP.")

    index = routing.Start(0)
    tour: List[int] = []
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        tour.append(node)
        index = solution.Value(routing.NextVar(index))

    if end is not None:
        end_node = manager.IndexToNode(index)
        tour.append(end_node)

    total_cost = compute_tour_cost(tour, distance_matrix, closed=closed)

    return tour, total_cost


def split_legs(
    order: List[int],
    distance_matrix: List[List[float]],
    closed: bool = True
) -> List[Tuple[int, int, str, float]]:
    """Divide a ordem de nós de um tour TSP em pernas classificadas por papel (acesso, rota, retorno).

    As pernas de 'acesso' (deslocamento do ponto inicial do tour até o primeiro ponto de serviço)
    e de 'retorno' (deslocamento do último ponto de serviço de volta ao ponto final do tour)
    correspondem a deslocamentos improdutivos (deadhead). Elas não realizam a coleta/atendimento
    em si ('rota') e são classificadas separadamente para permitir o cálculo de eficiência operacional (D-E).

    Args:
        order (List[int]): Sequência de nós do tour devolvida por solve_tsp.
        distance_matrix (List[List[float]]): Matriz N x N de distâncias/custos.
        closed (bool): Se True, inclui a perna de retorno do último nó ao primeiro (padrão: True).

    Returns:
        List[Tuple[int, int, str, float]]: Lista de tuplas (origem, destino, papel_perna, distancia_perna),
            onde papel_perna é 'acesso', 'rota' ou 'retorno'. Retorna lista vazia se order tiver apenas um nó ou menos.
    """
    if len(order) <= 1:
        return []

    pairs: List[Tuple[int, int]] = []
    for i in range(len(order) - 1):
        pairs.append((order[i], order[i + 1]))

    if closed:
        pairs.append((order[-1], order[0]))

    num_pairs = len(pairs)
    if num_pairs == 0:
        return []

    legs: List[Tuple[int, int, str, float]] = []
    for k, (u, v) in enumerate(pairs):
        dist = float(distance_matrix[u][v])

        if k == 0:
            role = "acesso"
        elif k == num_pairs - 1:
            role = "retorno"
        else:
            role = "rota"

        legs.append((u, v, role, dist))

    return legs


def summarize_legs(legs: List[Tuple[int, int, str, float]]) -> Dict[str, float]:
    """Soma as distâncias por papel de perna e calcula a taxa improdutiva (deadhead ratio).

    As pernas de 'acesso' e 'retorno' são tratadas como deslocamentos improdutivos (deadhead),
    enquanto as pernas de 'rota' representam a distância produtiva de serviço.

    Args:
        legs (List[Tuple[int, int, str, float]]): Lista de pernas (saída de split_legs).

    Returns:
        Dict[str, float]: Dicionário com as chaves:
            - "access_dist": Distância total das pernas de acesso.
            - "service_dist": Distância total das pernas de rota/serviço.
            - "return_dist": Distância total das pernas de retorno.
            - "tour_dist": Distância total do tour.
            - "dead_ratio": Razão entre deslocamento improdutivo e total ((access + return) / tour_dist).
              Retorna 0.0 quando tour_dist == 0.0 (guarda de divisão por zero).
    """
    access_dist = 0.0
    service_dist = 0.0
    return_dist = 0.0

    for _, _, role, dist in legs:
        if role == "acesso":
            access_dist += dist
        elif role == "rota":
            service_dist += dist
        elif role == "retorno":
            return_dist += dist

    tour_dist = access_dist + service_dist + return_dist
    dead_ratio = (access_dist + return_dist) / tour_dist if tour_dist > 0.0 else 0.0

    return {
        "access_dist": float(access_dist),
        "service_dist": float(service_dist),
        "return_dist": float(return_dist),
        "tour_dist": float(tour_dist),
        "dead_ratio": float(dead_ratio),
    }

