# -*- coding: utf-8 -*-
import unittest

from core.routing.arc_routing import (
    find_odd_degree_nodes,
    shortest_path_between_nodes,
    match_odd_degree_nodes,
    build_eulerian_circuit,
)


def _simple_cycle_edges():
    """Ciclo simples com 3 trechos em triângulo: A-B, B-C, C-A (0 nós ímpares)."""
    return [
        {"id": "e1", "from_node": "A", "to_node": "B", "length": 10.0},
        {"id": "e2", "from_node": "B", "to_node": "C", "length": 15.0},
        {"id": "e3", "from_node": "C", "to_node": "A", "length": 20.0},
    ]


def _two_odd_nodes_edges():
    """Grafo simples em linha A-B-C: A(1), B(2), C(1) -> 2 nós ímpares (A e C)."""
    return [
        {"id": "e1", "from_node": "A", "to_node": "B", "length": 5.0},
        {"id": "e2", "from_node": "B", "to_node": "C", "length": 10.0},
    ]


def _four_odd_nodes_edges():
    """Quadrado com duas diagonais: A, B, C, D (todos com grau 3 -> 4 nós ímpares)."""
    return [
        {"id": "e1", "from_node": "A", "to_node": "B", "length": 1.0},
        {"id": "e2", "from_node": "B", "to_node": "C", "length": 1.0},
        {"id": "e3", "from_node": "C", "to_node": "D", "length": 1.0},
        {"id": "e4", "from_node": "D", "to_node": "A", "length": 1.0},
        {"id": "e5", "from_node": "A", "to_node": "C", "length": 1.41},
        {"id": "e6", "from_node": "B", "to_node": "D", "length": 1.41},
    ]


class TestFindOddDegreeNodes(unittest.TestCase):

    def test_simple_cycle_has_zero_odd_nodes(self):
        edges = _simple_cycle_edges()
        odd_nodes = find_odd_degree_nodes(edges)
        self.assertEqual(odd_nodes, [])

    def test_line_graph_has_two_odd_nodes(self):
        edges = _two_odd_nodes_edges()
        odd_nodes = find_odd_degree_nodes(edges)
        self.assertEqual(odd_nodes, ["A", "C"])

    def test_complete_quad_with_diagonals_has_four_odd_nodes(self):
        edges = _four_odd_nodes_edges()
        odd_nodes = find_odd_degree_nodes(edges)
        self.assertEqual(odd_nodes, ["A", "B", "C", "D"])

    def test_empty_edges_raises(self):
        with self.assertRaises(ValueError):
            find_odd_degree_nodes([])


class TestShortestPathBetweenNodes(unittest.TestCase):

    def test_shortest_path_on_cycle(self):
        edges = _simple_cycle_edges()
        dist, path = shortest_path_between_nodes(edges, "A", "B")
        self.assertEqual(dist, 10.0)
        self.assertEqual(path, ["e1"])

        dist, path = shortest_path_between_nodes(edges, "B", "A")
        self.assertEqual(dist, 10.0)
        self.assertEqual(path, ["e1"])

    def test_shortest_path_multihop(self):
        edges = _two_odd_nodes_edges()
        dist, path = shortest_path_between_nodes(edges, "A", "C")
        self.assertEqual(dist, 15.0)
        self.assertEqual(path, ["e1", "e2"])

    def test_same_source_and_target(self):
        edges = _simple_cycle_edges()
        dist, path = shortest_path_between_nodes(edges, "A", "A")
        self.assertEqual(dist, 0.0)
        self.assertEqual(path, [])

    def test_nonexistent_node_raises(self):
        edges = _simple_cycle_edges()
        with self.assertRaises(ValueError):
            shortest_path_between_nodes(edges, "A", "X")
        with self.assertRaises(ValueError):
            shortest_path_between_nodes(edges, "X", "A")

    def test_disconnected_nodes_raise(self):
        edges = _simple_cycle_edges() + [
            {"id": "e_iso", "from_node": "X", "to_node": "Y", "length": 5.0}
        ]
        with self.assertRaises(ValueError):
            shortest_path_between_nodes(edges, "A", "X")

    def test_empty_edges_raises(self):
        with self.assertRaises(ValueError):
            shortest_path_between_nodes([], "A", "B")


class TestMatchOddDegreeNodes(unittest.TestCase):

    def test_zero_odd_nodes_returns_empty(self):
        edges = _simple_cycle_edges()
        matched = match_odd_degree_nodes(edges, [])
        self.assertEqual(matched, [])

    def test_two_odd_nodes_matching(self):
        edges = _two_odd_nodes_edges()
        odd_nodes = find_odd_degree_nodes(edges)
        matched = match_odd_degree_nodes(edges, odd_nodes)
        self.assertEqual(len(matched), 1)
        u, v, path = matched[0]
        self.assertEqual((u, v), ("A", "C"))
        self.assertEqual(path, ["e1", "e2"])

    def test_four_odd_nodes_greedy_matching(self):
        edges = _four_odd_nodes_edges()
        odd_nodes = find_odd_degree_nodes(edges)
        matched = match_odd_degree_nodes(edges, odd_nodes)
        self.assertEqual(len(matched), 2)
        # Todos os 4 nós ímpares foram emparelhados
        paired_nodes = set()
        for u, v, _ in matched:
            paired_nodes.add(u)
            paired_nodes.add(v)
        self.assertEqual(paired_nodes, {"A", "B", "C", "D"})

    def test_odd_number_of_odd_nodes_raises(self):
        edges = _simple_cycle_edges()
        with self.assertRaises(ValueError):
            match_odd_degree_nodes(edges, ["A"])

    def test_disconnected_odd_nodes_raises(self):
        edges = _simple_cycle_edges() + [
            {"id": "e_iso", "from_node": "X", "to_node": "Y", "length": 5.0}
        ]
        with self.assertRaises(ValueError):
            match_odd_degree_nodes(edges, ["A", "X"])

    def test_empty_edges_raises(self):
        with self.assertRaises(ValueError):
            match_odd_degree_nodes([], ["A", "B"])


class TestBuildEulerianCircuit(unittest.TestCase):

    def test_simple_cycle_eulerian_circuit(self):
        edges = _simple_cycle_edges()
        circuit = build_eulerian_circuit(edges)
        self.assertEqual(len(circuit), 3)
        self.assertEqual(set(circuit), {"e1", "e2", "e3"})

    def test_two_odd_nodes_eulerian_circuit_with_duplication(self):
        edges = _two_odd_nodes_edges()
        odd_nodes = find_odd_degree_nodes(edges)
        matched = match_odd_degree_nodes(edges, odd_nodes)
        dup_ids = []
        for _, _, path in matched:
            dup_ids.extend(path)

        circuit = build_eulerian_circuit(edges, duplicated_edge_ids=dup_ids)
        self.assertEqual(len(circuit), len(edges) + len(dup_ids))
        # Trechos e1 e e2 devem aparecer 2 vezes cada no circuito
        self.assertEqual(circuit.count("e1"), 2)
        self.assertEqual(circuit.count("e2"), 2)

    def test_four_odd_nodes_eulerian_circuit_with_duplication(self):
        edges = _four_odd_nodes_edges()
        odd_nodes = find_odd_degree_nodes(edges)
        matched = match_odd_degree_nodes(edges, odd_nodes)
        dup_ids = []
        for _, _, path in matched:
            dup_ids.extend(path)

        circuit = build_eulerian_circuit(edges, duplicated_edge_ids=dup_ids)
        self.assertEqual(len(circuit), len(edges) + len(dup_ids))

    def test_nonexistent_duplicated_edge_raises(self):
        edges = _simple_cycle_edges()
        with self.assertRaises(ValueError):
            build_eulerian_circuit(edges, duplicated_edge_ids=["nonexistent"])

    def test_odd_degree_in_multigraph_raises(self):
        edges = _two_odd_nodes_edges()
        # Sem duplicar o caminho para zerar nós ímpares
        with self.assertRaises(ValueError):
            build_eulerian_circuit(edges, duplicated_edge_ids=[])

    def test_disconnected_graph_raises(self):
        edges = [
            {"id": "e1", "from_node": "A", "to_node": "B", "length": 1.0},
            {"id": "e2", "from_node": "B", "to_node": "A", "length": 1.0},
            {"id": "e3", "from_node": "C", "to_node": "D", "length": 1.0},
            {"id": "e4", "from_node": "D", "to_node": "C", "length": 1.0},
        ]
        with self.assertRaises(ValueError):
            build_eulerian_circuit(edges)

    def test_empty_edges_raises(self):
        with self.assertRaises(ValueError):
            build_eulerian_circuit([])


if __name__ == "__main__":
    unittest.main()
