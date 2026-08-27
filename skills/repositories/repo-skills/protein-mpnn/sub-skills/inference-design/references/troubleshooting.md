# Inference Troubleshooting

## Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'torch'`
- `ModuleNotFoundError: No module named 'numpy'`
- Import failures for `protein_mpnn_utils`

Fixes:

- Activate an environment with Python, PyTorch, and NumPy installed.
- Run from a ProteinMPNN checkout so `protein_mpnn_run.py` can import adjacent `protein_mpnn_utils.py`.
- If using CPU-only PyTorch, expect slower inference but no code changes are required.

## Missing or Wrong Weights

Symptoms:

- `FileNotFoundError` from `torch.load(checkpoint_path)`.
- A model name works for vanilla but not CA-only, or vice versa.

Fixes:

- Pass `--model_name` without `.pt`, for example `v_48_020`.
- Keep `--path_to_model_weights` as a folder containing `${model_name}.pt`, not a checkpoint file.
- Use available model families:
  - Vanilla: `v_48_002`, `v_48_010`, `v_48_020`, `v_48_030`.
  - Soluble: `v_48_002`, `v_48_010`, `v_48_020`, `v_48_030`.
  - CA-only: `v_48_002`, `v_48_010`, `v_48_020`.
- Do not copy or bundle weights into the skill; users need weights in their checkout.

## CA-Only and Soluble Flags

Symptom:

- The runner prints that CA-SolubleMPNN is not available and exits.

Fix:

- Use `--ca_only` for CA-only weights, or `--use_soluble_model` for soluble full-backbone weights, but not both.

## Missing `out_folder`

Symptoms:

- Path-related errors because `folder_for_outputs = args.out_folder` is `None`.
- No output directories appear.

Fix:

- Always provide `--out_folder some/output/path`.
- Ensure the parent location is writable. The runner creates `out_folder` and mode-specific subdirectories when possible.

## PDB vs JSONL Input Confusion

Symptoms:

- JSONL constraints are ignored.
- Expected batch targets do not run.
- Direct PDB chain choices override planned JSONL behavior.

Fixes:

- Use `--pdb_path` for one structure; use `--jsonl_path` for parsed batches.
- Do not pass both for normal workflows. If `--pdb_path` is non-empty, direct PDB mode is used.
- In direct PDB mode, use `--pdb_path_chains "A B"` to select designed chains.
- In JSONL mode, use `--chain_id_jsonl` for designed/fixed chain assignments; route construction to `../constraint-inputs/`.

## Score-Only Produces No Designed FASTA

Symptoms:

- User expected `seqs/*.fa`, but only `score_only/*.npz` appears.
- User asks why no new designed sequences were generated from a FASTA scoring run.

Explanation and fix:

- `--score_only 1` scores existing PDB/native and optional FASTA sequences. It intentionally skips sequence generation.
- `--path_to_fasta` is meaningful for scoring provided sequences, not seeding generation.
- Remove `--score_only 1` to generate new designs.
- Keep `--pdb_path_chains "A B"` aligned with FASTA sequences formatted as chain A sequence, `/`, chain B sequence.

## CPU Slowness and GPU Memory

Symptoms:

- CPU inference is slow.
- CUDA out-of-memory errors occur.

Fixes:

- Start with `--batch_size 1` and `--num_seq_per_target 1`.
- Reduce target length or split batches of many PDBs.
- Avoid multiple temperatures until the run works; each temperature multiplies generated outputs.
- For GPUs, increase `--batch_size` only after a successful small run.
- ProteinMPNN chooses `cuda:0` automatically when PyTorch reports CUDA availability; otherwise it uses CPU.

## Missing Output Subdirectories

Symptoms:

- `scores/`, `probs/`, or probability-only folders are absent.

Fixes:

- `seqs/` appears in default design mode.
- `scores/` requires `--save_score 1`.
- `probs/` requires `--save_probs 1`.
- `score_only/` requires `--score_only 1`.
- `conditional_probs_only/` requires `--conditional_probs_only 1`.
- `unconditional_probs_only/` requires `--unconditional_probs_only 1`.

## Integer Behavior for `num_seq_per_target` and `batch_size`

Symptom:

- Fewer sequences than expected are generated.

Cause:

- The runner computes `NUM_BATCHES = num_seq_per_target // batch_size`, then generates `NUM_BATCHES * batch_size` samples per temperature.

Fixes:

- Make `num_seq_per_target` divisible by `batch_size`.
- For exact small counts, set `--batch_size 1`.
- If `num_seq_per_target` is smaller than `batch_size`, no batches run.

## FASTA Formatting for Score-Only

Symptoms:

- Scores look wrong or sequence length mismatches occur.

Fixes:

- For multichain score-only FASTA, separate designed chains with `/` in alphabetically sorted designed-chain order.
- The runner strips `/` before indexing the sequence, so the combined sequence length must match designed positions.
- Include only amino acids from ProteinMPNN's expected alphabet unless intentionally testing unknown `X` handling.
