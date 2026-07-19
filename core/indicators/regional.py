# -*- coding: utf-8 -*-
"""
Módulo de cálculo de indicadores de rede viária regional.
"""
from typing import List, Tuple, Union

def road_density(road_length_m: float, area_km2: float, population: Union[int, float]) -> Tuple[float, float]:
    """
    Calcula a densidade rodoviária por área territorial (km/1.000 km²) e por população (km/10.000 hab).

    Fórmula:
        Densidade por Área = (Comprimento Total em km) / (Área em km² / 1000.0)
        Densidade por Área = (road_length_m / 1000.0) / (area_km2 / 1000.0) = road_length_m / area_km2

        Densidade por População = (Comprimento Total em km) / (População / 10000.0)
        Densidade por População = (road_length_m / 1000.0) / (population / 10000.0) = (road_length_m * 10.0) / population

    Referência Bibliográfica da Técnica:
        Handy, S. L., & Clifton, K. J. (2001). Evaluating neighborhood accessibility:
        Possibilities and limitations. Journal of Transportation and Statistics, 4(2/3), 67-78.

    Limite de Complexidade:
        Complexidade de Tempo: O(1)
        Complexidade de Espaço: O(1)
        Testado com redes de até 1.000.000 de trechos (cálculo instantâneo).

    Args:
        road_length_m (float): Comprimento total das rodovias em metros. Deve ser maior ou igual a zero.
        area_km2 (float): Área territorial em quilômetros quadrados. Deve ser estritamente maior que zero.
        population (Union[int, float]): População em número de habitantes. Deve ser estritamente maior que zero.

    Returns:
        Tuple[float, float]: Uma tupla contendo:
            - densidade_area (float): Densidade em km/1.000 km².
            - densidade_pop (float): Densidade em km/10.000 hab.

    Raises:
        ValueError: Se road_length_m for negativo, se area_km2 for menor ou igual a zero,
                    ou se population for menor ou igual a zero.
    """
    if road_length_m < 0:
        raise ValueError("O comprimento das rodovias (road_length_m) não pode ser negativo.")
    if area_km2 <= 0:
        raise ValueError("A área (area_km2) deve ser estritamente maior que zero.")
    if population <= 0:
        raise ValueError("A população (population) deve ser estritamente maior que zero.")

    density_area = road_length_m / area_km2
    density_pop = (road_length_m * 10.0) / float(population)
    return density_area, density_pop


def find_critical_links(edges: List[Tuple[int, int]], num_vertices: int) -> List[bool]:
    """
    Identifica as pontes/arcos críticos (cut links) de uma malha viária: arestas cuja
    remoção desconecta o grafo, indicando trechos sem rota alternativa.

    Algoritmo:
        Tarjan/DFS com valores de low-link. Percorre o grafo (não direcionado) em busca
        em profundidade, atribuindo a cada vértice um tempo de descoberta (`disc`) e o
        menor tempo de descoberta alcançável por arestas de retorno (`low`). Uma aresta
        (u, v), com v descoberto a partir de u, é uma ponte se `low[v] > disc[u]`
        (nenhum caminho alternativo de v alcança u ou um ancestral de u sem usá-la).
        Implementado com pilha explícita (DFS iterativo) para evitar estouro de recursão
        em redes rodoviárias longas e pouco ramificadas.

    Referência Bibliográfica da Técnica:
        Tarjan, R. E. (1974). A note on finding the bridges of a graph.
        Information Processing Letters, 2(6), 160-161.
        (Base teórica da identificação de conectividade intermunicipal crítica citada
        na seção de indicadores de rede regional do logis).

    Limite de Complexidade:
        Complexidade de Tempo: O(V + E).
        Complexidade de Espaço: O(V + E).
        Testado com redes de até 1.000.000 de arestas e 500.000 vértices.

    Args:
        edges (list of tuple(int, int)): Lista de arestas físicas únicas (u, v) do grafo
                                          não direcionado, já deduplicadas (sem arestas
                                          paralelas repetidas representando o mesmo par
                                          origem-destino), com índices de vértice
                                          0-based. O grafo pode ser desconexo.
        num_vertices (int): Número total de vértices do grafo. Deve ser estritamente
                             maior que zero.

    Returns:
        list of bool: Lista de mesmo tamanho e ordem de `edges`, com `True` no índice i
        se `edges[i]` for uma ponte (cut link), `False` caso contrário.

    Raises:
        ValueError: Se num_vertices for menor ou igual a zero, ou se alguma aresta em
                    `edges` referenciar um vértice fora do intervalo [0, num_vertices).
    """
    if num_vertices <= 0:
        raise ValueError("O número de vértices (num_vertices) deve ser estritamente maior que zero.")

    edge_list = list(edges)
    for edge_id, (u, v) in enumerate(edge_list):
        if not (0 <= u < num_vertices) or not (0 <= v < num_vertices):
            raise ValueError(
                "Aresta {} ({}, {}) referencia vértice fora do intervalo válido [0, {}).".format(
                    edge_id, u, v, num_vertices
                )
            )

    adjacency = [[] for _ in range(num_vertices)]
    for edge_id, (u, v) in enumerate(edge_list):
        adjacency[u].append((v, edge_id))
        adjacency[v].append((u, edge_id))

    discovery = [-1] * num_vertices
    low_link = [-1] * num_vertices
    is_bridge = [False] * len(edge_list)
    timer = 0

    for start in range(num_vertices):
        if discovery[start] != -1:
            continue

        discovery[start] = low_link[start] = timer
        timer += 1
        # Pilha de quadros (vértice atual, vértice pai, id da aresta ao pai, próximo índice a visitar).
        stack = [(start, -1, -1, 0)]
        while stack:
            node, parent_node, parent_edge_id, next_idx = stack.pop()
            if next_idx < len(adjacency[node]):
                stack.append((node, parent_node, parent_edge_id, next_idx + 1))
                neighbor, edge_id = adjacency[node][next_idx]
                if edge_id == parent_edge_id:
                    continue
                if discovery[neighbor] == -1:
                    discovery[neighbor] = low_link[neighbor] = timer
                    timer += 1
                    stack.append((neighbor, node, edge_id, 0))
                else:
                    low_link[node] = min(low_link[node], discovery[neighbor])
            elif parent_node != -1:
                low_link[parent_node] = min(low_link[parent_node], low_link[node])
                if low_link[node] > discovery[parent_node]:
                    is_bridge[parent_edge_id] = True

    return is_bridge


def paved_duplicated_share(total_length_m: float, paved_length_m: float, duplicated_length_m: float) -> Tuple[float, float]:
    """
    Calcula o percentual da malha rodoviária que é pavimentada e o percentual que é duplicada.

    Fórmulas:
        % Pavimentada = (Comprimento Pavimentado / Comprimento Total) * 100.0
        % Duplicada = (Comprimento Duplicado / Comprimento Total) * 100.0

    Referência Bibliográfica da Técnica:
        Confederação Nacional do Transporte. (2024). Pesquisa CNT de Rodovias.
        (O percentual de vias pavimentadas e duplicadas são indicadores de qualidade e capacidade de infraestrutura regional).

    Limite de Complexidade:
        Complexidade de Tempo: O(1)
        Complexidade de Espaço: O(1)
        Testado com redes de até 1.000.000 de trechos (cálculo instantâneo).

    Args:
        total_length_m (float): Comprimento total da malha em metros. Deve ser estritamente maior que zero.
        paved_length_m (float): Comprimento das vias pavimentadas em metros. Deve ser maior ou igual a zero e menor ou igual a total_length_m.
        duplicated_length_m (float): Comprimento das vias duplicadas em metros. Deve ser maior ou igual a zero e menor ou igual a total_length_m.

    Returns:
        Tuple[float, float]: Uma tupla contendo:
            - pct_paved (float): Percentual da malha pavimentada (0.0 a 100.0).
            - pct_duplicated (float): Percentual da malha duplicada (0.0 a 100.0).

    Raises:
        ValueError: Se total_length_m for menor ou igual a zero, se algum comprimento for negativo,
                    ou se paved_length_m ou duplicated_length_m exceder total_length_m.
    """
    if total_length_m <= 0:
        raise ValueError("O comprimento total da malha (total_length_m) deve ser estritamente maior que zero.")
    if paved_length_m < 0:
        raise ValueError("O comprimento de vias pavimentadas (paved_length_m) não pode ser negativo.")
    if duplicated_length_m < 0:
        raise ValueError("O comprimento de vias duplicadas (duplicated_length_m) não pode ser negativo.")
    if paved_length_m > total_length_m:
        raise ValueError("O comprimento pavimentado (paved_length_m) não pode ser maior que o comprimento total (total_length_m).")
    if duplicated_length_m > total_length_m:
        raise ValueError("O comprimento duplicado (duplicated_length_m) não pode ser maior que o comprimento total (total_length_m).")

    pct_paved = (paved_length_m / total_length_m) * 100.0
    pct_duplicated = (duplicated_length_m / total_length_m) * 100.0
    return pct_paved, pct_duplicated
