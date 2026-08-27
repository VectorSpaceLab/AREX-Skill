# Import/export workflows

## Load a network

Choose the narrowest entry point that matches the source.

1. Use `pypsa.Network(import_name=...)` when the file suffix or directory already identifies the format.
2. Use an explicit `import_from_*` method when you need `skip_time=True`, a custom Excel engine, or a converter-specific option.
3. Use a cloud URI only when cloud-path handling and the provider client are installed.
4. Treat CSV folder loading as the easiest way to inspect or repair a broken import.

## Export a network

Pick the destination format by task.

- **netCDF**: default choice for large or solved networks.
- **CSV folder**: best when a human needs to inspect or edit component tables and time series.
- **HDF5**: only when an existing pipeline expects an HDF store and the optional dependency is present.
- **Excel**: only for small networks or manual exchange.

When you know the network will later be reloaded with standard types included, export with `export_standard_types=True` and remember to reinitialize with `ignore_standard_types=True`.

## Round-trip validation

Use a fresh `Network` instance for the reload step.

1. Build or load a tiny network.
2. Export to a temporary location.
3. Reload into a new `Network`.
4. Compare the original and reloaded networks with `equals(...)`.
5. If you need a narrower check, compare `meta`, `snapshots`, `investment_periods`, and the few component tables relevant to the task.

For large or solved networks, prefer netCDF first and then validate only the parts you care about if full equality is too strict for your use case.

## Repair a broken CSV folder import

Use this pattern when a CSV folder has misnamed files or a bad time-series layout.

1. Load static tables only with `skip_time=True` to confirm the component schema still imports.
2. Check that the folder contains `network.csv`, `snapshots.csv`, `meta.json`, and `crs.json` when expected.
3. Make sure every time-series file follows `<component>-<attr>.csv` exactly.
4. Make sure piecewise files follow `<component>-<attr>-pw.csv` exactly.
5. Check that `snapshots.csv` has the expected index columns and row count.
6. Re-export after fixing the file names or snapshot table, then retry the full import.

## Example networks

- Use `pypsa.examples.<name>()` for the supported example loaders.
- Use `pypsa.examples.clear_cache()` when you need to reset cached example files.
- If the cache is empty and requests are disabled, the load must fail rather than download.
- If a versioned example URL fails with a 404, the loader falls back to the `latest` example path.

## PYPOWER and pandapower converters

### PYPOWER

- `import_from_pypower_ppc(...)` expects a version 2 PPC dictionary.
- The importer rescales `baseMVA` to a 1 MVA base.
- Import is the supported direction; export back to PYPOWER is not.
- Use this path when you need to convert an existing PYPOWER case into a PyPSA network for further work.

### pandapower

- `import_from_pandapower_net(...)` is beta and only covers a subset of pandapower data.
- Use `extra_line_data=True` when you need the detailed line parameters rather than only the line type.
- Use `use_pandapower_index=True` when you want to preserve pandapower's integer indices.
- Unsupported or limited features include three-winding transformers, switches, `in_service` status, tap positions, and related shunt-impedance details; simplify those away before import or build the PyPSA network directly.

## Cloud object storage

- CSV, netCDF, and HDF5 imports/exports can use cloud URIs when cloud-path handling is installed.
- Check that the cloud provider client and credentials are available before relying on the URI path.
- For offline work or missing credentials, use a local temporary path and sync outside PyPSA.
- Keep cloud-based checks read-only or temporary; do not rely on a live network request during smoke validation.
