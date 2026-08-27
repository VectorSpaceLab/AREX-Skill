# pyproj API selection overview

## Choose the object by the task

| Need | Primary object/API | Validate before use |
|---|---|---|
| Define or inspect a coordinate reference system | `CRS`, `CRS.from_user_input`, `CRS.from_epsg`, explicit WKT/JSON/CF parsers | `type_name`, `axis_info`, `area_of_use`, datum, and representation fidelity |
| Query authorities, codes, UTM, or AOI candidates | `pyproj.database`, `AreaOfInterest`, `CRSInfo` | Candidate count, area bounds, deprecation, and selection policy |
| Convert between CRSs or datums | `Transformer.from_crs` | Source/target axes, `always_xy`, operation description, accuracy, area, and grid availability |
| Execute a reviewed PROJ pipeline | `Transformer.from_pipeline` | Pipeline definition, units, dimensionality, and numeric round-trip |
| Projection within one datum | `Proj` | Projection definition, units, inverse behavior, and area of use; do not use it as a generic datum shifter |
| Ellipsoidal distance, azimuth, path, or area | `Geod` | Ellipsoid, `(lon, lat)` order, angular mode, output units, and polygon orientation |
| Locate native data/runtime problems | `datadir`, `network`, `show_versions`, `pyproj -v` | Import, runtime/compiled PROJ versions, `proj.db`, selected data path, and network policy |

## Core public exports

The package exports `CRS`, `Geod`, `Proj`, `Transformer`, the legacy
compatibility functions `transform` and `itransform`, database maps, and
`show_versions`. Prefer object-oriented APIs for new code. The module-level
transform functions remain useful only while maintaining older applications.

## Common representation rules

- Authority identifiers such as `EPSG:4326`, WKT2, and PROJJSON are generally
  safer long-term storage forms than PROJ4 strings.
- A CRS's native axis order is metadata. Application input order can be made
  explicit with `Transformer.from_crs(..., always_xy=True)`; record the choice.
- `CRS.to_epsg()` and `to_authority()` are confidence-based matches. A returned
  code is not proof that the original WKT/PROJ string had identical semantics.
- A projection conversion embedded in a `CRS` is metadata. It is not executed
  until a transformer or projection object is called.
- Core coordinates and distances are numeric arrays/scalars; optional adapters
  such as Shapely geometry and dataframe/xarray containers need their own
  installed dependencies.

## Minimal coherent environment

A supported `pyproj` distribution includes its native PROJ runtime and data.
Source builds additionally need a compatible PROJ installation and Cython.
Verify `import pyproj`, `pyproj.proj_version_str`,
`pyproj.__proj_compiled_version__`, and `datadir.get_data_dir()` before
investigating API behavior. Missing transformation grids affect selected
operations, not basic CRS construction or ordinary ellipsoidal calculations.
