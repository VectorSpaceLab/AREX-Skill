# ProteinMPNN Troubleshooting

## Install And Import

- Symptom: `ModuleNotFoundError: No module named 'torch'` or `numpy`.
  - Cause: the active Python environment does not include ProteinMPNN runtime dependencies.
  - Fix: install PyTorch for the target CPU/GPU stack and install NumPy, then rerun `python protein_mpnn_run.py --help`.

- Symptom: `ModuleNotFoundError: No module named 'protein_mpnn_utils'`.
  - Cause: command is not running from a checkout where `protein_mpnn_run.py` and `protein_mpnn_utils.py` are together, or the script directory is not on `PYTHONPATH`.
  - Fix: run commands from the ProteinMPNN checkout root or call the script with the checkout root as the working directory.

## Checkout Layout

- Symptom: default model weights are not found.
  - Cause: the expected `vanilla_model_weights/`, `soluble_model_weights/`, or `ca_model_weights/` folders are missing or the command is using a copied script outside the checkout.
  - Fix: keep runner scripts and weight folders in the checkout layout, or pass `--path_to_model_weights` to a folder containing `<model_name>.pt`.

- Symptom: `--ca_only --use_soluble_model` exits early.
  - Cause: CA-soluble weights are not available in this code path.
  - Fix: use CA-only without `--use_soluble_model`, or use soluble full-backbone weights without `--ca_only`.

## Routing Mistakes

- If the user is asking how to prepare `chain_id_jsonl`, `fixed_positions_jsonl`, `tied_positions_jsonl`, `bias_AA_jsonl`, `bias_by_res_jsonl`, `omit_AA_jsonl`, or `pssm_jsonl`, route to `sub-skills/constraint-inputs/`.
- If the user is asking how to choose `--sampling_temp`, `--score_only`, `--save_probs`, `--unconditional_probs_only`, `--conditional_probs_only`, `--model_name`, or `--path_to_model_weights`, route to `sub-skills/inference-design/`.
- If the user is asking about `training.py`, `list.csv`, cluster files, debug training, SLURM, or custom checkpoints, route to `sub-skills/training-custom-models/`.

## Runtime Safety

- Full inference can be slow on CPU; start with `--batch_size 1`, a small `--num_seq_per_target`, and explicit `--seed` for reproducible smoke checks.
- Full training is expensive and normally requires large datasets and GPU/HPC resources; do not launch it as an implicit verification step.
- Notebook workflows may involve network, Colab, or external tools. Treat notebooks as evidence and adapt their commands rather than running them automatically.
