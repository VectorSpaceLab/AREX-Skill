# Training and Evaluation Troubleshooting

Use this reference to diagnose SaProt training, fine-tuning, zero-shot benchmark, and ClinVar aggregation failures without accidentally escalating to full expensive runs.

## Missing Weights or Tokenizer Files

Symptoms:

- Model initialization fails while loading `config_path`.
- Tokenizer loading fails.
- Checkpoint reload after training fails.

Checks:

- Confirm `model.kwargs.config_path` points to the local model directory expected by the selected model class.
- Confirm `model.save_path` exists only when resuming or testing from a previous checkpoint is intended.
- For `load_prev_scheduler: true`, confirm the checkpoint was saved with optimizer and scheduler state; otherwise set `load_prev_scheduler: false` in a copied config.
- Do not confuse a Hugging Face model directory with an ESM-style `.pt` checkpoint.

## Missing Data or Wrong Working Directory

Symptoms:

- LMDB path not found.
- Zero-shot loop sees no datasets.
- Outputs are written to an unexpected location.

Checks:

- Run `saprot_config_check.py -c <config.yaml> --repo-root <intended-run-root> --check-exists`.
- Resolve relative paths from the process working directory used for the launcher.
- Validate `dataset.train_lmdb`, `dataset.valid_lmdb`, `dataset.test_lmdb`, or `setting.dataset_dir` depending on launcher.
- Confirm parent directories for `setting.out_path`, `model.kwargs.log_dir`, and `model.save_path` are intentional.

## CUDA Device Mismatch

Symptoms:

- Lightning reports invalid GPU device IDs.
- A run starts on more GPUs than intended.
- A single-GPU smoke test hangs in distributed setup.

Checks:

- Match `Trainer.devices` to the number of visible devices in `CUDA_VISIBLE_DEVICES`.
- Use `Trainer.accelerator: cpu`, `Trainer.devices: 1`, and `precision: 32` for CPU-only diagnostics.
- Keep `WORLD_SIZE: 1`, `num_nodes: 1`, and `NODE_RANK: 0` for local single-process smoke tests.
- Lower dataloader `num_workers` when debugging hangs or resource exhaustion.

## DDP and `NODE_RANK` Behavior

Symptoms:

- Logging disappears unexpectedly.
- Multiple nodes fight over the same port.
- Rank-dependent checkpoint or metric behavior is inconsistent.

Checks:

- The training launcher disables `Trainer.logger` when `setting.os_environ.NODE_RANK != 0`.
- Existing shell environment values override YAML defaults for the training launcher, so inspect the live environment when behavior differs from the file.
- Ensure `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, and `NODE_RANK` are coordinated across nodes.
- Confirm `Trainer.strategy.find_unused_parameters` is appropriate for the selected model and task; changing it can hide or expose DDP graph issues.

## WandB Logger Problems

Symptoms:

- Run prompts for login or fails with a WandB authentication error.
- Training unexpectedly contacts external services.
- Non-root nodes try to log.

Checks:

- Set `Trainer.logger: false` for diagnostics, dry-runs, and non-interactive runs.
- If logging is required, provide `WANDB_API_KEY` through the environment or a private config copy.
- Keep `setting.wandb_config.project` and `setting.wandb_config.name` specific to the run.
- Consider `WANDB_MODE: offline` for isolated experiments if compatible with user goals.

## Foldseek Path Problems

Symptoms:

- Zero-shot mutation evaluation fails while deriving structure tokens.
- A config contains a machine-specific absolute Foldseek path.
- ClinVar or ProteinGym evaluation fails before scoring variants.

Checks:

- Inspect `model.kwargs.foldseek_path` with `saprot_config_check.py`.
- Replace stale absolute paths with a user-approved local Foldseek executable path.
- Ensure the executable has execute permissions.
- For direct mutation helper usage where the combined AA+3Di sequence is already known, route to `model-inference` instead of launching benchmark configs.

## ClinVar Log and Column Problems

Symptoms:

- AUC aggregation finds no CSV files.
- AUC aggregation fails on missing columns.
- ROC AUC errors because labels or predictions are missing.
- Duplicate prediction rows change results unexpectedly.

Checks:

- Confirm the zero-shot ClinVar config has `model.kwargs.log_clinvar: true` and a writable `model.kwargs.log_dir`.
- Confirm prediction CSVs contain `protein_name`, `mutations`, and `evol_indices`.
- Confirm labels CSV contains `protein_name`, `mutations`, and `ClinVar_labels` unless alternate column names are passed to the bundled script.
- Use the bundled `compute_clinvar_auc.py` to validate exact duplicates, conflicting duplicates, missing prediction joins, and ambiguous `0.5` labels.
- If duplicate predictions conflict, decide whether to keep `first`, keep `last`, or fail; failing is safest for benchmark reporting.

## Dependency Pin or API Drift Problems

Symptoms:

- Lightning hook names or arguments fail.
- `torchmetrics.Accuracy` requires a task argument.
- Transformers or tokenizer loading APIs differ from expected behavior.

Checks:

- Treat old PyTorch, Lightning, TorchMetrics, and Transformers versions as part of the run contract.
- Prefer the repository's documented environment when reproducing benchmark results.
- For diagnostics, use scripts in this skill that avoid importing heavy ML libraries.
- Do not edit runtime model code just to satisfy a local dependency mismatch unless the user explicitly asks for a port.

## Expensive Run Prevention

Red flags before execution:

- Pretraining configs or any config with very large `max_steps` or `min_steps`.
- `Trainer.devices` greater than `1` or `num_nodes` greater than `1`.
- `Trainer.logger: true` with WandB settings.
- Benchmark `setting.dataset_dir` containing many LMDB child directories.
- High dataloader `num_workers` on a shared or constrained machine.
- Checkpoint `save_path` under an existing weights directory.

Mitigation:

- Convert to a copied one-GPU or CPU diagnostic config.
- Add small Lightning batch limits where appropriate.
- Use tiny copied LMDB subsets for zero-shot smoke tests.
- Ask the user before launching full training or benchmark runs.
