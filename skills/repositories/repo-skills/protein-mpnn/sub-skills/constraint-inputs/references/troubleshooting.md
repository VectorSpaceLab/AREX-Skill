# Constraint Troubleshooting

## Positions Look Shifted Or Wrong

Cause: ProteinMPNN helper constraints use 1-based positions in the parsed chain sequence, not PDB residue IDs.

Fix:

- Inspect `seq_chain_<chain>` in the parsed JSONL.
- Map PDB numbering, insertion codes, and missing residues to parsed sequence positions before writing `position_list`.
- Do not pass zero-based positions; position `0` is invalid.

## `position_list` Does Not Match Chains

Cause: `position_list` is comma-separated per chain and follows `--chain_list` order.

Example:

```text
--chain_list "A C"
--position_list "1 2 3, 10 11"
```

This means chain `A` gets `[1, 2, 3]` and chain `C` gets `[10, 11]`. If chain `B` should also receive positions, include it in `--chain_list` and add a third comma-separated list.

## Designed Or Fixed Chains Are Not What The User Expected

Cause: `assign_fixed_chains.py --chain_list` names designed chains. All other parsed chains become fixed.

Fix:

- Validate `assigned_pdbs.jsonl`.
- Confirm every chain in the designed and fixed lists appears in the parsed target.
- If no `--chain_id_jsonl` is provided to ProteinMPNN, all chains may be designed depending on runtime settings.

## Design-Only Positions Were Interpreted Backwards

Cause: `make_fixed_positions_dict.py` normally treats `position_list` as fixed positions. The `--specify_non_fixed` flag inverts the meaning: listed positions are designable, and the output dictionary contains every other position as fixed.

Fix:

- Use `--specify_non_fixed` only for “design only these residues”.
- After generation, inspect the output fixed-position lists and confirm they are the complement of the requested design-only lists.

## Chain Names Do Not Match Parsed PDB Keys

Cause: Constraint files use chain ids from parsed keys like `seq_chain_A`, not necessarily the user’s intended biological labels.

Fix:

- Inspect parsed JSONL keys.
- Use the exact suffix after `seq_chain_` in `--chain_list`, fixed-position dictionaries, tied-position dictionaries, PSSM dictionaries, and omit dictionaries.

## Homooligomer Tied Positions Fail Or Produce Bad Ties

Cause: Homooligomer mode ties positions `1..L` across every parsed chain using the first chain length. It assumes equal chain lengths.

Fix:

- Validate with `--require-homooligomer-equal-length`.
- If chain lengths differ, create explicit tied-position groups only for aligned positions.
- Avoid tying chains that are not intended to share sequence/sampling constraints.

## Tied Positions Have Unequal List Lengths

Cause: Explicit tied positions pair by list index across chains.

Fix:

- Ensure every comma-separated list in `--position_list` has the same count.
- Validate positions are within each chain’s parsed length.
- For weighted positive/negative ties, ensure positions and beta lists have equal lengths.

## PSSM `.npz` Is Missing Chain Keys

Cause: `make_pssm_input_dict.py` expects every parsed chain to have `<chain>_coef`, `<chain>_bias`, and `<chain>_odds` in the target `.npz`.

Fix:

- For chain `B`, check for `B_coef`, `B_bias`, and `B_odds`.
- `B_coef` must be length `L`.
- `B_bias` and `B_odds` must have shape `[L, 21]`.
- If odds are unavailable but the workflow requires the helper, regenerate the `.npz` or add an intentional zero log-odds matrix with the correct shape.

## PSSM Bias Does Not Seem To Affect Design

Cause: PSSM strength depends on both per-residue `pssm_coef` and runtime `--pssm_multi`; `--pssm_bias_flag 1` is needed to use `pssm_bias` probabilities.

Fix:

- Confirm `pssm_coef` has nonzero values at intended residues.
- Use `--pssm_multi` greater than `0.0`.
- Include `--pssm_bias_flag 1` when using PSSM probability bias.
- Confirm `pssm_bias` rows have 21 numeric values and are probability-like.

## Amino-Acid Bias Has The Wrong Direction

Cause: Positive and negative signs are easy to invert.

Fix:

- Positive global or per-residue bias makes an amino acid more likely.
- Negative bias makes an amino acid less likely.
- Start with moderate values and increase only when stronger steering is needed.

## Per-Residue Bias Shape Fails

Cause: `--bias_by_res_jsonl` requires one `[21]` row per parsed residue per chain.

Fix:

- Count `len(seq_chain_<chain>)` in parsed JSONL.
- Ensure the bias matrix has exactly that many rows.
- Ensure every row has exactly 21 numeric values in alphabet order `ACDEFGHIKLMNPQRSTVWYX`.

## Invalid JSONL Or Multiple Dictionary Lines

Cause: Parsed-PDB JSONL and constraint dictionary JSONL have different conventions. Parsed files can have many lines; helper-generated constraint dictionaries generally contain a single JSON object on one line.

Fix:

- For parsed PDBs, allow one target object per line.
- For chain assignment, fixed positions, tied positions, bias-by-res, omit dictionaries, and PSSM dictionaries, keep one top-level dictionary on one non-empty line.
- Run `validate_constraint_jsonl.py` before `protein_mpnn_run.py`.

## Omit AA Utility Is Unsafe To Reuse Directly

Cause: The source `other_tools/make_omit_AA.py` is hard-coded and writes to a local path.

Fix:

- Use global `--omit_AAs` when possible.
- For per-residue omit constraints, generate the schema explicitly and validate chain names and positions.
- Do not copy local absolute paths or machine-specific output names into reusable workflows.
