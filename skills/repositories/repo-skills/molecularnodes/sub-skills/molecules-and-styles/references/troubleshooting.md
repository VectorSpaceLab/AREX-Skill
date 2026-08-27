# Troubleshooting and validation

Use this page to classify the failure before changing a style or rebuilding a
molecule. The static molecule/style path requires a Blender 5.2 host, the
MolecularNodes assets, and an object-creating `Molecule`. Pure Python
MDAnalysis, Biotite, or `mn.color` work can validate input data, but it cannot
validate Blender objects, named attributes, Geometry Nodes links, materials,
or evaluated geometry.

## Host and context

Start every host-side diagnosis with the runtime boundary:

```python
import bpy
import molecularnodes as mn

assert bpy.app.version[:2] == (5, 2)
assert bpy.context.scene is not None
assert hasattr(bpy.context.scene, "MNSession")
```

The `Molecule` constructor creates its managers and, when `create_object=True`,
creates the mesh, stores attributes, installs the `Molecular Nodes` modifier,
registers asset nodes, and makes the object active. A molecule created with
`create_object=False` has no object/modifier to style; create the object before
calling `add_style` or entering the style-tree workflow. A host that has not
registered the MolecularNodes session or addon properties is a host/setup
failure, not a selection or material failure.

When a manual node constructor reports that it must be created inside a
`TreeBuilder` context, use the documented `with mol.tree:` or
`with mol.tree.reset() as (atoms, join):` context. Do not instantiate
`g.Style...` or `g.SetColor` at module scope and then try to attach the node to a
different tree. `reset()` is destructive; use `with mol.tree` for recovery or
append-only edits.

If a script depends on `bpy.context` or UI property updates, run it in the
Blender main Python context rather than a detached pure-Python process. Keep the
molecule object and its node tree in the same host session while inspecting
links and evaluated geometry.

## Missing assets and incomplete setup

MolecularNodes style groups and preset materials are asset-backed. Typical
symptoms of an unavailable or stale asset bundle include:

- an asset group cannot be appended or constructed;
- `Style Spheres`, `Style Cartoon`, or another expected node-tree name is absent;
- a preset material cannot create its node tree;
- a style node exists but has no expected `Selection` or `Material` socket.

Check installation and asset availability before changing Python kwargs:

```python
from molecularnodes.nodes import geometry as g
from nodebpy.builder import TreeBuilder

with TreeBuilder.geometry("asset_probe"):
    probe = g.StyleSpheres()

assert probe.node.node_tree.name == "Style Spheres"
assert probe.node.inputs.get("Selection") is not None
assert probe.node.inputs.get("Material") is not None
```

This is an asset/API probe, not a repository example or native test. If it
fails, preserve the failure and repair the MolecularNodes installation or asset
registration. Do not replace an absent asset with a guessed node group, a
positional socket index, or a copied private path.

## Loader and attribute validation

Classify acquisition separately from styling. For a local file, check the
supported suffix before debugging Geometry Nodes: `.pdb`, `.cif`, `.bcif`,
`.sdf`, and `.mol` are dispatched by `Molecule.from_file()`/the one-file
`Molecule.load()` route. A topology plus coordinates invokes
`MDAnalysis.Universe` instead and is a different loader route.

After an object-creating load, validate in this order:

```python
assert mol.universe.atoms.n_atoms > 0
assert mol.object is not None
assert mol.modifier_node_tree is not None
names = mol.list_attributes(drop_hidden=False)
for required in ("atomic_number", "Color"):
    assert required in names
```

`list_attributes()` returns names on the molecule's object mesh. Optional
attributes can be absent when the input topology does not provide the data.
The default `Color` field is explicitly stored as a `FLOAT_COLOR` attribute;
use the actual attribute collection or `mol.named_attribute("Color")` to check
that it exists and has one RGBA row per atom. The `evaluate=True` option reads
after modifier evaluation and is useful only after the modifier and its assets
are valid.

For a custom attribute, keep the data aligned with atom order and use an
explicit type when inference could be ambiguous:

```python
import databpy as db

mol.store_named_attribute(
    data=mask,
    name="show_ligand",
    atype=db.AttributeTypes.BOOLEAN,
)
mol.store_named_attribute(
    data=rgba,
    name="Color",
    atype=db.AttributeTypes.FLOAT_COLOR,
)
```

The default storage domain is point. A boolean selection must have one value
per atom and a color field must have four normalized components per atom. A
length/domain/type error is an attribute-storage issue; it should be fixed
before inspecting style sockets.

## Style names and socket mismatches

Use only the six exact direct `add_style()` names in this sub-skill:
`spheres`, `sticks`, `ball_and_stick`, `cartoon`, `ribbon`, and `surface`.
The implementation checks a broader internal `styles_mapping` before indexing
`STYLE_NODE_MAPPING`; legacy aliases such as `atoms`, `vdw`, and `ball+stick`
can pass the first check but are not safe direct keys and can fail later with a
mapping error. Density and oxDNA keys belong to other workflows.

When a keyword or socket fails, inspect both the generated constructor and the
instantiated Blender node instead of translating a label by guesswork:

```python
import inspect
from molecularnodes.nodes import geometry as g

print(inspect.signature(g.StyleCartoon))
# after the node is in a tree:
for socket in style_node.inputs:
    print(socket.name, socket.bl_idname, socket.type)
```

The current assets expose input names such as `Selection` and `Material`, but
Blender socket types and generated wrapper parameter names are separate
contracts. Validate with `node.inputs.get(name)`, `socket.bl_idname`, and the
node-tree interface's `socket_type`. If a requested style keyword is not in the
current generated signature, stop rather than passing a guessed old name. If a
style swap changes its interface, re-check `Selection`, `Material`, all links,
and the final join after the swap.

A successful `add_style()` should leave the molecule's existing branches intact
and append its style output to the tree join. Verify that style nodes connect to
one final `GeometryNodeJoinGeometry` and that the expected output reaches the
group output. A missing join or a disconnected branch is a tree-composition
failure, not a loader failure.

## Invalid selections and recovery

`add_style()` resolves a string in this order:

1. if the string is an existing object attribute name, it uses that name
   directly;
2. otherwise it validates the string with MDAnalysis and creates a managed
   selection attribute;
3. if both checks fail, it emits `UserWarning`, returns no selection name, and
   still appends the style as an unmasked branch.

The current implementation checks attribute-name existence, not its Blender
attribute type. Therefore an existing `Color`, numeric, or vector attribute is
not a valid selection even if the name lookup succeeds; use a dedicated boolean
attribute and verify its type before passing the name.

A managed selection has different recovery semantics:

```python
sel = mol.selections.from_string("resid 1:10", name="focus")
sel.string = "not valid"     # message is set; last good mask remains
sel.string = "resid 1:5"     # message clears; the mask is updated
```

For an invalid `add_style()` branch, do not reset the whole tree. Create a valid
managed selection and append a corrected branch, then inspect or remove only the
bad style node if it should not remain. For a valid expression selecting zero
atoms, treat an all-false mask as an input/selection result rather than a parser
error and inspect the selected atom count.

When a branch is selected, its `Selection` input should be linked from a
boolean `GeometryNodeInputNamedAttribute` whose name is the intended managed or
manually stored attribute. An unmasked branch may have no selection link by
design.

## Materials and colors

A preset instance owns a new material datablock and the style node receives its
`.material`. If the material parameter is a string in `add_style()`, the method
tries to append that name from the MolecularNodes material asset; a string is
not the safe way to select an arbitrary custom material already in
`bpy.data.materials`. Pass the actual `bpy.types.Material` for that case. If a
preset constructs successfully but the style's `Material` socket is empty,
check the assignment after the style node is created and confirm that the
socket is `NodeSocketMaterial`.

For a color problem, distinguish these cases:

- a Python helper output has the wrong scale: 8-bit helpers return RGB/alpha
  values based on 255, while `random_rgb`, `color_chains`, and node color fields
  use normalized values;
- `Color` is absent or has the wrong type: re-check object creation and explicit
  `FLOAT_COLOR` storage;
- a constant works but a varying field does not: inspect the color node's output
  and the `SetColor` color link;
- the node is linked but the style ignores it: inspect the style/material asset's
  color path and evaluate the geometry after confirming the material is attached.

Use `NamedAttribute.color("Color")` for a named RGBA field and
`NamedAttribute.boolean("selection_name")` for a selection. These data types
are not interchangeable. Do not repair a color mismatch by changing a
selection socket or by storing a four-vector as a boolean.

## Source, network, and cache handoffs

Record the source kind and acquisition policy when handing a molecule to
another workflow. A fetched entity records its accession in `mol.props.code`
and `mol.props.database`; a path-backed local entity records its file source in
its object properties. An in-memory binary buffer has no useful path metadata,
so preserve the accession/format/cache decision separately.

The downloader accepts dotted or undotted `cif`, `pdb`, and `bcif` format names
and can cache to a directory or return an in-memory object. The current
`Molecule.from_file()` dispatcher accepts a path or `io.BytesIO` (treated as
BinaryCIF), but not `io.StringIO`. Consequently:

- `Molecule.fetch(..., format=".bcif", cache=None)` can hand a binary buffer to
  the one-file loader;
- text fetches with `format=".cif"` or `".pdb"` and `cache=None` return a
  `StringIO` from the downloader, which the current `Molecule.fetch()` path
  cannot dispatch successfully;
- use a cached/path-backed text fetch or BinaryCIF for an in-memory handoff;
- a network, HTTP, or cache miss is an acquisition failure. Retry with a known
  local/cached source before changing a style tree.

For a sibling workflow, hand off the `Molecule` object when the same Blender
session is available, plus the object name, source metadata, `Color` and
selection attribute names, and the current tree/join state. Rebuilding from the
source can lose managed selections, custom attributes, material ownership, and
style branches. If the source is unavailable, report the missing source/cache
and the last verified object/attribute state rather than claiming a style
failure was recovered.

## Synthetic validation cases

Use small, deterministic host cases rather than native repository tests or
examples:

1. Load one local static structure, store a custom boolean selection and a
   normalized custom RGBA field, append two differently selected style branches
   with two independent preset instances, and assert the `Selection` named
   attributes, `Material` datablock identity, `Color` type/length, and one final
   join.
2. Build a valid managed selection, deliberately submit an invalid expression,
   then repair it without resetting the tree; separately exercise a cached
   BinaryCIF handoff and a `cache=None` text handoff to ensure the latter is
   reported as an acquisition/dispatcher limitation rather than a Geometry
   Nodes error.

These cases exceed a single happy-path style call because they test ownership,
field typing, branch preservation, and recovery boundaries together.
