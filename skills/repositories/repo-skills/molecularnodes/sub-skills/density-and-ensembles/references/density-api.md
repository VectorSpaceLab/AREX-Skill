# Density grid API

This reference describes the MolecularNodes 5.2.0 `Grids` implementation. It is
an operating contract, not a promise that every file with a familiar suffix is
valid. Perform local path and format checks before entering Blender; perform
volume import, Geometry Nodes evaluation, and collection checks in the Blender
5.2 host.

## Runtime boundary

`Grids.load()` has this signature:

```python
mn.entities.density.Grids.load(
    file_path,
    name=None,
    style="density_surface",
    invert=False,
    center=False,
    overwrite=False,
)
```

`file_path` may be `str` or `pathlib.Path`, but the caller should first require
an existing regular, non-empty local file. `Grids` resolves the path for
parsing and cache creation. The object property written by `load()` is the
string supplied to `load()` (`object.mn.filepath`); reload code resolves that
recorded value later.

The constructor parses the grid and converts it to VDB before `create_object()`
imports the VDB. Therefore `Grids.load()` is not a parser-only operation. It
needs `bpy`, the Blender volume importer, MolecularNodes node assets, and the
bundled `openvdb` module. A Python-only preflight can use `gridData.Grid` and,
for MRC-family files, `mrcfile`, but it cannot prove that the Blender volume or
Geometry Nodes object will evaluate.

## Current format dispatch

The `Grids` class documents these plain formats:

| Input | Current route | Notes |
| --- | --- | --- |
| `.dx` | GridDataFormats DX | OpenDX parser; `.dx.gz` is handled by the DX reader. |
| `.plt` | GridDataFormats PLT | The installed PLT reader opens the binary file directly; do not assume `.plt.gz` works merely because `gz` is listed in the class docstring. |
| `.ccp4` | GridDataFormats MRC | The MRC reader is used; MRC-family fallback is available. |
| `.mrc` | GridDataFormats MRC | The MRC reader is used; MRC-family fallback is available. |
| `.map` | Forced MRC | `Grids` passes `file_format="mrc"` for `.map`, `.map.gz`, and `.map.bz2`. |
| `.pickle` | GridDataFormats Python pickle | The loader expects the GridDataFormats pickle dictionary. Treat pickle input as trusted code, not a safe data format. `.pkl` is accepted by the installed loader as `PKL`, although it is not listed in the `Grids` class docstring. |

The class docstring also lists `.dx.gz`, `.ccp4.gz`, `.mrc.gz`, `.map.gz`, and
several `.bz2` forms. The installed GridDataFormats 1.2.0 autodetector unwraps
one `.gz` suffix but does not unwrap `.bz2`; MolecularNodes then falls back to
`mrcfile` only for MRC-family input. In practice:

- `.mrc.gz`, `.mrc.bz2`, `.ccp4.gz`, `.ccp4.bz2`, `.map.gz`, and `.map.bz2`
  are MRC-family candidates. `mrcfile` supports gzip and bzip2 and the
  MolecularNodes fallback opens these by compression signature.
- `.dx.gz` can use the GridDataFormats DX gzip path.
- `.dx.bz2`, `.plt.bz2`, and `.pickle.bz2` are not dispatched by the installed
  loader and have no MolecularNodes fallback.
- `.plt.gz` and `.pickle.gz` may be recognized as PLT/PICKLE by suffix, but the
  installed readers open the compressed bytes as ordinary binary input. Decompress
  them to a local `.plt`/`.pickle` fixture before loading unless a host-specific
  probe proves otherwise.

For reproducible operation, prefer an uncompressed `.dx`, `.plt`, `.mrc`,
`.map`, `.ccp4`, or `.pickle`, or a known-working compressed MRC-family file.
Suffix matching is effectively case-sensitive (`Path.suffix` and the explicit
`.map` check), so normalize or reject uppercase extensions during preflight.
There is no public `file_format` argument on `Grids.load()` with which to
override dispatch.

## Conversion and coordinate contract

The current conversion path is:

1. `Grids.grid_to_vdb()` calls `bpy.utils.expose_bundled_modules()` and imports
   `openvdb`.
2. It computes a neighboring cache using `Density.path_to_vdb()`.
3. It parses with GridDataFormats first. If that raises, it attempts an
   `mrcfile.open(..., permissive=True)` fallback and constructs a minimal grid
   from the data, voxel size, and header origin.
4. If `invert=True`, values become `max(grid) - grid`; positions and voxel
   spacing are unchanged.
5. The array is copied to an OpenVDB grid named `density`, marked as a fog
   volume, and scaled by `delta * 0.1`. The MolecularNodes world scale is thus
   0.1 Blender units per source coordinate unit (normally Angstroms).
6. With `center=False`, the VDB translation is the parsed grid origin. With
   `center=True`, the translation is `-shape * 0.5 * delta`; this is based on
   array shape and spacing rather than the parsed origin. The translation is
   also scaled by 0.1.
7. `databpy.import_vdb(..., collection=coll.mn())` imports the volume, and
   `create_object()` sets `object.location = (0, 0, 0)` and
   `object.mn.entity_type = "density"`.

`center` changes placement, not data values. `invert` changes values, not
placement. Neither option rotates or rescales an atomic model. Keep the same
placement convention for any structure overlaid on the map; see
[`cryoem-workflows.md`](cryoem-workflows.md).

The parsed `density.grid` is the GridDataFormats-like object. Useful preflight
fields are `grid.grid`, `grid.delta`, `grid.origin`, `grid.metadata`, and
`grid.grid.shape`. The conversion adds metadata keys `filepath`, `invert`, and
`center` to the in-memory grid metadata. These are also used by density
annotations. The source filepath is not written as a VDB identity field.

## VDB cache identity and ownership

`path_to_vdb()` uses the source directory and the first dot-separated basename
component, then appends `_center` and/or `_invert` and `.vdb`:

```text
<source-directory>/<first-basename-component>[_center][_invert].vdb
```

Consequences:

- `map.mrc`, `map.map.gz`, and `map.other.mrc` can collide when they share the
  same first basename component and directory.
- The cache identity includes only the source directory/basename convention and
  the two boolean options. It does **not** include source mtime, size, hash,
  parser version, voxel spacing, world scale, or source format.
- A changed source file with the same derived name and the same `center` and
  `invert` flags can be silently served by `overwrite=False`.
- A VDB is reused only when `openvdb.readAllGridMetadata()` finds both
  `MN_invert` and `MN_center` with matching values. A missing or corrupt
  metadata read can itself fail; it is not proof that the cache is safe.
- `overwrite=True` removes and rewrites the neighboring file after parsing.
  Use it after changing source content, suspecting a stale cache, or recovering
  from a wrong center/invert conversion.

The imported Blender volume data points at the neighboring VDB. Inspect the
volume data filepath (`density.object.data.filepath` on the host) and not only
`density.object.mn.filepath`: the former is the generated cache, while the
latter is the recorded source argument. Several imported objects may share the
same cache. Before deleting a VDB, search all volume data blocks/objects for
that cache path and remove the file only when no object references it. Moving
or deleting a referenced VDB breaks the volume.

## Styles, thresholds, and attributes

`style` is looked up in a fixed mapping:

```python
{
    "density_iso_surface": DensityStyleISOSurface,
    "density_surface": DensityStyleSurface,
    "density_wire": DensityStyleWire,
}
```

An unknown non-`None` style raises a `KeyError`. `style=None` imports the
volume without adding the MolecularNodes density style; do not call
`named_attribute("position")` as a visual/evaluated check until a suitable
modifier exists.

When a style is added, MolecularNodes computes the initial threshold as the
`0.995` quantile of the parsed scalar array and passes it to the selected style.
This is a heuristic, not a contour level guaranteed to produce geometry. An
empty, constant, NaN-heavy, inverted, or very noisy map can yield no visible
surface or an unexpectedly large one. A threshold that is too high produces an
empty result; one that is too low can expose the whole volume/noise. Check
finite data and min/max during preflight, then inspect the actual style node
socket in Blender. Depending on the asset, use the exposed `Threshold` or
`ISO Value` socket; do not assume a Python property named `iso_value` exists.

The ISO style exposes the most map-specific controls: threshold, contour
visibility, contour-only mode, contour thickness/color, slice width/center,
positive and negative colors, smooth shading, and material. Surface exposes
threshold, dust suppression, color, smooth shading, and material. Wire exposes
threshold, dust suppression, radius, resolution, color, and material. Socket
names are the asset interface names; inspect `style_node.inputs` on the host.

A successful host-side acceptance check should include:

```python
assert density.object is not None
assert density.props.entity_type == "density"
assert density.object.location == (0, 0, 0)
assert density.object.users_collection[0] == mn.blender.coll.mn()
assert len(density.named_attribute("position")) > 0
```

The final position assertion evaluates the object through the MolecularNodes
modifier and is therefore Blender-host validation, not parser validation. For a
centered map, compare the evaluated position centroid to zero with a tolerance;
the exact value depends on the data, voxel convention, and threshold.

## Evidence boundary

This contract was audited against `molecularnodes/entities/density/grids.py`,
`molecularnodes/entities/density/base.py`,
`molecularnodes/blender/coll.py`,
`molecularnodes/entities/density/annotations.py`,
`molecularnodes/nodes/geometry.py`, `docs/api/_density.qmd`, and
`docs/tutorials/cryoem.qmd` in the repository, plus the installed
GridDataFormats 1.2.0 and mrcfile 1.5.4 APIs in the MolecularNodes 5.2.0
inspection environment. No native tests or examples are part of this audit.
