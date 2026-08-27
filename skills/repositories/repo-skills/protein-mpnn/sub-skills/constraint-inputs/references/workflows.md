# Constraint Workflows

These workflows assume commands are run from a ProteinMPNN checkout and write intermediate files under `constraints/`. Adapt file names and folders, but keep the same JSONL shapes.

## Design Chains A/C, Fix Specific Positions

Use this when the user says “design chains A and C, but keep these residues fixed.”

```bash
mkdir -p constraints outputs

python helper_scripts/parse_multiple_chains.py \
  --input_path data/pdbs/ \
  --output_path constraints/parsed_pdbs.jsonl

python helper_scripts/assign_fixed_chains.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/assigned_pdbs.jsonl \
  --chain_list "A C"

python helper_scripts/make_fixed_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/fixed_pdbs.jsonl \
  --chain_list "A C" \
  --position_list "1 2 3 4 5 6 7 8 23 25, 10 11 12 13 14 15 16 17 18 19 20 40"

python "$SKILL_DIR/scripts/validate_constraint_jsonl.py" \
  --parsed constraints/parsed_pdbs.jsonl \
  --chain-id constraints/assigned_pdbs.jsonl \
  --fixed-positions constraints/fixed_pdbs.jsonl
```

Then route to `../inference-design/` for the `protein_mpnn_run.py` command using `--jsonl_path`, `--chain_id_jsonl`, and `--fixed_positions_jsonl`.

## Design Only Listed Positions

Use this when the user says “only mutate these positions; leave everything else fixed.” The helper flag is intentionally inverted: `--specify_non_fixed` means the provided lists are designable positions, and the output dictionary contains all other positions as fixed.

```bash
python helper_scripts/make_fixed_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/fixed_pdbs.jsonl \
  --chain_list "A C" \
  --position_list "1 2 3 4 5 6 7 8 9 10, 3 4 5 6 7 8" \
  --specify_non_fixed

python "$SKILL_DIR/scripts/validate_constraint_jsonl.py" \
  --parsed constraints/parsed_pdbs.jsonl \
  --fixed-positions constraints/fixed_pdbs.jsonl
```

Before running design, confirm the user’s residue numbers are parsed-chain positions. If they gave PDB residue IDs, map them to parsed sequence positions first.

## Tie Chains A/C While Also Fixing Positions

Use this when the user needs symmetric or coupled sampling across designed chains.

```bash
python helper_scripts/make_fixed_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/fixed_pdbs.jsonl \
  --chain_list "A C" \
  --position_list "9 10 11 12 13 14 15 16 17 18 19 20 21 22 23, 10 11 18 19 20 22"

python helper_scripts/make_tied_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/tied_pdbs.jsonl \
  --chain_list "A C" \
  --position_list "1 2 3 4 5 6 7 8, 1 2 3 4 5 6 7 8"

python "$SKILL_DIR/scripts/validate_constraint_jsonl.py" \
  --parsed constraints/parsed_pdbs.jsonl \
  --fixed-positions constraints/fixed_pdbs.jsonl \
  --tied-positions constraints/tied_pdbs.jsonl
```

Each comma-separated tied-position list must have identical length. The first entry in chain A is tied to the first entry in chain C, and so on.

## Homooligomer Symmetry

Use this when every parsed chain should be tied residue-by-residue.

```bash
python helper_scripts/parse_multiple_chains.py \
  --input_path data/homooligomer_pdbs/ \
  --output_path constraints/parsed_pdbs.jsonl

python helper_scripts/make_tied_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/tied_pdbs.jsonl \
  --homooligomer 1

python "$SKILL_DIR/scripts/validate_constraint_jsonl.py" \
  --parsed constraints/parsed_pdbs.jsonl \
  --tied-positions constraints/tied_pdbs.jsonl \
  --require-homooligomer-equal-length
```

Only use this mode when chains are intended to have equal length. The helper uses the first chain length to generate tied positions.

## Global Amino-Acid Bias

Use this when the user wants to globally favor or suppress residue types.

```bash
python helper_scripts/make_bias_AA.py \
  --output_path constraints/bias_pdbs.jsonl \
  --AA_list "D E H K N Q R S T W Y" \
  --bias_list "1.39 1.39 1.39 1.39 1.39 1.39 1.39 1.39 1.39 1.39 1.39"

python "$SKILL_DIR/scripts/validate_constraint_jsonl.py" \
  --bias-aa constraints/bias_pdbs.jsonl
```

Positive values increase sampling likelihood; negative values reduce it. Use modest values first unless the user explicitly wants strong steering.

## Per-Residue Bias

Use this when the user wants residue-specific preferences. The source helper is a hard-coded template, so generate the dictionary intentionally from the user’s desired positions.

Checklist:

1. Load parsed PDB JSONL and record chain lengths.
2. Create a `[length, 21]` numeric matrix per target chain.
3. Use ProteinMPNN alphabet order `ACDEFGHIKLMNPQRSTVWYX`.
4. Place positive values for favored amino acids and negative values for suppressed amino acids.
5. Validate shape before design.

```bash
python "$SKILL_DIR/scripts/validate_constraint_jsonl.py" \
  --parsed constraints/parsed_pdbs.jsonl \
  --bias-by-res constraints/bias_by_res.jsonl
```

## PSSM-Guided Design

Use this when the user has per-target `.npz` files containing PSSM arrays.

```bash
python helper_scripts/make_pssm_input_dict.py \
  --jsonl_input_path constraints/parsed_pdbs.jsonl \
  --PSSM_input_path constraints/pssm_npz/ \
  --output_path constraints/pssm.jsonl

python "$SKILL_DIR/scripts/validate_constraint_jsonl.py" \
  --parsed constraints/parsed_pdbs.jsonl \
  --pssm constraints/pssm.jsonl
```

The final design command should include `--pssm_jsonl constraints/pssm.jsonl`, a `--pssm_multi` value such as `0.3`, and `--pssm_bias_flag 1` when using `pssm_bias` probabilities.

## Difficult Case: Chain A/C Design With Design-Only Positions

If a user asks to design chains `A` and `C` but mutate only selected residues:

1. Parse PDBs.
2. Assign designed chains with `--chain_list "A C"`.
3. Generate fixed positions with `--specify_non_fixed`.
4. Validate both chain assignment and fixed-position dictionaries.
5. Route to `../inference-design/` for final sampling.

This case catches the common confusion that `fixed_pdbs.jsonl` will contain the complement of the positions the user provided.

## Difficult Case: PSSM Missing Chain B Odds

If `make_pssm_input_dict.py` fails or design fails for chain `B`:

1. Confirm parsed JSONL contains `seq_chain_B` for that target.
2. Confirm the target `.npz` has `B_coef`, `B_bias`, and `B_odds`.
3. Confirm `B_coef` length equals `len(seq_chain_B)`.
4. Confirm `B_bias` and `B_odds` are `[len(seq_chain_B), 21]`.
5. If `B_odds` is missing, regenerate the `.npz` or create an explicit zero log-odds matrix if that matches the user’s intended PSSM semantics.
