# -*- coding: utf-8 -*-
"""Pipeline SNV regional: WFS → GeoPackage.

Baixa a malha rodoviária federal do SNV (DNIT) para uma UF, calcula atributos
de custo (length, speed, travel_time) com base no tipo de superfície,
e gera as camadas de links e nós no GeoPackage regional.

Referência Bibliográfica da Técnica:
    DNIT (Departamento Nacional de Infraestrutura de Transportes). (2025).
    Sistema Rodoviário Nacional (SRN/SNV) - Especificações Técnicas. Brasília: DNIT.

Limite de Complexidade:
    Complexidade de Tempo: O(N) onde N é o número de trechos de rodovias na UF.
    Complexidade de Espaço: O(N) para o armazenamento de links e nós em memória antes da gravação.
    Testado com malhas regionais de UFs de grande porte (ex.: MG com mais de 10.000 trechos).
"""
import os
import shutil
from pathlib import Path

from qgis.core import (
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsFields,
    QgsProject,
    QgsWkbTypes,
    QgsDistanceArea,
    QgsCoordinateReferenceSystem,
    QgsVectorFileWriter
)

from .. import qgis_compat
from ..connectors import wfs
from ..sources import SOURCES

_DEFAULT_SNV_SPEEDS = {
    "duplicada": 110.0,
    "pavimentada": 80.0,
    "implantada": 60.0,
    "terra": 40.0,
    "leito natural": 30.0,
    "planejada": 30.0,
}


def _parse_snv_speed(ds_superfi):
    """Mapeia a velocidade da rodovia com base no tipo de superfície."""
    if not ds_superfi:
        return 60.0
    ds_lower = str(ds_superfi).lower().strip()
    if "duplicada" in ds_lower:
        return 110.0
    elif "pavimentada" in ds_lower:
        return 80.0
    elif "implantada" in ds_lower:
        return 60.0
    elif "terra" in ds_lower:
        return 40.0
    elif "natural" in ds_lower:
        return 30.0
    elif "planejada" in ds_lower:
        return 30.0
    return 60.0


def _calcular_comprimento_metros(geom):
    """Calcula o comprimento da geometria em metros usando o elipsoide GRS80."""
    da = QgsDistanceArea()
    crs = QgsCoordinateReferenceSystem("EPSG:4674")
    da.setSourceCrs(crs, QgsProject.instance().transformContext())
    da.setEllipsoid(crs.ellipsoidAcronym())
    return da.measureLength(geom)


def _extract_nodes_from_layer(layer):
    """Extrai pontos de extremidade das polilinhas do SNV, removendo duplicados."""
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


def _create_nodes_layer(nodes_set, layer_name="snv_nodes"):
    """Cria QgsVectorLayer em memória contendo os nós da rede."""
    layer = QgsVectorLayer(
        f"Point?crs=EPSG:4674&field=node_id:long&field=x:double&field=y:double",
        layer_name,
        "memory"
    )
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


def _grava_gpkg(layer, gpkg_path, layer_name):
    """Salva a camada informada em um GeoPackage regional."""
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


def build_snv_state_network(uf, gpkg_path, force=False, feedback=None):
    """Constrói camadas de links/nós do SNV (DNIT) para a UF informada.

    Baixa os dados do WFS do DNIT filtrados pela UF, cria atributos de custo
    (length, speed, travel_time) e grava no GeoPackage.
    """
    def log(msg):
        if feedback is not None:
            feedback.pushInfo(msg)

    # Normaliza a UF para maiúsculo sem espaços
    uf = str(uf).upper().strip()

    # 1. Se force=False, tenta carregar as camadas prontas do GeoPackage
    if not force and os.path.exists(gpkg_path):
        links_layer = QgsVectorLayer(f"{gpkg_path}|layername=snv_links_{uf}", f"snv_links_{uf}", "ogr")
        nodes_layer = QgsVectorLayer(f"{gpkg_path}|layername=snv_nodes_{uf}", f"snv_nodes_{uf}", "ogr")
        if links_layer.isValid() and nodes_layer.isValid():
            log(f"SNV: rede regional para {uf} carregada do GeoPackage existente")
            return {
                "layers": {
                    f"snv_links_{uf}": links_layer,
                    f"snv_nodes_{uf}": nodes_layer
                },
                "metadata": {
                    "uf": uf,
                    "links": links_layer.featureCount(),
                    "nodes": nodes_layer.featureCount(),
                    "gpkg_ok": True,
                    "cached": True
                }
            }

    cache_dir = Path(os.path.dirname(gpkg_path) or ".")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"snv_{uf}.geojson"

    wfs_layer = None

    # 2. Se force=False, tenta carregar a camada bruta do cache local (GeoJSON)
    if cache_path.exists() and not force:
        log(f"SNV: carregando do cache local: {cache_path}")
        wfs_layer = QgsVectorLayer(str(cache_path), f"snv_raw_{uf}", "ogr")
        if not wfs_layer.isValid():
            log("SNV: arquivo de cache inválido, rebaixando...")
            wfs_layer = None

    # 3. Baixa via WFS se necessário
    if wfs_layer is None:
        source_conf = None
        for src in SOURCES:
            if src.get("id") == "dnit_snv":
                source_conf = src
                break

        if not source_conf:
            raise RuntimeError("Fonte declarativa 'dnit_snv' não encontrada no catálogo de fontes.")

        endpoint = source_conf["endpoint"]
        type_name = source_conf["type_name"]
        srs = source_conf.get("srs", "EPSG:4674")

        cql_filter = f"sg_uf = '{uf}'"
        log(f"SNV: baixando rodovias para {uf} via WFS ({cql_filter})")

        wfs_layer = wfs.fetch_layer(
            endpoint=endpoint,
            type_name=type_name,
            layer_name=f"snv_raw_{uf}",
            srs=srs,
            cql_filter=cql_filter
        )

        if not wfs_layer.isValid():
            err_msg = getattr(wfs_layer, "error_msg", "erro desconhecido")
            log(f"SNV: erro ao obter camada WFS: {err_msg}")
            return {
                "layers": {f"snv_links_{uf}": None, f"snv_nodes_{uf}": None},
                "metadata": {"uf": uf, "erro": f"Falha WFS: {err_msg}"}
            }

        # Salva no cache local copiando o arquivo GeoJSON temporário gerado pelo WFS
        temp_path = wfs_layer.source()
        if temp_path and os.path.exists(temp_path):
            try:
                shutil.copy(temp_path, cache_path)
                log(f"SNV: cache salvo em {cache_path}")
            except Exception as e:
                log(f"SNV: falha ao salvar cache: {e}")

    log(f"SNV: processando {wfs_layer.featureCount()} trechos da UF {uf}")

    # 4. Cria camada de links em memória
    fields = QgsFields()
    fields.append(QgsField("id_trecho", qgis_compat.field_type("int")))
    fields.append(QgsField("vl_codigo", qgis_compat.field_type("string")))
    fields.append(QgsField("vl_br", qgis_compat.field_type("string")))
    fields.append(QgsField("sg_uf", qgis_compat.field_type("string")))
    fields.append(QgsField("ds_superfi", qgis_compat.field_type("string")))
    fields.append(QgsField("ds_jurisdi", qgis_compat.field_type("string")))
    fields.append(QgsField("oneway", qgis_compat.field_type("string")))
    fields.append(QgsField("length", qgis_compat.field_type("double")))
    fields.append(QgsField("speed", qgis_compat.field_type("double")))
    fields.append(QgsField("travel_time", qgis_compat.field_type("double")))

    uri = (
        "LineString?crs=EPSG:4674&field=id_trecho:int&field=vl_codigo:string&"
        "field=vl_br:string&field=sg_uf:string&field=ds_superfi:string&"
        "field=ds_jurisdi:string&field=oneway:string&field=length:double&"
        "field=speed:double&field=travel_time:double"
    )
    links_layer = QgsVectorLayer(uri, f"snv_links_{uf}", "memory")
    links_layer.startEditing()

    for idx, feat_wfs in enumerate(wfs_layer.getFeatures()):
        geom = feat_wfs.geometry()
        if not geom or geom.isEmpty():
            continue

        # Tenta obter um ID de trecho único a partir dos campos do GeoServer
        id_trecho = None
        for field_name in ["id_trecho_", "id_trecho", "ogc_fid"]:
            if field_name in feat_wfs.fields().names():
                val = feat_wfs.attribute(field_name)
                if val is not None:
                    try:
                        id_trecho = int(val)
                        break
                    except (ValueError, TypeError):
                        pass
        if id_trecho is None:
            id_trecho = idx

        vl_codigo = str(feat_wfs.attribute("vl_codigo")) if "vl_codigo" in feat_wfs.fields().names() else ""
        vl_br = str(feat_wfs.attribute("vl_br")) if "vl_br" in feat_wfs.fields().names() else ""
        sg_uf = str(feat_wfs.attribute("sg_uf")) if "sg_uf" in feat_wfs.fields().names() else uf
        ds_superfi = str(feat_wfs.attribute("ds_superfi")) if "ds_superfi" in feat_wfs.fields().names() else ""
        ds_jurisdi = str(feat_wfs.attribute("ds_jurisdi")) if "ds_jurisdi" in feat_wfs.fields().names() else ""

        # Obter extensão em metros
        vl_extensa = feat_wfs.attribute("vl_extensa") if "vl_extensa" in feat_wfs.fields().names() else None
        try:
            length_m = float(vl_extensa) * 1000.0 if vl_extensa is not None else 0.0
        except (ValueError, TypeError):
            length_m = 0.0

        if length_m <= 0:
            length_m = _calcular_comprimento_metros(geom)

        speed_kmh = _parse_snv_speed(ds_superfi)
        speed_mps = speed_kmh / 3.6
        time_s = length_m / speed_mps if speed_mps > 0 else 0.0

        feat = QgsFeature(fields)
        feat.setGeometry(geom)
        feat["id_trecho"] = id_trecho
        feat["vl_codigo"] = vl_codigo
        feat["vl_br"] = vl_br
        feat["sg_uf"] = sg_uf
        feat["ds_superfi"] = ds_superfi
        feat["ds_jurisdi"] = ds_jurisdi
        feat["oneway"] = "no"
        feat["length"] = length_m
        feat["speed"] = speed_kmh
        feat["travel_time"] = time_s
        links_layer.addFeature(feat)

    links_layer.commitChanges()

    # 5. Extrai nós e cria camada de nós
    nodes_set = _extract_nodes_from_layer(links_layer)
    nodes_layer = _create_nodes_layer(nodes_set, f"snv_nodes_{uf}")

    # 6. Grava camadas no GeoPackage
    ok_links, err_links = _grava_gpkg(links_layer, gpkg_path, f"snv_links_{uf}")
    ok_nodes, err_nodes = _grava_gpkg(nodes_layer, gpkg_path, f"snv_nodes_{uf}")

    if ok_links:
        log(f"SNV: gravadas {links_layer.featureCount()} linhas em {os.path.basename(gpkg_path)}")
    else:
        log(f"SNV: erro ao gravar links no GPKG: {err_links}")

    if ok_nodes:
        log(f"SNV: gravados {nodes_layer.featureCount()} nós em {os.path.basename(gpkg_path)}")
    else:
        log(f"SNV: erro ao gravar nós no GPKG: {err_nodes}")

    final_links = QgsVectorLayer(f"{gpkg_path}|layername=snv_links_{uf}", f"snv_links_{uf}", "ogr")
    final_nodes = QgsVectorLayer(f"{gpkg_path}|layername=snv_nodes_{uf}", f"snv_nodes_{uf}", "ogr")

    return {
        "layers": {
            f"snv_links_{uf}": final_links,
            f"snv_nodes_{uf}": final_nodes
        },
        "metadata": {
            "uf": uf,
            "links": final_links.featureCount() if final_links.isValid() else 0,
            "nodes": final_nodes.featureCount() if final_nodes.isValid() else 0,
            "gpkg_ok": ok_links and ok_nodes,
            "cached": False
        }
    }
