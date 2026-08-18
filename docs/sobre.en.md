# About logis

## Motivation

Logistics analysis — network indicators, routing, facility location — often requires stepping outside QGIS: exporting the road network, building a graph in another programming language, running an external solver, and importing the results back as a vector layer. **logis** exists to eliminate this friction. The premise is that the entire workflow — from processed road network to final route or optimal distribution center location — happens inside QGIS, using Brazilian public datasets (OSM, DNIT/SNV, IBGE/geobr) and without relying on external tools or stacks for core tasks.

## The three modules and three layers

The division into three modules — **Urban**, **Regional**, and **Specialized** (waste collection currently) — reflects the spatial scale of the analyzed network rather than an arbitrary functional breakdown. A municipal road network (OSM) and a national highway network (SNV) differ significantly in data volume, granularity, and demand sources, justifying separate graph-building pipelines. The Specialized module inherits the network from the Urban module, but alters the problem type: in waste collection, demand resides on **streets**, not points — hence routing uses arc-based algorithms (CPP/RPP/CARP) rather than node-based ones (VRP/TSP).

Within each module, the same sequence of three layers is repeated — **Indicators**, **Routing**, and **Facility location** — matching the natural progression of a logistics project: first understand the network and demand, then determine how to serve it (routes), and finally locate supporting infrastructure (DCs, hubs, depots, drop-off sites, transfer stations). Structuring every module uniformly keeps functionality predictable across scales.

## Zero mandatory dependencies

logis runs on **PyQGIS + Python standard library** alone. This constraint is not aesthetic: installing Python packages inside a QGIS environment is fragile or impossible in many user setups — Flatpak isolates system Python, Windows requires discovering the correct OSGeo4W Shell environment, and standard users often lack privileges to modify `sys.path`. A plugin requiring `pip install` simply breaks for a segment of users beyond author control.

Consequently, graphs and shortest paths rely on native `QgsGraph`, `QgsGraphBuilder`, and `QgsGraphAnalyzer` classes, while spatial processing uses built-in `processing.run()` with `native:`/`qgis:` providers. Optimization — VRP, facility location, arc routing — is solved by default using **classic pure Python heuristics**: Clarke-Wright savings, sweep, 2-opt/or-opt, Teitz-Bart for p-median, greedy set covering, greedy matching, and Hierholzer algorithm for the Chinese Postman Problem. These heuristics provide good, though not strictly optimal, solutions — a trade-off explicitly stated in the user interface.

`pyarrow` and `OR-Tools` are the only exceptions, and both are strictly **optional**: imports are lazy and guarded, falling back automatically to pure Python implementations if packages are missing or fail to install (e.g. in Flatpak or restricted environments). Details on installing OR-Tools correctly are documented in [OR-Tools](ortools.md).

## Relationship with GisBR

logis reuses module **logic** from [GisBR](https://github.com/d-camargo/gisbr) — OSM network pipelines, connectors, download caching, geographic boundaries, and demographics — via adapted copies rather than import dependencies: logis does not import the `gisbr` package. When GisBR is installed in QGIS, invoking `gisbr:read_*` algorithms via `processing.run()` is preferred; in its absence, embedded fallbacks ensure logis remains fully self-contained.

## Status and license

logis is at version **0.1.5**, marked as `experimental` in the official QGIS plugin repository. In this phase, internal APIs, algorithm identifiers, and output formats may change between releases without backward compatibility guarantees — experimental plugins must be enabled in the Plugin Manager to install it (see [Installation Guide](guias/instalacao.md)). The license is **GPL-3.0**, inherited from GisBR logic.
