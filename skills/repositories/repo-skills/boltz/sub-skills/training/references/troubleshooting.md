# Training Troubleshooting

Use this page before a long training launch. Most Boltz training failures are config, data, checkpoint, logging, or resource problems that can be caught with a debug launch and the bundled checker.

## Placeholders Remain In Config

Symptoms:

- Paths such as `SET_PATH_HERE`, `PATH_TO_TARGETS_DIR`, `PATH_TO_MSA_DIR`, `PATH_TO_SYMMETRY_FILE`, or `PATH_TO_CHECKPOINT_FILE` remain in the YAML.
- Hydra may instantiate, then the data module fails with missing files or directories.

Fix:

- Replace every placeholder with a real path or set optional checkpoint fields to `null`.
- From this skill's `sub-skills/training/` directory, run:

  ```bash
  python scripts/boltz_training_config_check.py train.yaml
  ```

## Missing Processed Data Or Symmetry File

Symptoms:

- `manifest.json` missing.
- `target_dir/structures/<id>.npz` missing once samples load.
- `data.symmetries` points to a nonexistent `symmetry.pkl`.
- Repeated messages like `Failed to load input ... Skipping.`

Fix:

- Confirm training data was processed by Boltz data-preparation steps before training.
- Each dataset needs a target directory with `manifest.json` and `structures/` plus an MSA directory containing `.npz` MSA files referenced by manifest records.
- Confirm `data.symmetries` points to the ligand symmetry pickle.
- If using a split file, confirm it is a newline-delimited list of record IDs and that validation records exist in the manifest.

## Hydra `_target_` Import Errors

Symptoms:

- Errors like `Error locating target`, `ModuleNotFoundError`, or `AttributeError` while instantiating `_target_` entries.
- Common target families are data module config, sampler, cropper, filters, tokenizer, featurizer, and model class.

Fix:

- Verify the active environment has the intended Boltz package installed.
- Run the checker with optional imports:

  ```bash
  python scripts/boltz_training_config_check.py train.yaml --check-imports
  ```

- If `boltz.model.model.Boltz1` fails but `boltz.model.models.boltz1.Boltz1` exists, compare the installed package version with the config template source before editing the target.
- Do not change model targets casually; checkpoint compatibility depends on class and constructor fields.

## GPU Memory Or Slow First Batches

Symptoms:

- CUDA out-of-memory during featurization, pairformer, diffusion, validation, or confidence scoring.
- Very slow startup due to large padded crops, many workers, compilation, or validation sampling.

Fix:

- Start with debug mode and smaller crops in the user's Boltz training environment. Validate this override set before launching:

  ```text
  debug=1 data.max_tokens=256 data.max_atoms=2304 data.samples_per_epoch=8 trainer.max_epochs=1 disable_checkpoint=true
  ```

- Reduce `data.max_tokens`, `data.max_atoms`, `data.max_seqs`, `model.training_args.diffusion_multiplicity`, `model.training_args.diffusion_samples`, or validation `diffusion_samples` as appropriate.
- Keep `batch_size: 1` for large crops.
- Keep activation checkpointing on for memory-constrained runs.
- Disable `compile_*` options during debugging.
- Remember validation can be more expensive than training when `sampling_steps` and `diffusion_samples` are high.

## DDP Or Multi-GPU Failures

Symptoms:

- Failures only appear with `trainer.devices > 1`.
- Worker logs hide the original dataset or import exception.
- DDP reports unused parameters.

Fix:

- Reproduce with `debug=1` first; the launcher forces one device and `num_workers=0`.
- Once single-device works, scale to multiple devices.
- Set `find_unused_parameters: true` only for actual DDP unused-parameter errors.
- Make sure each worker can read the same data paths and output directory.

## Wandb Login, Offline, Or Permission Problems

Symptoms:

- Run hangs or fails during wandb initialization.
- Permission errors writing wandb files under the output directory.

Fix:

- Remove/comment the `wandb:` block for local smoke tests.
- Use `debug=1`; the training script disables wandb in debug mode.
- If logging is required, authenticate or set wandb offline mode before launch, and ensure `output` is writable.

## Resume And Pretrained Are Confused

Symptoms:

- A run starts from unexpected weights.
- Optimizer/scheduler state is not restored.
- `pretrained` appears ignored.

Fix:

- Use `resume` to continue an interrupted Lightning run.
- Use `pretrained` to initialize weights for a new run only when `resume` is empty.
- The launcher condition is `if cfg.pretrained and not cfg.resume`; therefore `resume` wins when both are set.
- For confidence training, `load_confidence_from_trunk: true` modifies a temporary checkpoint to broadcast trunk weights into the confidence module. Source comments say this is only for starting from scratch, not for a pretrained confidence model.

## Validation Has No Records

Symptoms:

- Validation loaders are empty or validation metrics never appear.
- Split file path is wrong or IDs do not match manifest records.

Fix:

- Confirm `data.datasets[*].split` exists and contains IDs present in the dataset manifest.
- Split matching lowercases IDs, so case mismatch is tolerated, but spelling/version suffixes still matter.
- If intentionally overfitting, set `data.overfit` so validation uses training records.

## DataLoader Recursion Or Repeated Skips

Symptoms:

- Repeated `Failed to load input`, `Tokenizer failed`, `Cropper failed`, or `Featurizer failed` messages.
- Training appears stuck before useful batches.

Fix:

- Treat repeated skips as a data compatibility issue, not normal progress.
- Validate that records in `manifest.json` have corresponding structure `.npz` files and MSA ids.
- Reduce crop size temporarily if the cropper fails on large complexes.
- Re-run preprocessing for malformed records or filter them out with split/filter settings.

## Scheduler Configuration Error

Symptoms:

- Scheduler raises `warmup_no_steps must not exceed start_decay_after_n_steps`.

Fix:

- Ensure `model.training_args.lr_warmup_no_steps <= model.training_args.lr_start_decay_after_n_steps`.
- Keep `lr_decay_every_n_steps` positive.

## Boltz-2 Training Docs Gap

Symptoms:

- User asks for exact Boltz-2 training recipe, affinity training, or Boltz-2-specific config edits.

Fix:

- State that the inspected training docs mark updated Boltz-2 training information as coming soon.
- Ask for an existing Boltz-2 config or official updated docs before making architecture-specific changes.
- You may still check general launcher mechanics, data paths, checkpoint intent, and resource settings.