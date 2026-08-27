# Training CLI Reference

OpenFold training is driven by `train_openfold.py`. The generated helpers in this sub-skill produce command lines only; they do not import OpenFold or launch training.

## Required Positionals

Current `train_openfold.py` requires five positional arguments, in order:

1. `train_data_dir`: directory containing training mmCIF files.
2. `train_alignment_dir`: directory containing precomputed training alignments, or the directory containing alignment DB shards when `--alignment_index_path` points at the index file.
3. `template_mmcif_dir`: directory containing template mmCIF files.
4. `output_dir`: directory for checkpoints, logs, and trainer outputs.
5. `max_template_date`: template cutoff date, typically `YYYY-MM-DD`.

Some older docs show `--max_template_date`; for this checkout it is positional. Build commands with the positional date unless the target checkout has been rechecked and differs.

## Core Data Flags

Use these when the training data was prepared by the data-preparation workflow:

- `--train_chain_data_cache_path`: chain cache for training examples; strongly recommended for standard OpenFold training data.
- `--train_mmcif_data_cache_path`: mmCIF metadata cache for the training structures when available.
- `--template_release_dates_cache_path`: cache of template release dates used with the template cutoff.
- `--alignment_index_path`: index file for an alignment DB layout; omit when using one alignment directory per chain.
- `--obsolete_pdbs_file_path`: `obsolete.dat` file used to filter obsolete PDB entries.
- `--train_filter_path`: optional newline-delimited allowlist of training examples.
- `--use_single_seq_mode`: requests single-sequence embeddings instead of MSAs; confirm it is intended because it changes data assumptions.

Route creation or validation of these files to `../data-preparation/`.

## Validation and Distillation Flags

- `--val_data_dir` and `--val_alignment_dir`: validation mmCIFs and precomputed validation alignments.
- `--val_mmcif_data_cache_path`: validation mmCIF metadata cache.
- `--distillation_data_dir` and `--distillation_alignment_dir`: self-distillation structures and alignments.
- `--distillation_chain_data_cache_path`: chain cache for distillation examples.
- `--distillation_alignment_index_path`: alignment DB index for distillation alignments.
- `--distillation_filter_path`: newline-delimited allowlist for distillation examples.
- `--_distillation_structure_index_path`: internal/advanced index path; use only when matching a known prepared dataset.

Validation and distillation paths must match the same alignment layout expectations as training paths.

## Training Behavior Flags

- `--config_preset`: `initial_training` for from-scratch training, `finetuning` for fine-tuning, or another preset validated for the model/task.
- `--experiment_config_json`: flattened JSON overrides such as `{"data.train.crop_size": 128}`.
- `--seed`: required for distributed training; recommended for all reproducible runs.
- `--num_nodes`: number of Lightning nodes.
- `--gpus`: GPUs per node used for strategy selection and effective batch size accounting.
- `--precision`: Lightning precision string. The script default is `bf16`; docs recommend BF16 on A100s. Do not pass `16` with DeepSpeed.
- `--max_epochs`, `--train_epoch_len`, `--accumulate_grad_batches`, `--log_every_n_steps`, `--num_sanity_val_steps`, `--reload_dataloaders_every_n_epochs`: Lightning/runtime controls.
- `--checkpoint_every_epoch`: save a checkpoint every epoch.
- `--early_stopping`, `--min_delta`, `--patience`: validation-based early stopping controls.
- `--log_lr` and `--log_performance`: record learning rate and performance metrics.
- `--script_modules`: TorchScript eligible model components; use only after model imports are healthy.

The script includes a typo in its internal trainer keyword list (`flush_logs_ever_n_steps`) while the CLI flag is `--flush_logs_every_n_steps`; validate behavior on the target version before relying on that specific setting. Older documentation shows `--num_workers`, but the inspected current argparse does not define that flag; configure worker count through the data config or a version-specific extra only after rechecking the target checkout.

## Checkpoint and Weight Flags

- `--resume_from_ckpt PATH`: load from a PyTorch Lightning/OpenFold checkpoint file or a DeepSpeed checkpoint directory.
- `--resume_model_weights_only true`: fine-tune by importing only model weights from `--resume_from_ckpt` instead of restoring trainer state.
- `--resume_from_jax_params PATH`: initialize from JAX `.npz` parameters.

OpenFold rejects specifying both `--resume_from_ckpt` and `--resume_from_jax_params`. For fine-tuning, pair `--config_preset finetuning` with `--resume_model_weights_only true` when the intent is to import weights but start a fresh optimizer/scheduler state.

## Logging Flags

- `--wandb`: enable Weights & Biases logging.
- `--experiment_name`: run name.
- `--wandb_id`: previous run ID to resume.
- `--wandb_project`: W&B project.
- `--wandb_entity`: W&B user/team.

When W&B is enabled, the training script also tries to save package versions and, for DeepSpeed, the DeepSpeed JSON and OpenFold config. Confirm W&B authentication and writable output directories before launch.

## Dry-Run Command Builder

`python scripts/build_training_command.py --help` describes a self-contained planner. It validates OpenFold-specific conflicts and emits a shell command such as:

```bash
python train_openfold.py TRAIN_MMCIFS TRAIN_ALIGNMENTS TEMPLATE_MMCIFS OUTPUT_DIR 2021-10-10 --config_preset initial_training --seed 42 --gpus 4 --num_nodes 1
```

Use `--python-executable` and `--train-script` to target a user checkout explicitly. The helper accepts user paths and does not assume where OpenFold is installed.
