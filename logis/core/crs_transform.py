# -*- coding: utf-8 -*-
"""
Verified coordinate transformations for the logis plugin.

This module provides checked coordinate transformations with strict validation.
It exists because QgsCoordinateTransform when short-circuited or invalid (as
observed in Windows / QGIS 4 environments) silently returns coordinates intact
without raising an exception. This caused geographic coordinates (in degrees) to
be passed along as projected metric coordinates (EPSG:5880), corrupting analysis
windows and calculations (e.g. logis 0.6.2 window +/-3000 meters added to degrees).

The functions here verify that transforms are valid, non-short-circuited, actively
displace probe points, and produce coordinates within plausible bounds for the
target CRS.
"""

from typing import Any, Iterable, List, Optional, Tuple, Union

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsCsException,
    QgsFeatureRequest,
    QgsPointXY,
    QgsRectangle,
    QgsWkbTypes,
)

try:
    from qgis.core import QgsProjUtils
except ImportError:
    QgsProjUtils = None

from .crs_check import _extract_xy, plausible_coords, point_moved, valid_extent


class TransformCheckError(RuntimeError):
    """Raised when coordinate transformation fails or produces implausible/unmoved coordinates.

    This exception exists because QgsCoordinateTransform when short-circuited or invalid
    silently returns the source coordinates intact without raising an error.
    """
    pass


def _qgis_version() -> str:
    """Return the QGIS version string or 'unknown'."""
    try:
        return str(Qgis.version())
    except (AttributeError, RuntimeError):
        return "unknown"


def _proj_version() -> str:
    """Return the PROJ version string or 'unknown'."""
    try:
        if QgsProjUtils is not None:
            return f"{QgsProjUtils.projVersionMajor()}.{QgsProjUtils.projVersionMinor()}"
    except (AttributeError, RuntimeError):
        return "unknown"
    return "unknown"


def checked_transform(
    src_crs: Any,
    dst_crs: Any,
    contexts: Any,
    probe: Any,
    factory: Any = None,
) -> Optional[Any]:
    """
    Build and verify a QgsCoordinateTransform across a list of candidate contexts.

    Attempts contexts in order. Accepts the first transform that is valid,
    not short-circuited, successfully transforms ``probe`` to a moved point,
    and produces coordinates that satisfy ``plausible_coords`` for ``dst_crs``.

    If ``src_crs == dst_crs`` (and both are valid), returns ``None`` (identity transform).
    If no candidate context yields a valid, verified transform, raises ``TransformCheckError``
    with a diagnostic summary detailing every attempted context, QGIS version, and PROJ version.

    :param src_crs: Source CRS (QgsCoordinateReferenceSystem or authid string).
    :param dst_crs: Destination CRS (QgsCoordinateReferenceSystem or authid string).
    :param contexts: Iterable of transform contexts (e.g. QgsCoordinateTransformContext or QgsProject)
                     or a single context.
    :param probe: Coordinates (x, y) or QgsPointXY within the source CRS used to verify transformation.
    :param factory: Callable to construct the transform, signature (src, dst, context).
                    Defaults to QgsCoordinateTransform.
    :return: A verified transform object, or None if source and destination are identical.
    :raises TransformCheckError: If destination/source CRS is invalid or no context produces a valid transform.
    """
    src = QgsCoordinateReferenceSystem(src_crs) if isinstance(src_crs, str) else src_crs
    dst = QgsCoordinateReferenceSystem(dst_crs) if isinstance(dst_crs, str) else dst_crs

    src_valid = bool(hasattr(src, "isValid") and src.isValid())
    dst_valid = bool(hasattr(dst, "isValid") and dst.isValid())

    src_authid = src.authid() if src_valid and src.authid() else (str(src_crs) if isinstance(src_crs, str) else "<invalid CRS>")
    dst_authid = dst.authid() if dst_valid and dst.authid() else (str(dst_crs) if isinstance(dst_crs, str) else "<invalid CRS>")

    if src_valid and dst_valid and (src == dst or (src.authid() and src.authid() == dst.authid())):
        return None

    if isinstance(probe, QgsPointXY):
        probe_pt = probe
        probe_xy = (float(probe.x()), float(probe.y()))
    elif hasattr(probe, "x") and callable(probe.x):
        probe_pt = QgsPointXY(float(probe.x()), float(probe.y()))
        probe_xy = (float(probe.x()), float(probe.y()))
    elif isinstance(probe, (tuple, list)) and len(probe) >= 2:
        probe_pt = QgsPointXY(float(probe[0]), float(probe[1]))
        probe_xy = (float(probe[0]), float(probe[1]))
    else:
        raise TypeError(f"Invalid probe coordinate: {probe!r}")

    if contexts is None:
        context_list = [QgsCoordinateTransformContext()]
    elif isinstance(contexts, (list, tuple, set)):
        context_list = list(contexts)
    else:
        context_list = [contexts]

    tf_factory = factory if factory is not None else QgsCoordinateTransform

    attempts = []
    for ctx in context_list:
        try:
            ct = tf_factory(src, dst, ctx)
        except Exception as exc:
            attempts.append(f"factory raised with context {ctx!r}: {exc}")
            continue

        is_valid = bool(getattr(ct, "isValid", lambda: True)())
        is_short = bool(getattr(ct, "isShortCircuited", lambda: False)())

        if not is_valid or is_short:
            attempts.append(f"isValid={is_valid}, isShortCircuited={is_short}")
            continue

        try:
            dst_pt = ct.transform(probe_pt)
        except Exception as exc:
            attempts.append(f"isValid={is_valid}, isShortCircuited={is_short}, probe transform raised: {exc}")
            continue

        try:
            dst_xy = _extract_xy(dst_pt)
            dst_str = f"({dst_xy[0]:.4f}, {dst_xy[1]:.4f})"
        except (AttributeError, TypeError, ValueError):
            dst_xy = dst_pt
            dst_str = str(dst_pt)

        is_both_geo = bool(
            hasattr(src, "isGeographic")
            and hasattr(dst, "isGeographic")
            and src.isGeographic()
            and dst.isGeographic()
        )
        if not is_both_geo and not point_moved(probe_xy, dst_xy):
            attempts.append(
                f"isValid={is_valid}, isShortCircuited={is_short}, probe={probe_xy} -> dst={dst_str} (point did not move)"
            )
            continue

        if not plausible_coords(dst_authid, [dst_xy]):
            attempts.append(
                f"isValid={is_valid}, isShortCircuited={is_short}, probe={probe_xy} -> dst={dst_str} (implausible coordinates for {dst_authid})"
            )
            continue

        return ct

    qgis_ver = _qgis_version()
    proj_ver = _proj_version()
    attempts_detail = "\n".join(f"  [{i + 1}] {att}" for i, att in enumerate(attempts))
    msg = (
        f"Failed to verify coordinate transformation from {src_authid} to {dst_authid}.\n"
        f"QGIS version: {qgis_ver}, PROJ version: {proj_ver}.\n"
        f"Attempts ({len(attempts)} context(s) tested):\n"
        f"{attempts_detail}"
    )
    raise TransformCheckError(msg)


def transform_points(ct: Any, points: Iterable[Any], dst_authid: Any) -> List[Any]:
    """
    Transform a sequence of points using a verified coordinate transform.

    :param ct: QgsCoordinateTransform instance, or None for identity transform.
    :param points: Iterable of points (QgsPointXY, QgsPoint, or (x, y) tuples).
    :param dst_authid: Destination CRS authid string or QgsCoordinateReferenceSystem.
    :return: List of transformed points (or copies if ct is None).
    :raises TransformCheckError: If any transformed point fails transformation or has implausible coordinates.
    """
    authid = dst_authid.authid() if hasattr(dst_authid, "authid") else str(dst_authid)

    if ct is None:
        copied = []
        for pt in points:
            if isinstance(pt, QgsPointXY):
                copied.append(QgsPointXY(pt))
            elif hasattr(pt, "clone"):
                copied.append(pt.clone())
            elif isinstance(pt, (tuple, list)):
                copied.append((float(pt[0]), float(pt[1])))
            else:
                copied.append(pt)
        return copied

    results = []
    for idx, pt in enumerate(points):
        try:
            if isinstance(pt, QgsPointXY):
                t_pt = ct.transform(pt)
            elif isinstance(pt, (tuple, list)):
                t_pt = ct.transform(QgsPointXY(float(pt[0]), float(pt[1])))
            elif hasattr(pt, "x") and callable(pt.x):
                t_pt = ct.transform(QgsPointXY(float(pt.x()), float(pt.y())))
            else:
                t_pt = ct.transform(pt)
        except Exception as exc:
            raise TransformCheckError(
                f"Failed to transform point at index {idx} ({pt!r}) to {authid}: {exc}"
            ) from exc

        if not plausible_coords(authid, [t_pt]):
            try:
                val_str = f"({t_pt.x():.4f}, {t_pt.y():.4f})"
            except (AttributeError, TypeError, ValueError):
                val_str = str(t_pt)
            raise TransformCheckError(
                f"Transformed point at index {idx} with value {val_str} is implausible for destination CRS {authid}."
            )
        results.append(t_pt)

    return results


def transform_bbox(ct: Any, rect: Any, dst_authid: Any) -> Any:
    """
    Transform a bounding box using a verified coordinate transform.

    :param ct: QgsCoordinateTransform instance, or None for identity transform.
    :param rect: QgsRectangle or sequence (xmin, ymin, xmax, ymax).
    :param dst_authid: Destination CRS authid string or QgsCoordinateReferenceSystem.
    :return: Transformed QgsRectangle (or copy if ct is None).
    :raises TransformCheckError: If bounding box transform fails (e.g. QgsCsException),
                                results in invalid/degenerate extent, or has implausible corner coordinates.
    """
    authid = dst_authid.authid() if hasattr(dst_authid, "authid") else str(dst_authid)

    if isinstance(rect, (tuple, list)) and len(rect) >= 4:
        r = QgsRectangle(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
    elif isinstance(rect, QgsRectangle):
        r = rect
    else:
        r = rect

    if ct is None:
        return QgsRectangle(r)

    try:
        res = ct.transformBoundingBox(r)
    except QgsCsException as exc:
        r_str = r.toString() if hasattr(r, "toString") else str(r)
        raise TransformCheckError(
            f"Forward transform of bounding box {r_str} to {authid} failed: {exc}"
        ) from exc
    except Exception as exc:
        r_str = r.toString() if hasattr(r, "toString") else str(r)
        raise TransformCheckError(
            f"Forward transform of bounding box {r_str} to {authid} failed: {exc}"
        ) from exc

    xmin, ymin, xmax, ymax = res.xMinimum(), res.yMinimum(), res.xMaximum(), res.yMaximum()
    if not valid_extent(xmin, ymin, xmax, ymax):
        raise TransformCheckError(
            f"Transformed bounding box {res.toString()} is invalid or degenerate for destination CRS {authid}."
        )

    corners = [
        (xmin, ymin),
        (xmin, ymax),
        (xmax, ymin),
        (xmax, ymax),
    ]
    if not plausible_coords(authid, corners):
        raise TransformCheckError(
            f"Transformed bounding box {res.toString()} has corners {corners} implausible for destination CRS {authid}."
        )

    return res


def _extract_point_from_geom(geom: Any) -> QgsPointXY:
    """Return a QgsPointXY for a geometry (the point itself, or the centroid for a polygon)."""
    if geom.type() == QgsWkbTypes.GeometryType.PointGeometry:
        return geom.asPoint()
    return geom.centroid().asPoint()


def read_points_in_crs(
    source: Any,
    dst_crs: Any,
    context: Any,
    label: str,
) -> Tuple[List[Any], List[Any]]:
    """
    Read point (or polygon centroid) geometries from a QGIS Processing feature source,
    reprojected to ``dst_crs``, detecting the silent no-op documented for
    ``QgsFeatureRequest().setDestinationCrs()``: a feature whose transform fails comes back
    with an empty geometry instead of raising an exception or calling
    ``setTransformErrorCallback``.

    The source is read twice: once untouched, to keep the original features (with their
    original, non-empty geometry) that go to the output sink exactly as before; and once
    with the destination CRS request, to get the reprojected point (or centroid, for
    polygons). Both passes are matched by ``feat.id()``, and the returned lists follow the
    order of the first (untouched) pass.

    :param source: QgsProcessingFeatureSource (or QgsVectorLayer) to read from.
    :param dst_crs: Destination CRS (QgsCoordinateReferenceSystem or authid string).
    :param context: QgsProcessingContext; its ``transformContext()`` feeds the request.
    :param label: Human-readable identifier of the source, used in diagnostics.
    :return: Tuple ``(features, points)`` with the original features and their reprojected
             QgsPointXY, aligned by position. Features without geometry are skipped in both
             passes without error.
    :raises TransformCheckError: If a feature's geometry does not survive reprojection (comes
             back empty), or if the resulting points are implausible or did not move for
             ``dst_crs``.
    """
    dst = QgsCoordinateReferenceSystem(dst_crs) if isinstance(dst_crs, str) else dst_crs
    src_crs = source.sourceCrs()

    features: List[Any] = []
    original_points: List[Any] = []
    for feat in source.getFeatures():
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            continue
        features.append(feat)
        original_points.append(_extract_point_from_geom(geom))

    if not features:
        return [], []

    src_valid = bool(hasattr(src_crs, "isValid") and src_crs.isValid())
    dst_valid = bool(hasattr(dst, "isValid") and dst.isValid())

    src_authid = src_crs.authid() if src_valid and src_crs.authid() else str(src_crs)
    dst_authid = dst.authid() if dst_valid and dst.authid() else str(dst_crs)

    same_crs = bool(
        src_valid and dst_valid
        and (src_crs == dst or (src_crs.authid() and src_crs.authid() == dst.authid()))
    )
    if same_crs:
        return features, original_points

    request = QgsFeatureRequest().setDestinationCrs(dst, context.transformContext())
    reprojected_by_id = {feat.id(): feat.geometry() for feat in source.getFeatures(request)}

    points: List[Any] = []
    for feat in features:
        geom = reprojected_by_id.get(feat.id())
        if geom is None or geom.isEmpty():
            raise TransformCheckError(
                f"Failed to reproject feature id {feat.id()} of '{label}' from {src_authid} "
                f"to {dst_authid}: the transformed geometry came back empty (silent no-op of "
                f"QgsFeatureRequest().setDestinationCrs())."
            )
        points.append(_extract_point_from_geom(geom))

    if not plausible_coords(dst_authid, points):
        qgis_ver = _qgis_version()
        proj_ver = _proj_version()
        offenders = [
            f"id {feat.id()}: ({pt.x():.4f}, {pt.y():.4f})"
            for feat, pt in zip(features, points)
            if not plausible_coords(dst_authid, [pt])
        ]
        raise TransformCheckError(
            f"Reprojected points of '{label}' from {src_authid} to {dst_authid} are "
            f"implausible for the destination CRS.\n"
            f"QGIS version: {qgis_ver}, PROJ version: {proj_ver}.\n"
            f"Offending feature(s): {', '.join(offenders)}"
        )

    is_both_geo = bool(
        hasattr(src_crs, "isGeographic")
        and hasattr(dst, "isGeographic")
        and src_crs.isGeographic()
        and dst.isGeographic()
    )
    if not is_both_geo and not point_moved(original_points[0], points[0]):
        qgis_ver = _qgis_version()
        proj_ver = _proj_version()
        raise TransformCheckError(
            f"Failed to verify coordinate transformation of '{label}' from {src_authid} to "
            f"{dst_authid}: probe feature id {features[0].id()} "
            f"({original_points[0].x():.4f}, {original_points[0].y():.4f}) did not move after "
            f"reprojection to ({points[0].x():.4f}, {points[0].y():.4f}).\n"
            f"QGIS version: {qgis_ver}, PROJ version: {proj_ver}."
        )

    return features, points
