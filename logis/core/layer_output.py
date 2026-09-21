"""Nomes e destino das saídas para camadas geradas pelo Logis (D-J, D-K, D-L, D-M)."""

import os
import re
import unicodedata
from typing import Optional, Tuple


def slugify(nome: Optional[str]) -> str:
    """Converte um nome de camada/município em um slug em minúsculas e hífens.

    Remove acentos via NFKD, substitui espaços e '_' por '-', remove caracteres
    fora de [a-z0-9-], colapsa hífens repetidos e devolve 'rede' caso o resultado
    seja vazio.
    """
    if not nome:
        return "rede"
    s = unicodedata.normalize("NFKD", str(nome))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    return s if s else "rede"


def output_names(kind: str, mode: str, ref_name: Optional[str]) -> Tuple[str, str]:
    """Retorna o par (nome_linhas, nome_pontos) para camadas de saída de roteirização.

    Parâmetros:
      kind: 'TSP' ou 'CVRP'
      mode: 'rede' ou 'euclidiana'
      ref_name: nome da camada de referência para gerar o slug

    Retorna:
      Tuple[str, str]: (nome_linhas, nome_pontos) conforme tabela da D-L.
    """
    slug = slugify(ref_name)
    nome_linhas = f"{kind}-{mode}_{slug}"
    nome_pontos = f"{nome_linhas}_pontos"
    return (nome_linhas, nome_pontos)


def gpkg_path_from_source(source: Optional[str]) -> Optional[str]:
    """Recorta o caminho antes do '|' de uma origem de camada QGIS e verifica se é GPKG.

    Parsing de string puro sem dependência de PyQGIS, insensível a maiúsculas/minúsculas.
    Devolve o caminho se terminar em '.gpkg', senão None.
    """
    if not source or not isinstance(source, str):
        return None
    path = source.split("|", 1)[0].strip()
    if path.lower().endswith(".gpkg"):
        return path
    return None


def write_layer_to_gpkg(layer, gpkg_path: str, layer_name: str) -> Tuple[bool, str]:
    """Grava uma camada PyQGIS em um arquivo GeoPackage.

    Imports do PyQGIS são feitos dentro da função para permitir testes puros sem QGIS.
    Retorna (ok, erro) e nunca levanta exceção.
    """
    try:
        from qgis.core import QgsProject, QgsVectorFileWriter

        gpkg_str = str(gpkg_path)
        opts = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName = "GPKG"
        opts.layerName = layer_name
        opts.actionOnExistingFile = (
            QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
            if os.path.exists(gpkg_str)
            else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
        )
        ctx = QgsProject.instance().transformContext()
        res = QgsVectorFileWriter.writeAsVectorFormatV3(layer, gpkg_str, ctx, opts)
        ok = res[0] == QgsVectorFileWriter.WriterError.NoError
        err_msg = res[1] if len(res) > 1 else ""
        return (ok, err_msg)
    except Exception as e:
        return (False, str(e))
