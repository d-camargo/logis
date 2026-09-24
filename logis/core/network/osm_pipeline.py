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
from .municipios import normalize_code_muni


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


def _custos_de(comprimento_m, velocidade_kmh):
    """Calcula custos de rede (length, speed, travel_time) para uma feição.

    Função pura (sem dependência do PyQGIS).

    Parameters
    ----------
    comprimento_m : float, int or None
        Comprimento em metros. Se None, não numérico ou < 0, considera 0.0.
    velocidade_kmh : float, int or None
        Velocidade em km/h. Se nulo/None, não numérico ou <= 0, considera 40.0.

    Returns
    -------
    tuple of (float, float, float)
        (length, speed, travel_time em segundos)
    """
    if isinstance(comprimento_m, bool):
        len_val = 0.0
    else:
        try:
            len_val = float(comprimento_m) if comprimento_m is not None else 0.0
            if len_val < 0:
                len_val = 0.0
        except (ValueError, TypeError):
            len_val = 0.0

    if isinstance(velocidade_kmh, bool):
        spd_val = 40.0
    else:
        try:
            spd_val = float(velocidade_kmh) if velocidade_kmh is not None else 40.0
            if spd_val <= 0:
                spd_val = 40.0
        except (ValueError, TypeError):
            spd_val = 40.0

    speed_mps = spd_val / 3.6
    travel_time = len_val / speed_mps if speed_mps > 0 else 0.0

    return (len_val, spd_val, travel_time)


def _adapta_links_gisbr(layer):
    """Adapta camada de links originada do GisBR para o contrato do graph_builder.

    O GisBR produz uma camada de links com atributos como `comprimento_m` e
    `velocidade_kmh`. O `graph_builder` do logis exige que a camada de links
    possua os campos estandardizados:
    - `length`: comprimento da via em metros (derivado de `comprimento_m` ou da geometria).
    - `speed`: velocidade média em km/h (derivada de `velocidade_kmh`; se nula ou <= 0, fallback para 40.0 km/h).
    - `travel_time`: tempo de percurso em segundos (calculado como `length / (speed / 3.6)`).

    Mapeamento de campos:
    - Todos os campos originais da camada GisBR são mantidos intactos.
    - `length` <- `comprimento_m` (ou medido via elipsoide EPSG:4674 se ausente/inválido).
    - `speed` <- `velocidade_kmh` (fallback para 40.0 se nulo ou <= 0).
    - `travel_time` <- `length / (speed / 3.6)`.

    Parameters
    ----------
    layer : QgsVectorLayer
        Camada vetorial de links do GisBR (ou similar).

    Returns
    -------
    QgsVectorLayer or None
        Camada em memória EPSG:4674 contendo todos os campos originais mais `length`,
        `speed` e `travel_time`. Retorna None se a camada de entrada for inválida.
    """
    if layer is None or not layer.isValid():
        return None

    def _is_valid_number(val):
        if val is None or isinstance(val, bool):
            return False
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False

    field_names = [f.name() for f in layer.fields()]
    new_fields = QgsFields()
    for f in layer.fields():
        new_fields.append(f)

    for field_name in ("length", "speed", "travel_time"):
        if field_name not in field_names:
            new_fields.append(QgsField(field_name, qgis_compat.field_type("double")))

    layer_name = layer.name() if layer.name() else "osm_links_gisbr"
    uri = "LineString?crs=EPSG:4674"
    mem_layer = QgsVectorLayer(uri, layer_name, "memory")
    dp = mem_layer.dataProvider()
    dp.addAttributes(list(new_fields))
    mem_layer.updateFields()

    mem_layer.startEditing()
    for feat in layer.getFeatures():
        geom = feat.geometry()

        comp = None
        if "comprimento_m" in field_names:
            comp = feat["comprimento_m"]
        elif "length" in field_names:
            comp = feat["length"]

        if not _is_valid_number(comp) and geom and not geom.isEmpty():
            comp = _calcular_comprimento_metros(geom)

        vel = None
        if "velocidade_kmh" in field_names:
            vel = feat["velocidade_kmh"]
        elif "speed" in field_names:
            vel = feat["speed"]

        length_val, speed_val, travel_time_val = _custos_de(comp, vel)

        new_feat = QgsFeature(mem_layer.fields())
        if geom:
            new_feat.setGeometry(geom)

        for f in layer.fields():
            new_feat.setAttribute(f.name(), feat[f.name()])

        new_feat.setAttribute("length", length_val)
        new_feat.setAttribute("speed", speed_val)
        new_feat.setAttribute("travel_time", travel_time_val)

        mem_layer.addFeature(new_feat)

    mem_layer.commitChanges()
    return mem_layer


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


def _resolve_layer(out, layer_name, context=None):
    if isinstance(out, str):
        if context is not None and hasattr(context, "getMapLayer"):
            lyr = context.getMapLayer(out)
            if lyr is not None:
                return lyr
        return QgsProject.instance().mapLayer(out) or QgsVectorLayer(out, layer_name, "ogr")
    return out


def _municipio_poligono(code_muni, nome_muni=None, feedback=None):
    """Poligono do municipio p/ recorte. None se falhar."""
    import processing
    
    code_muni_norm = normalize_code_muni(code_muni)

    if has_gisbr():
        try:
            out = processing.run("gisbr:read_municipality", {
                "CODE": code_muni_norm,
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
        uf_code = code_muni_norm[:2]
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
                    expr = f'"{col}" = {int(code_muni_norm)}'
                else:
                    expr = f'"{col}" = \'{code_muni_norm}\''
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
    if layer is None or not layer.isValid():
        return False, "layer invalida"
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


def build_osm_network(code_muni, nome_muni, gpkg_path, force=False, feedback=None, context=None):
    """Despacha a construção da rede OSM municipal para GisBR (se disponível) ou pipeline nativo (logis)."""
    code = normalize_code_muni(code_muni)
    if has_gisbr("gisbr:osm_network"):
        import processing

        res_gisbr = processing.run(
            "gisbr:osm_network",
            {
                "CODE": code,
                "FORCE": force,
                "REDE": 0,
                "PONTAS_SOLTAS": False,
                "LINKS": "TEMPORARY_OUTPUT",
                "NODES": "TEMPORARY_OUTPUT",
                "PROBLEMAS": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=context is not None,
        )

        links_layer = _resolve_layer(res_gisbr.get("LINKS"), f"osm_links_{code}", context=context)
        nodes_layer = _resolve_layer(res_gisbr.get("NODES"), f"osm_nodes_{code}", context=context)

        osm_links = _adapta_links_gisbr(links_layer)
        osm_nodes = nodes_layer

        ok_links, _ = _grava_gpkg(osm_links, gpkg_path, f"osm_links_{code}")
        ok_nodes, _ = _grava_gpkg(osm_nodes, gpkg_path, f"osm_nodes_{code}")

        return {
            "raw_cache": None,
            "layers": {
                "osm_links_raw": None,
                "osm_links": osm_links,
                "osm_nodes": osm_nodes,
            },
            "metadata": {
                "code_muni": str(code),
                "nome_muni": nome_muni,
                "backend": "gisbr",
                "links_clipped": osm_links.featureCount() if osm_links and osm_links.isValid() else 0,
                "nodes": osm_nodes.featureCount() if osm_nodes and osm_nodes.isValid() else 0,
                "gpkg_ok": ok_links and ok_nodes,
            },
        }

    res = build_osm_municipal_network(code, nome_muni, gpkg_path, force=force, feedback=feedback)
    if isinstance(res, dict) and "metadata" in res and isinstance(res["metadata"], dict):
        res["metadata"]["backend"] = "logis"
    return res
