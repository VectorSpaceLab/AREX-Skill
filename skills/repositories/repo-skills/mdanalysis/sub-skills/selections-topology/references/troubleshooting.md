# Troubleshooting Selections and Topology

## `SelectionError` or Unexpected Token

Symptoms:

- `SelectionError: Unknown selection token: ...`
- `SelectionError: Unexpected token at end of selection string: ...`
- `SelectionError: Selection failed: ...`

Checks:

1. Confirm the selector keyword exists and matches case exactly.
2. Add parentheses around mixed `and`/`or` expressions.
3. Ensure numeric ranges are parseable: use `resid 1:5`, `resid 1 to 5`, or `mass -5 - -3`.
4. Escape literal values that collide with selection keywords, for example `resname \water`.
5. For custom topology attributes, confirm the class defines `singular`, `attrname`, and a supported `dtype`.

## Empty Selection from Case or Missing Attribute

Symptoms:

- `u.select_atoms("resname sol")` returns zero atoms though solvent exists.
- `u.select_atoms("element H")` fails or returns empty for a topology without elements.

Checks:

1. Inspect actual values with `set(u.atoms.resnames)`, `set(u.atoms.names)`, or the relevant attribute.
2. Remember string values are case-sensitive.
3. Add missing attributes if they can be determined safely: `u.add_TopologyAttr("elements", values)`.
4. Use topology guessing only when heuristic errors are acceptable and documented.

## Reordered or Deduplicated AtomGroup

Symptoms:

- A manually ordered group like `u.atoms[[5, 1, 0]]` becomes `[0, 1, 5]` after selection.
- Duplicate atoms disappear.

Cause:

- Selection results are unique and sorted by topology index by default.

Fixes:

```python
ordered = u.atoms[[5, 1, 0]]
kept = ordered.select_atoms("all", sorted=False)
```

For duplicates, avoid selection language and use slicing or concatenation (`ag1 + ag2`) because selections intentionally remove duplicates.

## Geometric Selection Includes/Excludes Surprising Atoms

Symptoms:

- `around`, `point`, `sphzone`, or `cyzone` results differ from raw Euclidean intuition.

Checks:

1. Inspect `u.dimensions`; geometric selections use periodic minimum-image behavior by default.
2. Retry with `periodic=False` if the task describes nonperiodic Cartesian distances.
3. Verify coordinates are in the expected current trajectory frame.
4. Verify the reference selection is nonempty and, for `around`, remember atoms in the reference selection are excluded from the result.

Route distance-matrix validation or algorithmic analysis to `../../analysis-workflows/SKILL.md`.

## Missing Topology Attributes

Symptoms:

- `NoDataError` or `AttributeError` for `masses`, `charges`, `elements`, `bonds`, `fragments`, `molnums`, etc.
- Selection token exists but cannot evaluate because the universe lacks the attribute.

Fixes:

1. Check `hasattr(u.atoms, "masses")` or attempt direct access in a small `try`/`except`.
2. Add known values with `u.add_TopologyAttr("masses", values)`.
3. For built-ins, pass plural attribute names to `add_TopologyAttr()` and singular names in selection text.
4. For connectivity, add known bonds with `u.add_TopologyAttr("bonds", pairs)` before using fragments or bonded selections.
5. Do not fabricate scientific topology data silently; record when attributes are guessed.

## Custom Topology Attribute Selection Fails

Symptoms:

- `Unknown selection token: 'is_ligand'` after adding custom data.
- `ValueError: No base class defined for dtype ...`.
- Size mismatch errors while adding or setting values.

Fixes:

1. Subclass the correct level: `AtomAttr` for per-atom data, `ResidueAttr` for per-residue data, `SegmentAttr` for per-segment data.
2. Define `attrname` as the plural access name and `singular` as the selection token.
3. Use supported `dtype` values: `bool`, integer, float, string/object.
4. Supply values matching the target level length.
5. Use ranges for float selectors: `score 0.5 to 1.5`; exact float equality emits `SelectionWarning` and uses `rtol`/`atol`.

## SMARTS / RDKit Optional Dependency Problems

Symptoms:

- `smarts ...` raises import/converter errors.
- SMARTS returns too few atoms with a max-match warning.
- Chirality or aromaticity does not match expectations.

Fixes:

1. Confirm RDKit is installed in the runtime environment.
2. Ensure topology has enough chemical metadata for RDKit conversion; bonds/elements/formal charges may be needed.
3. Pass converter options through `rdkit_kwargs`, for example `rdkit_kwargs={"force": True}` when appropriate.
4. Increase `smarts_kwargs={"maxMatches": ...}` if MDAnalysis warns the default cap was reached.
5. Route RDKit converter setup and optional dependency installation to `../../formats-converters/SKILL.md`.

## Float Range Precision

Symptoms:

- `mass 0.3` matches more/fewer atoms than expected.
- A `SelectionWarning` recommends ranges and `rtol`/`atol`.

Fixes:

- Prefer inclusive ranges: `mass 0.299 to 0.301`.
- Use `rtol=0, atol=0` only when exact binary equality is required.
- For generated code, make tolerance choices explicit and explain why.

## Updating Selection Cost or Staleness

Symptoms:

- A loop over frames is slow.
- A selection updates when it should be static, or a sliced updating group no longer updates.

Fixes:

1. Use `updating=True` only for frame-dependent selections (`prop`, geometric selections, or selections chained to moving groups).
2. Cache static topology selections once outside the trajectory loop.
3. Remember updating groups update lazily when accessed after frame changes, not when `next(u.trajectory)` is called.
4. Slicing an updating group returns a static `AtomGroup`; recreate the updating selection if dynamic behavior is required.
5. For expensive geometric updating selections, consider a more targeted reference group or a dedicated analysis workflow in `../../analysis-workflows/SKILL.md`.

## Exporter Format Errors

Symptoms:

- `NotImplementedError: Writing as ... is not implemented`.
- Output uses unexpected index base.

Fixes:

1. Use extensions or default formats recognized by `MDAnalysis.selections`: Gromacs/`ndx`, CHARMM/`str`, PyMol/`pml`, VMD, and Jmol/`spt`.
2. Check the target tool's expected index base. Gromacs/CHARMM/PyMOL writers use 1-based terms; VMD/Jmol output uses zero-based atom indices.
3. For coordinate/topology writers rather than selection exporters, route to `../../universe-io/SKILL.md`.
