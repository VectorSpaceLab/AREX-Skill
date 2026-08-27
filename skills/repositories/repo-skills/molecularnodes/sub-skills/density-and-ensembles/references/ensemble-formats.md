# STAR and CellPack ensemble formats

MolecularNodes 5.2.0 has two ensemble loaders:

```python
mn.entities.ensemble.StarFile.load(
    local_star, name="particles", node_setup=True
)

mn.entities.ensemble.CellPack.load(
    local_cif_or_bcif, name="pack", node_setup=True
)
```

Use a local, existing, non-empty regular file first. The loaders are Blender
entity constructors, not parser-only functions: they register a session entity,
create Blender objects, store named attributes, and (usually) build Geometry
Nodes. For parser-only preflight, call the installed `starfile`, `biotite`, or
related readers directly and inspect the resulting table/CIF categories. Do not
claim a Blender ownership or node-graph check from a successful Python parse.

## Shared load and metadata contract

`Ensemble.load()` constructs the subclass, calls `create_object()`, and then
writes the source argument to `object.mn.filepath`. The subclass resolves the
path for its own reads. The returned object is the data object for the ensemble.
The entity type is:

- `ensemble-star` for `StarFile`;
- `ensemble-cellpack` for `CellPack`.

The object is owned by the `Molecular Nodes` collection. Always validate
`entity.object`, `entity.props.entity_type`, `entity.object.mn.filepath`, and
`entity.object.users_collection` on the Blender host. A relative source path may
be recorded as supplied even though the parser used a resolved path.

`node_setup` is not equivalent for the two loaders:

- For `StarFile`, `node_setup=False` creates the point object and attributes but
  does not add the Starfile Instances Geometry Nodes branch.
- For `CellPack`, `node_setup=False` suppresses the per-molecule style modifier,
  but `create_object()` still creates the data object's root
  `Ensemble Instance` node tree and the instance collection. It is useful for
  lightweight ownership/attribute checks, not for a completely parser-only
  operation.

Neither loader has `center` or `invert` arguments. STAR coordinates and CellPack
transforms retain their source placement, subject to the fixed 0.1 world scale
and the STAR shift/defocus rules below. Do not apply an unrecorded centering or
contrast inversion while diagnosing an alignment problem.

## RELION and cisTEM STAR

### What the current reader does

`StarFile._read()` calls `starfile.read(path, always_dict=True)`, takes the first
value from the returned mapping, and requires that value to be a pandas
`DataFrame`. Object columns are converted to pandas categorical columns. The
loader then detects only these schemas:

- RELION if the DataFrame contains `rlnAnglePsi`;
- cisTEM if it contains `cisTEMAnglePsi`.

All other STAR dialects are rejected with a
`ValueError` stating that only RELION >=3.1 or cisTEM are supported. A file can
therefore be syntactically valid STAR and still be unsupported. Also note that
only the first block is used. A multi-block RELION file whose coordinates or
pixel size exist only in a later block is not merged by this implementation;
there is no current optics/particles join in `StarFile`.

Before host loading, check that the selected DataFrame is non-empty and has the
required columns for the detected schema. For RELION, the current coordinate
and rotation columns are:

```text
rlnCoordinateX, rlnCoordinateY, rlnCoordinateZ
rlnAngleRot, rlnAngleTilt, rlnAnglePsi
```

For cisTEM, the current reader first computes `cisTEMZFromDefocus`, so it needs:

```text
cisTEMOriginalXPosition, cisTEMOriginalYPosition
cisTEMDefocus1, cisTEMDefocus2
cisTEMAnglePhi, cisTEMAngleTheta, cisTEMAnglePsi
```

Optional shift columns are schema-specific. RELION uses
`rlnOriginXAngst`, `rlnOriginYAngst`, `rlnOriginZAngst`; cisTEM looks for
`origin_x`, `origin_y`, and `origin_z`. If all three are present, the shifts are
subtracted from the coordinate columns. Missing optional shifts are treated as zero. A partially present shift triplet
is silently ignored by this implementation because the column selection raises
`KeyError`; preflight it and reject or repair it rather than assuming a partial
shift was applied.

### Coordinate and rotation rules

The stored point positions are in Blender units:

```text
RELION: (coordinate - optional Angstrom shift)
        * rlnImagePixelSize when that column exists
        * 0.1
cisTEM: (X, Y, ZFromDefocus - optional origin shift) * 0.1
```

`RelionDataFrame.scale` uses per-row `rlnImagePixelSize` when present and uses
ones otherwise. `CistemDataFrame` inherits the unit scale and does not use
`cisTEMPixelSize`; do not silently insert a cisTEM pixel-size conversion into a
recovery that is meant to match MolecularNodes 5.2.0.

For cisTEM, `cisTEMZFromDefocus` is computed as the mean of
`cisTEMDefocus1` and `cisTEMDefocus2`, then shifted by its DataFrame median. It
is not a source Z coordinate. Missing/non-numeric defocus values can make this
step fail or produce unusable positions.

Rotations are converted from the schema's three Euler columns using SciPy
`Rotation.from_euler("ZYZ", angles, degrees=True).inv()`. The Geometry Nodes
rotation helpers use the corresponding RELION or cisTEM convention. If a
rotation attribute is being audited, compare the stored quaternion convention
rather than comparing raw Euler triples.

### Attributes and image IDs

`EnsembleDataFrame.store_data_on_object()` creates one point object and stores:

- every numeric DataFrame column as a named attribute;
- every categorical column as integer category codes;
- `object.mn.categories` as a JSON-serializable mapping from column name to
  category labels;
- `image_id` as integer category codes from the first available column in this
  order: `rlnImageName`, `rlnMicrographName`, `rlnTomoName`,
  `cisTEMOriginalImageFilename`.

If no candidate image column exists, `image_id` is all zeros. Missing categorical
values can carry pandas code `-1`; do not interpret codes as labels without
consulting `object.mn.categories`. Every stored attribute should have the same
row count as the input DataFrame. A host-side STAR acceptance check should
verify non-empty positions, expected coordinate/rotation/shift/defocus lengths,
`ensemble-star` metadata, and the categories property.

The optional `_convert_mrc_to_tiff()` path is separate from STAR point parsing.
It needs an already-created object and Starfile node, resolves a referenced
micrograph first as written and then relative to the STAR directory (with a
RELION parent fallback), and writes an adjacent `.tiff`. Missing micrographs are
not a reason to relabel a valid STAR file or to download data implicitly.

## CellPack CIF and BinaryCIF

### Format and source schema

`CellPackReader.read()` dispatches exactly on lowercase `.cif` and `.bcif`:

- `.cif` uses the MolecularNodes whitespace-stripping text reader;
- `.bcif` uses `biotite.structure.io.pdbx.BinaryCIFFile.read()`.

Other suffixes raise `ValueError`. The CellPack path is not a generic mmCIF
molecule loader. It expects the assembly and atom categories needed by
`PDBXReader._assemblies()` and `get_structure()`, including the operational
categories `pdbx_struct_assembly_gen` and `pdbx_struct_oper_list` and a usable
`atom_site` structure. Missing matrix columns, operation IDs, assembly IDs, or
atom data are schema failures even if the CIF syntax itself parses.

The reader obtains all assemblies and turns each operation into a structured
transform array with fields:

```text
assembly_id, sym_id, chain_id, transform (4 x 4), pdb_model_num
```

The matrix is used as a homogeneous transform. The molecule dictionary is
built by chain ID. PETWORLD-like data can take a fallback path that reads each
model separately, marks `_is_petworld`, and uses model-derived molecule IDs.
This is a compatibility branch, not a guarantee that arbitrary multi-model
CIF files are CellPack assemblies.

### Blender objects, transforms, and scale

`CellPack.create_object()` creates:

1. a transform data object in `Molecular Nodes`;
2. one molecule object per `file.mol_ids` in a collection named
   `cellpack_<name>` under `.MN_data`;
3. a root Geometry Nodes tree on the data object, containing the
   `Ensemble Instance` node that consumes that collection.

The transform data object vertices are the transform translations multiplied by
0.1. The full `transform` named attribute is stored with the row/column
orientation expected by Geometry Nodes, along with integer assembly, symmetry,
chain, and model attributes when present. Molecule atom coordinates are also
created at 0.1 scale. There is no centering step, no contrast inversion, and no
source-to-target alignment beyond these stored transforms and the fixed world
scale.

The public `instance_collection` property stores the collection **name**, not a
live collection pointer, so it survives session serialization by looking up
`bpy.data.collections[name]`. Blender may suffix duplicate collection names;
validate the returned `entity.instance_collection.name` rather than rebuilding
`cellpack_<name>` by hand. Keep the data object and this collection together
when moving, deleting, duplicating, or saving the scene.

With `node_setup=True`, all instance molecule objects share one generated
`MN_pack_instance_<name>` style node group and receive a Molecular Nodes
modifier. With `node_setup=False`, the instance objects are still created but
lack those per-object style modifiers; the root data object still has the
instance branch as described above.

A CellPack host acceptance check should verify:

```python
assert entity.props.entity_type == "ensemble-cellpack"
assert len(entity.transformations) > 0
assert len(entity.molecules) > 0
assert entity.object.users_collection[0] == mn.blender.coll.mn()
assert entity.instance_collection is not None
assert entity.instance_collection.name in bpy.data.collections
assert entity.instance_collection.users  # collection is linked under .MN_data
```

Also inspect that every instance object is in `entity.instance_collection`,
that the collection is under `.MN_data`, and that the transform data object is
not accidentally moved into the hidden data collection. The exact evaluated
instance count depends on the source assembly and node realization settings.

## Ownership, placement, and deletion rules

- STAR data objects and CellPack transform data objects belong in
  `Molecular Nodes` and are the objects registered with the session.
- CellPack molecule objects belong in `cellpack_<name>` below `.MN_data`; they
  are implementation-owned instance sources, not independent ensemble entities
  to style or delete casually.
- `.MN_data` is hidden/excluded by the collection helper. A missing viewport
  display does not mean the instance collection was not created.
- Moving only an instance source object changes every placement that uses it.
  To move a CellPack ensemble as a unit, move the transform/data object or the
  root object as appropriate and preserve the collection link.
- Deleting a CellPack root without removing its instance collection leaves
  orphaned hidden objects. Before cleanup, verify no other root node tree uses
  that collection, then remove instance objects, the collection, and finally
  the root data object. Do not remove the shared `Molecular Nodes` or `.MN_data`
  collections.

For scene alignment with a map, choose the map's `center` convention and an
atomic model placement deliberately; the STAR/CellPack loaders do not provide
a matching center switch. See [`cryoem-workflows.md`](cryoem-workflows.md) for
map-plus-structure alignment and [`troubleshooting.md`](troubleshooting.md) for
failure recovery.

## Evidence boundary

This contract was audited against `molecularnodes/entities/ensemble/base.py`,
`molecularnodes/entities/ensemble/star.py`,
`molecularnodes/entities/ensemble/cellpack.py`,
`molecularnodes/entities/ensemble/reader.py`,
`molecularnodes/entities/molecule/pdbx.py`,
`molecularnodes/blender/coll.py`, `molecularnodes/blender/mesh.py`,
`molecularnodes/entities/utilities.py`, `molecularnodes/ui/props.py`,
`tests/test_star.py`, and `tests/test_cellpack.py` in the repository. It was
also checked against the installed starfile 0.5.13, biotite 1.7.1, and databpy
0.8.0 APIs in the MolecularNodes 5.2.0 inspection environment. No native tests
or examples were run.
