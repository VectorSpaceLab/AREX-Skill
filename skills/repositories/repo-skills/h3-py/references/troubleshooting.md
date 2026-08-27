# Cross-cutting troubleshooting

Read this reference when installation, import, version, or cross-workflow
behavior is unclear. Route algorithm-specific failures to the nearest
sub-skill troubleshooting reference.

## Import and installation

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: h3` | The active Python differs from the one where `h3` was installed | Run `python -m pip show h3`, then use that same interpreter for the import and `check_h3_environment.py`. |
| Import fails while building from a checkout with a CMake error about missing H3 core files | A source checkout has an uninitialized core submodule or incomplete source distribution | Prefer a published wheel. For an authorized source build, restore the package's H3 core source and retry; do not debug Python calls until import succeeds. |
| A different package appears under `import h3` | Environment shadowing or an unrelated distribution | Print `h3.__file__`, `h3.versions()`, and distribution metadata; remove the conflicting distribution in the intended environment. |
| Python version rejected | Runtime is older than the package floor | Use Python 3.10 or newer, keeping the package and interpreter in the same environment. |
| `h3.api.numpy_int` import fails for missing NumPy | NumPy extra was not installed | Run `python -m pip install 'h3[numpy]'` or choose `basic_int`/`memview_int` when NumPy is not wanted. |

## Coordinate and index mistakes

- H3 geographic arguments are `(lat, lng)` in degrees. GeoJSON and most
  `__geo_interface__` objects use `(lng, lat)`; swap at exactly one boundary.
- A valid-looking 15-character hexadecimal string can still be the wrong H3
  index kind, resolution, or source. Use `is_valid_cell`,
  `is_valid_directed_edge`, and `is_valid_vertex` rather than string shape
  checks.
- `H3CellInvalidError`, `H3IndexInvalidError`, and `H3ResDomainError` mean
  repair the input or resolution; do not catch them and continue with guessed
  values.
- Strings belong to the default API, Python integers to `basic_int`, and
  typed arrays/views to the corresponding integer APIs. Convert explicitly
  with `str_to_int` and `int_to_str`.

## Resolution, topology, and units

- Resolutions are `0..15`. A parent target cannot be finer than its cell; a
  child target cannot be coarser than its parent.
- Grid distance, grid paths, local IJ, and many hierarchy calls require
  same-resolution cells. Mixed-resolution input should be normalized first.
- `compact_cells` needs a valid, non-duplicate, same-resolution collection and
  only replaces complete sibling sets. It is not a generic geometry
  simplifier.
- Use `km`, `m`, or `rads` for lengths and distances; use `km^2`, `m^2`, or
  `rads^2` for areas. Invalid units raise `ValueError`.
- Pentagons have five neighbors/vertices rather than the usual six. Do not
  hard-code a six-element result.

## Polygon boundary

If the input is a polygon, hole, GeoJSON wrapper, CRS, or dateline issue, stop
using the generic index route and read
[polygon-geospatial troubleshooting](../sub-skills/polygon-geospatial/references/troubleshooting.md).
The bundled validator can identify ring nesting, coordinate-range, closure, and
CRS warnings without modifying input.

## Reporting a failure

Capture `h3.versions()`, the selected API module, input kind and resolution,
coordinate order, units, and the smallest reproducible call. Include the
exception class and message. Never report an unordered collection mismatch
until normalizing it as a set or sorted list.
