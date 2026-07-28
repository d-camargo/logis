# -*- coding: utf-8 -*-
"""Catálogo declarativo de fontes do módulo regional (CLAUDE.md §4)."""

SOURCES = [
    {
        "id": "dnit_snv",
        "eixo": "transportes",
        "nome": "DNIT — SNV (rodovias federais)",
        "protocolo": "wfs",
        "endpoint": "https://geoservicos.inde.gov.br/geoserver/DNIT/ows",
        "type_name": "DNIT:snv_202507a",
        "srs": "EPSG:4674",
        "filtro": {"tipo": "bbox"},
        "licenca": "Publica",
    }
]
