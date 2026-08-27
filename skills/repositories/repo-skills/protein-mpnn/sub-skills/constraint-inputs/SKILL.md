---
name: constraint-inputs
description: "Prepare and validate ProteinMPNN parsed-PDB JSONL and
  design-constraint dictionaries for fixed chains, fixed/design-only positions,
  tied or symmetric positions, amino-acid bias, per-residue bias, omitted amino
  acids, and PSSM-guided design."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ProteinMPNN Constraint Inputs

Use this sub-skill when a user needs to create, inspect, repair, or validate ProteinMPNN constraint input files before running `protein_mpnn_run.py`.

## When To Use

- Parse a folder of `.pdb` files into the `--jsonl_path` parsed-PDB JSONL consumed by ProteinMPNN.
- Choose designed chains and fixed chains with `--chain_id_jsonl`.
- Build fixed-position dictionaries for `--fixed_positions_jsonl`, including the inverted `--specify_non_fixed` workflow for “design only these residues”.
- Tie residues across chains with `--tied_positions_jsonl`, including homooligomer symmetry and positive/negative tied-chain betas.
- Add global amino-acid bias with `--bias_AA_jsonl` or per-residue bias with `--bias_by_res_jsonl`.
- Prepare safe schema guidance for `--omit_AAs`, `--omit_AA_jsonl`, and `--pssm_jsonl` without relying on ad hoc local-path utilities.

## Quick Routing

- For final sequence generation commands, sampling options, score-only mode, and output interpretation, use `../inference-design/`.
- For custom training data layout or model training, use `../training-custom-models/`.
- For constraint JSONL schema, helper commands, and validation, stay here.

## Core Workflow

1. Parse PDBs into one JSON object per line:

```bash
python helper_scripts/parse_multiple_chains.py \
  --input_path data/pdbs/ \
  --output_path constraints/parsed_pdbs.jsonl
```

2. Assign designed chains, for example design chains `A` and `C` while all other parsed chains remain fixed:

```bash
python helper_scripts/assign_fixed_chains.py \
  --input_path constraints/parsed_pdbs.jsonl \
  --output_path constraints/assigned_pdbs.jsonl \
  --chain_list "A C"
```

3. Create one or more constraint dictionaries, validate them with the bundled script, then pass them to `protein_mpnn_run.py`. Set `SKILL_DIR` to this sub-skill directory in the agent skill library.

```bash
python "$SKILL_DIR/scripts/validate_constraint_jsonl.py" \
  --parsed constraints/parsed_pdbs.jsonl \
  --chain-id constraints/assigned_pdbs.jsonl \
  --fixed-positions constraints/fixed_pdbs.jsonl \
  --tied-positions constraints/tied_pdbs.jsonl \
  --bias-aa constraints/bias_pdbs.jsonl \
  --pssm constraints/pssm.jsonl
```

## Required References

- `references/helper-cli-reference.md` lists the helper commands and the ProteinMPNN flags they prepare.
- `references/data-formats.md` defines the JSONL and dictionary shapes accepted by the validator and ProteinMPNN.
- `references/workflows.md` gives copy-adaptable workflows for fixed/design-only positions, tied chains, homooligomers, amino-acid bias, and PSSM inputs.
- `references/troubleshooting.md` covers common constraint mistakes and how to diagnose them.

## Important Rules

- Residue positions in helper-generated constraint files are 1-based positions in the parsed chain sequence, not PDB residue IDs.
- `position_list` uses comma-separated per-chain lists that must align with `chain_list` order.
- Chain letters in every constraint dictionary must match `seq_chain_<chain>` keys in the parsed-PDB JSONL.
- Most helper-generated constraint files are JSONL by extension but contain a single JSON object on one line.
- Homooligomer tied positions assume all tied chains share the same parsed sequence length.
- PSSM `.npz` inputs must provide `<chain>_coef`, `<chain>_bias`, and `<chain>_odds` for each designed chain; bias and odds arrays are length-by-21.

## Exclusions

Do not copy or depend on `helper_scripts/other_tools/make_omit_AA.py` or `helper_scripts/other_tools/make_pssm_dict.py`. Those utilities are hard-coded/ad hoc in the source repo. Use the schemas in `references/data-formats.md` and the validator in `scripts/validate_constraint_jsonl.py` instead.
