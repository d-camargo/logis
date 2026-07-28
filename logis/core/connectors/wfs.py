# -*- coding: utf-8 -*-
"""Conector WFS.

Baixa feicoes de servicos WFS oficiais usando a pilha de rede do QGIS
(QgsBlockingNetworkRequest) — robusta a SSL/proxy do GeoServer (padrao
herdado do desafio-2/GisBR). Saida GeoJSON (outputFormat application/json);
fallback GDAL /vsicurl/. Filtro por CQL_FILTER ou bbox.

So MONTA a camada (QgsVectorLayer).
"""
from datetime import datetime
import tempfile
import urllib.parse

from qgis.core import QgsVectorLayer, QgsBlockingNetworkRequest
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

_UA = "logis-qgis/0.1 (+https://github.com/d-camargo/logis)"


def _stamp(layer, fonte):
    layer.setCustomProperty("data_extracao", datetime.now().strftime("%Y-%m-%d"))
    layer.setCustomProperty("fonte", fonte)
    return layer


def _invalid(layer_name, msg):
    layer = QgsVectorLayer("", layer_name, "ogr")
    layer.error_msg = msg
    return layer


def _layer_from_geojson_bytes(data, layer_name):
    tmp = tempfile.NamedTemporaryFile(suffix=".geojson", delete=False)
    tmp.write(data)
    tmp.close()
    return QgsVectorLayer(tmp.name, layer_name, "ogr")


def build_url(endpoint, type_name, srs="EPSG:4674",
              output_format="application/json", cql_filter=None, bbox=None,
              version="2.0.0"):
    """Monta a URL GetFeature. Use cql_filter OU bbox (cql tem prioridade).

    bbox: tupla (minx, miny, maxx, maxy) em graus EPSG:4674.
    ATENCAO (a validar no QGIS): em WFS 2.0.0 a ordem de eixo pode ser
    lat,lon; usamos a forma curta 'EPSG:4674' (lon,lat na maioria dos
    GeoServer). Se algum servico desalinhar, inverter para miny,minx,maxy,maxx.
    """
    params = {
        "service": "WFS",
        "version": version,
        "request": "GetFeature",
        "typeNames": type_name,
        "srsName": srs,
        "outputFormat": output_format,
    }
    if cql_filter:
        params["CQL_FILTER"] = cql_filter
    elif bbox:
        minx, miny, maxx, maxy = bbox
        params["bbox"] = "{},{},{},{},{}".format(minx, miny, maxx, maxy, srs)
    sep = "&" if "?" in endpoint else "?"
    return endpoint + sep + urllib.parse.urlencode(params)


def fetch_layer(endpoint, type_name, layer_name, srs="EPSG:4674",
                output_format="application/json", cql_filter=None, bbox=None,
                version="2.0.0"):
    """Retorna um QgsVectorLayer do WFS (filtrado), ou um layer invalido com
    .error_msg em caso de falha. NAO levanta excecao."""
    url = build_url(endpoint, type_name, srs=srs, output_format=output_format,
                    cql_filter=cql_filter, bbox=bbox, version=version)

    # 1) Pilha de rede do QGIS (respeita SSL/proxy do app)
    erro = None
    try:
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", _UA.encode("utf-8"))
        blocking = QgsBlockingNetworkRequest()
        blocking.get(req, True)
        reply = blocking.reply()
        data = bytes(reply.content())
        if data:
            layer = _layer_from_geojson_bytes(data, layer_name)
            if layer.isValid():
                return _stamp(layer, "WFS GeoJSON")
            erro = "GeoJSON recebido, mas o GDAL nao abriu a camada."
        else:
            erro = reply.errorString() or "resposta vazia"
    except Exception as exc:
        erro = "{}: {}".format(type(exc).__name__, exc)

    # 2) Fallback GDAL /vsicurl/
    layer = QgsVectorLayer("/vsicurl/" + url, layer_name, "ogr")
    if layer.isValid():
        return _stamp(layer, "WFS GeoJSON/vsicurl")

    return _invalid(layer_name, "Falha WFS ({}). {}".format(type_name, erro or ""))
