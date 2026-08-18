# logis

*A QGIS plugin to support logistics projects in Brazil.*

**logis** brings network analysis, routing, and facility location tools applied to Brazilian reality directly into QGIS, using national public datasets (OSM, DNIT/SNV, IBGE/geobr) and operating entirely within the QGIS environment.

## The three modules

| Module | Scope | Base network |
|---|---|---|
| **Urban Logistics** | City / municipality | Processed OSM road network (pipeline derived from GisBR) |
| **Regional Logistics** | State / country | National datasets (DNIT/SNV, geobr) + state datasets (e.g. IDE-Sisema/MG) |
| **Specialized Logistics** | Urban services with arc routing — initial case: waste collection | Urban network from the Urban module |

## The three layers

Each module delivers three functionality layers:

1. **Indicators** — metrics calculated on the network and demographic/economic data.
2. **Routing** — VRP/TSP (node-based) and Arc Routing (edge-based, in the specialized module).
3. **Facility location** — p-median, p-center, maximum coverage (MCLP), and set covering (LSCP), to locate DCs, hubs, depots, drop-off sites, and transfer stations.

## Zero mandatory dependencies

logis runs on **PyQGIS + Python standard library** alone. No `networkx`, `igraph`, or `OSMnx`: graphs and shortest paths use native `QgsGraph`, `QgsGraphBuilder`, and `QgsGraphAnalyzer` classes, and optimization heuristics (Clarke-Wright savings, sweep, 2-opt/or-opt, Teitz-Bart, greedy matching, Hierholzer) are implemented in pure Python.

Two external libraries are accepted as **optional** — the plugin works normally without them:

- `pyarrow` — fallback for reading Parquet files when the corresponding GDAL driver is unavailable.
- `OR-Tools` — optional optimization backend with lazy import and automatic fallback to pure Python heuristics.

Data is output in SIRGAS 2000 / EPSG:4674, reprojected to a metric CRS only for intermediate distance and time calculations.

## Project status

| | |
|---|---|
| **Version** | 0.1.5 |
| **Status** | `experimental` |
| **License** | GPL-3.0 |
| **QGIS** | 3.16 or higher (Qt6 / QGIS 4 compatible) |

Because it is marked as `experimental`, you must enable experimental plugins in the QGIS Plugin Manager to see and install it — the [Installation Guide](guias/instalacao.md) details the procedure.

## Where to start

| Section | What you will find |
|---|---|
| [**Installation**](guias/instalacao.md) | How to install the plugin in QGIS and optionally enable the OR-Tools backend. |
| [**Guides**](guias/urbano.md) | End-to-end workflows: [Urban Logistics](guias/urbano.md), [Regional Logistics](guias/regional.md), and [Waste Collection](guias/residuos.md). |
| [**Algorithms**](algoritmos/index.md) | Technical reference of routines: [Overview](algoritmos/index.md), [Urban Indicators](algoritmos/urbano.md), [Regional Indicators](algoritmos/regional.md), [Routing](algoritmos/roteirizacao.md), [Facility Location](algoritmos/localizacao.md), and [Waste Collection](algoritmos/residuos.md). |

---

For motivation and project context, see [About logis](sobre.md). For dataset provenance, see the [Data Sources Reference](referencia/fontes_dados.md).
