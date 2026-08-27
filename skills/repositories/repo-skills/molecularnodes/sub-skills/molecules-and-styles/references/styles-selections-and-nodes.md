# Styles, selections, and Geometry Nodes

## `add_style` contract

The simple append API is:

```python
mol.add_style(
    style="spheres",
    selection=None,
    material="MN Default",
    **kwargs,
) -> Molecule
```

It returns the same Molecule, so calls can be chained. The six supported direct
style names and their node groups are:

| `style` | Geometry group | Useful inputs |
| --- | --- | --- |
| `spheres` | `Style Spheres` | `sphere_geometry`, `quality`, `scale`, `shade_smooth`, `material` |
| `sticks` | `Style Sticks` | `sphere_geometry`, `quality`, `scale`, `shade_smooth`, `material` |
| `ball_and_stick` | `Style Ball and Stick` | `quality`, `sphere_geometry`, `sphere_scale`, `bond_split`, `bond_scale`, `bond_find`, `bond_find_scale`, `shade_smooth`, `material` |
| `cartoon` | `Style Cartoon` | `quality`, peptide/helix/sheet shape and thickness settings, `loop_radius`, nucleic settings, `color_blur`, `shade_smooth`, `material` |
| `ribbon` | `Style Ribbon` | `quality`, `peptide_radius`, backbone smoothing/threshold, nucleic settings, base geometry/scale, `base_resolution`, `base_realize`, `shade_smooth`, `material` |
| `surface` | `Style Surface` | `quality`, `surface_scale`, `surface_relax`, `offset`, `fillet`, `mean_width`, `mean_iterations`, `separate_by`, `group_id`, `color_source`, `color_blur`, `shade_smooth`, `material` |

Defaults are owned by the asset node groups. For exact defaults and socket
names, inspect the corresponding `g.Style...` constructor in the installed
package rather than hard-coding an old asset version. The direct method forwards
`**kwargs` to that constructor. A string outside the internal mapping raises
`ValueError` and lists the mapping keys; legacy aliases inside that mapping are
not necessarily resolvable by the final direct-style mapping.

The internal `styles_mapping` table contains legacy aliases and styles owned by
other sub-skills. Do not assume every mapping key is a safe direct
`add_style` input: `add_style` first checks that broader table but ultimately
indexes `STYLE_NODE_MAPPING`, whose safe direct keys are the six names above.
For example, aliases such as `atoms`, `vdw`, and `ball+stick` can pass the first
check but are not valid keys for this call path. Use the six exact names and
route density or oxDNA styling elsewhere.

Examples:

```python
mol.add_style("cartoon", quality=4, loop_radius=0.4)
mol.add_style(
    "ball_and_stick",
    selection="not protein",
    sphere_geometry="Mesh",
    bond_find=True,
    bond_find_scale=1.0,
)
mol.add_style("surface", selection="resid 100:150", quality=2)
```

Each successful call adds another style branch to the same tree. A selection is
implemented by a `GeometryNodeInputNamedAttribute` boolean field wired into the
style node's `Selection` input.

## Selection forms and ordering

`selection` accepts exactly three useful forms:

1. **`None`** — no mask is supplied; the style sees all atoms.
2. **An `MDAnalysis.core.groups.AtomGroup`** — the group is stored as a new
   managed selection through `mol.selections.from_atomgroup(...)`. It gets a
   generated name unless `from_atomgroup(..., name="...")` is called separately.
3. **A string** — first interpreted as the name of an existing mesh attribute
   (including a manually stored boolean field), otherwise parsed as an MDAnalysis
   selection phrase and stored through `mol.selections.from_string(...)`.

This ordering means a selection phrase that happens to equal an attribute name
uses the attribute directly and does not create a new managed item. The current
implementation checks only whether the name exists; it does not verify that an
existing attribute is boolean before constructing `NamedAttribute.boolean(...)`.
Keep selection names dedicated to boolean attributes and validate their Blender
type before styling. Make custom attribute names unambiguous, for example
`show_ligand` rather than a phrase.

```python
import databpy as db

# MDAnalysis phrase -> managed selection and boolean attribute
mol.add_style("spheres", selection="resid 1:10")

# Existing boolean attribute -> direct Named Attribute node, no new manager item
mol.store_named_attribute(mask, "show_ligand", atype=db.AttributeTypes.BOOLEAN)
mol.add_style("surface", selection="show_ligand")

# AtomGroup -> managed selection
ligand = mol.universe.select_atoms("resname LIG")
mol.add_style("ball_and_stick", selection=ligand)
```

`SelectionManager.from_string` has this signature:

```python
mol.selections.from_string(
    string: str,
    *,
    updating: bool = True,
    periodic: bool = True,
    name: str | None = None,
) -> TrajectorySelectionItem
```

It creates a UI item, an AtomGroup, and a boolean mesh attribute. Use
`updating=False` for a deliberately static selection. `periodic` controls
periodic-boundary behavior for geometric expressions such as `around`; it is
not needed for ordinary residue/name selections. `from_atomgroup(atomgroup,
name=None)` stores a pre-existing group and marks the UI item as originating from
an AtomGroup.

## Invalid-selection semantics and recovery

There are two different failure paths:

- `mol.add_style("cartoon", selection="not valid")` validates the string before
  creating a managed item. It emits `UserWarning`, returns `None` for the mask,
  and still appends the cartoon node. The branch is therefore unmasked and the
  warning says that nothing will be displayed unless the attribute is later
  created. Existing branches are not changed.
- `sel = mol.selections.from_string("protein")`; then `sel.string = "bad"`
  exercises the UI/property update path. The item receives a non-empty `message`,
  the cached AtomGroup and last good boolean attribute remain in place, and the
  bad expression is not committed as a new mask. Assigning a valid expression
  clears `message` and updates the attribute.

For recovery, never reset the whole tree merely to fix one selection:

```python
# preserve current style branches
with warnings.catch_warnings():
    warnings.simplefilter("always")
    mol.add_style("surface", selection="bad selection")

fixed = mol.selections.from_string("resid 1:20", name="surface_focus")
mol.add_style("surface", selection=fixed.name, material="MN Transparent Outline")
```

If the bad branch is visible and should be removed, identify its style node in
`mol.modifier_node_tree.nodes` and remove that node only after checking its
links. Do not delete the molecule object or its final join as a shortcut.

## Tree lifecycle

`MolecularTree` wraps a Blender `GeometryNodeTree` and exposes `atoms`,
`geometry`, and `join` sockets. The builder supports `>>` composition.

### Append while preserving work

```python
from molecularnodes.nodes import geometry as g

with mol.tree as tree:
    tree.atoms >> g.StyleCartoon(material=mat.material) >> tree.join
    tree.atoms >> g.StyleSpheres(scale=0.5) >> tree.join
```

`tree.atoms` finds the first geometry input and adds one if missing. `tree.join`
finds an existing `GeometryNodeJoinGeometry` feeding the output, otherwise adds
one. When existing real work feeds the output directly, it is linked into the
new join instead of being orphaned. A bare input-to-output passthrough is
intentionally dropped when the first branch is added.

### Reset deliberately

```python
with mol.tree.reset(input="Atoms", output="Geometry") as (atoms, join):
    atoms >> g.StyleRibbon(quality=3) >> join
```

`reset(input="Atoms", output="Geometry")` clears all tree nodes and interface
sockets, recreates the requested geometry input/output, and yields the sockets
for this exact tree. The returned `atoms` and `join` are the same sockets later
reachable as `mol.tree.atoms` and `mol.tree.join`. A custom input name is valid:
`reset(input="Volume")`; `tree.atoms` still finds that geometry input. Treat
`reset()` as destructive and use it only for a clean composition.

## Manual node composition

The generated asset node constructors are imported from
`molecularnodes.nodes.geometry`; the generic `NamedAttribute` helper comes from
`nodebpy.nodes.geometry`:

```python
from molecularnodes.nodes import geometry as g
from nodebpy.nodes.geometry import NamedAttribute

with mol.tree.reset() as (atoms, join):
    color = g.ColorElement()
    cartoon = g.StyleCartoon(
        selection=NamedAttribute.boolean("protein"),
        quality=3,
        loop_radius=0.4,
        material=mat.material,
    )
    atoms >> g.SetColor(color=color) >> cartoon >> join
```

Useful color/field nodes include `ColorElement`, `ColorRainbow`, `ColorPLDDT`,
`ColorResName`, `ColorSecondaryStructure`, `ColorAttributeMap`,
`ColorAttributeRandom`, `ColorBackbone`, and `SetColor`. `SetColor` accepts
`atoms`, `selection`, and `color`, and returns the geometry to continue the
branch. `NamedAttribute.boolean(name)` is the preferred field input for a
managed or manually stored boolean attribute.

A branch can use a selection node directly:

```python
sel = mol.selections.from_string("resname LYS", name="lysines")
with mol.tree.reset() as (atoms, join):
    atoms >> g.StyleSticks(selection=sel.node(), scale=0.3) >> join
    atoms >> g.SetColor(color=g.ColorRainbow()) >> g.StyleCartoon() >> join
```

Do not rely on `node.name` to identify an instanced asset after swaps. The helper
`molecularnodes.nodes.nodes.node_group_name(node)` returns the actual node-tree
name, and `get_style_node(mol.object)` finds the primary style node. The helper
`get_nodes_last_output(mol.node_group)` returns the final node and output socket;
`realize_instances(mol.object)` inserts a Realize Instances node at the end when
evaluated mesh access requires realized instances.

## Branch validation

After composing styles, inspect the tree rather than trusting the call return:

```python
ng = mol.modifier_node_tree
style_nodes = [
    n for n in ng.nodes
    if getattr(n, "node_tree", None)
    and "Style" in n.node_tree.name
]
assert len(style_nodes) >= 2
join_nodes = [n for n in ng.nodes if n.bl_idname == "GeometryNodeJoinGeometry"]
assert len(join_nodes) == 1
assert all(any(link.from_node is node for link in join_nodes[0].inputs[0].links)
           for node in style_nodes)
```

For a selected branch, assert that `style.inputs["Selection"].links` has a
source named-attribute node and that its `Name.default_value` is the expected
attribute. For an unmasked branch, the selection socket may have no link. The
node-group names and socket labels are asset contracts; if the asset is missing,
repair the host/add-on installation before changing Python code.

## Node-group reuse and swaps

MolecularNodes assets are reusable Geometry Node groups. `nodes.new_tree(name,
fallback=True)` returns an existing GeometryNodeTree with that name; it does not
silently duplicate it. A Molecule's modifier group is distinct from the shared
style asset groups. When a style is swapped in place, use the node helper that
preserves links rather than deleting and recreating the branch:

```python
from molecularnodes.nodes import nodes

style_node = next(
    n for n in mol.modifier_node_tree.nodes
    if nodes.node_group_name(n) == "Style Cartoon"
)
nodes.swap(style_node, "Style Surface")
```

Re-check the selection/material links after a swap because the replacement may
have different sockets. Keep the object's `Molecular Nodes` modifier attached to
its own modifier tree; do not link multiple molecule objects to one mutable
modifier tree unless shared state is intentional.
