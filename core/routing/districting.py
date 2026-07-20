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
"""Districting (setorização) pure-Python heuristics module for the logis plugin.

Provides pure Python implementations for arc-based collection sectorization:
- Farthest-first seed selection (Gonzalez k-center) over the edge-adjacency graph.
- Seed-growing region construction balanced by accumulated load.
- Local boundary-edge exchange search to improve load balance while preserving contiguity.

Edges are represented as dicts:
    {"id": edge_id, "from_node": node_key, "to_node": node_key, "length": float, "load": float}
Two edges are neighbors if they share a "from_node"/"to_node" value (node_key).
`node_key` is computed by the caller (the Processing algorithm layer), not by this module.

References:
    - Gonzalez, T. F. (1985). Clustering to minimize the maximum intercluster distance.
      Theoretical Computer Science, 38, 293-306.
    - Kalcsics, J., Nickel, S., & Schröder, M. (2005). Towards a unified territorial
      design approach – Applications, algorithms and GIS integration. Top, 13(1), 1-56.

Complexity/Scale limits:
    - select_seed_edges_farthest_first: O(K * E), K seeds each doing one O(E) BFS.
    - grow_sectors_from_seeds: O(E log E), priority queue keyed by sector load.
    - rebalance_boundary_edges: O(I * E), I = max_iterations, each iteration scans
      boundary edges and runs BFS connectivity checks bounded by the sector size.
    - Tested scale: up to ~5,000 road segments (neighborhood/collection-district scale).
"""

import heapq
from collections import deque
from typing import List, Dict, Optional, Set


def _validate_edges(edges: List[Dict]) -> Dict[object, Dict]:
    """Validates the edges list and returns a dict of edge_id -> edge."""
    if not edges:
        raise ValueError("A lista de trechos (edges) não pode ser vazia.")

    edge_by_id = {}
    for idx, edge in enumerate(edges):
        for key in ("id", "from_node", "to_node", "length", "load"):
            if key not in edge:
                raise ValueError(
                    f"Trecho no índice {idx} não possui a chave obrigatória '{key}'."
                )
        edge_id = edge["id"]
        if edge_id in edge_by_id:
            raise ValueError(f"Identificador de trecho duplicado: {edge_id}.")
        edge_by_id[edge_id] = edge

    return edge_by_id


def _build_adjacency(edge_by_id: Dict[object, Dict]) -> Dict[object, Set[object]]:
    """Builds edge_id -> set of neighboring edge_ids sharing a node_key."""
    edges_by_node: Dict[object, List[object]] = {}
    for edge_id, edge in edge_by_id.items():
        edges_by_node.setdefault(edge["from_node"], []).append(edge_id)
        edges_by_node.setdefault(edge["to_node"], []).append(edge_id)

    adjacency = {edge_id: set() for edge_id in edge_by_id}
    for node_edges in edges_by_node.values():
        for a in node_edges:
            for b in node_edges:
                if a != b:
                    adjacency[a].add(b)

    return adjacency


def _multi_source_bfs_distance(
    seeds: List[object],
    adjacency: Dict[object, Set[object]]
) -> Dict[object, float]:
    """Returns hop-distance from the nearest seed for every edge (BFS, unreachable = inf)."""
    dist = {edge_id: float("inf") for edge_id in adjacency}
    queue = deque()
    for seed in seeds:
        dist[seed] = 0
        queue.append(seed)

    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if dist[neighbor] == float("inf"):
                dist[neighbor] = dist[current] + 1
                queue.append(neighbor)

    return dist


def select_seed_edges_farthest_first(
    edges: List[Dict],
    num_sectors: int,
    start_edge_id: Optional[object] = None
) -> List[object]:
    """Selects `num_sectors` seed edges by greedy farthest-first traversal (Gonzalez k-center).

    Starts from `start_edge_id` (or the first edge in `edges` if omitted) and, at each
    step, picks the not-yet-seed edge that is farthest (in adjacency hops, via BFS) from
    every seed already chosen. This spreads seeds across the network, a good starting
    point for compact sectors.

    Referência Bibliográfica da Técnica:
        Gonzalez, T. F. (1985). Clustering to minimize the maximum intercluster distance.
        Theoretical Computer Science, 38, 293-306.

    Limite de Complexidade:
        Complexidade de Tempo: O(K * E) — K sementes, cada uma com uma BFS O(E).
        Testado até ~5.000 trechos de via.

    Args:
        edges: Lista de trechos de via (ver formato do módulo).
        num_sectors: Número de setores/sementes desejado (1 <= num_sectors <= len(edges)).
        start_edge_id: Id do trecho inicial (opcional; default: primeiro trecho da lista).

    Returns:
        Lista de edge_ids das sementes escolhidas, na ordem em que foram selecionadas.

    Raises:
        ValueError: edges vazio, num_sectors fora do intervalo válido, ou start_edge_id
            inexistente entre os trechos.
    """
    edge_by_id = _validate_edges(edges)

    if not isinstance(num_sectors, int) or not (1 <= num_sectors <= len(edge_by_id)):
        raise ValueError(
            f"num_sectors ({num_sectors}) deve ser um inteiro entre 1 e {len(edge_by_id)}."
        )

    if start_edge_id is None:
        start_edge_id = edges[0]["id"]
    elif start_edge_id not in edge_by_id:
        raise ValueError(f"start_edge_id inexistente entre os trechos: {start_edge_id}.")

    adjacency = _build_adjacency(edge_by_id)

    seeds = [start_edge_id]
    seed_set = {start_edge_id}

    order_index = {edge["id"]: idx for idx, edge in enumerate(edges)}

    while len(seeds) < num_sectors:
        dist = _multi_source_bfs_distance(seeds, adjacency)
        next_seed = max(
            (edge_id for edge_id in edge_by_id if edge_id not in seed_set),
            key=lambda edge_id: (dist[edge_id], -order_index[edge_id])
        )
        seeds.append(next_seed)
        seed_set.add(next_seed)

    return seeds


def grow_sectors_from_seeds(
    edges: List[Dict],
    seed_edge_ids: List[object]
) -> Dict[object, int]:
    """Grows contiguous sectors from seed edges, balancing accumulated load.

    Maintains a BFS frontier of unassigned edges adjacent to each sector. At each step,
    expands the sector with the smallest accumulated load by assigning it the next
    (closest, in BFS order) frontier edge. Contiguity is preserved by construction (a
    sector only ever grows from edges already assigned to it).

    Referência Bibliográfica da Técnica:
        Kalcsics, J., Nickel, S., & Schröder, M. (2005). Towards a unified territorial
        design approach – Applications, algorithms and GIS integration. Top, 13(1), 1-56.

    Limite de Complexidade:
        Complexidade de Tempo: O(E log E) — fila de prioridade por carga acumulada do setor.
        Testado até ~5.000 trechos de via.

    Args:
        edges: Lista de trechos de via (ver formato do módulo).
        seed_edge_ids: Lista de edge_ids das sementes (uma por setor); o setor resultante
            é identificado pelo índice (0-based) da semente nesta lista.

    Returns:
        Dict mapeando edge_id -> sector_id (inteiro 0-based, índice da semente).

    Raises:
        ValueError: edges vazio, seed_edge_ids vazio/duplicado/inexistente, ou algum
            trecho é inalcançável a partir de todas as sementes (rede desconectada).
    """
    edge_by_id = _validate_edges(edges)

    if not seed_edge_ids:
        raise ValueError("A lista de sementes (seed_edge_ids) não pode ser vazia.")
    if len(set(seed_edge_ids)) != len(seed_edge_ids):
        raise ValueError("As sementes (seed_edge_ids) devem ser trechos distintos.")
    for seed_id in seed_edge_ids:
        if seed_id not in edge_by_id:
            raise ValueError(f"Semente inexistente entre os trechos: {seed_id}.")

    adjacency = _build_adjacency(edge_by_id)
    num_sectors = len(seed_edge_ids)

    sector_of_edge: Dict[object, int] = {}
    sector_load = [0.0] * num_sectors
    frontier = [deque() for _ in range(num_sectors)]

    for sector_id, seed_id in enumerate(seed_edge_ids):
        sector_of_edge[seed_id] = sector_id
        sector_load[sector_id] += edge_by_id[seed_id]["load"]
        for neighbor in adjacency[seed_id]:
            frontier[sector_id].append(neighbor)

    heap = [(sector_load[i], i) for i in range(num_sectors)]
    heapq.heapify(heap)

    total_edges = len(edge_by_id)
    assigned_count = num_sectors

    while heap and assigned_count < total_edges:
        load, sector_id = heapq.heappop(heap)
        if load != sector_load[sector_id]:
            continue  # stale heap entry, load has since changed

        while frontier[sector_id] and frontier[sector_id][0] in sector_of_edge:
            frontier[sector_id].popleft()

        if not frontier[sector_id]:
            continue  # this sector's frontier is exhausted, it stops growing

        edge_id = frontier[sector_id].popleft()
        sector_of_edge[edge_id] = sector_id
        sector_load[sector_id] += edge_by_id[edge_id]["load"]
        assigned_count += 1

        for neighbor in adjacency[edge_id]:
            if neighbor not in sector_of_edge:
                frontier[sector_id].append(neighbor)

        heapq.heappush(heap, (sector_load[sector_id], sector_id))

    if assigned_count < total_edges:
        unreachable = [edge_id for edge_id in edge_by_id if edge_id not in sector_of_edge]
        raise ValueError(
            "Rede desconectada: os seguintes trechos são inalcançáveis a partir das "
            f"sementes fornecidas: {unreachable}."
        )

    return sector_of_edge


def _sector_edges(sector_id: int, sector_of_edge: Dict[object, int]) -> Set[object]:
    return {edge_id for edge_id, s in sector_of_edge.items() if s == sector_id}


def _is_sector_contiguous_without(
    sector_id: int,
    remove_edge_id: object,
    adjacency: Dict[object, Set[object]],
    sector_of_edge: Dict[object, int]
) -> bool:
    """Checks whether sector_id minus remove_edge_id remains a single connected component."""
    remaining = _sector_edges(sector_id, sector_of_edge) - {remove_edge_id}
    if not remaining:
        return False
    if len(remaining) == 1:
        return True

    start = next(iter(remaining))
    visited = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor in remaining and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return len(visited) == len(remaining)


def rebalance_boundary_edges(
    edges: List[Dict],
    sector_of_edge: Dict[object, int],
    max_iterations: int = 50
) -> Dict[object, int]:
    """Improves load balance between sectors by exchanging boundary edges.

    At each iteration, considers the boundary edges (adjacent to a different sector)
    of the heaviest-loaded sector, and tests moving each one to its lightest neighboring
    sector. A move is only accepted if it (a) reduces the gap between the heaviest and
    lightest sector load, and (b) leaves the origin sector connected without that edge
    (checked by BFS over the sector's remaining edges). Stops when no move improves
    balance or `max_iterations` is reached.

    Referência Bibliográfica da Técnica:
        Kalcsics, J., Nickel, S., & Schröder, M. (2005). Towards a unified territorial
        design approach – Applications, algorithms and GIS integration. Top, 13(1), 1-56.

    Limite de Complexidade:
        Complexidade de Tempo: O(I * E), I = max_iterations, cada iteração varre trechos
        de fronteira e faz checagens de conectividade limitadas ao setor.
        Testado até ~5.000 trechos de via.

    Args:
        edges: Lista de trechos de via (ver formato do módulo).
        sector_of_edge: Dict edge_id -> sector_id (ex.: saída de grow_sectors_from_seeds).
        max_iterations: Número máximo de iterações de troca (default: 50).

    Returns:
        Dict edge_id -> sector_id rebalanceado (novo dict; a entrada não é modificada).

    Raises:
        ValueError: edges vazio ou sector_of_edge não cobre todos os trechos.
    """
    edge_by_id = _validate_edges(edges)

    if set(sector_of_edge.keys()) != set(edge_by_id.keys()):
        raise ValueError("sector_of_edge deve conter exatamente um setor para cada trecho em edges.")

    adjacency = _build_adjacency(edge_by_id)
    sector_of_edge = dict(sector_of_edge)

    for _ in range(max_iterations):
        loads: Dict[int, float] = {}
        for edge_id, sector_id in sector_of_edge.items():
            loads[sector_id] = loads.get(sector_id, 0.0) + edge_by_id[edge_id]["load"]

        if len(loads) < 2:
            break

        heavy_sector = max(loads, key=loads.get)
        current_diff = max(loads.values()) - min(loads.values())

        boundary_edges = [
            edge_id for edge_id, sector_id in sector_of_edge.items()
            if sector_id == heavy_sector
            and any(sector_of_edge[neighbor] != heavy_sector for neighbor in adjacency[edge_id])
        ]

        if not boundary_edges:
            break

        best_move = None
        best_diff = current_diff

        for edge_id in boundary_edges:
            neighbor_sectors = {
                sector_of_edge[neighbor] for neighbor in adjacency[edge_id]
                if sector_of_edge[neighbor] != heavy_sector
            }
            edge_load = edge_by_id[edge_id]["load"]

            for target_sector in neighbor_sectors:
                new_loads = dict(loads)
                new_loads[heavy_sector] -= edge_load
                new_loads[target_sector] = new_loads.get(target_sector, 0.0) + edge_load
                new_diff = max(new_loads.values()) - min(new_loads.values())

                if new_diff < best_diff - 1e-9 and _is_sector_contiguous_without(
                    heavy_sector, edge_id, adjacency, sector_of_edge
                ):
                    best_diff = new_diff
                    best_move = (edge_id, target_sector)

        if best_move is None:
            break

        edge_id, target_sector = best_move
        sector_of_edge[edge_id] = target_sector

    return sector_of_edge
