# -*- coding: utf-8 -*-
import unittest

from logis.core.routing.districting import (
    select_seed_edges_farthest_first,
    grow_sectors_from_seeds,
    rebalance_boundary_edges,
    connected_components,
)


def _line_edges(n, load=1.0):
    """N trechos em linha: (0)-e0-(1)-e1-(2)-...-(n)."""
    return [
        {"id": i, "from_node": (i,), "to_node": (i + 1,), "length": 1.0, "load": load}
        for i in range(n)
    ]


def _star_edges():
    """Uma junção central com 4 raios (trechos e0..e3 tocando o nó central 'C')."""
    return [
        {"id": "e0", "from_node": "C", "to_node": "n0", "length": 1.0, "load": 1.0},
        {"id": "e1", "from_node": "C", "to_node": "n1", "length": 1.0, "load": 1.0},
        {"id": "e2", "from_node": "C", "to_node": "n2", "length": 1.0, "load": 1.0},
        {"id": "e3", "from_node": "C", "to_node": "n3", "length": 1.0, "load": 1.0},
    ]


class TestSelectSeedEdgesFarthestFirst(unittest.TestCase):

    def test_line_topology_picks_spread_out_seeds(self):
        edges = _line_edges(5)  # ids 0..4
        seeds = select_seed_edges_farthest_first(edges, num_sectors=2, start_edge_id=0)
        self.assertEqual(len(seeds), 2)
        self.assertEqual(seeds[0], 0)
        self.assertEqual(seeds[1], 4)  # o mais distante de 0 na linha

    def test_star_topology_spreads_across_rays(self):
        edges = _star_edges()
        seeds = select_seed_edges_farthest_first(edges, num_sectors=4, start_edge_id="e0")
        self.assertEqual(len(seeds), 4)
        self.assertEqual(set(seeds), {"e0", "e1", "e2", "e3"})

    def test_default_start_is_first_edge(self):
        edges = _line_edges(3)
        seeds = select_seed_edges_farthest_first(edges, num_sectors=1)
        self.assertEqual(seeds, [0])

    def test_empty_edges_raises(self):
        with self.assertRaises(ValueError):
            select_seed_edges_farthest_first([], num_sectors=1)

    def test_num_sectors_invalid_raises(self):
        edges = _line_edges(3)
        with self.assertRaises(ValueError):
            select_seed_edges_farthest_first(edges, num_sectors=0)
        with self.assertRaises(ValueError):
            select_seed_edges_farthest_first(edges, num_sectors=10)

    def test_nonexistent_start_edge_raises(self):
        edges = _line_edges(3)
        with self.assertRaises(ValueError):
            select_seed_edges_farthest_first(edges, num_sectors=1, start_edge_id=999)


class TestGrowSectorsFromSeeds(unittest.TestCase):

    def test_line_topology_assigns_every_edge(self):
        edges = _line_edges(6)
        sector_of_edge = grow_sectors_from_seeds(edges, seed_edge_ids=[0, 5])
        self.assertEqual(set(sector_of_edge.keys()), {e["id"] for e in edges})
        self.assertEqual(len(set(sector_of_edge.values())), 2)

    def test_growth_favors_lighter_sector(self):
        # semente 0 pesada, semente 4 leve: setor 1 deve crescer primeiro
        edges = [
            {"id": 0, "from_node": (0,), "to_node": (1,), "length": 1.0, "load": 100.0},
            {"id": 1, "from_node": (1,), "to_node": (2,), "length": 1.0, "load": 1.0},
            {"id": 2, "from_node": (2,), "to_node": (3,), "length": 1.0, "load": 1.0},
            {"id": 3, "from_node": (3,), "to_node": (4,), "length": 1.0, "load": 1.0},
            {"id": 4, "from_node": (4,), "to_node": (5,), "length": 1.0, "load": 1.0},
        ]
        sector_of_edge = grow_sectors_from_seeds(edges, seed_edge_ids=[0, 4])
        # a semente leve (setor 1) deve absorver os trechos intermediários antes da pesada
        self.assertEqual(sector_of_edge[1], 1)

    def test_empty_seed_list_raises(self):
        edges = _line_edges(3)
        with self.assertRaises(ValueError):
            grow_sectors_from_seeds(edges, seed_edge_ids=[])

    def test_duplicate_seeds_raise(self):
        edges = _line_edges(3)
        with self.assertRaises(ValueError):
            grow_sectors_from_seeds(edges, seed_edge_ids=[0, 0])

    def test_nonexistent_seed_raises(self):
        edges = _line_edges(3)
        with self.assertRaises(ValueError):
            grow_sectors_from_seeds(edges, seed_edge_ids=[0, 999])

    def test_disconnected_graph_raises(self):
        edges = _line_edges(2) + [
            {"id": 100, "from_node": ("isolated_a",), "to_node": ("isolated_b",), "length": 1.0, "load": 1.0}
        ]
        with self.assertRaises(ValueError):
            grow_sectors_from_seeds(edges, seed_edge_ids=[0])

    def test_internal_vertex_via_nodes_connects_and_grows(self):
        # (i) dois trechos que se tocam só num vértice interno (o "nodes" de um contém a ponta do outro)
        # -> vizinhos, e grow_sectors_from_seeds com uma semente cobre os dois
        e1 = {
            "id": "main",
            "from_node": (0, 0),
            "to_node": (0, 10),
            "length": 10.0,
            "load": 2.0,
            "nodes": [(0, 0), (0, 5), (0, 10)],
        }
        e2 = {
            "id": "branch",
            "from_node": (0, 5),
            "to_node": (5, 5),
            "length": 5.0,
            "load": 1.0,
        }
        sector_of_edge = grow_sectors_from_seeds([e1, e2], seed_edge_ids=["main"])
        self.assertEqual(sector_of_edge, {"main": 0, "branch": 0})

    def test_internal_vertex_without_nodes_raises_value_error(self):
        # (ii) o mesmo par sem "nodes" -> continua levantando ValueError (retrocompatível)
        e1 = {
            "id": "main",
            "from_node": (0, 0),
            "to_node": (0, 10),
            "length": 10.0,
            "load": 2.0,
        }
        e2 = {
            "id": "branch",
            "from_node": (0, 5),
            "to_node": (5, 5),
            "length": 5.0,
            "load": 1.0,
        }
        with self.assertRaises(ValueError):
            grow_sectors_from_seeds([e1, e2], seed_edge_ids=["main"])


class TestRebalanceBoundaryEdges(unittest.TestCase):

    def test_moves_boundary_edge_to_lighten_heavy_sector(self):
        # linha de 4 trechos; setor 0 = {0, 1} (carga 20), setor 1 = {2, 3} (carga 2)
        # mover o trecho de fronteira 1 para o setor 1 equilibra melhor a carga.
        edges = [
            {"id": 0, "from_node": (0,), "to_node": (1,), "length": 1.0, "load": 10.0},
            {"id": 1, "from_node": (1,), "to_node": (2,), "length": 1.0, "load": 10.0},
            {"id": 2, "from_node": (2,), "to_node": (3,), "length": 1.0, "load": 1.0},
            {"id": 3, "from_node": (3,), "to_node": (4,), "length": 1.0, "load": 1.0},
        ]
        sector_of_edge = {0: 0, 1: 0, 2: 1, 3: 1}

        result = rebalance_boundary_edges(edges, sector_of_edge, max_iterations=50)

        self.assertEqual(result[1], 1)  # trecho de fronteira migrou para o setor mais leve
        self.assertEqual(result[0], 0)
        self.assertEqual(result[2], 1)
        self.assertEqual(result[3], 1)

    def test_does_not_empty_a_sector(self):
        # setor 0 tem só o trecho 0; não deve ser esvaziado mesmo que pesado
        edges = [
            {"id": 0, "from_node": (0,), "to_node": (1,), "length": 1.0, "load": 100.0},
            {"id": 1, "from_node": (1,), "to_node": (2,), "length": 1.0, "load": 1.0},
        ]
        sector_of_edge = {0: 0, 1: 1}
        result = rebalance_boundary_edges(edges, sector_of_edge, max_iterations=50)
        self.assertEqual(set(k for k, v in result.items() if v == 0), {0})

    def test_incomplete_sector_mapping_raises(self):
        edges = _line_edges(3)
        with self.assertRaises(ValueError):
            rebalance_boundary_edges(edges, sector_of_edge={0: 0}, max_iterations=10)

    def test_empty_edges_raises(self):
        with self.assertRaises(ValueError):
            rebalance_boundary_edges([], sector_of_edge={}, max_iterations=10)


class TestConnectedComponents(unittest.TestCase):

    def test_line_and_island_orders_larger_component_first(self):
        # (iii) connected_components com uma linha de 5 trechos mais uma ilha de 1 trecho
        # -> dois componentes, a linha primeiro
        line = _line_edges(5, load=1.0)
        island = [
            {"id": "island", "from_node": (100,), "to_node": (101,), "length": 1.0, "load": 1.0}
        ]
        edges = line + island
        comps = connected_components(edges)
        self.assertEqual(len(comps), 2)
        self.assertEqual(comps[0], [0, 1, 2, 3, 4])
        self.assertEqual(comps[1], ["island"])

    def test_tie_in_load_broken_by_number_of_edges(self):
        # (iv) empate de carga resolvido pelo número de trechos
        edges = [
            {"id": "single", "from_node": "a", "to_node": "b", "length": 1.0, "load": 10.0},
            {"id": "pair_1", "from_node": "c", "to_node": "d", "length": 1.0, "load": 5.0},
            {"id": "pair_2", "from_node": "d", "to_node": "e", "length": 1.0, "load": 5.0},
        ]
        comps = connected_components(edges)
        self.assertEqual(len(comps), 2)
        self.assertEqual(comps[0], ["pair_1", "pair_2"])
        self.assertEqual(comps[1], ["single"])

        # Desempate terciário: mesma carga e mesmo nº de trechos -> ordem de entrada do 1º trecho
        equal_edges = [
            {"id": "first", "from_node": "x1", "to_node": "x2", "length": 1.0, "load": 5.0},
            {"id": "second", "from_node": "y1", "to_node": "y2", "length": 1.0, "load": 5.0},
        ]
        equal_comps = connected_components(equal_edges)
        self.assertEqual(equal_comps, [["first"], ["second"]])

    def test_connected_network_returns_single_component_with_all_ids(self):
        # (v) rede conexa -> um componente com todos os ids
        edges = _line_edges(4)
        comps = connected_components(edges)
        self.assertEqual(len(comps), 1)
        self.assertEqual(set(comps[0]), {0, 1, 2, 3})

    def test_empty_edges_raises(self):
        with self.assertRaises(ValueError):
            connected_components([])


if __name__ == "__main__":
    unittest.main()
