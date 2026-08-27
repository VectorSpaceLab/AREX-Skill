# Optional I/O dependencies

| Capability | Package(s) | Typical methods | What fails when missing | Safe fallback |
|---|---|---|---|---|
| HDF5 import/export | `tables` via `pypsa[hdf5]` | `import_from_hdf5(...)`, `export_to_hdf5(...)` | PyPSA raises a missing-optional-dependency error for HDF5 use | Use netCDF or CSV instead |
| Excel export | `openpyxl` via `pypsa[excel]` | `export_to_excel(...)` | Excel export cannot create the workbook | Use CSV or netCDF |
| Excel import | `python_calamine` via `pypsa[excel]` for the default reader | `import_from_excel(...)` | The default Excel reader cannot open the file | Use CSV or netCDF, or switch to another installed Excel engine if appropriate |
| Cloud paths | `cloudpathlib` plus a provider client | CSV, netCDF, and HDF5 path handling | Cloud URIs are not available or fail authentication | Use a local path and sync externally |
| PYPOWER conversion | `pypower` | `import_from_pypower_ppc(...)` | The source converter code cannot be imported or used | Build the network directly in PyPSA |
| pandapower conversion | `pandapower` | `import_from_pandapower_net(...)` | The source converter code cannot be imported or used | Build the network directly in PyPSA |

## Dependency-specific notes

### HDF5

- The missing-dependency message should point users to `pypsa[hdf5]`.
- HDF5 is optional, not the default archival format.
- Use netCDF first when you only need a portable archive.

### Excel

- Export uses `openpyxl` by default.
- Import uses `calamine` by default.
- Excel is intended for small networks and manual exchange, not for large archives.

### Cloud paths

- Cloud support depends on `cloudpathlib`.
- Provider clients and credentials are separate from PyPSA itself.
- If requests are disabled, URL-based loads and example downloads should fail fast rather than silently fetch data.

### PYPOWER and pandapower

- These are conversion helpers, not core dependencies for PyPSA networks.
- Keep them optional in documentation and smoke scripts.
- Treat pandapower as a limited importer, not a full equivalence layer.
