---
name: cli-data-and-network
description: "Diagnose pyproj installation and native PROJ runtime state, use
  the CLI safely, select PROJ data directories, and plan network-backed
  transformation-grid discovery without hiding downloads or mutating state
  unexpectedly."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CLI, data, and network operations

Use this route when the task is about installing or importing `pyproj`, checking
its Python/PROJ versions, reading `pyproj` CLI help, selecting PROJ data
locations, enabling network access, or finding and synchronizing transformation
grids. Start with the read-only diagnostic when the runtime is uncertain:
[`scripts/diagnose_pyproj.py`](scripts/diagnose_pyproj.py).

## Route and boundaries

- Installation prerequisites, CLI syntax, data-directory precedence, network
  policy, and grid synchronization belong here.
- CRS construction/database questions go to
  [`../crs-and-database/SKILL.md`](../crs-and-database/SKILL.md).
- Coordinate operations, missing-grid operation selection, and transform
  accuracy go to [`../coordinate-transformations/SKILL.md`](../coordinate-transformations/SKILL.md).
- Ellipsoid distances, azimuths, and areas go to
  [`../geodesic-calculations/SKILL.md`](../geodesic-calculations/SKILL.md).
- Maintainer CI, wheel/release automation, and build-pipeline edits are out of
  scope. Source-build prerequisites are documented only to diagnose an install.

## Minimal operating sequence

1. Run `python -m pyproj --help` (or the installed `pyproj --help`) and the
   bundled diagnostic. Confirm that import succeeds, runtime and compiled PROJ
   versions are compatible, and a valid directory containing `proj.db` is
   selected.
2. For a detailed report, run `python -m pyproj -v` or `pyproj -v`. Compare
   `PROJ (runtime)`, `PROJ (compiled)`, `data dir`, database versions, Python,
   and dependency information. Do not treat a version report as proof that a
   particular grid is installed.
3. Decide whether the job needs no grids, a bounded pre-download, or PROJ
   network access. Keep network disabled unless the task explicitly permits
   remote resources, and never replace this decision with an automatic wrapper.
4. Before `sync`, choose an explicit target and a filter. Prefer
   `pyproj sync --list-files` for inspection, while remembering that obtaining
   the grid manifest may itself fetch `files.geojson` when it is absent or
   stale. Use an explicit directory and review the listed names before any
   download.
5. If a failure mentions SQLite, `proj.db`, a missing data directory, or a
   runtime/compiled mismatch, follow
   [`references/troubleshooting.md`](references/troubleshooting.md) before
   retrying a transformation.

## Operating contracts

- **Inputs:** an installed package or source-build request; optional CLI
  arguments; optional `PROJ_DATA`/legacy `PROJ_LIB`, `PROJ_NETWORK`, and CA
  bundle settings; and, for grid discovery, a source id, filename, area of use,
  or geographic `west,south,east,north` bounding box.
- **Outputs:** help/version text; a selected data-directory string; a boolean
  network state; or a tuple of GeoJSON feature dictionaries from
  `pyproj.sync.get_transform_grid_list`. A sync download writes a manifest and
  grid files only where the selected CLI target permits it.
- **Validation:** import must complete; `get_data_dir()` must resolve to a
  path containing `proj.db`; runtime and compiled PROJ versions should match
  for a coherent install; filters must be narrow enough to review; checksums
  must pass when the sync implementation supplies one.
- **Recovery:** isolate `PROJ_DATA`/`PROJ_LIB` and competing installations,
  select one coherent data tree, restart the Python process after changing
  environment variables, then rerun the read-only checks. For network or
  checksum failures, preserve the original partial-download cleanup behavior
  and retry only after checking target writability, CA certificates, network
  permission, and available disk space.

## Linked depth

- [CLI command reference](references/cli-reference.md) covers parser behavior,
  arguments, outputs, and side-effect boundaries.
- [Installation and runtime](references/installation-and-runtime.md) covers
  wheels/conda/source prerequisites, version inspection, data paths, and
  network APIs.
- [Grid synchronization](references/grid-sync.md) covers manifest filtering,
  antimeridian boxes, download policy, and safe preflight.
- [Troubleshooting](references/troubleshooting.md) covers native mismatches,
  SQLite errors, invalid paths, certificates, and recovery ordering.

This route deliberately does not download grids itself. The bundled diagnostic
is read-only and has safe defaults; a human or calling workflow must explicitly
approve any `sync` download.
