# -*- coding: utf-8 -*-
"""
/***************************************************************************
 logis
                                 A QGIS plugin
 Complemento do QGIS para apoiar projetos de logística no Brasil
                              -------------------
        begin                : 2026-07-19
        copyright            : (C) 2026 by Diego Camargo
        email                : 
        license              : GPL-3.0
 ***************************************************************************/
"""
"""Graph Builder module for the logis plugin.

Builds a QgsGraph from a LineString/MultiLineString vector layer representing a transportation network.
Supports distance-based and speed/travel-time-based edge costs, and respects one-way constraints.

References:
    - Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. Numerische Mathematik, 1(1), 269-271.
    - QGIS Documentation: Network Analysis Library (https://docs.qgis.org/)

Complexity/Scale limits:
    - Tested network scale: up to 50,000 edges and 40,000 vertices (typical large municipal network).
    - Construction complexity: O(E) where E is the number of edges.
    - Space complexity: O(V + E) where V is the number of vertices.
"""

from qgis.core import (
    QgsVectorLayer,
    QgsCoordinateReferenceSystem,
    QgsField,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsCoordinateTransform,
    QgsFeatureRequest,
    QgsWkbTypes,
    QgsCsException
)
from .. import qgis_compat
from ..crs_check import valid_extent
from qgis.analysis import (
    QgsVectorLayerDirector,
    QgsGraphBuilder,
    QgsNetworkDistanceStrategy,
    QgsNetworkSpeedStrategy,
    QgsNetworkStrategy
)


class TravelTimeStrategy(QgsNetworkStrategy):
    """Custom network strategy to calculate travel time cost.

    If a travel time field is available, prorates it by (arc distance / total feature
    length) — QgsVectorLayerDirector splits each feature into one arc per pair of
    consecutive vertices, so the precomputed travel_time (for the whole feature) must
    be scaled down per arc, or multi-vertex features would have their full travel time
    charged on every arc.
    Otherwise, calculates travel time from feature distance (meters) and speed (km/h).
    """

    def __init__(self, travel_time_idx=-1, speed_idx=-1, default_speed=40.0):
        super().__init__()
        self.travel_time_idx = travel_time_idx
        self.speed_idx = speed_idx
        self.default_speed = default_speed

    def cost(self, distance, feature):
        # 1. Try to read travel time directly if field exists
        if self.travel_time_idx != -1:
            val = feature.attribute(self.travel_time_idx)
            try:
                c = float(val)
                if c >= 0:
                    # Scale by distance / total_length of feature
                    length_val = feature.attribute("length") if "length" in feature.fields().names() else None
                    try:
                        total_len = float(length_val) if length_val is not None else 0.0
                    except (ValueError, TypeError):
                        total_len = 0.0

                    if total_len <= 0:
                        geom = feature.geometry()
                        total_len = geom.length() if geom else 0.0

                    if total_len > 0:
                        return c * (distance / total_len)
                    return c
            except (ValueError, TypeError):
                pass

        # 2. Otherwise calculate travel time using speed and distance
        speed = self.default_speed
        if self.speed_idx != -1:
            val = feature.attribute(self.speed_idx)
            try:
                s = float(val)
                if s > 0:
                    speed = s
            except (ValueError, TypeError):
                pass

        # Convert speed from km/h to m/s
        speed_mps = speed / 3.6
        return distance / speed_mps if speed_mps > 0 else 0.0

    def requiredAttributes(self):
        attrs = []
        if self.travel_time_idx != -1:
            attrs.append(self.travel_time_idx)
        if self.speed_idx != -1:
            attrs.append(self.speed_idx)
        return attrs


def build_graph(
    layer,
    oneway_field="oneway",
    speed_field="speed",
    travel_time_field="travel_time",
    target_crs="EPSG:5880",
    points=None,
    extent=None,
    feedback=None
):
    """Builds a QgsGraph from a vector line layer, reprojecting to a metric CRS.

    Args:
        layer (QgsVectorLayer): The input line vector layer (e.g. EPSG:4674).
        oneway_field (str): Name of the field containing one-way info.
        speed_field (str): Name of the field containing speed limits in km/h.
        travel_time_field (str): Name of the field containing pre-calculated travel time in seconds.
        target_crs (str or QgsCoordinateReferenceSystem): Target metric CRS (default EPSG:5880).
        points (list of QgsPointXY, optional): List of coordinates to snap/tie to the graph.

    Returns:
        dict: A dictionary containing:
            - "graph": The built QgsGraph object.
            - "snapped_points": List of snapped QgsPointXY corresponding to the input 'points'.
            - "director": The QgsVectorLayerDirector used to build the graph.
            - "crs": The target metric CRS object.
    """
    if not layer or not layer.isValid():
        raise ValueError("Invalid input layer.")

    # 1. Resolve CRS and ensure it is metric for calculations
    if isinstance(target_crs, str):
        crs_obj = QgsCoordinateReferenceSystem(target_crs)
    elif isinstance(target_crs, QgsCoordinateReferenceSystem):
        crs_obj = target_crs
    else:
        crs_obj = QgsCoordinateReferenceSystem("EPSG:5880")

    if extent is None:
        import processing
        # Always reproject to memory layer to ensure metric calculation and avoid altering original layer
        reproj_params = {
            "INPUT": layer,
            "TARGET_CRS": crs_obj.authid(),
            "OUTPUT": "memory:"
        }
        reproj_res = processing.run("native:reprojectlayer", reproj_params)
        working_layer = reproj_res["OUTPUT"]

        if not working_layer or not working_layer.isValid():
            raise RuntimeError("Failed to reproject network layer.")
    else:
        if not valid_extent(extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()):
            raise ValueError(f"Invalid analysis window extent: {extent}")
        transform_back = QgsCoordinateTransform(crs_obj, layer.crs(), QgsProject.instance())
        try:
            source_extent = transform_back.transformBoundingBox(extent)
        except QgsCsException as exc:
            src = crs_obj.authid()
            dst = layer.crs().authid()
            raise RuntimeError(f"Could not transform the analysis window {extent} from {src} to {dst}: {exc}")
        request = QgsFeatureRequest().setFilterRect(source_extent)

        geom_str = QgsWkbTypes.displayString(layer.wkbType())
        working_layer = QgsVectorLayer(f"{geom_str}?crs={crs_obj.authid()}", "working", "memory")
        if not working_layer.isValid():
            raise RuntimeError("Failed to create memory layer for extent.")

        working_layer.dataProvider().addAttributes(layer.fields())
        working_layer.updateFields()

        transform = QgsCoordinateTransform(layer.crs(), crs_obj, QgsProject.instance())
        feats = []
        for f in layer.getFeatures(request):
            geom = f.geometry()
            if geom:
                geom.transform(transform)
                f.setGeometry(geom)
            feats.append(f)

        working_layer.dataProvider().addFeatures(feats)

        if working_layer.featureCount() == 0:
            raise RuntimeError("No features found in the specified extent.")

    if feedback:
        feedback.pushInfo(f"Features in window: {working_layer.featureCount()}")

    # 2. Standardize direction values into a new memory field
    working_layer.startEditing()
    direction_field_name = "_direction"
    working_layer.addAttribute(QgsField(direction_field_name, qgis_compat.field_type("string")))
    working_layer.updateFields()

    dir_idx = working_layer.fields().indexOf(direction_field_name)
    orig_oneway_idx = working_layer.fields().indexOf(oneway_field)

    for feat in working_layer.getFeatures():
        oneway_val = ""
        if orig_oneway_idx != -1:
            oneway_val = str(feat.attribute(orig_oneway_idx)).strip().lower()

        # Map typical OSM values: "yes"/"1"/"true" (forward), "-1" (backward), other/empty (two-way)
        if oneway_val in ("yes", "1", "true"):
            mapped = "F"
        elif oneway_val == "-1":
            mapped = "B"
        else:
            mapped = "T"

        working_layer.changeAttributeValue(feat.id(), dir_idx, mapped)

    working_layer.commitChanges()

    # 3. Create the Director
    director = QgsVectorLayerDirector(
        working_layer,
        dir_idx,
        "F",
        "B",
        "T",
        QgsVectorLayerDirector.Direction.DirectionBoth
    )

    # 4. Add cost strategies
    # Strategy 0: Distance
    dist_strategy = QgsNetworkDistanceStrategy()
    director.addStrategy(dist_strategy)

    # Strategy 1: Travel Time
    travel_time_idx = working_layer.fields().indexOf(travel_time_field)
    speed_idx = working_layer.fields().indexOf(speed_field)
    time_strategy = TravelTimeStrategy(
        travel_time_idx=travel_time_idx,
        speed_idx=speed_idx,
        default_speed=40.0
    )
    director.addStrategy(time_strategy)

    # 5. Build the graph and tie points
    builder = QgsGraphBuilder(crs_obj)
    
    input_points = points if points is not None else []
    snapped_points = director.makeGraph(builder, input_points)
    graph = builder.graph()

    if points is not None and len(snapped_points) != len(points):
        raise RuntimeError(f"Graph director returned {len(snapped_points)} tied points, expected {len(points)}")

    if feedback:
        feedback.pushInfo(f"Graph built: {graph.vertexCount()} vertices, {graph.edgeCount()} edges")

    return {
        "graph": graph,
        "snapped_points": snapped_points,
        "director": director,
        "crs": crs_obj
    }
