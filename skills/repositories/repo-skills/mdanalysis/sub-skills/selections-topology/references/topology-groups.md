# Topology and Groups

MDAnalysis separates topology metadata from coordinates. Selection behavior depends on which topology attributes are present, what level they live at, and whether bonds/fragments were loaded or guessed.

## Group Objects

| Object | Typical source | Notes |
| --- | --- | --- |
| `AtomGroup` | `u.atoms`, indexing, slicing, `select_atoms()` | Central object for positions, topology attrs, group math, writing selections, and most analyses. |
| `ResidueGroup` | `u.residues`, `ag.residues` | Sorted unique residues represented by atoms in an `AtomGroup`. |
| `SegmentGroup` | `u.segments`, `ag.segments` | Sorted unique segments represented by atoms/residues. |
| `UpdatingAtomGroup` | `select_atoms(..., updating=True)` | AtomGroup-like object that re-evaluates lazily after trajectory frame changes. |

Group navigation is level-aware:

```python
ag = u.select_atoms("resname ALA")
residues = ag.residues
segments = ag.segments
atoms_again = residues.atoms
```

`ag.residues` and `ag.segments` return sorted unique higher-level groups, not a per-atom list.

## Indexing, Uniqueness, and Set-Like Operations

- `ag.indices`/`ag.ix` are zero-based topology indices.
- Slicing and fancy indexing preserve order and can preserve duplicates.
- `ag.unique` returns a sorted unique group.
- `ag.asunique(sorted=False)` removes duplicates while preserving first-seen order when possible.
- `ag + other` / `ag.concatenate(other)` preserves order and duplicates.
- `ag.union(other)`, `ag.intersection(other)`, `ag.difference(other)`, `ag.subtract(other)`, and `ag.symmetric_difference(other)` are set-like operations; use them when duplicates are not meaningful.
- Group equality compares atom identities and order; two groups from different universes are not interchangeable for selection `group` keywords.

## Splitting and Grouping

Useful topology-aware grouping helpers:

```python
for residue_atoms in ag.split("residue"):
    ...

by_resname = ag.groupby("resnames")
by_resname_and_mass = ag.groupby(["resnames", "masses"])
```

`split(level)` supports `"atom"`, `"residue"`, `"molecule"`, and `"segment"`. Molecule and fragment behavior require suitable topology connectivity.

`groupby(topattrs)` returns a dictionary keyed by attribute value or tuple of values. It requires the requested topology attributes to exist.

## Built-In Topology Attributes

Common atom-level attributes include:

- `names` / selector `name`
- `ids` / selector `id`
- `types` / selector `type`
- `elements` / selector `element`
- `masses` / selector `mass`
- `charges` / selector `charge`
- `formalcharges` / selector `formalcharge`
- `chainIDs` / selector `chainID`
- `record_types` / selector `record_type`
- `radii` / selector `radius`
- `tempfactors` / selector `tempfactor`
- `aromaticities` / selector `aromaticity`

Common residue-level attributes include `resids`/`resid`, `resnums`/`resnum`, `resnames`/`resname`, `icodes`/`icode`, and `molnums`/`molnum`. Common segment-level attributes include `segids`/`segid`.

Not every file format supplies every attribute. Accessing a missing attribute raises `NoDataError` or `AttributeError` depending on the attribute path and context.

## Adding Built-In Attributes

Use `Universe.add_TopologyAttr()` to attach built-in attributes:

```python
u.add_TopologyAttr("masses", values=[12.0, 1.0, 16.0])
u.add_TopologyAttr("charges")  # blank/zero defaults when supported
```

Rules:

- Values must match the intrinsic level length: atom attributes need `n_atoms`, residue attributes need `n_residues`, and segment attributes need `n_segments`.
- Built-in names are plural (`"masses"`, `"resnames"`, `"segids"`), while selection tokens are usually singular (`mass`, `resname`, `segid`).
- Unknown attribute names raise `ValueError` with the recognized names list.

## Custom Topology Attributes

Subclass `AtomAttr`, `ResidueAttr`, or `SegmentAttr` to add custom data. Selectable custom attributes need a singular name and supported dtype.

```python
from MDAnalysis.core.topologyattrs import AtomAttr

class IsLigand(AtomAttr):
    attrname = "is_ligands"
    singular = "is_ligand"
    dtype = bool

u.add_TopologyAttr(IsLigand([False, True, True, False]))
ligand_atoms = u.select_atoms("is_ligand")
```

Float and integer custom attributes support inclusive ranges:

```python
class Scores(AtomAttr):
    attrname = "scores"
    singular = "score"
    dtype = float

u.add_TopologyAttr(Scores([0.1, 0.5, 1.0, 2.0]))
mid = u.select_atoms("score 0.5 to 1.5")
```

If a dtype is unsupported, class creation can warn that no selection keyword could be generated, or direct selector generation can raise `ValueError`. The attribute can still be useful for direct Python access if implemented correctly.

## Coordinates as Group Data

`AtomGroup.positions` reads/writes the current trajectory frame positions. Coordinate-based selectors (`prop`, `around`, `point`, zones/layers) are frame-dependent.

- `u.dimensions` controls periodic box behavior for geometric selectors when `periodic=True`.
- `center_of_geometry()`, `center_of_mass()`, and related compound options rely on topology/coordinate data. `center_of_mass()` requires masses.
- Route numerical distance matrices and analysis algorithms to `../../analysis-workflows/SKILL.md`.

## Bonds, Fragments, and Molecules

Connectivity-sensitive APIs require bonds:

- `u.bonds` / `ag.bonds` expose topology bonds when loaded or added.
- `ag.fragments` and `same fragment as ...` need bond information.
- `bonded selection` returns atoms bonded to a selection; without bonds it returns empty for selection language and many direct fragment operations raise `NoDataError`.
- `wrap()`/`unwrap()` with compound values such as `fragments` or `molecules` can require bonds or molnums; route coordinate transformation workflows to `../../transformations-writing/SKILL.md`.

Add bonds explicitly when known:

```python
u.add_TopologyAttr("bonds", [(0, 1), (1, 2)])
connected = u.select_atoms("same fragment as index 0")
```

## Topology Guessing

`MDAnalysis.topology.guessers` provides legacy helper functions for deriving missing attributes from names/coordinates:

```python
from MDAnalysis.topology.guessers import guess_types, guess_masses, guess_bonds

elements_or_types = guess_types(u.atoms.names)
u.add_TopologyAttr("types", elements_or_types)
u.add_TopologyAttr("masses", guess_masses(elements_or_types))
```

Important caveats:

- Element/type guessing from atom names is heuristic and can be wrong for virtual sites, unusual naming conventions, coarse-grained beads, or ambiguous atom names.
- `guess_masses()` validates atom types and can raise `ValueError` for unknown types; `get_atom_mass()` returns `0.0` for unknown elements.
- `guess_bonds(atoms, coords, box=None, vdwradii=None, fudge_factor=0.55, lower_bound=0.1)` uses distance cutoffs from van der Waals radii and can miss/overcreate bonds. Provide `vdwradii` for unusual types.
- Guessed bonds are not chemically validated; check results before using fragments, molecules, or bonded selections.
- Some newer Universe construction paths expose `to_guess`/`force_guess` options; route file-loading decisions to `../../universe-io/SKILL.md`.

## Safe Synthetic Universe Pattern

For examples and probes, avoid source repo test data and create minimal systems:

```python
import MDAnalysis as mda

u = mda.Universe.empty(
    6,
    n_residues=3,
    n_segments=1,
    atom_resindex=[0, 0, 1, 1, 2, 2],
    residue_segindex=[0, 0, 0],
    trajectory=True,
)
u.add_TopologyAttr("names", ["N", "CA", "C", "O", "OW", "HW"])
u.add_TopologyAttr("resnames", ["ALA", "ALA", "SOL"])
u.add_TopologyAttr("resids", [1, 2, 3])
u.add_TopologyAttr("segids", ["SYS"])
```

Use this pattern in generated validation scripts; do not reference original checkout files or bundled MDAnalysis test data.
