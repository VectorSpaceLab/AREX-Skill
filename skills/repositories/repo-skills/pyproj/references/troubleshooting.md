# Cross-cutting troubleshooting

## Import or native extension failure

**Symptom:** `import pyproj` fails with a missing `_context`, `_crs`, `_geod`,
or `_transformer` module, an unresolved shared library, or a compiler error.

**Check:** Use a supported binary wheel/Conda package first. For a source build,
confirm Python compatibility, Cython, PROJ headers/libraries, and the minimum
PROJ version documented by the active release. Do not call the pure Python files
an installed package; pyproj requires native extensions.

**Recovery:** Create a clean environment and install one coherent distribution.
For a source build, set `PROJ_DIR` to the intended PROJ base or set the
explicit `PROJ_LIBDIR`, `PROJ_INCDIR`, and `PROJ_VERSION` values. Re-run an
import/version check in a fresh process. Avoid mixing old system PROJ libraries
with a newer Python package.

## `proj.db` or SQLite errors

**Symptom:** `DataDirError`, `proj.db not found`, `SQLite error on SELECT`,
missing authority records, or a runtime/compiled PROJ mismatch.

**Check:** Run the bundled diagnostic and `python -m pyproj -v`. Inspect the
selected data directory and verify it contains `proj.db`; compare runtime and
compiled PROJ versions. Print `PROJ_DATA` and legacy `PROJ_LIB` values without
assuming both are valid fallbacks.

**Recovery:** Remove or correct invalid environment overrides, isolate competing
PROJ installations, and choose one matching data tree. Use `datadir.set_data_dir`
for a deliberate current-process override or restart the process after changing
environment variables. Do not point a new runtime at an older database.

## Wrong coordinates despite a successful call

**Symptom:** Values are plausible but swapped, shifted, or outside the expected
region.

**Check:** Inspect source/target `CRS.axis_info`, units, `area_of_use`, datum,
and selected transformer description. Decide whether application inputs are
`(lon, lat)` or native CRS order. Validate a known control point and, where
possible, perform a reverse transformation.

**Recovery:** Use `always_xy=True` when the application contract is x/y or
longitude/latitude, then keep that contract in all calls. Route datum changes to
`Transformer.from_crs`; do not substitute `Proj` merely because it returns
numbers.

## Missing or lower-accuracy operation

**Symptom:** `TransformerGroup.best_available` is false, operations are listed
as unavailable, `only_best=True` fails, or results use a ballpark fallback.

**Check:** Inspect unavailable operation grids, area/accuracy filters, network
state, and the selected data directory. Treat a displayed download URL as
metadata, not permission to fetch it.

**Recovery:** Decide whether the task permits a lower-accuracy or ballpark
operation. If not, arrange the required grid in an explicit data workflow,
verify its checksum and license, and rerun with strict selection. Keep network
and data-directory changes in the CLI/data route.

## Invalid CRS, AOI, or serialization

**Symptom:** `CRSError`, empty database results, ambiguous UTM candidates, or a
PROJ string/WKT round-trip changes the authority or axes.

**Check:** Use the parser that matches the representation, validate AOI order as
west/south/east/north degrees, inspect every candidate, and compare with
`is_exact_same` or `equals` rather than only `to_epsg()`.

**Recovery:** Preserve the original representation, correct the parser or AOI,
raise the selection rule when multiple candidates remain, and prefer WKT2 or
PROJJSON when lossless storage is required.

## Geod result or optional geometry problem

**Symptom:** Distance is off by a factor, area sign is unexpected, or geometry
methods raise an import/type error.

**Check:** Confirm `Geod` ellipsoid, `(lon, lat)` order, degrees versus radians,
metres versus square metres, polygon winding, and input shape. Determine
whether the failure is missing Shapely or an invalid geometry object.

**Recovery:** Use coordinate-array `line_length` or
`polygon_area_perimeter` for the core fallback. Preserve signed area unless an
unsigned value is explicitly requested; do not silently normalize winding.

## CLI, certificate, or grid-sync issue

**Symptom:** CLI parser errors, `sync` cannot fetch a manifest/grid, TLS errors,
checksum mismatch, or a write permission failure.

**Check:** Run `pyproj --help`; narrow the sync filters and use an explicit target
only after approval. Check network permission, CA bundle variables, target
writability, free space, and whether the manifest itself requires a network
request.

**Recovery:** Keep network disabled by default, use `network.set_ca_bundle_path`
only with a validated certificate path or approved certifi fallback, retry only
with a bounded filter, and remove partial files only according to the explicit
sync policy. A failed optional grid download must not block core CRS/Geod work.
