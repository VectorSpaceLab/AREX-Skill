# Target data formats

## Seven-key target JSON

BindCraft target settings are a JSON object with exactly these operational
keys:

| Key | Type and meaning | Validation and use |
|---|---|---|
| `design_path` | string; directory for designs and statistics | Must be writable by the launch user. It is a destination, not an input PDB. The validator reports the path and does not create it. |
| `binder_name` | non-empty string; prefix for generated binder file/design names | Use a stable, filesystem-safe name without path separators. BindCraft combines it with length/seed/model labels. |
| `starting_pdb` | string; path to the target PDB | Must identify the intended target at launch. The validator reports absolute repository-specific paths rather than requiring them to exist; use an explicit `--pdb` to inspect a portable copy. |
| `chains` | non-empty string; comma-separated target chain IDs | These are the chains targeted by BindCraft; other PDB chains are ignored by the design input. Whitespace around comma-separated IDs is accepted by the validator and normalized for checking. |
| `target_hotspot_residues` | `null` or string; target site selector | `null` lets AF2 select a binding site. A string selects residue numbers/ranges or complete chains; see hotspot syntax below. |
| `lengths` | two-element integer array `[minimum, maximum]` | BindCraft samples the inclusive integer range from `min` through `max`; require positive values and `minimum <= maximum`. |
| `number_of_final_designs` | positive integer | Stop target for designs passing all configured filters; it is not a guarantee that this many designs will be found. |

A compact, portable template:

```json
{
  "design_path": "./bindcraft-runs/target-1/",
  "binder_name": "target1",
  "starting_pdb": "./inputs/target1_trimmed.pdb",
  "chains": "A",
  "target_hotspot_residues": "56",
  "lengths": [65, 150],
  "number_of_final_designs": 100
}
```

The checked-in PDL1 example uses the same schema. Replace its target and
output paths with paths valid on the launch host; never copy paths from a
notebook, another user's machine, or a source checkout into a new run.

## Chains and PDB assumptions

- The input is a PDB file that can be parsed by the BindCraft/ColabDesign
  stack. Chain IDs are taken from the PDB chain column; the validator reports
  chains and standard amino-acid residue identifiers it can parse.
- `chains` is a comma-separated selection, such as `A` or `A,B`. Select only
  target chains; do not include the designed binder chain in the starting
  target PDB.
- Residue numbers are the PDB author residue numbers, not zero-based sequence
  indexes. Insertion codes are preserved in summaries, but hotspot range
  validation is intentionally conservative around insertion-coded residues.
- Keep standard amino-acid ATOM records and the coordinates needed for the
  target surface. Heteroatoms, waters, alternate locations, malformed records,
  missing backbone atoms, non-contiguous numbering, and unresolved biological
  assembly questions need target-specific review; a parser pass does not prove
  structural suitability.
- A trimmed target can reduce runtime and GPU memory, but remove only regions
  that are not required for the intended interface or structural context.
  Compare the resulting chain/residue summary with the source structure before
  launching.
- The bundled PDL1 evidence contains one chain (`A`) and standard residues.
  numbered 18 through 132 (115 distinct residue IDs). It is a fixture for
  inspection, not a required runtime path.

## Hotspot syntax

BindCraft's documented forms are strings:

| Form | Meaning | Example |
|---|---|---|
| `null` | Let AF2 choose the binding site | `"target_hotspot_residues": null` |
| Single or comma-separated residue numbers | Residues on the selected target chain(s) | `"56"` or `"56,60,61"` |
| Numeric ranges | Inclusive residue ranges | `"2-10"` or `"56-60"` |
| Chain-qualified ranges/residues | Disambiguate a multi-chain target | `"A1-10,B1-20"` or `"A56,B60-61"` |
| Chain ID alone | Entire chain as the hotspot selection | `"A"` |

Use no spaces inside a chain-qualified token (`A1-10`, not `A 1-10`), and use
comma separators between tokens. The source documents do not define a stable
meaning for negative residue numbers, insertion-code hotspot tokens, or
mixed/unqualified tokens across multiple chains; avoid those forms unless the
installed ColabDesign parser has been tested for the exact target. A selected
hotspot must belong to a selected target chain and its residue number must be
present in the PDB. A range is inclusive and should be checked before launch.
An empty string is not the preferred representation; use JSON `null` when no
site is specified. (The pipeline currently treats an empty hotspot string as
no hotspot, but `null` is clearer and portable.)

Examples:

```json
"chains": "A",
"target_hotspot_residues": "56"
```

```json
"chains": "A,B",
"target_hotspot_residues": "A56-60,B102,B110-112"
```

```json
"chains": "A,B",
"target_hotspot_residues": "A"
```

For an unconstrained site:

```json
"chains": "A",
"target_hotspot_residues": null
```

## Output paths and names

Use a separate, empty-or-new `design_path` per campaign so trajectory,
MPNN, accepted, rejected, and CSV artifacts cannot be confused with another
run. Ensure the launching account can traverse the parent and write the
folder. Use `binder_name` as a label, not a path; avoid `/`, `\\`, control
characters, and ambiguous whitespace. A validator warning about an absolute
or repository-looking path is a portability reminder, not a requirement to
make that path exist.
