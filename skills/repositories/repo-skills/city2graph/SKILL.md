---
name: "city2graph"
description: "Use the city2graph 1.0.0 Python package to construct, validate,
  transform, and troubleshoot geospatial, spatial-topology, morphology,
  mobility, transportation, heterogeneous, and GNN-ready graphs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# city2graph operating router

Use this skill for the public `city2graph` package when a task turns geospatial
features or local mobility/transit data into graph tables, graph libraries, or
PyTorch Geometric objects. The package is GeoDataFrame-first: preserve stable
IDs in indexes, preserve CRS, and inspect typed output dictionaries before
converting representations.

## Route by the user's starting point

- **Graph representation, metadata, NetworkX/rustworkx/PyG, heterogeneous
  relations, or metapaths:** read
  [graph-conversion](sub-skills/graph-conversion/SKILL.md).
- **Point/polygon spatial relations, proximity, contiguity, reachability,
  isochrones, tessellation, clipping, dual graphs, or topology cleanup:** read
  [spatial-topology](sub-skills/spatial-topology/SKILL.md).
- **Building footprints plus movement segments, tessellation barriers,
  place/movement composition, or multi-distance morphology:** read
  [urban-morphology](sub-skills/urban-morphology/SKILL.md).
- **OD matrices, local GTFS/GBFS feeds, dated stop legs, or transit summary
  graphs:** read
  [mobility-and-transport](sub-skills/mobility-and-transport/SKILL.md).
- **Overture area/place resolution, controlled layer acquisition, clipping,
  connector splitting, or passable segment preprocessing:** read
  [data-ingestion](sub-skills/data-ingestion/SKILL.md).

For compound tasks, start with the ingestion or graph-construction route that
matches the input, then hand the resulting GeoDataFrame tables to
`urban-morphology`, `spatial-topology`, or `graph-conversion` as appropriate.
The sibling skills are the detailed operating graph; this file stays a router.

## Shared operating contract

1. Inspect the input representation and decide whether it is homogeneous or
   typed. Do not merge node types whose ID namespaces are intentionally
   separate.
2. Establish a CRS before metric operations. Use WGS84 for Overture download
   bounds, but use a suitable projected CRS for lengths, distances, buffers,
   tessellation, network budgets, and morphology.
3. Keep GeoDataFrame indexes as the canonical node/edge ID contract: node IDs
   come from node indexes, and edge endpoints are the first two levels of an
   edge MultiIndex. Verify endpoint membership and CRS consistency before
   conversion.
4. Make direction, reciprocal-edge, multigraph-key, self-loop, threshold,
   geometry, and optional-dependency choices explicit. Do not infer them from
   a downstream graph class after the fact.
5. Prefer local fixtures and in-memory data for reproducible checks. Live
   Overture/Nominatim/GTFS/GBFS access, remote releases, and large downloads
   are runtime prerequisites rather than required offline verification.
6. Preserve metadata and provenance: record package version, source data/feed
   paths, CRS, ID columns, filters, warning conditions, and parameters. Keep
   `graph_metadata` on PyG objects and graph metadata on NetworkX objects when
   round-tripping.
7. Treat `as_nx` compatibility arguments as deprecated where the package says
   so; prefer returning GeoDataFrames and then calling the shared conversion
   utilities.

## Installation and capability gates

Install the public package in a fresh environment with the smallest capability
set that matches the task:

```bash
python -m pip install city2graph
# Add CPU PyTorch Geometric support only when tensor conversion is needed:
python -m pip install 'city2graph[cpu]'
```

A minimal core import check is:

```bash
python -c "import city2graph; print(city2graph.__version__)"
```

For the PyG route, also import `torch` and `torch_geometric`, then run a tiny
CPU conversion before selecting any other device. Probe optional dependencies
before use rather than claiming that every installation supports every backend.
The CPU PyG route is covered by the companion verification artifacts; CUDA,
ROCm, and MPS are optional and must not be inferred from a CPU import.

Cross-cutting installation, CRS, schema, optional-dependency, data-source, and
representation failures are summarized in
[references/troubleshooting.md](references/troubleshooting.md). Package
snapshot and routing metadata are in
[references/repo-provenance.md](references/repo-provenance.md) and
[references/repo-routing-metadata.json](references/repo-routing-metadata.json).

## Handoff checklist

Before handing a result to analysis or a downstream graph library, confirm:

- the selected sub-skill owns the workflow and its references were read;
- every non-empty layer has the intended CRS and compatible geometry types;
- node and edge IDs/index names are stable and endpoints resolve;
- output relation keys, directionality, edge counts, weights, and geometry
  semantics match the request;
- optional dependencies and device selection were probed explicitly;
- warnings, empty/fallback results, external-service assumptions, and any
  unverified backend are recorded rather than hidden.

This generated skill is self-contained and does not require the original
repository checkout, its notebooks, its test fixtures, or a live external
service at runtime.
