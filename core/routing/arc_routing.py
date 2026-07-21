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
Problem (CPP), Rural Postman Problem (RPP) component connection, and
Capacitated Arc Routing Problem (CARP) path-scanning heuristic on edge-based network graphs:
- Identification of odd-degree nodes in edge-based network graphs.
- Shortest path computation between node keys weighted by length (Dijkstra).
- Greedy matching of odd-degree nodes via shortest path search.
- Eulerian circuit construction (Hierholzer) over the duplicated-edge multigraph.
- Connecting required components for RPP via MST (Kruskal) over component representatives.
- CARP Path-Scanning heuristic (Golden et al., 1983) for capacity-constrained arc routing.

Edges are represented as dicts:
    {"id": edge_id, "from_node": node_key, "to_node": node_key, "length": float}
Required edges passed to solve_carp_path_scanning carry one additional key:
    {..., "load": float}  # kg of demand for the segment
Two edges share a node if they have matching "from_node" or "to_node" values.
`node_key` is computed by the caller (the Processing algorithm layer), not by this module.

References:
    - Edmonds, J., & Johnson, E. L. (1973). Matching, Euler tours and the Chinese postman.
      Mathematical Programming, 5(1), 88-124.
    - Hierholzer, C. (1873). Über die Möglichkeit, einen Linienzug ohne Wiederholung
      und ohne Unterbrechung zu umfahren. Mathematische Annalen, 6(1), 30-32.
    - Frederickson, G. N. (1979). Approximation algorithms for some postman problems.
      Journal of the ACM, 26(3), 538-554.
    - Golden, B. L., DeArmon, J. S., & Baker, E. K. (1983). Computational experiments with
      algorithms for a class of routing problems. Computers & Operations Research, 10(1), 47-59.

Complexity/Scale limits:
    - find_odd_degree_nodes: O(E), scans all edges and counts node degrees.
    - shortest_path_between_nodes: O(E log V), standard Dijkstra algorithm with priority queue.
    - match_odd_degree_nodes: O(K² log V), greedy pairing of K odd-degree nodes using Dijkstra.
    - connect_required_components: O(C² log V + C² log C), C components connected via Dijkstra + Kruskal.
    - solve_carp_path_scanning: O(R² · E log V), R = number of required edges per sector,
      E = total edges, V = vertices. Tested scale: up to ~500 required edges per sector
      (more conservative than the other functions — see its own docstring).
    - Tested scale (other functions): up to ~5,000 road segments (neighborhood/collection-district scale).
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


def _sort_key(x: object) -> Tuple[str, str]:
    """Chave determinística de ordenação para nós (suporta tipos mistos)."""
    return (type(x).__name__, str(x))


def connect_required_components(
    required_edges: List[Dict],
    full_edges: List[Dict]
) -> List[object]:
    """Identifica componentes conexos do subgrafo de trechos obrigatórios e conecta-os via MST.

    Identifica os componentes conexos formados pelos trechos em required_edges (BFS sobre
    from_node/to_node). Se houver mais de um componente, seleciona um nó representante por
    componente (o menor node_key para determinismo), calcula os caminhos mínimos entre
    todos os pares de representantes sobre full_edges (via shortest_path_between_nodes),
    e monta uma Árvore Geradora Mínima (MST via Kruskal) para conectar todos os componentes.

    Referência Bibliográfica da Técnica:
        - Frederickson, G. N. (1979). Approximation algorithms for some postman problems.
          Journal of the ACM, 26(3), 538-554.

    Limite de Complexidade:
        Complexidade de Tempo: O(C² log V + C² log C), onde C é o número de componentes
        conexos do subgrafo obrigatório e V é o número de vértices em full_edges.
        Testado com até ~5.000 trechos de via.

    Args:
        required_edges: Lista de trechos de via obrigatórios (ver formato do módulo).
        full_edges: Lista de todos os trechos de via da rede (obrigatórios + opcionais).

    Returns:
        Lista com a união (sem duplicatas) dos identificadores (edge_id) dos trechos
        que compõem os caminhos mínimos da MST para conectar os componentes.
        Retorna lista vazia ([]) se o subgrafo obrigatório já for conexo (um único componente).

    Raises:
        ValueError: Se required_edges ou full_edges forem vazias ou inválidas, ou se
            algum componente obrigatório não puder ser conectado a todos os demais
            (rede desconexa em full_edges).
    """
    _validate_edges(required_edges)
    _validate_edges(full_edges)

    req_nodes = set()
    req_adj: Dict[object, List[object]] = {}
    for edge in required_edges:
        u = edge["from_node"]
        v = edge["to_node"]
        req_nodes.add(u)
        req_nodes.add(v)
        if u not in req_adj:
            req_adj[u] = []
        if v not in req_adj:
            req_adj[v] = []
        req_adj[u].append(v)
        if u != v:
            req_adj[v].append(u)

    visited = set()
    components: List[List[object]] = []

    sorted_nodes = sorted(req_nodes, key=_sort_key)
    for node in sorted_nodes:
        if node not in visited:
            comp = []
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for nbr in req_adj[curr]:
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
            components.append(comp)

    if len(components) <= 1:
        return []

    representatives: List[object] = []
    for comp in components:
        rep = min(comp, key=_sort_key)
        representatives.append(rep)

    c_count = len(components)
    candidate_edges = []
    for i in range(c_count):
        for j in range(i + 1, c_count):
            u = representatives[i]
            v = representatives[j]
            try:
                dist, path_edge_ids = shortest_path_between_nodes(full_edges, u, v)
                candidate_edges.append((dist, i, j, path_edge_ids))
            except ValueError:
                pass

    candidate_edges.sort(key=lambda item: (item[0], item[1], item[2]))

    parent = list(range(c_count))

    def find(i: int) -> int:
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i: int, j: int) -> bool:
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j
            return True
        return False

    mst_paths: List[List[object]] = []
    edges_count = 0

    for dist, i, j, path_edge_ids in candidate_edges:
        if union(i, j):
            mst_paths.append(path_edge_ids)
            edges_count += 1
            if edges_count == c_count - 1:
                break

    if edges_count < c_count - 1:
        raise ValueError(
            "Não foi possível conectar todos os componentes obrigatórios: "
            "a rede (full_edges) é desconexa entre os componentes."
        )

    connector_edge_ids: List[object] = []
    seen = set()
    for path in mst_paths:
        for edge_id in path:
            if edge_id not in seen:
                seen.add(edge_id)
                connector_edge_ids.append(edge_id)

    return connector_edge_ids


def solve_carp_path_scanning(
    required_edges: List[Dict],
    full_edges: List[Dict],
    depot_node: object,
    vehicle_capacity: float
) -> List[Dict]:
    """Resolve o CARP (Capacitated Arc Routing Problem) via a heurística Path-Scanning.

    Constrói rotas de veículo com capacidade limitada a partir de um depósito, atendendo à
    demanda de cada trecho de via obrigatório. A cada passo, escolhe (por nearest-neighbor,
    via shortest_path_between_nodes sobre full_edges) o trecho obrigatório não servido mais
    próximo da posição atual que ainda caiba na capacidade restante (compara chegada por
    from_node e por to_node, escolhe a mais curta). Quando nenhum trecho remanescente couber
    na capacidade restante (ou nenhum for alcançável), fecha a rota retornando ao depósito e
    inicia a próxima. Versão simplificada de regra única de desempate (nearest-neighbor), não
    a versão com múltiplas regras de seleção do artigo original — mesma decisão de
    simplicidade já tomada para o matching guloso do CPP e o MST de representantes do RPP.

    Referência Bibliográfica da Técnica:
        - Golden, B. L., DeArmon, J. S., & Baker, E. K. (1983). Computational experiments
          with algorithms for a class of routing problems. Computers & Operations Research, 10(1), 47-59.

    Limite de Complexidade:
        Complexidade de Tempo: O(R² · E log V) no pior caso agregado sobre todas as rotas de
        um setor — R é o número de trechos obrigatórios, E é o número de trechos totais e V é
        o número de vértices. Testado com até ~500 trechos obrigatórios por setor (limite mais
        conservador que o das demais funções do módulo, coerente com o tamanho típico de um
        setor de coleta).

    Args:
        required_edges: Subconjunto de full_edges com uma chave adicional obrigatória "load"
            (float >= 0, kg de demanda do trecho).
        full_edges: Lista de todos os trechos da rede, usada para calcular os deslocamentos
            (deadhead) entre trechos obrigatórios e o depósito.
        depot_node: Identificador (node_key) do nó de partida/retorno de cada rota.
        vehicle_capacity: Capacidade máxima de carga do veículo, em kg (deve ser > 0).

    Returns:
        Lista de rotas, cada rota um dict:
            {"edges": lista ordenada de edge_id percorridos (deadhead + trechos obrigatórios,
                      na ordem de travessia), "load_kg": carga total da rota,
             "distance_m": distância total percorrida pela rota (serviço + deadhead)}.

    Raises:
        ValueError: Se required_edges ou full_edges forem vazios/inválidos, se algum trecho
            obrigatório não existir em full_edges ou não tiver a chave "load", se
            vehicle_capacity for <= 0, se depot_node não pertencer ao grafo, se a demanda de
            um trecho isolado exceder vehicle_capacity (sem split-delivery), ou se algum
            trecho obrigatório remanescente não puder ser servido (rede desconexa).
    """
    _validate_edges(required_edges)
    full_edge_by_id = _validate_edges(full_edges)

    if not isinstance(vehicle_capacity, (int, float)) or vehicle_capacity <= 0:
        raise ValueError("A capacidade do veículo (vehicle_capacity) deve ser estritamente maior que zero.")

    full_nodes = set()
    for edge in full_edge_by_id.values():
        full_nodes.add(edge["from_node"])
        full_nodes.add(edge["to_node"])

    if depot_node not in full_nodes:
        raise ValueError(f"Nó depósito '{depot_node}' não pertence ao grafo de trechos.")

    unserved: Dict[object, Dict] = {}
    for idx, edge in enumerate(required_edges):
        edge_id = edge["id"]
        if edge_id not in full_edge_by_id:
            raise ValueError(f"Trecho obrigatório '{edge_id}' não existe em full_edges.")
        if "load" not in edge:
            raise ValueError(f"Trecho obrigatório no índice {idx} ({edge_id}) não possui a chave 'load'.")
        load = edge["load"]
        if not isinstance(load, (int, float)) or load < 0:
            raise ValueError(f"Trecho obrigatório '{edge_id}' possui carga (load) inválida: {load}.")
        if load > vehicle_capacity:
            raise ValueError(
                f"Demanda do trecho '{edge_id}' ({load}) excede a capacidade do veículo ({vehicle_capacity})."
            )
        unserved[edge_id] = edge

    sp_cache: Dict[Tuple[object, object], Tuple[float, List[object]]] = {}

    def get_sp(u: object, v: object) -> Tuple[float, List[object]]:
        if u == v:
            return 0.0, []
        key = (u, v)
        if key not in sp_cache:
            try:
                sp_cache[key] = shortest_path_between_nodes(full_edges, u, v)
            except ValueError:
                sp_cache[key] = (float("inf"), [])
        return sp_cache[key]

    routes: List[Dict] = []

    while unserved:
        curr_node = depot_node
        curr_load = 0.0
        route_edges: List[object] = []
        route_dist = 0.0
        served_any = False

        while True:
            best_edge_id = None
            best_dist = float("inf")
            best_path: List[object] = []
            best_exit_node = None

            for edge_id, edge in unserved.items():
                load = float(edge["load"])
                if curr_load + load > vehicle_capacity + 1e-9:
                    continue

                u = edge["from_node"]
                v = edge["to_node"]

                dist_u, path_u = get_sp(curr_node, u)
                if dist_u < best_dist:
                    best_dist = dist_u
                    best_edge_id = edge_id
                    best_path = path_u
                    best_exit_node = v

                if u != v:
                    dist_v, path_v = get_sp(curr_node, v)
                    if dist_v < best_dist:
                        best_dist = dist_v
                        best_edge_id = edge_id
                        best_path = path_v
                        best_exit_node = u

            if best_edge_id is None:
                break

            edge = unserved.pop(best_edge_id)
            route_edges.extend(best_path)
            route_edges.append(best_edge_id)
            route_dist += best_dist + float(edge["length"])
            curr_load += float(edge["load"])
            curr_node = best_exit_node
            served_any = True

        if not served_any:
            raise ValueError(
                f"Não foi possível atender os trechos remanescentes: {list(unserved.keys())}."
            )

        if curr_node != depot_node:
            dist_back, path_back = get_sp(curr_node, depot_node)
            route_edges.extend(path_back)
            route_dist += dist_back

        routes.append({
            "edges": route_edges,
            "load_kg": curr_load,
            "distance_m": route_dist,
        })

    return routes




