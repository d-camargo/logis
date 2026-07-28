# -*- coding: utf-8 -*-
"""
/***************************************************************************
 logis
                                 A QGIS plugin
 Complemento do QGIS para apoiar projetos de logística no Brasil
                               -------------------
        begin                : 2026-07-19
        copyright            : (C) 2026 by Diego Camargo
        license              : GPL-3.0
 ***************************************************************************/
"""
"""Edge betweenness centrality module for the logis plugin.

Samples origin-destination pairs on a QgsGraph, computes their shortest paths via
Dijkstra, and delegates the betweenness aggregation to
`core.indicators.urban.edge_betweenness`.

References:
    - Freeman, L. C. (1977). A set of measures of centrality based on betweenness.
      Sociometry, 40(1), 35-41.
    - Brandes, U., & Pich, C. (2007). Centrality estimation in large networks.
      International Journal of Bifurcation and Chaos, 17(7), 2303-2318.
      (base teórica da aproximação por amostragem de pares OD usada aqui).
    - QGIS Documentation: Network Analysis Library (https://docs.qgis.org/)

Complexity/Scale limits:
    - Tested network scale: up to 50,000 edges and 40,000 vertices (typical large municipal network).
    - Time complexity: O(S * (E + V log V)) where S is the number of distinct sampled
      origins, V is vertices and E is edges (one Dijkstra run per distinct origin).
    - Space complexity: O(V + E).
"""

import random

from qgis.analysis import QgsGraphAnalyzer

from ..indicators.urban import edge_betweenness

LOG_TAG = "logis"


def sample_od_pairs(graph, num_samples, seed=None):
    """Randomly samples distinct origin-destination vertex pairs from a graph.

    Args:
        graph (QgsGraph): The network graph.
        num_samples (int): Number of OD pairs to sample. Must be strictly greater than zero.
        seed (int, optional): Seed for reproducible sampling.

    Returns:
        list of tuple(int, int): List of (origin_idx, destination_idx) vertex index pairs.
    """
    if num_samples <= 0:
        raise ValueError("O número de amostras (num_samples) deve ser estritamente maior que zero.")

    vertex_count = graph.vertexCount()
    if vertex_count < 2:
        raise ValueError("O grafo precisa de ao menos 2 vértices para amostrar pares OD.")

    rng = random.Random(seed)
    pairs = []
    for _ in range(num_samples):
        origin_idx = rng.randrange(vertex_count)
        destination_idx = rng.randrange(vertex_count)
        while destination_idx == origin_idx:
            destination_idx = rng.randrange(vertex_count)
        pairs.append((origin_idx, destination_idx))
    return pairs


def _path_edges(graph, tree, origin_idx, destination_idx):
    """Reconstructs the list of edge indices of the shortest path found by Dijkstra.

    Args:
        graph (QgsGraph): The network graph.
        tree (list of int): Dijkstra `tree` result: tree[v] is the incoming edge id
                             of the shortest path to vertex v, or -1 if unreachable/root.
        origin_idx (int): Origin vertex index (Dijkstra root).
        destination_idx (int): Destination vertex index.

    Returns:
        list of int: Edge indices traversed from origin to destination, in destination-to-origin
        order. Empty list if the destination is unreachable from the origin.
    """
    edges = []
    current = destination_idx
    while current != origin_idx:
        edge_id = tree[current]
        if edge_id == -1:
            return []
        edges.append(edge_id)
        edge = graph.edge(edge_id)
        current = edge.fromVertex() if edge.toVertex() == current else edge.toVertex()
    return edges


def compute_edge_betweenness(graph, num_samples, criterion_num=0, seed=None, feedback=None):
    """Computes approximate edge betweenness centrality by OD-pair sampling on a QgsGraph.

    Args:
        graph (QgsGraph): The network graph.
        num_samples (int): Number of OD pairs to sample. Must be strictly greater than zero.
        criterion_num (int): Strategy index for the shortest-path cost (e.g. 0 for distance, 1 for travel time).
        seed (int, optional): Seed for reproducible OD-pair sampling.
        feedback (QgsFeedback, optional): QGIS feedback object for progress reporting.

    Returns:
        list of float: List of length `graph.edgeCount()` with the approximate betweenness
        score of each edge (index i = score of edge i), in [0.0, 1.0].

    Raises:
        ValueError: If the graph is empty, num_samples is not positive, or no sampled
                    OD pair yields a connected path (all pairs unreachable).
    """
    if not graph or graph.vertexCount() == 0 or graph.edgeCount() == 0:
        raise ValueError("Grafo inválido ou vazio.")

    od_pairs = sample_od_pairs(graph, num_samples, seed=seed)

    # Agrupa destinos por origem para reaproveitar a árvore de Dijkstra de cada origem.
    destinations_by_origin = {}
    for origin_idx, destination_idx in od_pairs:
        destinations_by_origin.setdefault(origin_idx, []).append(destination_idx)

    paths = []
    total = len(destinations_by_origin)
    for i, (origin_idx, destinations) in enumerate(destinations_by_origin.items()):
        if feedback is not None and feedback.isCanceled():
            raise RuntimeError("Cálculo de betweenness cancelado pelo usuário.")

        tree, _costs = QgsGraphAnalyzer.dijkstra(graph, origin_idx, criterion_num)

        for destination_idx in destinations:
            path = _path_edges(graph, tree, origin_idx, destination_idx)
            if path:
                paths.append(path)

        if feedback is not None:
            feedback.setProgress(int((i + 1) / total * 100))

    if not paths:
        raise ValueError("Nenhum par OD amostrado resultou em caminho conectado.")

    return edge_betweenness(paths, graph.edgeCount())
