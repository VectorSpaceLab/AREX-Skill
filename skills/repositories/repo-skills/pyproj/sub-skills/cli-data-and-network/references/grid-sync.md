# Transformation-grid discovery and synchronization

## Decide whether grids are needed

CRS metadata lookup and ellipsoidal `Geod` calculations do not need datum
grid files. A datum transformation may choose a lower-accuracy or unavailable
operation when its preferred grid is absent. Route operation selection and
transform result validation to
[`../../coordinate-transformations/SKILL.md`](../../coordinate-transformations/SKILL.md);
use this reference for finding and explicitly obtaining the files.

The distribution's transformation-grid manifest is GeoJSON. Each feature is
expected to contain `properties.name`, `properties.source_id`, an optional
`properties.area_of_use`, `properties.sha256sum`, and a geometry used for
spatial filtering. Do not hard-code a URL or assume that a grid exists merely
because a transformation advertises it.

## Public discovery API

```python
from pyproj.aoi import BBox
from pyproj.sync import get_transform_grid_list

features = get_transform_grid_list(
    source_id="us_noaa",              # optional substring
    area_of_use="USA",                # optional substring
    filename="alaska",                # optional filename substring
    bbox=BBox(170, -90, -170, 90),     # optional geographic bounds
    spatial_test="intersects",        # or "contains"
    include_world_coverage=False,
    include_already_downloaded=True,
    target_directory="/chosen/manifest-cache",
)
```

The return value is a tuple of GeoJSON feature dictionaries. `source_id`,
`area_of_use`, and `filename` are substring filters. `intersects` keeps a grid
whose extent intersects the bbox; `contains` keeps one whose extent is wholly
contained by it. `include_world_coverage=False` removes global-extent features
from a bbox query. With `include_already_downloaded=False` (the default), names
already present in the user data directory or any selected PROJ data directory
are removed.

The `bbox` is a `BBox(west, south, east, north)` in degrees. The implementation
normalizes ordinary out-of-range longitudes and handles an east value below west
as an antimeridian crossing. It also handles GeoJSON multipolygon extents. For
reproducible filtering, pass a bounded bbox and `include_world_coverage=False`
when global grids are not required.

The optional `target_directory` controls where `files.geojson` is cached; it is
not a permission bypass and does not make a directory writable. If the manifest
is missing or older than one day, discovery downloads it to that directory.
Therefore a supposedly read-only listing can have this one cache side effect.
Pre-create and inspect a dedicated cache, or use a previously cached manifest,
when that boundary matters.

## CLI listing and download policy

Use the CLI when a human-readable filter and explicit download are desired:

```bash
python -m pyproj sync --file us_noaa_alaska \
  --list-files --include-already-downloaded \
  --target-directory /chosen/manifest-cache
```

Review the two-line header and every selected feature. Then, only after a
network/data/disk approval, remove `--list-files` and keep the same narrow
filter and target. `--all` is intentionally broad and cannot be combined with
`--bbox`, `--source-id`, `--area-of-use`, `--file`, or `--list-files`; avoid it
for a bounded task. `--system-directory` writes to the main selected PROJ data
tree and should be treated as an administrative change.

The CLI uses the PROJ endpoint and the feature checksum when downloading. The
implementation retrieves each file to `<name>.part`, verifies SHA-256 when a
checksum is supplied, atomically renames it to its final name, and removes the
partial file on errors. A checksum mismatch is a failed download, not a reason
to disable verification. A failed request may raise a URL/network error; first
check connectivity, certificate configuration, target writability, space, and
whether the target is a coherent PROJ data location.

No automatic download helper belongs in this skill. If a caller needs a
programmatic download, it must own URL allowlisting, explicit target creation,
network approval, checksum verification, retry limits, and cleanup. Prefer the
supported CLI or PROJ's own synchronization tools instead.

## Safe network-grid preflight

Before enabling network or downloading, perform all of these checks:

1. Run the read-only diagnostic and confirm import, runtime/compiled PROJ
   compatibility, a valid `proj.db`, and the intended network default.
2. Decide whether the requested operation actually needs a grid; record the
   geographic area, acceptable accuracy, target directory, disk budget, and
   network permission.
3. Select one exact grid with `--file`, or a bounded `--bbox` plus source/area
   filters. Use `--list-files` and, if possible, a cached manifest first.
4. Check the target is writable, has sufficient space, and is not a mixed data
   tree. Check the CA bundle when TLS is involved.
5. Download only the approved files, keep verbose output, and verify the final
   file exists. Re-run the diagnostic and then let the transformation sibling
   validate the chosen operation.

If network is not approved, leave it disabled and install only explicitly
selected grids by an approved offline channel. Never silently fall back from a
failed secure download to an unverified file.
