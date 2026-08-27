---
name: pyproj
description: "Guide Python geospatial workflows with pyproj for CRS definition
  and inspection, coordinate transformation, geodesic measurement, PROJ database
  queries, and safe CLI, data-directory, and grid operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# pyproj operating guide

Use this skill when a task names `pyproj`, PROJ, EPSG/WKT/PROJJSON/CF coordinate
reference systems, CRS-to-CRS conversion, map projection, ellipsoidal distance
or area, UTM/AOI lookup, or PROJ data/grid diagnostics. It is a runtime guide
for the public package, not a maintainer guide for CI, release automation, or
building all optional integrations.

## Fast route

1. Check that a coherent `pyproj` installation imports and that its native PROJ
   runtime can locate `proj.db`. Use the read-only diagnostic linked from
   [`cli-data-and-network`](sub-skills/cli-data-and-network/SKILL.md) when the
   runtime is uncertain.
2. Normalize the user's coordinate convention, CRS representations, dimensions,
   units, geographic area, and required accuracy before choosing an API.
3. Read exactly the focused route below, then its linked references. Do not use
   a numeric result as proof that axis order, datum operation, grid availability,
   or units were correct.

## Focused routes

- [`crs-and-database`](sub-skills/crs-and-database/SKILL.md) — construct,
  inspect, compare, serialize, and query `CRS`, datums, axes, operations,
  authorities, areas of use, AOIs, UTM candidates, and PROJ database records.
- [`coordinate-transformations`](sub-skills/coordinate-transformations/SKILL.md)
  — execute reusable `Transformer` operations, pipelines, `TransformerGroup`
  selection, projection-only `Proj`, bounds, arrays, time, and grid-aware
  validation.
- [`geodesic-calculations`](sub-skills/geodesic-calculations/SKILL.md) — use
  `Geod` for ellipsoidal forward/inverse work, azimuths, intermediate points,
  line length, polygon area/perimeter, and optional Shapely adapters.
- [`cli-data-and-network`](sub-skills/cli-data-and-network/SKILL.md) — install
  or diagnose native runtime/data state, use CLI help/version commands, manage
  data directories, and plan explicit network-backed grid synchronization.

## Minimal installation and smoke check

For normal users, prefer a binary distribution:

```bash
python -m pip install pyproj
python -c "from pyproj import CRS, Geod, Transformer; print(CRS.from_epsg(4326).to_epsg()); print(Transformer.from_crs(4326, 3857, always_xy=True).transform(0, 0)); print(Geod(ellps='WGS84').inv(0, 0, 1, 1)[2])"
```

Conda-forge is an alternative for a coherent compiled stack:

```bash
conda create -n <new-env> -c conda-forge pyproj
conda run -n <new-env> python -c "import pyproj; print(pyproj.__version__, pyproj.proj_version_str)"
```

Do not casually mix pip and Conda packages. Core CRS, transformation, and
`Geod` workflows do not require remote transformation grids, although some
high-accuracy datum operations do. Treat Shapely, dataframe adapters, and
network grids as explicit optional surfaces.

## Shared operating rules

- Preserve authoritative CRS identifiers, WKT2, or PROJJSON when fidelity
  matters. PROJ4 strings are useful compatibility inputs but can lose metadata.
- Inspect `CRS.axis_info` before transforming. If application data is `(x, y)`
  or `(longitude, latitude)`, choose `always_xy=True` deliberately and record
  that interface contract.
- Use a reusable `Transformer` for CRS-to-CRS and datum changes. `Proj` is for
  projection within a datum, not a generic datum-shift converter.
- For `Geod`, coordinates are `(longitude, latitude)` and distances are metres;
  polygon areas are square metres and algebraically signed.
- Keep network access disabled unless explicitly approved. Never silently
  download grids, change a data directory, or treat a ballpark operation as an
  exact replacement.
- When native import, `proj.db`, or SQLite errors appear, stop API debugging
  and follow the runtime recovery in
  [`references/troubleshooting.md`](references/troubleshooting.md).

## Shared references and helper

- Read [`references/api-overview.md`](references/api-overview.md) for the
  package surface and choosing between CRS, Transformer, Proj, and Geod.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for
  cross-cutting installation, native-runtime, data, optional-dependency, and
  API failure triage.
- Run [`scripts/pyproj_smoke.py`](scripts/pyproj_smoke.py) for a deterministic,
  no-network CPU smoke check after installing the package.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before
  deciding whether this graph matches a changed source repository or needs a
  refresh. The structured router metadata is in
  [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json).

## Out of scope

This graph does not teach PROJ/pyproj release engineering, CI matrix
maintenance, wheel publication, broad GIS application frameworks, raster/vector
file I/O, or unbounded network data acquisition. Route those tasks to a more
appropriate skill or ask for a narrower pyproj API surface.
