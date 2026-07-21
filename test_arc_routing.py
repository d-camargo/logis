# -*- coding: utf-8 -*-
import unittest

from core.routing.arc_routing import (
    find_odd_degree_nodes,
    shortest_path_between_nodes,
    match_odd_degree_nodes,
    build_eulerian_circuit,
    connect_required_components,
    solve_carp_path_scanning,
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


class TestConnectRequiredComponents(unittest.TestCase):

    def test_single_component_returns_empty(self):
        req = _simple_cycle_edges()
        full = req
        connectors = connect_required_components(req, full)
        self.assertEqual(connectors, [])

    def test_two_components_connected_via_mst(self):
        req = [
            {"id": "e1", "from_node": "N1", "to_node": "N1", "length": 1.0},
            {"id": "e2", "from_node": "N2", "to_node": "N2", "length": 1.0},
        ]
        full = req + [
            {"id": "e_conn", "from_node": "N1", "to_node": "N2", "length": 5.0},
        ]
        connectors = connect_required_components(req, full)
        self.assertEqual(connectors, ["e_conn"])

    def test_three_components_connected_via_mst(self):
        req = [
            {"id": "e1", "from_node": "N1", "to_node": "N1", "length": 1.0},
            {"id": "e2", "from_node": "N2", "to_node": "N2", "length": 1.0},
            {"id": "e3", "from_node": "N3", "to_node": "N3", "length": 1.0},
        ]
        full = req + [
            {"id": "e12", "from_node": "N1", "to_node": "N2", "length": 2.0},
            {"id": "e23", "from_node": "N2", "to_node": "N3", "length": 3.0},
            {"id": "e13", "from_node": "N1", "to_node": "N3", "length": 10.0},
        ]
        connectors = connect_required_components(req, full)
        self.assertEqual(set(connectors), {"e12", "e23"})

    def test_disconnected_full_edges_raises(self):
        req = [
            {"id": "e1", "from_node": "A", "to_node": "B", "length": 1.0},
            {"id": "e2", "from_node": "C", "to_node": "D", "length": 1.0},
        ]
        full = req
        with self.assertRaises(ValueError):
            connect_required_components(req, full)

    def test_empty_required_edges_raises(self):
        full = _simple_cycle_edges()
        with self.assertRaises(ValueError):
            connect_required_components([], full)

    def test_empty_full_edges_raises(self):
        req = _simple_cycle_edges()
        with self.assertRaises(ValueError):
            connect_required_components(req, [])


class TestSolveCarpPathScanning(unittest.TestCase):

    def test_single_route_covers_all_demand(self):
        req = [
            {"id": "e1", "from_node": "D", "to_node": "A", "length": 5.0, "load": 3.0},
            {"id": "e2", "from_node": "A", "to_node": "B", "length": 5.0, "load": 4.0},
        ]
        routes = solve_carp_path_scanning(req, req, depot_node="D", vehicle_capacity=10.0)
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["load_kg"], 7.0)
        self.assertIn("e1", routes[0]["edges"])
        self.assertIn("e2", routes[0]["edges"])

    def test_capacity_forces_two_routes(self):
        req = [
            {"id": "e1", "from_node": "D", "to_node": "A", "length": 2.0, "load": 6.0},
            {"id": "e2", "from_node": "D", "to_node": "B", "length": 3.0, "load": 6.0},
        ]
        routes = solve_carp_path_scanning(req, req, depot_node="D", vehicle_capacity=10.0)
        self.assertEqual(len(routes), 2)
        self.assertEqual(sorted(r["load_kg"] for r in routes), [6.0, 6.0])

    def test_isolated_segment_exceeding_capacity_raises(self):
        req = [
            {"id": "e1", "from_node": "D", "to_node": "A", "length": 5.0, "load": 15.0},
        ]
        with self.assertRaises(ValueError):
            solve_carp_path_scanning(req, req, depot_node="D", vehicle_capacity=10.0)

    def test_single_required_edge_trivial_route(self):
        req = [
            {"id": "e1", "from_node": "D", "to_node": "A", "length": 4.0, "load": 2.0},
        ]
        routes = solve_carp_path_scanning(req, req, depot_node="D", vehicle_capacity=10.0)
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["load_kg"], 2.0)
        self.assertIn("e1", routes[0]["edges"])

    def test_empty_required_edges_raises(self):
        full = [
            {"id": "e1", "from_node": "D", "to_node": "A", "length": 5.0},
        ]
        with self.assertRaises(ValueError):
            solve_carp_path_scanning([], full, depot_node="D", vehicle_capacity=10.0)


if __name__ == "__main__":
    unittest.main()


