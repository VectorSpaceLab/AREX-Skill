# Density and ensemble troubleshooting

Use this as a recovery decision tree. Keep the original scene intact until the
failure is classified. Do not download a replacement map or relabel a file as
a different format merely because the first local parse failed.

## First response: classify without mutating Blender

1. Record the exact local path, suffix, `Path.is_file()`, and byte size.
2. Reject missing paths, directories, zero-byte files, and unsupported/case-
   mismatched suffixes.
3. Identify the route: grid, STAR, or CellPack.
4. Run a parser-only check with the appropriate installed reader where possible.
5. Record the full exception class/message and whether Blender was already
   mutated.
6. Only then enter the Blender host or retry with a known local fixture.

Parser-only checks can establish readability and schema/shape. They cannot
establish VDB cache ownership, Molecular Nodes collection ownership, node assets,
modifier evaluation, visible contour geometry, or CellPack instance linkage.
Those require Blender 5.2 with MolecularNodes 5.2.0. Do not run native repo
tests or examples as part of this recovery route.

## Missing, malformed, or unsupported local paths

### `FileNotFoundError`, `IOError`, or “file not found”

- Check spelling, case, symlinks, and whether the path was expanded/resolved.
- Confirm the source is local and non-empty before calling `Grids.load()`,
  `StarFile.load()`, or `CellPack.load()`.
- For a missing STAR-referenced micrograph, distinguish the optional
  `_convert_mrc_to_tiff()` operation from STAR point parsing. Search only the
  STAR-relative locations implemented by the loader; do not fetch silently.
- For an absent VDB, regenerate it from the source grid rather than creating an
  empty placeholder.

### Directory or zero-byte file

Reject before an importer. A directory may produce a misleading parser error;
a zero-byte input can leave a registered but unusable entity if failure happens
after entity construction. Preserve the scene, record the path, and use a
known local non-empty fixture.

### Unsupported suffix or schema

- Grid suffixes are dispatched by GridDataFormats 1.2.0 and the explicit
  MolecularNodes `.map`-as-MRC branch. There is no public format override on
  `Grids.load()`.
- `.map`/`.map.gz`/`.map.bz2` are sent to MRC parsing. `.mrc`/`.ccp4` may use
  the same MRC fallback after the first parser fails.
- A `.dx.bz2`, `.plt.bz2`, or `.pickle.bz2` file has no current fallback.
  Decompress to a local supported uncompressed form. Treat `.plt.gz` and
  `.pickle.gz` as suspect because suffix detection does not make their readers
  decompress the bytes.
- A valid STAR file must still expose the current RELION or cisTEM columns.
  A valid generic STAR, unsupported dialect, missing angle/coordinate column,
  or relevant data in a later block is an unsupported schema, not an invitation
  to infer columns.
- CellPack accepts lowercase `.cif` and `.bcif` only and requires assembly
  operation/atom categories. A generic mmCIF structure without CellPack
  assembly metadata is not automatically a CellPack.

## Density parse failure

`Grids.grid_to_vdb()` first tries GridDataFormats and then tries an
`mrcfile.open(..., permissive=True)` MRC-family fallback. For a failure:

1. Save the original exception and inspect `grid.grid`, shape, dtype, origin,
   and delta with a parser-only reader.
2. For MRC/CCP4/MAP, inspect dimensions, voxel size, orthorhombic cell angles,
   map mode, origin, start indices, and whether the data is truly 3-D. A
   permissive fallback can read a header that the primary parser rejects, so
   independently validate that the resulting array and spacing are sensible.
3. For DX, PLT, or GridDataFormats pickle, use the matching reader and do not
   assume the MRC fallback applies.
4. Reject empty arrays, non-finite-heavy data, nonsensical/non-positive voxel
   spacing, and a parser result whose shape is not a 3-D volume.
5. Retry only with a known local file or an explicitly repaired local copy.

Do not delete scene objects speculatively. A failure before VDB import should
not be “fixed” by removing an unrelated density object. If an entity was
registered but has no valid object, inspect the session before retrying and
remove only the failed/orphaned entity according to the host's session API.

## Stale, corrupt, or wrong-option VDB

The generated cache is adjacent to the source and is derived from the first
basename component plus `_center`/`_invert`. The current cache check reads VDB
metadata and compares only `MN_center` and `MN_invert`:

- It does not detect a changed source file with the same name and flags.
- It does not encode source mtime, size, hash, parser version, world scale, or
  source format.
- A VDB with missing/corrupt metadata may fail in `readAllGridMetadata()`
  instead of being safely regenerated.
- A wrong `center` or `invert` creates a different derived filename, while an
  already existing same-option cache may still be stale.

Recovery sequence:

1. Record the source path, intended `center`/`invert`, derived cache path, and
   every existing volume object/data filepath that points to it.
2. If no object needs the cache, remove only that neighboring generated VDB or
   pass `overwrite=True` to regenerate it.
3. If another object references the VDB, do not unlink it underneath that
   object. Rebuild to a separate source directory/collision-free name or plan
   a coordinated reload.
4. Re-import and check `density.object.data.filepath`,
   `density.object.mn.filepath`, `MN_invert`/`MN_center` metadata when available,
   object location, and collection ownership.
5. Re-evaluate positions and threshold; do not trust visual appearance from the
   previous cache.

Deleting the VDB while a Blender volume data block uses it breaks the scene.
Deleting only the volume object does not necessarily remove its data block or
file; check all users first.

## Empty or wrong density geometry

The initial threshold is `np.quantile(grid.grid, 0.995)`. Diagnose in this
order:

1. Confirm the parsed data is non-empty and finite enough to summarize.
2. Compare min, max, quantiles, and whether `invert` was used.
3. Inspect the final density style node's exposed socket. The asset may expose
   `Threshold` or `ISO Value`; `nodes.get_style_node()`/the modifier tree is
   the authority on the host.
4. Lower a too-high threshold for an empty map or raise a too-low threshold for
   a solid/noisy map. For ISO styles, check contour and slice settings; for
   surface/wire styles, check dust suppression and radius/resolution.
5. Confirm a Molecular Nodes modifier exists before calling
   `density.named_attribute("position")`.

An empty evaluated position array can indicate a threshold problem, no style or
modifier, an invalid volume import, or a source grid with no useful contrast.
It is not proof that the parser failed. `invert=True` changes scalar values
only, so it can change the visible region without changing the position
centroid.

## STAR failure branches

### STAR parser succeeds but `StarFile` rejects it

Inspect the first DataFrame returned by `starfile.read(..., always_dict=True)`.
The current reader takes the first value and checks for `rlnAnglePsi` or
`cisTEMAnglePsi`. Verify all required coordinate and rotation columns in
[`ensemble-formats.md`](ensemble-formats.md). Do not merge optics/particles or
rename columns in memory and then claim the unmodified source is supported;
record the repair as a separate local preprocessing step.

### RELION positions are wrong

Check that the first DataFrame contains `rlnImagePixelSize`. The current reader
uses it when present, subtracts `rlnOrigin*Angst` when the full shift triplet is
present, and then multiplies by 0.1. Pixel size stored only in a discarded optics
block is not used. Check image/micrograph category codes through
`object.mn.categories`, not by treating `image_id` as a filename.

### cisTEM positions are wrong or load raises

Check numeric `cisTEMDefocus1`/`cisTEMDefocus2`, angle columns, and original X/Y
columns. The reader creates Z from mean defocus minus its median and ignores
`cisTEMPixelSize`. Optional `origin_x/y/z` shifts are subtracted when the full
set exists. A file with true 3-D coordinates but no defocus columns does not
match the current cisTEM contract.

### STAR micrograph conversion fails

This is an optional MRC-to-TIFF operation, not a point-parser failure. Confirm
that the selected image column is present and categorical, the referenced MRC
exists in the loader's allowed relative locations, and the MRC contains data.
Preserve the STAR entity if only conversion failed. Do not switch to CellPack or
silently fetch the micrograph.

## CellPack failure branches

### CIF/BCIF syntax or category error

Confirm lowercase suffix and choose the matching biotite reader. Inspect that
the block contains usable `atom_site`, `pdbx_struct_assembly_gen`, and
`pdbx_struct_oper_list` data, including all matrix columns, operation IDs,
assembly IDs, and chain lists. Missing assembly metadata is a CellPack schema
failure even if `biotite` can read the file as a generic structure.

If molecule extraction raises `InvalidFileError`, the PETWORLD fallback may
attempt per-model extraction. Check that model numbers and atom annotations are
present; do not force this branch for arbitrary malformed CIF. Verify that
`entity.transformations` and `entity.molecules` are non-empty before creating
visual styles.

### CellPack loads but nothing is visible

`node_setup=False` still creates the root data object's `Ensemble Instance`
node tree, but leaves instance molecule objects without their shared style
modifier. Check the root modifier, the instance collection, and whether the
collection is hidden below `.MN_data`. Use `node_setup=True` when visualizing
without building per-instance styles manually.

### CellPack transforms or ownership are wrong

The data object stores translations and a full transform attribute at 0.1 scale;
molecule sources are also at 0.1. There is no center/invert transform. Check
that:

- `entity.object` is in `Molecular Nodes`;
- `entity.instance_collection` resolves to the actual collection name;
- all instance objects are members of that collection;
- the collection is linked below `.MN_data`;
- no instance source object was moved independently;
- the transform array is non-empty and has 4 x 4 matrices.

A collection with a Blender-generated `.001` suffix is not necessarily wrong;
use the stored `instance_collection` name. A deleted or renamed collection
breaks the root instance node and session reload.

## Placement, centering, and inversion recovery

When a map and model do not overlap:

1. Compare parser coordinates/origin/delta before Blender transforms.
2. Determine whether the map was converted with `center=False` or `center=True`.
3. Determine whether any structure or ensemble object was separately translated
   or scaled.
4. Remember that density `invert` changes values only; STAR and CellPack have no
   center/invert switches.
5. Rebuild the map cache with the intended flags and apply one explicit, recorded
   transform to the model/points if the map is centered.
6. Validate a known landmark and evaluated geometry, not only object origins.

Do not fix a placement mismatch by flipping map contrast, lowering threshold,
or deleting a source collection. Those operations change appearance/ownership,
not coordinate frames.

## Cleanup and final check

Before deleting anything, inspect:

```python
# Blender-host inspection sketch; do not run outside Blender.
source = density.object.mn.filepath
cache = density.object.data.filepath
owners = list(density.object.users_collection)
```

For CellPack also record `entity.instance_collection.name` and its objects. Remove
only generated orphan objects/collections/files after checking all users. The
final handoff should state the exact files, exception branch, cache decision,
center/invert choice, threshold, ownership result, and any unresolved backend
or schema uncertainty.

## Evidence boundary

This decision tree was audited against
`molecularnodes/entities/density/grids.py`,
`molecularnodes/entities/density/base.py`,
`molecularnodes/entities/ensemble/star.py`,
`molecularnodes/entities/ensemble/cellpack.py`,
`molecularnodes/entities/ensemble/reader.py`,
`molecularnodes/entities/molecule/pdbx.py`,
`molecularnodes/blender/coll.py`, `molecularnodes/ui/ops.py`,
`docs/tutorials/cryoem.qmd`, `docs/api/_density.qmd`, and the relevant density,
STAR, CellPack, and session test sources. Installed GridDataFormats 1.2.0,
mrcfile 1.5.4, starfile 0.5.13, biotite 1.7.1, databpy 0.8.0, Blender 5.2.0,
and MolecularNodes 5.2.0 metadata were inspected. No native tests/examples were
run, and no online data was acquired.
