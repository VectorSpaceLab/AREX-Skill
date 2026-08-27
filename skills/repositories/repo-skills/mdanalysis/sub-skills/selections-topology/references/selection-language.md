# Selection Language

`Universe.select_atoms()` delegates to `Universe.atoms.select_atoms()`. The verified public signature is:

```python
AtomGroup.select_atoms(
    sel, *othersel, periodic=True, rtol=1e-05, atol=1e-08,
    updating=False, sorted=True, rdkit_kwargs=None, smarts_kwargs=None,
    **selgroups,
)
```

It returns an `AtomGroup` by default, or an `UpdatingAtomGroup` when `updating=True`.

## Parse Model

- Selection keywords and values are case-sensitive: `resname SOL` and `resname sol` are different queries.
- Selections are tokenized on whitespace and parentheses. Use spaces around numeric ranges when needed: `mass -5 - -3`, `mass -5: -3`, and `mass -5 to -3` are valid range styles.
- `and` and `or` are both parser operations with the same precedence in current MDAnalysis. Use parentheses for mixed boolean expressions, for example `protein and not (resname ALA or resname LYS)`.
- Multiple values after many simple selectors are treated as alternatives: `resname MET GLY` is equivalent to `resname MET or resname GLY`.
- An empty selection string returns an empty `AtomGroup` and emits a `UserWarning`.
- Unknown tokens or malformed expressions raise `MDAnalysis.exceptions.SelectionError`.

## Core Keywords

| Selector | Meaning and notes |
| --- | --- |
| `all` | All atoms in the current group; unique and sorted unless `sorted=False` is used where supported by the final selection application. |
| `name`, `type`, `resname`, `segid`, `chainID`, `record_type`, `element`, `moltype`, `formalcharge` | Match topology attributes when present. Attribute names/values are topology-dependent. |
| `resid`, `resnum` | Inclusive integer ranges with `:`, `-`, or `to`; `resid` honors insertion codes when present. |
| `bynum`, `index` | Atom number ranges; `bynum` is 1-based and `index` is 0-based. |
| `protein`, `backbone`, `nucleic`, `nucleicbackbone`, `water` | Hard-coded residue/name definitions; nonstandard residue names can be missed. |
| `smarts` | RDKit-backed SMARTS query. Requires RDKit and converter-compatible topology information. |
| `chiral` | Selects recognized `R` or `S` stereocenters where chirality is available. |

String selectors use shell-style patterns from `fnmatch`: `*`, `?`, `[seq]`, and `[!seq]`. If a literal value collides with a selection keyword, escape it with a backslash, for example `resname \water`.

## Boolean and Grouping

- Combine with `not`, `and`, `or`, and parentheses.
- Prefer explicit parentheses in reusable skills or generated code: `segid SYS and not (name H* or name OW)`.
- `byres selection` expands to atoms in the same residue/segment as the matched atoms.
- `same <property> as <selection>` expands by shared property; common properties include `residue`, `segment`, `resname`, `name`, `type`, `mass`, coordinates (`x`, `y`, `z`), and `fragment` when bonds are available.
- `bonded selection` selects atoms bonded to the matched atoms; it returns empty when no bonds exist.

## Geometric Selections

| Selector | Pattern |
| --- | --- |
| `around` | `around <distance> <selection>` selects atoms within a cutoff of another selection, excluding atoms in the reference selection. |
| `point` | `point <x> <y> <z> <distance>` selects atoms within a cutoff of a coordinate. |
| `prop` | `prop [abs] x|y|z <operator> <value>` supports `<`, `>`, `<=`, `>=`, `==`, `!=`. |
| `sphzone`, `sphlayer`, `isolayer` | Spherical/isosurface zones around the center of geometry or around each reference atom depending on selector. |
| `cyzone`, `cylayer` | Cylindrical zones/layers centered on the reference center of geometry. |

Geometric selectors use `periodic=True` by default and consult `group.dimensions` when available. Set `periodic=False` when a prompt describes raw Cartesian distances without minimum-image behavior, or when a missing/wrong unit cell causes surprising matches.

## Sorting, Duplicates, and Order

Selection results are unique and sorted by topology index by default. This prevents duplicate atoms from complex expressions but surprises users who build ordered atom lists for angles/dihedrals.

```python
ordered = u.atoms[[5, 1, 0]]
ordered.select_atoms("all").indices                 # [0, 1, 5]
ordered.select_atoms("all", sorted=False).indices   # [5, 1, 0]
```

Guidelines:

- Use `sorted=False` when selecting within an already ordered unique group and you need to keep that order.
- Use slicing or concatenation (`ag1 + ag2`) when duplicate atoms are meaningful; set-like group operations remove duplicates.
- Passing multiple selection strings (`select_atoms("name N", "name CA")`) appends the independently selected results and is useful when order matters between selection clauses.

## Selection Groups and `global`

Pass existing `AtomGroup` objects through keyword arguments and reference them with `group <name>`:

```python
active_site = u.select_atoms("resid 10:20")
shell = u.select_atoms("around 4.0 group active", active=active_site)
```

Rules:

- `selgroups` values must be `AtomGroup` instances; passing `Atom`, `Residue`, lists, or arrays raises `TypeError`.
- The reserved group name `updating` cannot be used.
- When calling `select_atoms()` from a subset `AtomGroup`, ordinary selections are restricted to that subset.
- Prefix with `global` to evaluate against the whole universe, for example `lipids.select_atoms("around 10 global protein")`.
- `global group active` bypasses the caller subset intersection for the referenced group.

## Updating Selections

`updating=True` returns an `UpdatingAtomGroup` that lazily re-evaluates when accessed after the trajectory frame changes.

Use it for frame-dependent expressions such as:

```python
shell = u.select_atoms("resname SOL and around 3.5 protein", updating=True)
```

Important behavior:

- Updating selections can be chained from other updating groups, and the dependency updates propagate.
- Slicing an `UpdatingAtomGroup` or calling `select_atoms()` without `updating=True` returns a static `AtomGroup`.
- Updating groups cache until frame state changes; they still cost more than static selections when accessed repeatedly over many frames.
- Avoid `updating=True` for selections based only on static topology attributes such as `resname`, `name`, or `resid`.

## Attribute Selections

The singular name of a topology attribute becomes a selector when the attribute has a supported dtype:

| Dtype | Selector behavior |
| --- | --- |
| `bool` | `myflag`, `myflag True`, and `myflag False`; missing value defaults to `True`. |
| integer | Exact values or inclusive ranges: `resid 1:5`, `myint 1 to 3`. |
| float | Exact value with `np.isclose()` using `rtol`/`atol`, or inclusive ranges; prefer ranges. |
| string/object | Exact values and wildcard patterns. |

Float equality emits `SelectionWarning` because binary precision can make exact-looking values ambiguous. Prefer `mass 0.29 to 0.31` or pass explicit `rtol=0, atol=0` only when exact equality is intentional.

## SMARTS and RDKit

`smarts <query>` uses the RDKit converter internally:

```python
atoms = u.select_atoms(
    "smarts [#7;R]",
    rdkit_kwargs={"force": True},
    smarts_kwargs={"maxMatches": 5000},
)
```

Operational notes:

- RDKit must be installed; route converter setup or RDKit conversion details to `../../formats-converters/SKILL.md`.
- `rdkit_kwargs` are forwarded to the MDAnalysis RDKit converter.
- `smarts_kwargs` are forwarded to RDKit `GetSubstructMatches`; default `maxMatches` is `max(1000, 10 * n_atoms)`.
- A warning about max matches means the SMARTS result may be truncated; increase `smarts_kwargs={"maxMatches": ...}`.
- SMARTS results are combined into one unique atom set.

## Selection Exporters

MDAnalysis can write an `AtomGroup` selection for external tools:

```python
protein_ca = u.select_atoms("protein and name CA")
protein_ca.write("ca_selection.ndx", name="CA")
```

Supported writer families are registered by `MDAnalysis.selections` and include:

| Format | Typical output |
| --- | --- |
| Gromacs / `ndx` | GROMACS index groups with 1-based atom ids. |
| CHARMM / `str` | CHARMM `DEFINE ... SELECT` terms using `BYNUM`. |
| PyMol / `pml` | PyMOL `select` expressions. |
| VMD | VMD atom selection macro using zero-based `index`. |
| Jmol / `spt` | Jmol script selection. |

Use `MDAnalysis.selections.get_writer(filename, defaultformat)` for explicit writer-class lookup. Unsupported formats raise `NotImplementedError`. This sub-skill owns selection exporter guidance; route coordinate/topology file writing to `../../universe-io/SKILL.md`.
