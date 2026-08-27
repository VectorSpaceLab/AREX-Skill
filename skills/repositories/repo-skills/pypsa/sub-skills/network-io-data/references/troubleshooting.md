# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Missing optional dependency error for HDF5 or Excel | `tables`, `openpyxl`, or `python_calamine` is not installed | Install the matching optional extra or switch to CSV/netCDF |
| `Network(import_name=...)` rejects a path | The suffix does not match a supported import format or the path is not a directory/file of the expected type | Use the explicit `import_from_*` method or rename the source file to the correct format |
| CSV import misses a time series | The file name does not match `<component>-<attr>.csv` or the series index does not line up with `snapshots.csv` | Rename the file, repair the snapshot table, then re-import |
| Excel import ignores a sheet | The sheet name does not follow the expected naming pattern or was too long for Excel | Use standard component sheet names and the documented safe aliases for long piecewise names |
| Snapshot rows or weights look shifted | `snapshots.csv` or the `snapshots` sheet does not describe the same index as the time-series tables | Rebuild `snapshots.csv` / the snapshots sheet and re-export the data |
| `Snapshots ... are missing from ...` warning | A dynamic table is shorter than `n.snapshots` | Reindex the time-series table to the network snapshots before import or export |
| `Importing network from PyPSA version v...` warning | The file was written by an older PyPSA version | Read the release notes and re-export with the current version when practical |
| `pandas infers the str dtype ...` warning | Newer pandas versions infer `StringDtype` for strings | Set `pypsa.options.api.legacy_string_dtype` explicitly to the behavior you want |
| `Network requests are disabled` or example download fails | Offline mode is active, the cache is empty, or the remote URL/provider is unavailable | Seed the cache, enable requests only when intended, or use a local file |
| Cloud URI access fails | Missing cloud credentials or provider client | Install the provider client, authenticate, or use a local temporary path |
| Pandapower import is incomplete | Unsupported pandapower elements or settings are present, especially three-winding transformers, switches, `in_service` status, tap positions, and related shunt-impedance details | Remove the unsupported features or build the network directly in PyPSA |
| PYPOWER import gives a warning about version or unsupported fields | The PPC dictionary is not version 2 or contains unsupported PYPOWER features | Convert a simpler case or build the network directly in PyPSA |

## Repair checklist for difficult CSV imports

1. Load static tables only with `skip_time=True`.
2. Confirm that `network.csv`, `meta.json`, `crs.json`, and `snapshots.csv` are present when needed.
3. Verify that every dynamic file uses the exact `component-attr.csv` naming pattern.
4. Verify that every piecewise file uses the exact `component-attr-pw.csv` naming pattern.
5. Check that the snapshot index in `snapshots.csv` matches the row labels in the dynamic tables.
6. Re-export a known-good network after the repair and compare it with `equals(...)`.

## Format-choice guidance for large solved networks

- Start with netCDF unless a downstream tool forces a different format.
- Use CSV when the network must be inspected or repaired by hand.
- Use HDF5 only when an existing pipeline requires it and the optional dependency is already available.
- Use Excel only for small, manual exchanges.
- If cloud dependencies are unavailable, stay local and hand off the file outside PyPSA.
