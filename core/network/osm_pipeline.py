# -*- coding: utf-8 -*-
"""Pipeline OSM municipal: JSON → geometrias (links/nós).

Converte resultado Overpass em camadas QgsVectorLayer de segmentos de vias
e nós de extremidade, recortadas ao polígono municipal.
"""
import os
from pathlib import Path

from qgis.core import (
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsLineString,
    QgsFields,
    QgsProject,
    QgsWkbTypes,
    QgsDistanceArea,
    QgsCoordinateReferenceSystem,
    QgsVectorFileWriter
)

from .. import qgis_compat
from ..connectors import osm
from ..data_backend import has_gisbr


_DEFAULT_SPEEDS = {
    "motorway": 110.0,
    "trunk": 90.0,
    "primary": 70.0,
    "secondary": 60.0,
    "tertiary": 50.0,
    "residential": 40.0,
    "living_street": 30.0,
    "motorway_link": 60.0,
    "trunk_link": 50.0,
    "primary_link": 50.0,
    "secondary_link": 40.0,
    "tertiary_link": 40.0,
    "unclassified": 40.0,
    "service": 30.0,
    "track": 30.0,
}


def _parse_speed(way):
    """Extrai velocidade da tag maxspeed ou mapeia via highway."""
    tags = way.get("tags", {})
    maxspeed = tags.get("maxspeed", "")
    if maxspeed:
        digits = "".join(c for c in maxspeed if c.isdigit())
        if digits:
            try:
                speed_val = float(digits)
                if "mph" in maxspeed.lower():
                    speed_val = speed_val * 1.60934
                return speed_val
            except ValueError:
                pass
    
    highway = tags.get("highway", "")
    return _DEFAULT_SPEEDS.get(highway, 40.0)


def _calcular_comprimento_metros(geom):
    """Calcula o comprimento da geometria em metros usando o elipsoide GRS80."""
    da = QgsDistanceArea()
    crs = QgsCoordinateReferenceSystem("EPSG:4674")
    da.setSourceCrs(crs, QgsProject.instance().transformContext())
    da.setEllipsoid(crs.ellipsoidAcronym())
    return da.measureLength(geom)


def _parse_osm_ways(payload):
    """Extrai ways com tag highway do JSON Overpass."""
    if not payload or "elements" not in payload:
        return []
    ways = [e for e in payload["elements"] if e.get("type") == "way" and "tags" in e and "highway" in e["tags"]]
    return ways


def _way_to_linestring(way_osm, nodes_dict):
    """Converte way OSM em QgsLineString (EPSG:4674 lon,lat)."""
    coords = []
    for node_id in way_osm.get("nodes", []):
        if node_id in nodes_dict:
            lon, lat = nodes_dict[node_id]
            coords.append(QgsPoint(lon, lat))
    return QgsLineString(coords) if len(coords) >= 2 else None


def _build_nodes_dict(payload):
    """Cria mapa node_id → (lon, lat) do JSON Overpass."""
    nodes_dict = {}
    if payload and "elements" in payload:
        for el in payload["elements"]:
            if el.get("type") == "node" and "lat" in el and "lon" in el:
                nodes_dict[el["id"]] = (el["lon"], el["lat"])
    return nodes_dict


def _create_links_layer(ways, nodes_dict, layer_name="osm_links_raw"):
    """Cria QgsVectorLayer de LineString a partir de ways, com custos."""
    fields = QgsFields()
    fields.append(QgsField("way_id", qgis_compat.field_type("int")))
    fields.append(QgsField("highway", qgis_compat.field_type("string")))
    fields.append(QgsField("name", qgis_compat.field_type("string")))
    fields.append(QgsField("oneway", qgis_compat.field_type("string")))
    fields.append(QgsField("length", qgis_compat.field_type("double")))
    fields.append(QgsField("speed", qgis_compat.field_type("double")))
    fields.append(QgsField("travel_time", qgis_compat.field_type("double")))
    
    uri = "LineString?crs=EPSG:4674&field=way_id:long&field=highway:string&field=name:string&field=oneway:string&field=length:double&field=speed:double&field=travel_time:double"
    layer = QgsVectorLayer(uri, layer_name, "memory")
    layer.startEditing()
    
    for way in ways:
        geom = _way_to_linestring(way, nodes_dict)
        if geom is None:
            continue
        
        qgeom = QgsGeometry(geom)
        length_m = _calcular_comprimento_metros(qgeom)
        speed_kmh = _parse_speed(way)
        speed_mps = speed_kmh / 3.6
        time_s = length_m / speed_mps if speed_mps > 0 else 0.0
        
        feat = QgsFeature(fields)
        feat.setGeometry(qgeom)
        feat["way_id"] = way.get("id", 0)
        feat["highway"] = way.get("tags", {}).get("highway", "")
        feat["name"] = way.get("tags", {}).get("name", "")
        feat["oneway"] = way.get("tags", {}).get("oneway", "no")
        feat["length"] = length_m
        feat["speed"] = speed_kmh
        feat["travel_time"] = time_s
        layer.addFeature(feat)
    
    layer.commitChanges()
    return layer


def _extract_nodes_from_layer(layer):
    """Extrai pontos de extremidade de LineStringLayer (LineString ou MultiLineString), deduplica."""
    nodes_set = set()
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom and geom.type() == QgsWkbTypes.GeometryType.LineGeometry:
            if geom.isMultipart():
                polylines = geom.asMultiPolyline()
                for polyline in polylines:
                    if polyline:
                        nodes_set.add((polyline[0].x(), polyline[0].y()))
                        if len(polyline) > 1:
                            nodes_set.add((polyline[-1].x(), polyline[-1].y()))
            else:
                coord_list = geom.asPolyline()
                if coord_list:
                    nodes_set.add((coord_list[0].x(), coord_list[0].y()))
                    if len(coord_list) > 1:
                        nodes_set.add((coord_list[-1].x(), coord_list[-1].y()))
    return list(nodes_set)


def _create_nodes_layer(nodes_set, layer_name="osm_nodes"):
    """Cria QgsVectorLayer de Points a partir de conjunto (lon,lat)."""
    layer = QgsVectorLayer(f"Point?crs=EPSG:4674&field=node_id:long&field=x:double&field=y:double", layer_name, "memory")
    layer.startEditing()
    
    fields = QgsFields()
    fields.append(QgsField("node_id", qgis_compat.field_type("int")))
    fields.append(QgsField("x", qgis_compat.field_type("double")))
    fields.append(QgsField("y", qgis_compat.field_type("double")))
    
    for i, (lon, lat) in enumerate(sorted(nodes_set)):
        feat = QgsFeature(fields)
        feat.setGeometry(QgsGeometry(QgsPoint(lon, lat)))
        feat["node_id"] = i
        feat["x"] = lon
        feat["y"] = lat
        layer.addFeature(feat)
    
    layer.commitChanges()
    return layer


def _recorta_poligono(layer, poligono, layer_name):
    """Recorta layer pelo polígono (native:clip)."""
    import processing
    try:
        out = processing.run("native:clip", {
            "INPUT": layer, "OVERLAY": poligono, "OUTPUT": "TEMPORARY_OUTPUT",
        })["OUTPUT"]
        if isinstance(out, str):
            return QgsVectorLayer(out, layer_name, "ogr")
        return out
    except Exception:
        return None


def _resolve_layer(out, layer_name):
    if isinstance(out, str):
        return QgsProject.instance().mapLayer(out) or QgsVectorLayer(out, layer_name, "ogr")
    return out


def _municipio_poligono(code_muni, nome_muni=None, feedback=None):
    """Poligono do municipio p/ recorte. None se falhar."""
    import processing
    
    if has_gisbr():
        try:
            out = processing.run("gisbr:read_municipality", {
                "CODE": str(code_muni),
                "SIMPLIFIED": True,
                "OUTPUT": "TEMPORARY_OUTPUT",
            })["OUTPUT"]
            layer = _resolve_layer(out, "municipio")
            if layer is None or not layer.isValid():
                return None
            return layer
        except Exception as e:
            if feedback is not None:
                feedback.pushInfo(f"Erro ao obter municipio via GisBR: {e}")
            return None
    else:
        # Fallback: baixar diretamente usando o downloader do logis
        from .. import downloader
        uf_code = str(code_muni)[:2]
        url = f"https://www.ipea.gov.br/geobr/data_gpkg/municipality/2020/{uf_code}municipality_2020_simplified.gpkg"
        try:
            local_path = downloader.fetch(url, feedback=feedback)
            layer = QgsVectorLayer(str(local_path), "municipio", "ogr")
            if not layer.isValid():
                return None
            field_names = [f.name() for f in layer.fields()]
            col = "code_muni" if "code_muni" in field_names else "code"
            if col in field_names:
                field = layer.fields().field(col)
                if field.isNumeric():
                    expr = f'"{col}" = {int(code_muni)}'
                else:
                    expr = f'"{col}" = \'{code_muni}\''
                if not layer.setSubsetString(expr):
                    return None
            return layer
        except Exception as e:
            if feedback is not None:
                feedback.pushInfo(f"Erro no fallback do municipio: {e}")
            return None


def _bbox_da_camada(layer):
    extent = layer.extent()
    return (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())


def _update_cost_attributes(layer):
    """Calcula ou atualiza os campos length e travel_time com base na geometria atual."""
    if not layer.startEditing():
        return
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom:
            length_m = _calcular_comprimento_metros(geom)
            speed_kmh = feat["speed"] if "speed" in feat.fields().names() else 40.0
            if not isinstance(speed_kmh, (int, float)) or speed_kmh <= 0:
                speed_kmh = 40.0
            speed_mps = speed_kmh / 3.6
            time_s = length_m / speed_mps if speed_mps > 0 else 0.0
            
            fid = feat.id()
            length_idx = layer.fields().indexOf("length")
            time_idx = layer.fields().indexOf("travel_time")
            if length_idx != -1:
                layer.changeAttributeValue(fid, length_idx, length_m)
            if time_idx != -1:
                layer.changeAttributeValue(fid, time_idx, time_s)
    layer.commitChanges()


def _grava_gpkg(layer, gpkg_path, layer_name):
    """Salva a camada em um GeoPackage."""
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GPKG"
    opts.layerName = layer_name
    opts.actionOnExistingFile = (
        QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer if os.path.exists(gpkg_path)
        else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
    )
    ctx = QgsProject.instance().transformContext()
    res = QgsVectorFileWriter.writeAsVectorFormatV3(layer, gpkg_path, ctx, opts)
    return res[0] == QgsVectorFileWriter.WriterError.NoError, res[1]


def build_osm_municipal_network(code_muni, nome_muni, gpkg_path, force=False, feedback=None):
    """Constrói camadas de links/nós OSM do município."""
    def log(msg):
        if feedback is not None:
            feedback.pushInfo(msg)

    municipio = _municipio_poligono(code_muni, nome_muni, feedback)
    if municipio is None:
        return {"raw_cache": None, "layers": {"osm_links_raw": None, "osm_links": None, "osm_nodes": None},
                "metadata": {"code_muni": str(code_muni), "nome_muni": nome_muni, "erro": "nao foi possivel resolver o municipio"}}

    bbox = _bbox_da_camada(municipio)
    cache_dir = Path(os.path.dirname(gpkg_path) or ".")
    cache_path = cache_dir / "osm_overpass_{}.json".format(code_muni)
    payload = None
    if cache_path.exists() and not force:
        payload = osm.load_overpass_cache(cache_path)
        if payload is not None:
            log("OSM: cache reutilizado")
    if payload is None:
        log("OSM: consultando Overpass")
        try:
            payload = osm.fetch_overpass_json(bbox, timeout=180, cache_path=cache_path, feedback=feedback)
            osm.save_overpass_cache(payload, cache_path)
        except osm.OverpassError as e:
            log(f"Erro no Overpass: {e}")
            return {"raw_cache": None, "layers": {"osm_links_raw": None, "osm_links": None, "osm_nodes": None},
                    "metadata": {"code_muni": str(code_muni), "nome_muni": nome_muni, "erro": str(e)}}

    # Extrair ways e nós
    ways = _parse_osm_ways(payload)
    nodes_dict = _build_nodes_dict(payload)
    log(f"OSM: {len(ways)} ways encontrados, {len(nodes_dict)} nós")

    # Criar camada raw
    osm_links_raw = _create_links_layer(ways, nodes_dict, "osm_links_raw")
    if osm_links_raw.featureCount() == 0:
        log("OSM: nenhum way com highway encontrado no bbox")
        return {"raw_cache": str(cache_path), "layers": {"osm_links_raw": None, "osm_links": None, "osm_nodes": None},
                "metadata": {"code_muni": str(code_muni), "nome_muni": nome_muni, "bbox": bbox, "municipio_layer": municipio.name()}}

    log(f"OSM: {osm_links_raw.featureCount()} links no bbox")

    # Recortar pelo polígono
    osm_links = _recorta_poligono(osm_links_raw, municipio, "osm_links")
    if osm_links is None or not osm_links.isValid():
        log("OSM: falha ao recortar pelo polígono municipal")
        return {"raw_cache": str(cache_path), "layers": {"osm_links_raw": osm_links_raw, "osm_links": None, "osm_nodes": None},
                "metadata": {"code_muni": str(code_muni), "nome_muni": nome_muni, "bbox": bbox, "municipio_layer": municipio.name()}}

    # Atualizar comprimento e tempo de viagem das feições recortadas
    _update_cost_attributes(osm_links)

    log(f"OSM: {osm_links.featureCount()} links dentro do município")

    # Gerar nós de extremidade
    nodes_set = _extract_nodes_from_layer(osm_links)
    osm_nodes = _create_nodes_layer(nodes_set, "osm_nodes")
    log(f"OSM: {osm_nodes.featureCount()} nós de extremidade (deduplicados)")

    # Gravar em GeoPackage
    ok_links, _ = _grava_gpkg(osm_links, gpkg_path, f"osm_links_{code_muni}")
    ok_nodes, _ = _grava_gpkg(osm_nodes, gpkg_path, f"osm_nodes_{code_muni}")
    if ok_links:
        log(f"OSM: gravadas {osm_links.featureCount()} linhas em {os.path.basename(gpkg_path)}")
    if ok_nodes:
        log(f"OSM: gravados {osm_nodes.featureCount()} nós em {os.path.basename(gpkg_path)}")

    return {
        "raw_cache": str(cache_path),
        "layers": {"osm_links_raw": osm_links_raw, "osm_links": osm_links, "osm_nodes": osm_nodes},
        "metadata": {
            "code_muni": str(code_muni),
            "nome_muni": nome_muni,
            "bbox": bbox,
            "municipio_layer": municipio.name(),
            "links_raw": osm_links_raw.featureCount(),
            "links_clipped": osm_links.featureCount(),
            "nodes": osm_nodes.featureCount(),
            "gpkg_ok": ok_links and ok_nodes,
        },
    }
