---
name: inference-design
description: "Run and adapt ProteinMPNN inference/design workflows, including
  single-PDB design, parsed JSONL batches, monomer and multichain design,
  CA-only and soluble models, score-only mode, probability outputs, output
  interpretation, and CPU/GPU-safe command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ProteinMPNN Inference Design

Use this sub-skill when a user wants to run `protein_mpnn_run.py`, change inference flags, choose model weights, interpret generated FASTA/NPZ outputs, or debug ProteinMPNN design runs.

## Quick Routing

- Use direct PDB mode when the user has one structure: `--pdb_path structure.pdb --pdb_path_chains "A B"`.
- Use parsed JSONL mode when the user has many PDBs or precomputed helper JSONL inputs: `--jsonl_path parsed_pdbs.jsonl` plus optional constraint JSONL files.
- Route chain assignment, fixed positions, tied positions, amino-acid bias, omit masks, and PSSM builder details to `../constraint-inputs/`.
- Route retraining, custom checkpoint production, or modifying model architecture/training scripts to `../training-custom-models/`.
- Use `scripts/build_inference_command.py` to print safe `protein_mpnn_run.py` commands without copying ProteinMPNN model code.

## Minimum Runtime Assumptions

- The user runs from a ProteinMPNN checkout containing `protein_mpnn_run.py`, `protein_mpnn_utils.py`, and model weight folders.
- Python can import `torch` and `numpy` in the selected environment.
- Model weights are present locally; this skill does not bundle or copy `.pt` weight files.
- `--out_folder` is required because ProteinMPNN writes `seqs/`, `scores/`, `probs/`, `score_only/`, `conditional_probs_only/`, or `unconditional_probs_only/` under it.

## Start Here

1. Identify input style: single PDB (`--pdb_path`) or parsed batch JSONL (`--jsonl_path`). Do not pass both unless intentionally testing argument precedence; direct PDB mode wins when `--pdb_path` is non-empty.
2. Identify task mode: design sequences, score existing sequence/backbone pairs, save sampled probabilities, or emit conditional/unconditional probabilities.
3. Choose weights: default full-backbone vanilla, `--use_soluble_model` for soluble full-backbone weights, or `--ca_only` for CA-only weights.
4. Set conservative controls first: `--batch_size 1`, explicit `--seed`, one or more `--sampling_temp` values, and a small `--num_seq_per_target` for dry runs.
5. Read the references in this sub-skill before changing less common flags.

## References

- `references/cli-reference.md` lists the important `protein_mpnn_run.py` flags and model-family rules.
- `references/workflows.md` gives distilled recipes for examples 1, 2, 3, score-only, score-only from FASTA, CA-only, soluble, and probability-only runs.
- `references/output-formats.md` explains `seqs/*.fa` headers and NPZ payloads.
- `references/troubleshooting.md` covers common runtime failures and safe CPU/GPU adjustments.

## Bundled Helper

Print a direct-PDB dry-run command:

```bash
python skills/protein-mpnn/sub-skills/inference-design/scripts/build_inference_command.py \
  --pdb-path inputs/my_target.pdb \
  --chains "A B" \
  --out-folder outputs/my_design \
  --num-seq-per-target 2 \
  --batch-size 1 \
  --seed 37
```

Print a parsed-JSONL score-only command using a FASTA:

```bash
python skills/protein-mpnn/sub-skills/inference-design/scripts/build_inference_command.py \
  --jsonl-path outputs/parsed_pdbs.jsonl \
  --out-folder outputs/score_existing \
  --score-only \
  --path-to-fasta outputs/seqs/target.fa \
  --num-seq-per-target 5 \
  --batch-size 1
```

The helper prints a command only; it does not run ProteinMPNN and does not create helper JSONL files.
