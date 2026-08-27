# Molecule lifecycle and static loading

## Runtime boundary

The public object is `molecularnodes.entities.molecule.base.Molecule`. It is a
`MolecularEntity` backed by an `MDAnalysis.Universe` and a Blender mesh object.
The supported production host is Blender 5.2 with `bpy` 5.2. The package facts
for this skill are MolecularNodes 5.2.0, Python 3.13, `databpy` 0.8.0,
`nodebpy` 520.11.0, MDAnalysis 2.10.0, and Biotite 1.7.1. A pure Python
`MDAnalysis` or Biotite probe can inspect input data, but cannot prove that a
MolecularNodes object, modifier, named attribute, Geometry Nodes tree, or
material is usable.

## Construction signatures

```python
Molecule(
    universe: MDAnalysis.Universe,
    name: str = "NewUniverseObject",
    world_scale: float = 0.1,
    create_object: bool = True,
) -> Molecule

Molecule.load(
    topology: str | pathlib.Path,
    coordinates: str | pathlib.Path | None = None,
    name: str | None = None,
    style: str | None = None,
    selection: str | None = None,
    create_object: bool = True,
    **kwargs,
) -> Molecule

Molecule.from_file(
    file_path: str | pathlib.Path | io.BytesIO,
    name: str | None = None,
) -> Molecule

Molecule.fetch(
    code: str,
    format: str = ".bcif",
    cache: str | pathlib.Path | None = download.CACHE_DIR,
    database: str = "rcsb",
) -> Molecule
```

`Molecule` construction registers the entity in the active MolecularNodes
session, creates a `SelectionManager`, frame manager, annotation manager, DSSP
manager, and (unless disabled) a Blender object. The managers exist on every
Molecule, but trajectory playback, annotations, and DSSP workflows belong to
sibling skills; this skill only uses the selection manager as the bridge to
style masks.

`world_scale` multiplies Angstrom positions before writing Blender coordinates.
Keep the scale consistent across custom geometry and materials. The source's
standard default is `0.1`; do not infer a different scale from an old example.

## Choose the correct loader

### Wrap an existing Universe

Use the constructor when the caller already owns a valid Universe:

```python
import MDAnalysis as mda
import molecularnodes as mn

universe = mda.Universe(topology_path, coordinate_path)
mol = mn.Molecule(universe, name="prepared", world_scale=0.1)
```

The Universe must expose topology and positions. The object creation path writes
vertices from `atoms.positions * world_scale`, copies bonds when present, then
stores standard attributes and creates the `Molecular Nodes` Geometry Nodes
modifier. `create_object=False` is useful only for a caller that will defer
Blender-object creation; do not style a Molecule until `mol.object` and its
modifier exist.

### Load a local structure or an MD topology/coordinates pair

`Molecule.load(topology, coordinates=None, ...)` has two distinct routes:

- With only `topology`, it delegates to `from_file`. Supported suffixes are
  `.pdb`, `.cif`, `.bcif`, `.sdf`, and `.mol`; the Biotite reader and converter
  create the Universe. `style` and `selection` are applied after the object is
  created when `style` is not `None`.
- With `coordinates`, it calls `MDAnalysis.Universe(topology, coordinates, **kwargs)`.
  `topology` and `coordinates` are passed to MDAnalysis rather than to the
  Biotite file dispatcher. The resulting `Molecule` receives `name` (or
  `"NewMolecule"`) and `create_object`; `world_scale` is not a separate
  `Molecule.load` parameter and should be supplied by constructing
  `Molecule(universe, world_scale=...)` yourself if a non-default scale is
  required. A requested style is only applied when `create_object` is true.

Examples:

```python
static = mn.Molecule.load("fixtures/1BNA.cif", name="dna")
static.add_style("ribbon")

md = mn.Molecule.load("topology.psf", "coordinates.dcd", name="md")
md.add_style("spheres", selection="resname LYS")
```

The second example is a trajectory-capable Universe even though this skill does
not cover playback. Handoff frame changes and dynamic updates to the sibling
trajectory skill.

### Convert a Biotite structure directly

`Molecule.from_file` calls `read_structure(file_path)`, then
`universe_from_atoms(reader.array)`. `read_structure` dispatches as follows:

| Input | Reader |
| --- | --- |
| `.cif`, `.bcif` | Biotite PDBX reader |
| `.pdb` | Biotite PDB reader |
| `.sdf`, `.mol` | Biotite SDF reader |
| `io.BytesIO` | BinaryCIF/PDBX reader |
| other suffix | `biotite.file.InvalidFileError` |

The return value is a reader with `.array` (`AtomArray` or `AtomArrayStack`),
`.n_models`, `.chain_ids()`, `.entity_ids()`, and `.assemblies(...)`. A file
loaded from a path receives its stem as the default object name and records the
file source in object properties. An in-memory buffer does not have a path name.

`universe_from_atoms` preserves coordinates, Biotite topology, bonds, and
selected file annotations. A multi-model `AtomArrayStack` is loaded as multiple
Universe frames; the first model supplies the topology. Bond type/order is kept
as a mesh edge attribute because MDAnalysis topology does not retain the order
in the same form. This is why a local SDF can retain connectivity for
ball-and-stick styling.

### Fetch a database structure

```python
mol = mn.Molecule.fetch(
    "4ozs",
    format=".bcif",
    cache="fixtures/cache",
    database="rcsb",
)
```

`fetch` uses `StructureDownloader`, calls `from_file` on the downloaded path,
and records `mol.props.code` and `mol.props.database`. `format` examples are
`.bcif`, `.cif`, and `.pdb` (the tests also exercise equivalent strings). A
network or cache failure is an input acquisition failure, not a style failure;
fall back to a local fixture or a known cache before debugging Geometry Nodes.

## Object and attribute contract

After a successful object-creating load, check:

```python
assert mol.universe.atoms.n_atoms > 0
assert mol.object is not None
assert mol.modifier_node_tree is not None
attrs = mol.list_attributes(drop_hidden=False)
```

The entity stores common atom data as mesh attributes. Names include:
`atomic_number`, `vdw_radii`, `mass`, `res_id`, `ures_id`, `segid`, `res_name`,
`atom_id`, `b_factor`, `occupancy`, `charge`, `chain_id`, `atom_types`,
`atom_name`, `lipophobicity`, `Color`, `is_alpha_carbon`, `is_backbone`,
`is_side_chain`, `is_solvent`, `is_nucleic`, `is_lipid`, `is_peptide`,
`is_hetero`, `is_carb`, `entity_id`, and `sec_struct` when the source can supply
them. `position` is the geometry position attribute. Some attributes are
skipped when the Universe lacks required topology data; treat `list_attributes`
as the capability check rather than assuming every optional field exists.

The default `Color` field is written explicitly as a float color attribute.
Most selection fields are boolean attributes. The public calls used by this
skill have these forms:

```python
import databpy

mol.store_named_attribute(data=array, name="my_field")
mol.store_named_attribute(
    data=mask,
    name="my_mask",
    atype=databpy.AttributeTypes.BOOLEAN,
)
values = mol.named_attribute("my_field")
evaluated = mol.named_attribute("position", evaluate=True)
mol.remove_named_attribute("my_mask")
```

Use a per-atom array with the same length and order as `mol.atoms`. Use an
explicit `atype` for colors (`FLOAT_COLOR`) and booleans when inference could
be ambiguous. Store a selection through `mol.selections.from_string` or
`from_atomgroup` when it should be editable and synchronized; direct storage is
appropriate for a deliberate stable mask.

## Structural verification with local fixtures

A minimal host check can load a fixture and assert the core contract:

```python
mol = mn.Molecule.load("fixtures/1BNA.cif")
assert mol.props.entity_type == mn.entities.base.EntityType.MOLECULE.value
assert mol.universe.trajectory.n_frames == 1
for name in ("atomic_number", "chain_id", "Color", "is_backbone"):
    assert name in mol.list_attributes(drop_hidden=False)
assert mol.named_attribute("position").shape[1] == 3
```

Use a small SDF to check connectivity:

```python
mol = mn.Molecule.load("fixtures/caffeine.sdf")
assert len(mol.object.data.edges) > 0
```

Use a multi-model BCIF fixture only to prove converter preservation:

```python
mol = mn.Molecule.load("fixtures/2M6Q.bcif")
assert mol.universe.trajectory.n_frames > 1
```

Do not turn the last check into a playback workflow here. The trajectory sibling
owns frame changes and frame-dependent attributes.
