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
"""Arc Routing pure-Python heuristics module for the logis plugin.

Provides pure Python implementations for the undirected Chinese Postman
Problem (CPP) on edge-based network graphs (RPP and CARP are out of scope
for this module — see CLAUDE.md section 6):
- Identification of odd-degree nodes in edge-based network graphs.
- Shortest path computation between node keys weighted by length (Dijkstra).
- Greedy matching of odd-degree nodes via shortest path search.
- Eulerian circuit construction (Hierholzer) over the duplicated-edge multigraph.

Edges are represented as dicts:
    {"id": edge_id, "from_node": node_key, "to_node": node_key, "length": float}
Two edges share a node if they have matching "from_node" or "to_node" values.
`node_key` is computed by the caller (the Processing algorithm layer), not by this module.

References:
    - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
      Mathematical Programming, 5(1), 88-124.
    - Hierholzer, C. (1873). Über die Möglichkeit, einen Linienzug ohne Wiederholung
      und ohne Unterbrechung zu umfahren. Mathematische Annalen, 6(1), 30-32.

Complexity/Scale limits:
    - find_odd_degree_nodes: O(E), scans all edges and counts node degrees.
    - shortest_path_between_nodes: O(E log V), standard Dijkstra algorithm with priority queue.
    - match_odd_degree_nodes: O(K² log V), greedy pairing of K odd-degree nodes using Dijkstra.
    - Tested scale: up to ~5,000 road segments (neighborhood/collection-district scale).
"""

import heapq
from typing import List, Dict, Tuple, Optional


def _validate_edges(edges: List[Dict]) -> Dict[object, Dict]:
    """Validates the edges list and returns a dict of edge_id -> edge."""
    if not edges:
        raise ValueError("A lista de trechos (edges) não pode ser vazia.")

    edge_by_id = {}
    for idx, edge in enumerate(edges):
        for key in ("id", "from_node", "to_node", "length"):
            if key not in edge:
                raise ValueError(
                    f"Trecho no índice {idx} não possui a chave obrigatória '{key}'."
                )
        length = edge["length"]
        if not isinstance(length, (int, float)) or length < 0:
            raise ValueError(
                f"Trecho no índice {idx} tem comprimento (length) inválido: {length}."
            )

        edge_id = edge["id"]
        if edge_id in edge_by_id:
            raise ValueError(f"Identificador de trecho duplicado: {edge_id}.")
        edge_by_id[edge_id] = edge

    return edge_by_id


def find_odd_degree_nodes(edges: List[Dict]) -> List[object]:
    """Localiza todos os nós de grau ímpar no grafo formado pelos trechos de via.

    Calcula o grau de cada nó somando as incidências dos trechos. Trechos em laço
    (self-loops, onde de_nó == para_nó) contribuem com +2 para o grau do nó.

    Referência Bibliográfica da Técnica:
        - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
          Mathematical Programming, 5(1), 88-124.
        - Hierholzer, C. (1873). Über die Möglichkeit, einen Linienzug ohne Wiederholung
          und ohne Unterbrechung zu umfahren. Mathematische Annalen, 6(1), 30-32.

    Limite de Complexidade:
        Complexidade de Tempo: O(E) — varre a lista de trechos e calcula os graus dos nós.
        Testado com até ~5.000 trechos de via.

    Args:
        edges: Lista de trechos de via (ver formato do módulo).

    Returns:
        Lista com os identificadores (node_key) dos nós de grau ímpar.

    Raises:
        ValueError: Se a lista de trechos for vazia ou inválida.
    """
    _validate_edges(edges)

    degree: Dict[object, int] = {}
    node_order: List[object] = []

    for edge in edges:
        u = edge["from_node"]
        v = edge["to_node"]

        if u not in degree:
            node_order.append(u)
            degree[u] = 0
        if v not in degree:
            node_order.append(v)
            degree[v] = 0

        if u == v:
            degree[u] += 2
        else:
            degree[u] += 1
            degree[v] += 1

    odd_nodes = [node for node in node_order if degree[node] % 2 != 0]

    try:
        return sorted(odd_nodes)
    except TypeError:
        return odd_nodes


def shortest_path_between_nodes(
    edges: List[Dict],
    source: object,
    target: object
) -> Tuple[float, List[object]]:
    """Calcula o caminho mínimo entre dois nós da rede ponderado por comprimento (length).

    Utiliza o algoritmo de Dijkstra com fila de prioridade (min-heap) sobre o grafo
    de nós derivado da lista de trechos de via.

    Referência Bibliográfica da Técnica:
        - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
          Mathematical Programming, 5(1), 88-124.
        - Hierholzer, C. (1873). Über die Möglichkeit, einen Linienzug ohne Wiederholung
          und ohne Unterbrechung zu umfahren. Mathematische Annalen, 6(1), 30-32.

    Limite de Complexidade:
        Complexidade de Tempo: O(E log V) — Dijkstra ponderado com min-heap.
        Testado com até ~5.000 trechos de via.

    Args:
        edges: Lista de trechos de via (ver formato do módulo).
        source: Identificador (node_key) do nó de origem.
        target: Identificador (node_key) do nó de destino.

    Returns:
        Tupla (distância_total, lista_de_edge_ids) contendo a distância acumulada
        e os IDs dos trechos que compõem o caminho ordenado de origem a destino.

    Raises:
        ValueError: Se a lista de trechos for inválida, se origem/destino não pertencerem
            ao grafo, ou se não houver caminho entre origem e destino (rede desconectada).
    """
    edge_by_id = _validate_edges(edges)

    nodes = set()
    for edge in edge_by_id.values():
        nodes.add(edge["from_node"])
        nodes.add(edge["to_node"])

    if source not in nodes:
        raise ValueError(f"Nó origem '{source}' não pertence ao grafo.")
    if target not in nodes:
        raise ValueError(f"Nó destino '{target}' não pertence ao grafo.")

    if source == target:
        return 0.0, []

    adjacency: Dict[object, List[Tuple[object, object, float]]] = {n: [] for n in nodes}
    for edge_id, edge in edge_by_id.items():
        u = edge["from_node"]
        v = edge["to_node"]
        length = float(edge["length"])
        adjacency[u].append((v, edge_id, length))
        if u != v:
            adjacency[v].append((u, edge_id, length))

    distances: Dict[object, float] = {n: float("inf") for n in nodes}
    previous: Dict[object, Tuple[object, object]] = {}

    distances[source] = 0.0
    counter = 0
    pq: List[Tuple[float, int, object]] = [(0.0, counter, source)]

    while pq:
        dist, _, current = heapq.heappop(pq)
        if dist > distances[current]:
            continue
        if current == target:
            break

        for neighbor, edge_id, weight in adjacency[current]:
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = (current, edge_id)
                counter += 1
                heapq.heappush(pq, (new_dist, counter, neighbor))

    if distances[target] == float("inf"):
        raise ValueError(
            f"Não há caminho entre o nó origem '{source}' e o nó destino '{target}'."
        )

    path_edges = []
    curr = target
    while curr != source:
        prev_node, edge_id = previous[curr]
        path_edges.append(edge_id)
        curr = prev_node

    path_edges.reverse()
    return distances[target], path_edges


def match_odd_degree_nodes(
    edges: List[Dict],
    odd_nodes: List[object]
) -> List[Tuple[object, object, List[object]]]:
    """Emparelha os nós de grau ímpar de forma gulosa utilizando o caminho mínimo.

    Enquanto houver nós ímpares não emparelhados, seleciona o primeiro nó da lista,
    calcula o caminho mínimo (via shortest_path_between_nodes) até cada outro nó ímpar
    remanescente e emparelha-o com o mais próximo. Retorna os pares emparelhados
    junto com a sequência de trechos (edge_id) a serem duplicados.

    Referência Bibliográfica da Técnica:
        - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
          Mathematical Programming, 5(1), 88-124.
        - Hierholzer, C. (1873). Über die Möglichkeit, einen Linienzug ohne Wiederholung
          und ohne Unterbrechung zu umfahren. Mathematische Annalen, 6(1), 30-32.

    Limite de Complexidade:
        Complexidade de Tempo: O(K² log V) — onde K é o número de nós ímpares e V é o
        número de vértices. Testado com até ~5.000 trechos de via.

    Args:
        edges: Lista de trechos de via (ver formato do módulo).
        odd_nodes: Lista de identificadores (node_key) dos nós de grau ímpar.

    Returns:
        Lista de tuplas no formato (nó_origem, nó_destino, lista_edge_ids_caminho).

    Raises:
        ValueError: Se a lista de trechos for inválida, se a quantidade de nós ímpares
            for ímpar, ou se não houver caminho até nenhum outro nó ímpar remanescente.
    """
    _validate_edges(edges)

    if len(odd_nodes) % 2 != 0:
        raise ValueError("O número de nós de grau ímpar deve ser par.")

    remaining = list(odd_nodes)
    matched_pairs: List[Tuple[object, object, List[object]]] = []

    while remaining:
        u = remaining.pop(0)
        best_v = None
        best_dist = float("inf")
        best_path = None

        for v in remaining:
            try:
                dist, path = shortest_path_between_nodes(edges, u, v)
            except ValueError:
                continue

            if dist < best_dist:
                best_dist = dist
                best_v = v
                best_path = path

        if best_v is None:
            raise ValueError(
                f"Não foi possível emparelhar o nó '{u}': sem caminho para outros nós ímpares."
            )

        remaining.remove(best_v)
        matched_pairs.append((u, best_v, best_path))

    return matched_pairs


class _EdgeInstance:
    """Representa uma instância de trecho no multigrafo."""

    def __init__(self, instance_id: int, edge_id: object, u: object, v: object):
        self.instance_id = instance_id
        self.edge_id = edge_id
        self.u = u
        self.v = v
        self.used = False


def build_eulerian_circuit(
    edges: List[Dict],
    duplicated_edge_ids: Optional[List[object]] = None
) -> List[object]:
    """Constrói um circuito euleriano sobre o multigrafo de trechos de via.

    Duplica no grafo original os trechos especificados em duplicated_edge_ids (resultantes
    do emparelhamento dos nós de grau ímpar) e aplica o algoritmo de Hierholzer para
    encontrar uma sequência ordenada de travessia que percorre todas as arestas.

    Referência Bibliográfica da Técnica:
        - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
          Mathematical Programming, 5(1), 88-124.
        - Hierholzer, C. (1873). Über die Möglichkeit, einen Linienzug ohne Wiederholung
          und ohne Unterbrechung zu umfahren. Mathematische Annalen, 6(1), 30-32.

    Limite de Complexidade:
        Complexidade de Tempo: O(E) — algoritmo de Hierholzer sobre o multigrafo.
        Testado com até ~5.000 trechos de via.

    Args:
        edges: Lista de trechos de via (ver formato do módulo).
        duplicated_edge_ids: Lista de IDs dos trechos a serem duplicados (opcional).

    Returns:
        Lista com a sequência ordenada de edge_id que compõe o circuito euleriano.
        Trechos duplicados aparecem múltiplas vezes na ordem de travessia.

    Raises:
        ValueError: Se a lista de trechos for vazia ou inválida, se algum ID duplicado
            não existir, se o multigrafo contiver nó de grau ímpar, ou se o grafo for desconexo.
    """
    edge_by_id = _validate_edges(edges)

    if duplicated_edge_ids is None:
        duplicated_edge_ids = []

    multigraph_instances: List[_EdgeInstance] = []
    instance_counter = 0

    for edge in edges:
        inst = _EdgeInstance(
            instance_counter, edge["id"], edge["from_node"], edge["to_node"]
        )
        multigraph_instances.append(inst)
        instance_counter += 1

    for dup_id in duplicated_edge_ids:
        if dup_id not in edge_by_id:
            raise ValueError(f"Trecho duplicado '{dup_id}' não existe na lista de trechos.")
        orig_edge = edge_by_id[dup_id]
        inst = _EdgeInstance(
            instance_counter, dup_id, orig_edge["from_node"], orig_edge["to_node"]
        )
        multigraph_instances.append(inst)
        instance_counter += 1

    degree: Dict[object, int] = {}
    nodes = set()

    for inst in multigraph_instances:
        u = inst.u
        v = inst.v
        nodes.add(u)
        nodes.add(v)
        degree[u] = degree.get(u, 0) + 1
        degree[v] = degree.get(v, 0) + 1

    for node, deg in degree.items():
        if deg % 2 != 0:
            raise ValueError(
                f"O nó '{node}' possui grau ímpar ({deg}) no multigrafo resultante."
            )

    adj: Dict[object, List[Tuple[object, _EdgeInstance]]] = {n: [] for n in nodes}
    for inst in multigraph_instances:
        u = inst.u
        v = inst.v
        adj[u].append((v, inst))
        if u != v:
            adj[v].append((u, inst))

    start_node = multigraph_instances[0].u

    stack: List[Tuple[object, Optional[object]]] = [(start_node, None)]
    circuit_rev: List[object] = []

    while stack:
        curr_node, _ = stack[-1]

        next_edge = None
        while adj[curr_node]:
            nbr, inst = adj[curr_node].pop()
            if not inst.used:
                inst.used = True
                next_edge = (nbr, inst.edge_id)
                break

        if next_edge is not None:
            nbr, edge_id = next_edge
            stack.append((nbr, edge_id))
        else:
            node, edge_id = stack.pop()
            if edge_id is not None:
                circuit_rev.append(edge_id)

    circuit = circuit_rev[::-1]

    if len(circuit) != len(multigraph_instances):
        raise ValueError(
            "O grafo do setor é desconexo (não foi possível percorrer todos os trechos em um único circuito)."
        )

    return circuit


