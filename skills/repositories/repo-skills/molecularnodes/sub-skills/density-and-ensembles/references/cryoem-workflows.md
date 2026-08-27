# Local cryo-EM map workflows

Use this reference when a local density map is combined with an atomic model,
STAR particle points, or a color/contour visualization. The central rule is to
separate **source parsing** from **Blender-host validation** and to make map
placement choices explicit before loading anything.

## Local-file-first preflight

Require a real local file for every map and structure input:

```python
from pathlib import Path

path = Path(user_value).expanduser()
if not path.is_file():
    raise FileNotFoundError(path)
if path.stat().st_size == 0:
    raise ValueError(f"empty input: {path}")
```

Reject directories, missing paths, zero-byte files, unsupported suffixes, and
malformed content before calling an importer. An EMDB accession is an
acquisition request, not a `file_path`; do not silently turn a missing local map
into an online request. If data acquisition is explicitly requested, complete
it outside this local runtime route, record the resulting local path, and then
start preflight again.

A parser-only check can read a map with `gridData.Grid` (and use the
MolecularNodes MRC fallback logic conceptually with `mrcfile`) and inspect
shape, finite values, `origin`, and `delta`. It can read a structure through its
native parser and inspect coordinates. It cannot prove VDB conversion, volume
ownership, a density style, contour visibility, or nearest-attribute sampling.
Those checks require Blender 5.2, MolecularNodes 5.2.0, node assets, and
bundled OpenVDB support.

## Choose one map coordinate policy

### Preserve source placement (recommended for map/structure pairs)

Call:

```python
density = mn.entities.density.Grids.load(
    local_map,
    name="map",
    style="density_iso_surface",
    center=False,
    invert=False,
)
```

With `center=False`, the VDB uses the parsed grid origin and the object itself
is set to location `(0, 0, 0)`. MolecularNodes atom objects are created from
source coordinates multiplied by 0.1. If the map header origin and structure
coordinates use the same reference frame, this preserves their expected
alignment. Validate the map's actual `grid.origin`, voxel spacing, axis order,
and structure coordinate convention rather than assuming every MRC producer
uses the same origin semantics.

### Center the volume deliberately

With `center=True`, MolecularNodes translates the volume by
`-shape * 0.5 * delta` before applying the 0.1 scale. It does not center by
mass, density centroid, or header origin, and it does not move an atomic model.
To overlay a structure, apply the identical documented translation in the same
coordinate units to the model (normally by moving the model object by the
scaled offset or by preprocessing coordinates), then check a known landmark.
Do not use a generic model centroid as a substitute for the volume box center.

A practical record for every pair is:

```text
map center: false or true
map invert: false or true
map source origin and delta: recorded from parser
structure transform: unchanged or explicit scaled translation
alignment landmark/check: recorded after host validation
```

If the map was previously converted with a different center choice, pass
`overwrite=True` or use the distinct center-suffixed cache. See
[`density-api.md`](density-api.md).

### Invert only scalar contrast

`invert=True` replaces every grid value with `max(grid) - grid`. It is useful
when a tomogram's contrast is reversed, but it does not flip coordinates,
change the origin, or mirror the structure. Inversion changes the useful
contour range, so a threshold selected for the non-inverted map may become
empty or expose a large background volume. Validate finite min/max/quantiles
and choose a new host-side threshold after inversion.

## Map import and visual validation

The default `density_surface` style, and the explicit
`density_iso_surface`/`density_wire` styles, start from a threshold equal to the
0.995 quantile of the parsed data. It is only an initial heuristic. For a
visible result:

1. confirm `density.object` exists, `entity_type == "density"`, and the first
   user collection is `mn.blender.coll.mn()`;
2. inspect the generated density style node and use the actual exposed socket,
   `Threshold` or `ISO Value`;
3. choose a finite value appropriate to the map's value range;
4. evaluate the object and confirm non-empty positions/geometry;
5. if it is empty, lower the threshold gradually; if it is a noisy solid block,
   raise it or use dust suppression where the selected style provides it.

A parser result with a non-empty 3-D array is not proof of visible geometry.
`style=None` intentionally skips style setup, and `named_attribute("position")`
requires a usable object/modifier evaluation path. A malformed map may fail
before an object is created; a bad style key or an import failure can leave
partial Blender state, so inspect the scene before retrying.

The ISO style's map-specific controls are exposed as Geometry Nodes inputs:
contours, contour-only mode, contour width/color, slice width/center, positive
and negative colors, smooth shading, material, and the threshold/ISO socket.
Use those sockets rather than undocumented Python attributes. A slice is a
visual clipping operation; it does not change source placement.

## Structure overlay and color transfer

Load the atomic model through the appropriate molecule/structure sibling route,
keeping its source coordinates and the map's center choice consistent. A ribbon
or cartoon style replaces the visible atom geometry, so it is not a reliable
source for nearest-atom attribute sampling. For map coloring:

1. retain or duplicate a structure object whose evaluated geometry exposes atom
   points and the required attributes (`Color`, chain/residue fields, or other
   sampled data);
2. use the MolecularNodes `Sample Nearest Attribute` asset, implemented as the
   `Sample Nearest Atoms` geometry group, with that atom geometry as its input;
3. connect the sampled color or attribute to the density style's color input;
4. validate that the atom object and map occupy the same coordinate frame before
   interpreting the color pattern.

Sampling a ribbon-only display can sample the wrong geometry or provide no
atom-level attribute. Sampling from an atom object does not repair a map/model
translation mismatch.

## STAR points over a map

A STAR load creates a point data object in `Molecular Nodes`. It does not have a
map center switch. RELION point positions use coordinate minus optional
Angstrom shifts, optional `rlnImagePixelSize`, and then 0.1 world scale.
cisTEM uses X/Y and a defocus-derived Z, optional origin shifts, and then 0.1;
its `cisTEMPixelSize` is not used by the current implementation. Therefore:

- preflight whether STAR coordinates are tomogram pixels, Angstroms, or another
  source unit;
- verify RELION pixel-size data is in the selected first DataFrame, not only an
  unmerged optics block;
- do not center STAR points just because the volume was centered unless the same
  explicit transform is applied to the points;
- use a known particle or landmark to validate alignment, not only bounding-box
  overlap.

The current STAR reader accepts only columns identifying RELION or cisTEM by
angle names and takes the first DataFrame returned by `starfile`. A syntactically
valid alternative STAR schema, a multi-block file with data in a later block,
or missing required coordinates/angles must be reported as unsupported rather
than guessed.

## Placement and ownership checklist

For a map plus atomic model or particle ensemble, record and check:

- local source paths and non-zero sizes;
- map format and parser shape/origin/delta;
- `center` and `invert` values;
- map cache path and whether it was freshly rebuilt;
- map object location `(0, 0, 0)` and `Molecular Nodes` ownership;
- structure/STAR/CellPack object scale and any explicit object translation;
- CellPack transform object plus its `instance_collection`, if present;
- a known alignment landmark and an evaluated geometry result;
- the style socket and threshold used for the visual check.

Do not move or delete a CellPack instance source or a density VDB merely to make
the viewport look centered. Preserve the generated object/collection structure
until all users have been checked. For the cleanup and failure branches, use
[`troubleshooting.md`](troubleshooting.md).

## Evidence boundary

This reference was checked against `molecularnodes/entities/density/grids.py`,
`molecularnodes/entities/density/annotations.py`,
`molecularnodes/entities/ensemble/star.py`,
`molecularnodes/entities/ensemble/cellpack.py`,
`molecularnodes/nodes/geometry.py`, `molecularnodes/assets/nodes.yml`,
`docs/tutorials/cryoem.qmd`, `docs/api/_density.qmd`, and the density/STAR tests
as source evidence. Installed Blender 5.2.0 and MolecularNodes 5.2.0 package
metadata were inspected; no native tests or examples were run and no online
EMDB data was fetched.
