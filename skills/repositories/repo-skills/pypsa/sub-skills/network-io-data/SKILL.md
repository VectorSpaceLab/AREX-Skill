---
name: network-io-data
description: "Load, save, and validate PyPSA networks across CSV folders,
  netCDF, HDF5, Excel, cloud paths, and external import converters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Network I/O and Data Formats

Use this sub-skill for PyPSA tasks that import, export, repair, or round-trip network data and example-network loads.

## Use when
- `Network(import_name=...)` must load from a CSV folder, netCDF, HDF5, Excel file, URL, or cloud URI.
- You need `import_from_*` or `export_to_*` format guidance.
- You need CSV folder layout, netCDF, HDF5, Excel, cloud object storage, or external converter behavior.
- You need example-network cache or download behavior.

## Do not use for
- Component meaning, schema design, or network assembly details; use [`../network-modeling/SKILL.md`](../network-modeling/SKILL.md).
- Optimization or power-flow after loading; use [`../optimization-powerflow/SKILL.md`](../optimization-powerflow/SKILL.md).
- Statistics, plotting, or clustering on loaded networks; use [`../analysis-visualization/SKILL.md`](../analysis-visualization/SKILL.md).

## Start here
1. Read [`references/data-formats.md`](references/data-formats.md) for supported formats, file layouts, and format choice rules.
2. Read [`references/import-export-workflows.md`](references/import-export-workflows.md) for load/save/repair/round-trip workflows.
3. Read [`references/optional-io-dependencies.md`](references/optional-io-dependencies.md) before using HDF5, Excel, cloud paths, or external converters.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) for layout, dependency, version, cache, and converter failures.
5. Run [`scripts/pypsa_io_roundtrip_smoke.py`](scripts/pypsa_io_roundtrip_smoke.py) to check tiny CSV and netCDF round-trips.

## Primary API surface
- `pypsa.Network(import_name=...)`
- `Network.import_from_csv_folder(...)` / `export_to_csv_folder(...)`
- `Network.import_from_netcdf(...)` / `export_to_netcdf(...)`
- `Network.import_from_hdf5(...)` / `export_to_hdf5(...)`
- `Network.import_from_excel(...)` / `export_to_excel(...)`
- `Network.import_from_pypower_ppc(...)`
- `Network.import_from_pandapower_net(...)`
- `pypsa.examples.<name>()` and `pypsa.examples.clear_cache()`

## Validation hints
- Prefer netCDF for large or solved networks.
- Use CSV when you need a human-readable folder layout or folder-based cloud storage.
- Validate a round-trip with a fresh `Network` and `equals(...)`, then confirm snapshots, meta, and CRS if relevant.
- If a format is unavailable, fall back to CSV or netCDF and explain the missing optional dependency.
