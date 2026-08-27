# Constraint Helper CLI Reference

ProteinMPNN is commonly run from a checkout with Python, PyTorch, and NumPy available. These helpers write JSONL/dictionary inputs for `protein_mpnn_run.py`; keep generated files under a working output directory such as `constraints/`.

## `parse_multiple_chains.py`

Creates the parsed-PDB JSONL used as `--jsonl_path`.

```bash
python helper_scripts/parse_multiple_chains.py \
  --input_path data/pdbs/ \
  --output_path constraints/parsed_pdbs.jsonl
```

Options:

- `--input_path`: folder containing `.pdb` files.
- `--output_path`: parsed-PDB JSONL path.
- `--ca_only`: parse backbone-only/CA-only structures; downstream inference must also use compatible CA-only settings.

Output shape: one JSON object per PDB line with `name`, `num_of_chains`, `seq`, `seq_chain_<chain>`, and `coords_chain_<chain>` fields.

## `assign_fixed_chains.py`

Creates a chain assignment dictionary used as `--chain_id_jsonl`.

```bash
python helper_scripts/assign_fixed_chains.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/assigned_pdbs.jsonl \
  --chain_list "A C"
```

- `--chain_list` is the space-separated list of chains to design.
- Chains present in the parsed PDB but omitted from `--chain_list` become fixed chains.
- Output values are `[designed_chains, fixed_chains]`, for example `{"target": [["A", "C"], ["B"]]}`.

## `make_fixed_positions_dict.py`

Creates a fixed-position dictionary used as `--fixed_positions_jsonl`.

Fix listed residues while designing the rest of the selected chains:

```bash
python helper_scripts/make_fixed_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/fixed_pdbs.jsonl \
  --chain_list "A C" \
  --position_list "1 2 3 4 5, 10 11 12"
```

Design only listed residues and fix all other residues with `--specify_non_fixed`:

```bash
python helper_scripts/make_fixed_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/fixed_pdbs.jsonl \
  --chain_list "A C" \
  --position_list "1 2 3 4 5, 10 11 12" \
  --specify_non_fixed
```

Rules:

- Positions are 1-based parsed-chain positions.
- `position_list` is comma-separated by chain and follows `chain_list` order.
- Without `--specify_non_fixed`, listed positions are fixed.
- With `--specify_non_fixed`, listed positions are designable and the helper writes their complement as fixed.

## `make_tied_positions_dict.py`

Creates a tied-position dictionary used as `--tied_positions_jsonl`.

Tie explicit positions across selected chains:

```bash
python helper_scripts/make_tied_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/tied_pdbs.jsonl \
  --chain_list "A C" \
  --position_list "1 2 3 4, 1 2 3 4"
```

Tie every residue across all chains in a homooligomer:

```bash
python helper_scripts/make_tied_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/tied_pdbs.jsonl \
  --homooligomer 1
```

Rules:

- Every comma-separated list in `--position_list` must have the same number of positions.
- Each tied entry is a dictionary such as `{"A": [1], "C": [1]}`.
- Homooligomer mode ties position `i` across all parsed chains and assumes equal chain lengths.

## `make_pos_neg_tied_positions_dict.py`

Creates weighted tied-position dictionaries for positive/negative design variants.

```bash
python helper_scripts/make_pos_neg_tied_positions_dict.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/tied_pdbs.jsonl \
  --homooligomer 1 \
  --pos_neg_chain_list "A B, C D" \
  --pos_neg_chain_betas "1.0 -0.5, 1.0 -0.5"
```

Weighted tied entries use `{"A": [[1], [1.0]], "B": [[1], [-0.5]]}` where the first list is positions and the second list is tie weights. Positive weights encourage matching; negative weights discourage matching; `0.0` removes that chain’s tied-energy contribution.

## `make_bias_AA.py`

Creates a global amino-acid bias dictionary used as `--bias_AA_jsonl`.

```bash
python helper_scripts/make_bias_AA.py \
  --output_path constraints/bias_pdbs.jsonl \
  --AA_list "D E H K N Q R S T W Y" \
  --bias_list "1.39 1.39 1.39 1.39 1.39 1.39 1.39 1.39 1.39 1.39 1.39"
```

- Positive values make amino acids more likely.
- Negative values make amino acids less likely.
- Amino-acid symbols should be from `ACDEFGHIKLMNPQRSTVWYX`.

## `make_bias_per_res_dict.py`

Creates a per-residue bias dictionary used as `--bias_by_res_jsonl`, but the source helper is a template with hard-coded chain and residue logic. Prefer generating this schema directly or adapting a local copy deliberately.

Expected output shape per target: `{"A": [[21 floats], [21 floats], ...]}` with one length-21 vector for every parsed residue in the chain.

## `make_pssm_input_dict.py`

Creates a PSSM dictionary used as `--pssm_jsonl`.

```bash
python helper_scripts/make_pssm_input_dict.py \
  --jsonl_input_path constraints/parsed_pdbs.jsonl \
  --PSSM_input_path constraints/pssm_npz/ \
  --output_path constraints/pssm.jsonl
```

For each parsed target named `target`, the helper loads `constraints/pssm_npz/target.npz`. For each chain, the `.npz` must contain:

- `<chain>_coef`: length `L`, per-position coefficient from `0.0` to `1.0`.
- `<chain>_bias`: shape `[L, 21]`, PSSM probability distribution over ProteinMPNN alphabet.
- `<chain>_odds`: shape `[L, 21]`, log-odds values; helper writes it as `pssm_log_odds`.

Use `protein_mpnn_run.py --pssm_jsonl constraints/pssm.jsonl --pssm_multi 0.3 --pssm_bias_flag 1` to apply PSSM bias during design.

## Omit Amino Acids

- Use `protein_mpnn_run.py --omit_AAs "AC"` for a global omit list.
- For per-residue omit dictionaries, do not use the source repo’s hard-coded `other_tools/make_omit_AA.py`; follow `references/data-formats.md` and validate the JSON shape before design.
