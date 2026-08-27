# Training Workflows

## Initial Training Checklist

1. Confirm the user has a GPU-capable OpenFold runtime. CPU-only training is not supported for practical OpenFold training.
2. Route dataset construction to `../data-preparation/` and verify the user has mmCIFs, precomputed alignments or alignment DBs, template mmCIFs, cache files, duplicate/cluster handling, and obsolete PDB metadata as needed.
3. Choose `--config_preset initial_training` unless the user specifies a different validated preset.
4. Include `--seed` for reproducibility and always include it for `--gpus > 1` or `--num_nodes > 1`.
5. Add `--train_chain_data_cache_path`, `--template_release_dates_cache_path`, and `--obsolete_pdbs_file_path` for standard PDB/OpenProteinSet-style training.
6. Use validation flags only when validation mmCIFs/alignments/caches are prepared.
7. Decide whether to use DDP or DeepSpeed before launch; do not retrofit DeepSpeed onto a running command without checking precision and checkpoint expectations.

Minimal planned command shape:

```bash
python train_openfold.py TRAIN_MMCIFS TRAIN_ALIGNMENTS TEMPLATE_MMCIFS OUTPUT_DIR 2021-10-10 --config_preset initial_training --seed 42 --gpus 1 --num_nodes 1
```

For alignment DBs, `train_alignment_dir` is the directory containing DB shards and `--alignment_index_path` points to the DB index.

## Fine-Tuning From Existing OpenFold Weights

Use this when the user wants to initialize from existing model weights but train a new optimizer/scheduler run:

```bash
python train_openfold.py TRAIN_MMCIFS TRAIN_ALIGNMENT_DB TEMPLATE_MMCIFS OUTPUT_DIR 2021-10-10 --config_preset finetuning --alignment_index_path TRAIN_ALIGNMENT_DB_INDEX --train_chain_data_cache_path CHAIN_CACHE_JSON --template_release_dates_cache_path TEMPLATE_CACHE_JSON --obsolete_pdbs_file_path OBSOLETE_DAT --seed 4242022 --gpus 4 --num_nodes 1 --resume_from_ckpt CHECKPOINT_PATH --resume_model_weights_only true
```

Notes:

- `--resume_model_weights_only true` imports model parameters and avoids restoring the trainer state.
- `--resume_from_ckpt` may point to a checkpoint file or a DeepSpeed checkpoint directory depending on how the source run saved weights.
- Do not also pass `--resume_from_jax_params`.
- Use `--config_preset finetuning` unless there is a documented reason to use another preset.

## Resuming an Interrupted Training Run

Use this when the user wants to continue optimizer, scheduler, and trainer state:

```bash
python train_openfold.py TRAIN_MMCIFS TRAIN_ALIGNMENTS TEMPLATE_MMCIFS OUTPUT_DIR 2021-10-10 --config_preset initial_training --seed 42 --gpus 4 --num_nodes 1 --resume_from_ckpt CHECKPOINT_PATH
```

Do not pass `--resume_model_weights_only true` for a full resume. If resuming a DeepSpeed run from a directory, ensure the directory contains a `latest` tag file and the expected checkpoint tag subdirectory.

## Initializing From JAX Parameters

Use `--resume_from_jax_params PARAMS_NPZ` only when the source weights are AlphaFold/JAX-style `.npz` parameters and no OpenFold checkpoint is being used. OpenFold rejects combining this with `--resume_from_ckpt`.

## Validation and Early Stopping

Add validation paths together:

```bash
--val_data_dir VAL_MMCIFS --val_alignment_dir VAL_ALIGNMENTS --val_mmcif_data_cache_path VAL_CACHE_JSON --early_stopping true --min_delta 0.0 --patience 3
```

Validation metrics are logged under validation prefixes and can drive early stopping. Validation data must have matching alignments/caches and should use the same template date/cache policy as the training setup.

## Self-Distillation

Distillation data is optional and separate from validation:

```bash
--distillation_data_dir DISTILLATION_STRUCTURES --distillation_alignment_dir DISTILLATION_ALIGNMENTS --distillation_chain_data_cache_path DISTILLATION_CHAIN_CACHE_JSON
```

If distillation alignments use DB shards, add `--distillation_alignment_index_path`. If only a subset should be used, add `--distillation_filter_path`. Route construction and validation of distillation data to `../data-preparation/`.

## Experiment Config Overrides

`--experiment_config_json` accepts a JSON object whose keys are flattened config paths. Example:

```json
{
  "data.train.crop_size": 128,
  "data.train.max_extra_msa": 512
}
```

Only override keys that exist in the OpenFold config for the selected preset. Use `templates/experiment_config.json` as a starting point and route deep config validation to `../model-apis/`.

## Logging and Outputs

Expected output directory contents vary by Lightning strategy but commonly include checkpoints, W&B run files if enabled, performance logs if `--log_performance true`, and callback outputs. Ensure `output_dir` is writable by every rank that needs it and is on shared storage for multi-node runs.
