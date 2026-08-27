---
name: molecules-and-styles
description: "Load static MolecularNodes structures, compose geometry-node
  styles and selections, and control named attributes, colors, materials, and
  converter-backed molecule imports in a Blender 5.2 host."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Molecules and styles

Use this sub-skill for the static-structure path of MolecularNodes: create a
Universe-backed `Molecule`, load a local PDB/mmCIF/BCIF/SDF/MOL file or fetch a
structure, then build one or more visible style branches with selections,
attributes, colors, and materials. The runtime is Blender 5.2 (or a compatible
`bpy` 5.2 host); pure Python helpers do not replace that host for object, mesh,
Geometry Nodes, or material work.

## Route here for

- `Molecule(universe, ...)`, `Molecule.from_file(...)`, `Molecule.load(...)`, and
  `Molecule.fetch(...)` for static structures and file-backed multi-model input.
- `add_style()` with `spheres`, `sticks`, `ball_and_stick`, `cartoon`, `ribbon`,
  or `surface`, including style keyword arguments and material assignment.
- MDAnalysis selection strings, `AtomGroup` selections, existing boolean named
  attributes, and managed selection recovery.
- `with mol.tree:` composition, `tree.reset()` clean-slate composition, reusable
  `atoms`/`join` sockets, `SetColor`, named attributes, and style-node inspection.
- MolecularNodes material presets, custom nodebpy materials, IUPAC/chain/PLDDT
  color helpers, and Biotite-to-MDAnalysis static structure conversion.

## Do not handle here

- Frame playback, streaming trajectories, dynamic trajectory calculations, or
  trajectory-specific interpolation: route to
  [trajectories-and-annotations](../trajectories-and-annotations/SKILL.md).
- Annotation objects, labels, measurements, or annotation visibility: route to
  [trajectories-and-annotations](../trajectories-and-annotations/SKILL.md).
- EM density, CellPack, STAR ensembles, and density-specific node trees: route to
  [density-and-ensembles](../density-and-ensembles/SKILL.md).
- `Canvas`, cameras, render engines, snapshots, compositor, and render output:
  route to [scene-and-rendering](../scene-and-rendering/SKILL.md).

## Operating workflow

1. **Confirm the host and input.** Run molecule/object/node/material operations in
   Blender 5.2 with the MolecularNodes assets available. For deterministic checks,
   prefer a local fixture and `Molecule.load(path)`; use `fetch(code, cache=...)`
   only when the cache or network is intentionally available.
2. **Choose the loader.** Use `Molecule(universe)` when an MDAnalysis Universe
   already exists, `from_file(path_or_supported_BytesIO)` for one structure file,
   `load(topology, coordinates=None)` for a convenient file/MD split, and
   `fetch(code, format='.bcif', cache=..., database='rcsb')` for a database source.
   See [molecule API](references/molecule-api.md).
3. **Check the object before styling.** A successful load creates a Blender mesh,
   standard attributes, and the `Molecular Nodes` modifier unless object creation
   was explicitly disabled on the topology-plus-coordinates route. Inspect
   `mol.universe`, `mol.object`, `mol.modifier_node_tree`, and
   `mol.list_attributes(drop_hidden=False)` before adding branches.
4. **Start simple or take control.** Call `mol.add_style(style, selection=..., material=...,
   **kwargs)` for an append-only style. Use `with mol.tree.reset() as (atoms, join):`
   only when intentionally discarding the current tree. Use `with mol.tree as tree:`
   to preserve branches and reuse the existing geometry input and final join.
5. **Make selection semantics explicit.** A string is first checked as an existing
   boolean attribute, then parsed as an MDAnalysis selection phrase. An `AtomGroup`
   becomes a managed named selection. Validate selection strings before relying on a
   branch; an invalid `add_style` string warns and creates an unmasked branch.
6. **Attach color and material at the right layer.** Use a geometry color node and
   `SetColor` to modify the `Color` field before a style, or let a style consume the
   stored field. Pass a preset instance, its `.material`, a Blender material, an
   asset material name, or `None` according to the style contract. See the material
   and color reference.
7. **Validate the result in the host.** Confirm style nodes feed one final join,
   the style selection input is driven by the intended `Named Attribute`, material
   sockets point to the intended datablock, and evaluated geometry contains the
   expected attributes. Run the local fixture cases in the verification section of
   [troubleshooting](references/troubleshooting.md).

## Canonical recipes

### Append two independent representations

```python
import molecularnodes as mn

mol = mn.Molecule.load("1BNA.cif")
mol.add_style("cartoon", selection="protein", material="MN Ambient Occlusion")
mol.add_style(
    "surface",
    selection="resid 1:20",
    material=mn.material.TransparentOutline(alpha=0.45),
    quality=2,
)
```

Each call appends a branch to the same tree. Do not call `tree.reset()` between
these calls unless the first branch is meant to be removed.

### Compose a clean custom tree

```python
from molecularnodes.nodes import geometry as g

mat = mn.material.AmbientOcclusion(distance=0.5)
with mol.tree.reset() as (atoms, join):
    atoms >> g.SetColor(color=g.ColorElement()) >> g.StyleCartoon(
        quality=3, material=mat.material
    ) >> join
```

`reset()` returns the input and join sockets that belong to the new tree. Use
`with mol.tree` instead for incremental edits.

### Recover a managed selection without losing existing branches

```python
sel = mol.selections.from_string("resid 1:10", name="focus")
mol.add_style("spheres", selection=sel.name)
sel.string = "not a valid selection"   # message is set; last good mask remains
sel.string = "resid 1:5"                # message clears; attribute is updated
```

If `add_style(selection="bad syntax")` has already warned, leave existing style
branches intact, create a valid managed selection, and append a corrected branch.
Inspect or remove the bad branch explicitly rather than resetting the whole tree.

## Contracts and references

- [Molecule API and loading](references/molecule-api.md) — constructors,
  loader distinctions, converter inputs, attributes, and local-file checks.
- [Styles, selections, and nodes](references/styles-selections-and-nodes.md) —
  accepted styles, selection forms, tree lifecycle, node signatures, and branch
  validation.
- [Materials and colors](references/materials-and-colors.md) — preset signatures,
  material ownership, color helpers, and node-based coloring.
- [Troubleshooting and validation](references/troubleshooting.md) — failure
  recovery, Blender context checks, synthetic hard cases, and fixture assertions.

When a workflow crosses a boundary, preserve the `Molecule` object and named
attribute names in the handoff so the sibling skill can continue without rebuilding
the structure or destroying its style tree.
