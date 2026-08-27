# Data formats

## Format choice cheat sheet

| Format | Best for | Strengths | Limits |
|---|---|---|---|
| CSV folder | Human-readable exchange, folder sync, manual repair, cloud-folder storage | Plain text, diffable, easy to inspect per component | More files, slower than netCDF, no stochastic export support |
| netCDF | Large networks, solved networks, default round-trips, compact archival | Compact, fast, lazy loading, cross-language friendly, supports scenarios | Binary, less convenient to hand-edit |
| HDF5 | Legacy pipelines that already use HDF stores | Compact and familiar to many data pipelines | Optional dependency, no stochastic export support |
| Excel | Small networks and manual review | Easy to share with non-coders | Slow, sheet-name limits, optional dependency, not for large networks |
| PYPOWER | Import from case dictionaries | Useful bridge from older power-system tooling | Import only, feature coverage is limited |
| pandapower | Import from pandapower networks | Useful bridge from pandapower models | Beta importer, limited feature coverage, export not supported |

## Common entry points

`Network(import_name=...)` dispatches by suffix or directory:

- `.h5` → HDF5
- `.nc` → netCDF
- `.xls`, `.xlsx`, `.xlsm`, `.xlsb` → Excel
- directory → CSV folder
- URL or cloud URI → the corresponding format loader when supported

Use the explicit `import_from_*` methods when you want `skip_time=True`, a specific engine, or a more controlled repair workflow.

## API signatures to remember

| API | Signature |
|---|---|
| `pypsa.Network` | `Network(import_name="", name="Unnamed Network", ignore_standard_types=False, **kwargs)` |
| CSV import | `import_from_csv_folder(path, encoding=None, quotechar='"', skip_time=False)` |
| CSV export | `export_to_csv_folder(path, encoding=None, quotechar='"', export_standard_types=False)` |
| netCDF import | `import_from_netcdf(path, skip_time=False)` where `path` may be a path or `xarray.Dataset` |
| netCDF export | `export_to_netcdf(path=None, export_standard_types=False, compression=None, float32=False)` |
| HDF5 import | `import_from_hdf5(path, skip_time=False)` |
| HDF5 export | `export_to_hdf5(path, export_standard_types=False, **kwargs)` |
| Excel import | `import_from_excel(path, skip_time=False, engine="calamine")` |
| Excel export | `export_to_excel(path, export_standard_types=False, engine="openpyxl")` |
| PYPOWER import | `import_from_pypower_ppc(ppc, overwrite_zero_s_nom=None)` |
| pandapower import | `import_from_pandapower_net(net, extra_line_data=False, use_pandapower_index=False)` |

## CSV folder layout

CSV folders are the most transparent layout.

### Required files

| File | Purpose |
|---|---|
| `network.csv` | Scalar network attributes, including `name` and `pypsa_version`. |
| `meta.json` | `n.meta` serialized as JSON. |
| `crs.json` | CRS metadata for geometric data. |
| `snapshots.csv` | Snapshot index and snapshot weighting columns. |
| `investment_periods.csv` | Investment-period index and weighting columns. |
| `<component>.csv` | Static component table for the component list name, such as `buses.csv` or `generators.csv`. |
| `<component>-<attr>.csv` | Time-series table for one dynamic attribute. |
| `<component>-<attr>-pw.csv` | Piecewise table for piecewise attributes. |

### Layout rules

- Static tables use the component list name, not the class name.
- Time-series tables use exactly one `-` separator before the attribute name.
- Piecewise tables add the `-pw` suffix.
- Only non-default values are written.
- `skip_time=True` imports only the static side of a CSV folder.
- Missing values are filled from component defaults during import.
- Shape geometries are written as WKT text and restored as geometries on import.

### Snapshot and time-series alignment

- `snapshots.csv` controls the network snapshot index.
- If `period`, `timestep`, or `snapshot` columns are present, PyPSA builds the snapshot index from them.
- Time-series files must have rows aligned to `n.snapshots`.
- Missing snapshot rows are filled with the attribute default and a warning is emitted.
- Misnamed files are ignored, so repair the filename first if a series does not load.

## netCDF layout

netCDF is the preferred archival format for large or solved networks.

### Layout rules

- Network attributes are stored as `network_*` attributes.
- `n.meta` and CRS metadata are stored in dataset attributes.
- Static data uses `*_i` coordinates and `*_`-prefixed variables.
- Time series use `*_t_*` variables.
- Piecewise data use `*_pw_*` variables.
- Snapshot and investment-period coordinates are stored as dedicated coordinates and variables.
- Scenario data is supported in netCDF and not in the CSV, HDF5, or Excel exporters.
- `export_to_netcdf(path=None)` returns an `xarray.Dataset` without writing a file.

### Practical notes

- netCDF is compact and usually the safest choice when you need a single-file archive.
- netCDF is the best default for a large solved network when optional extras are limited.
- Cloud URIs are supported when cloud-path handling is installed.

## HDF5 layout

HDF5 stores are useful when an existing pipeline already expects an HDF store.

### Layout rules

- `/network` stores scalar attributes.
- `/meta` and `/crs` store JSON blobs.
- `/snapshots` and `/investment_periods` store the index tables.
- `/component` stores static component tables.
- `/component_t/attr` stores time-series tables.
- `/component_p/attr` stores piecewise tables.
- Cloud URIs are supported when cloud-path handling is installed.

## Excel layout

Excel is best kept to small networks and manual exchange.

### Layout rules

- `network`, `meta`, `crs`, `snapshots`, and `investment_periods` are dedicated sheets.
- Component sheets use the same naming pattern as CSV folders.
- Time-series sheets use `<component>-<attr>`.
- Piecewise sheets use `<component>-<attr>-pw`.
- Long sheet names are mapped to safe aliases for known piecewise attributes so they fit Excel's 31-character limit.
- Sheets that do not follow the naming pattern are ignored on import.

### Practical notes

- The default exporter uses `openpyxl`.
- The default importer uses `calamine`.
- Use Excel only when the network is small enough that workbook size and sheet naming remain manageable.

## External converters

| Converter | What it does | Notes |
|---|---|---|
| `import_from_pypower_ppc(...)` | Builds a PyPSA network from a PYPOWER case dictionary | Version 2 is expected; export back to PYPOWER is not supported. |
| `import_from_pandapower_net(...)` | Builds a PyPSA network from a pandapower network | Import is beta and only a subset of pandapower features is supported. |

## Example-network cache behavior

- `pypsa.examples.<name>()` loads a bundled example network from cache or downloads it if missing.
- The cache is versioned, so a package upgrade may look in a new cache location.
- `pypsa.examples.clear_cache()` removes cached example networks.
- If network requests are disabled, a cache miss raises instead of downloading.
- If a versioned example URL returns 404, the loader falls back to the `latest` path.
