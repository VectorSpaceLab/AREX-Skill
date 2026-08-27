# Reaction Data Formats

This reference covers the text formats used by DGL-LifeSci WLN reaction center prediction and candidate ranking.

## Raw Reaction Files

A raw custom reaction file has one reaction SMILES per non-empty line:

```text
[CH3:1][Cl:2].[OH:3]>>[CH3:1][OH:3]
```

Required structure:

- Use `>>` exactly once to separate reactants from products.
- Put reactants on the left and product on the right.
- Separate multiple reactants with `.`.
- Provide atom mapping numbers such as `:1`, `:2`, `:3` for atoms participating in the mapped reaction.
- Prefer consecutive atom-map numbers starting at 1. Non-consecutive maps can trigger molAtomMapNumber failures inside WLN preprocessing.
- Keep one reaction per line. Blank lines should be removed before dataset construction.

DGL-LifeSci's WLN preprocessing uses RDKit to compute graph edits from mapped reactant/product bonds, then stores processed lines with the original reaction plus edit labels.

## Processed Reaction Files

A processed reaction line contains the reaction and its graph edits separated by whitespace:

```text
[CH3:1][Cl:2].[OH:3]>>[CH3:1][OH:3] 1-2-0.0;1-3-1.0
```

Graph edit fields:

- `atom1-atom2-change_type` records one changed atom pair.
- Atom ids are one-based atom-map numbers in the text file.
- `change_type=0.0` means bond loss.
- `change_type=1.0`, `2.0`, `3.0`, and `1.5` mean forming single, double, triple, and aromatic bonds.
- Multiple edits are separated by `;`.

Typical file names from custom center preprocessing:

- `train_valid_reactions.proc`
- `train_invalid_reactions.proc`
- `val_valid_reactions.proc`
- `val_invalid_reactions.proc`
- `test_valid_reactions.proc`
- `test_invalid_reactions.proc`

For ranking, use the valid processed file matching the candidate-bond file. Do not feed invalid processed rows into `WLNRankDataset`.

## Candidate Bond Files

A candidate-bond file has one line per processed reaction. Each line contains semicolon-delimited candidate bond changes:

```text
1 2 0.0 4.317;1 3 1.0 3.902;
```

Candidate fields:

- `atom1 atom2 change_type score` separated by spaces.
- Atom ids are one-based map numbers in the file; datasets convert them to zero-based internally.
- `change_type` uses the same values as graph edits: `0.0`, `1.0`, `2.0`, `3.0`, `1.5`.
- `score` is a numeric center-model score.
- A trailing semicolon is accepted and is how the rexgen-direct utility writes rows.

Alignment rules:

- The number of candidate-bond lines must equal the number of processed reaction lines.
- Keep line order unchanged between processed reactions and candidate bonds.
- Empty candidate lines are syntactically allowed but usually mean no candidate products can be ranked for that reaction.

## Size and Candidate Cutoffs

Ranking data construction applies several cutoffs:

| Field | Default | Effect |
| --- | --- | --- |
| `size_cutoff` | `100` | `WLNRankDataset.ignore_large(True)` skips reactions whose reactants contain more atoms than this cutoff. |
| `max_num_changes_per_reaction` | `5` | Enumerates candidate product combos up to this many bond changes. |
| `num_candidate_bond_changes` | `16` | Keeps this many candidate bond changes after filtering impossible/no-op changes. |
| `max_num_change_combos_per_reaction` | `150` or `1500` | Caps valid candidate product combos for train/eval. |

If a request has `size_cutoff`, `num_candidate_bond_changes`, or `max_num_change_combos_per_reaction` mismatched between candidate generation and ranking, expect missing ground-truth products, low `gfound`, or unexpectedly empty candidate batches.

## Validation Expectations

The bundled helper performs cheap text-level checks only. It intentionally does not require DGL-LifeSci, DGL, Torch, RDKit, downloads, or pretrained models.

Use it to catch:

- Missing `>>` separators.
- Empty reactant/product sides.
- Suspicious whitespace in reaction strings.
- Missing atom-map markers when requested.
- Very long lines that should be reviewed before expensive preprocessing.
- Malformed processed graph edits.
- Malformed candidate-bond records.
- Mismatched reaction/candidate row counts.

After text validation passes, rely on `WLNCenterDataset(..., check_reaction_validity=True)` for chemistry-aware RDKit validation and for writing valid/invalid processed splits.

## Common Minimal Fixtures

A tiny raw fixture can be useful for validating command wiring but is not a chemically complete benchmark:

```text
[CH3:1][Cl:2].[OH:3]>>[CH3:1][OH:3]
[CH3:1][Br:2].[NH2:3]>>[CH3:1][NH2:3]
```

A matching processed/candidate pair for testing text alignment could look like:

```text
[CH3:1][Cl:2].[OH:3]>>[CH3:1][OH:3] 1-2-0.0;1-3-1.0
[CH3:1][Br:2].[NH2:3]>>[CH3:1][NH2:3] 1-2-0.0;1-3-1.0
```

```text
1 2 0.0 4.0;1 3 1.0 3.5;
1 2 0.0 4.1;1 3 1.0 3.4;
```

Use these only for parser and flow checks; they are not a substitute for RDKit/DGL dataset construction or model validation.
