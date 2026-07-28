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
"""OD Matrix module for the logis plugin.

Calculates Origin-Destination cost matrix using multi-origin Dijkstra algorithm
on a QgsGraph, with on-disk caching.

References:
    - Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. Numerische Mathematik, 1(1), 269-271.
    - QGIS Documentation: Network Analysis Library (https://docs.qgis.org/)

Complexity/Scale limits:
    - Tested network scale: up to 50,000 edges and 40,000 vertices (typical large municipal network).
    - Search complexity: O(O * (E + V log V)) where O is the number of origins, V is vertices, E is edges.
    - Space complexity: O(O * D) for the output matrix, where D is the number of destinations.
"""

import hashlib
import pickle
from pathlib import Path

from qgis.core import QgsPointXY, QgsMessageLog, Qgis
from qgis.analysis import QgsGraphAnalyzer, QgsGraph

from ..downloader import cache_dir

# Tag for QgsMessageLog
LOG_TAG = "logis"


def _resolve_nodes(graph, nodes):
    """Resolves a list of node indices or coordinates to graph vertex indices.

    Args:
        graph (QgsGraph): The network graph.
        nodes (list): List of node indices (int) or coordinates (QgsPointXY).

    Returns:
        list of int: List of graph vertex indices.
    """
    resolved = []
    for node in nodes:
        if isinstance(node, (int, float)):
            idx = int(node)
            try:
                graph.vertex(idx)
            except IndexError:
                raise ValueError(f"Vertex index {idx} does not exist in the graph.")
            resolved.append(idx)
        elif isinstance(node, QgsPointXY):
            idx = graph.findVertex(node)
            if idx == -1:
                raise ValueError(f"Point {node} not found in the graph. Ensure it was snapped to the graph during build.")
            resolved.append(idx)
        else:
            raise TypeError(f"Invalid node type: {type(node)}. Expected int or QgsPointXY.")
    return resolved


def _get_graph_hash(graph, criterion_num):
    """Generates a unique MD5 hash for the graph topology, coordinates, and cost strategy.

    Args:
        graph (QgsGraph): The network graph.
        criterion_num (int): Strategy index for optimization.

    Returns:
        str: MD5 hash of the graph.
    """
    h = hashlib.md5()
    h.update(f"V:{graph.vertexCount()}".encode('utf-8'))
    h.update(f"E:{graph.edgeCount()}".encode('utf-8'))
    h.update(f"C:{criterion_num}".encode('utf-8'))
    
    # Hash all vertices coordinates
    for i in range(graph.vertexCount()):
        pt = graph.vertex(i).point()
        h.update(f"{pt.x():.6f},{pt.y():.6f}".encode('utf-8'))
        
    # Hash all edges connections and costs
    for i in range(graph.edgeCount()):
        edge = graph.edge(i)
        h.update(f"{edge.fromVertex()}->{edge.toVertex()}:{edge.cost(criterion_num):.6f}".encode('utf-8'))
        
    return h.hexdigest()


def compute_od_matrix(
    graph,
    origins,
    destinations,
    criterion_num=0,
    cache_id=None,
    force=False,
    feedback=None
):
    """Computes the Origin-Destination cost matrix between origins and destinations on a QgsGraph.

    Args:
        graph (QgsGraph): The network graph.
        origins (list of int or list of QgsPointXY): List of origin node indices or coordinate points.
        destinations (list of int or list of QgsPointXY): List of destination node indices or coordinate points.
        criterion_num (int): Strategy index for optimization (e.g. 0 for distance, 1 for travel time).
        cache_id (str, optional): Unique ID to prefix/identify the cache file.
        force (bool): If True, ignores cached results and recomputes.
        feedback (QgsFeedback, optional): QGIS feedback object for logging and progress.

    Returns:
        list of list of float: A 2D matrix where matrix[i][j] is the shortest path cost from origins[i] to destinations[j].
    """
    if not graph or graph.vertexCount() == 0:
        raise ValueError("Invalid or empty graph.")

    # 1. Resolve origins and destinations to vertex indices
    origins_idx = _resolve_nodes(graph, origins)
    destinations_idx = _resolve_nodes(graph, destinations)

    # 2. Setup Cache
    try:
        c_dir = cache_dir()
    except Exception:
        # Fallback to standard user directory cache in case QStandardPaths fails (e.g., in headless script)
        c_dir = Path.home() / ".cache" / "logis"
    
    od_cache_dir = c_dir / "od_matrices"
    od_cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate matrix-specific MD5 signature
    graph_hash = _get_graph_hash(graph, criterion_num)
    
    h = hashlib.md5()
    h.update(graph_hash.encode('utf-8'))
    h.update(f"O:{origins_idx}".encode('utf-8'))
    h.update(f"D:{destinations_idx}".encode('utf-8'))
    if cache_id:
        h.update(f"ID:{cache_id}".encode('utf-8'))
        
    cache_key = h.hexdigest()
    prefix = f"{cache_id}_" if cache_id else ""
    cache_file = od_cache_dir / f"od_matrix_{prefix}{cache_key}.pkl"

    # 3. Try to load from cache
    if not force and cache_file.exists():
        msg = f"Reusing cached OD matrix: {cache_file.name}"
        if feedback is not None:
            feedback.pushInfo(f"[OD Cache] {msg}")
        QgsMessageLog.logMessage(msg, LOG_TAG, Qgis.MessageLevel.Info)
        
        try:
            with open(cache_file, "rb") as f:
                data = pickle.load(f)
            if isinstance(data, dict) and "matrix" in data:
                return data["matrix"]
            elif isinstance(data, list):
                return data
        except Exception as e:
            err_msg = f"Error loading cached OD matrix: {e}. Recomputing..."
            if feedback is not None:
                feedback.pushInfo(f"[OD Cache] {err_msg}")
            QgsMessageLog.logMessage(err_msg, LOG_TAG, Qgis.MessageLevel.Warning)

    # 4. Compute via multi-origin Dijkstra
    msg = f"Computing OD matrix for {len(origins_idx)} origins and {len(destinations_idx)} destinations..."
    if feedback is not None:
        feedback.pushInfo(f"[OD Matrix] {msg}")
    QgsMessageLog.logMessage(msg, LOG_TAG, Qgis.MessageLevel.Info)

    matrix = []
    total = len(origins_idx)
    for i, origin_idx in enumerate(origins_idx):
        if feedback is not None and feedback.isCanceled():
            raise RuntimeError("OD Matrix computation canceled by user.")
            
        tree, costs = QgsGraphAnalyzer.dijkstra(graph, origin_idx, criterion_num)
        
        row = []
        for dest_idx in destinations_idx:
            row.append(costs[dest_idx])
        matrix.append(row)
        
        if feedback is not None:
            percent = int((i + 1) / total * 100)
            feedback.setProgress(percent)

    # 5. Save to Cache
    try:
        cache_data = {
            "matrix": matrix,
            "origins": origins_idx,
            "destinations": destinations_idx,
            "criterion_num": criterion_num,
            "cache_id": cache_id
        }
        with open(cache_file, "wb") as f:
            pickle.dump(cache_data, f)
        
        save_msg = f"Saved OD matrix to cache: {cache_file.name}"
        if feedback is not None:
            feedback.pushInfo(f"[OD Cache] {save_msg}")
        QgsMessageLog.logMessage(save_msg, LOG_TAG, Qgis.MessageLevel.Info)
    except Exception as e:
        save_err = f"Failed to save OD matrix to cache: {e}"
        if feedback is not None:
            feedback.pushInfo(f"[OD Cache] {save_err}")
        QgsMessageLog.logMessage(save_err, LOG_TAG, Qgis.MessageLevel.Warning)

    return matrix
