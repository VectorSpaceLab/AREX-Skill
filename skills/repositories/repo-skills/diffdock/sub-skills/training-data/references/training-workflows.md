# Training Workflows

This reference distills DiffDock training entry points into safe planning steps. The bundled command builder prints commands only; it does not import DiffDock or start jobs.

## Score Model Training

Score-model training uses the repository `train.py` entry point and `utils.parsing.parse_train_args`. A training run constructs loaders, builds the model, writes `model_parameters.yml`, and saves checkpoint files under:

```text
<log_dir>/<run_name>/
```

Typical planning command:

```bash
python sub-skills/training-data/scripts/build_training_command.py \
  --mode score \
  --dataset pdbbind \
  --data-dir data/PDBBind_processed \
  --split-train data/splits/timesplit_no_lig_overlap_train \
  --split-val data/splits/timesplit_no_lig_overlap_val \
  --cache-path data/cache \
  --log-dir workdir/score \
  --run-name pdbbind_score_trial \
  --limit-complexes 32 \
  --n-epochs 1 \
  --batch-size 2
```

The printed command uses:

```bash
python -m train --dataset pdbbind --pdbbind_dir data/PDBBind_processed ...
```

For MOAD/DockGen-family training, `--dataset moad` maps `--data-dir` to `--moad_dir`; for sidechain training, `--dataset pdbsidechain` maps `--data-dir` to `--pdbsidechain_dir`.

## Confidence Model Training

Confidence training uses `confidence/confidence_train.py`. It needs a score-model run directory containing `model_parameters.yml` and a score checkpoint such as `best_model.pt` or `last_model.pt`.

Typical planning command:

```bash
python sub-skills/training-data/scripts/build_training_command.py \
  --mode confidence \
  --data-dir data/PDBBind_processed \
  --split-train data/splits/timesplit_no_lig_overlap_train \
  --split-val data/splits/timesplit_no_lig_overlap_val \
  --cache-path data/cacheNew \
  --log-dir workdir/confidence \
  --run-name pdbbind_confidence_trial \
  --original-model-dir workdir/score/pdbbind_score_trial \
  --limit-complexes 16 \
  --n-epochs 1 \
  --batch-size 2
```

The printed command uses:

```bash
python -m confidence.confidence_train --original_model_dir <score-run-dir> ...
```

Confidence dataset creation can run score-model inference to generate ligand positions and RMSDs. That preprocessing writes files such as `ligand_positions.pkl`, `ligand_positions_id<N>.pkl`, and `complex_names_in_same_order*.pkl` under a confidence cache path derived from `cache_path`, `original_model_dir`, split, and `limit_complexes`.

## Important Outputs

Score training writes:

- `model_parameters.yml`: YAML serialization of parser/config values; required for compatible inference and confidence training.
- `best_model.pt`: best validation-loss checkpoint.
- `last_model.pt`: restart checkpoint containing epoch, model, optimizer, and EMA state.
- `best_ema_model.pt`: present only after EMA is active and validation improves.
- `best_inference_epoch_model.pt` and `best_ema_inference_epoch_model.pt`: present only when validation inference runs and improves the selected inference metric.
- `epoch<N>_best_model.pt`: present only when `--save_model_freq` is set.

Confidence training writes:

- `model_parameters.yml`: confidence parser/config values for the confidence run.
- `best_model.pt`: best checkpoint by `--main_metric` and `--main_metric_goal`.
- `last_model.pt`: restart checkpoint containing epoch, model, and optimizer.
- `model_epoch<N>.pt` and `best_model_epoch<N>.pt`: present only when the corresponding save-frequency flags are positive.

Keep each `model_parameters.yml` beside its checkpoints. Do not copy a checkpoint alone and expect later inference or confidence training to infer architecture flags reliably.

## Restart And Pretrain Notes

Score training supports:

- `--restart_dir` plus `--restart_ckpt`: loads `<restart_dir>/<restart_ckpt>.pt`, restores optimizer and EMA when available, and continues from the saved epoch.
- `--restart_lr`: overwrites the optimizer learning rate on restart.
- `--pretrain_dir` plus `--pretrain_ckpt`: loads model weights from `<pretrain_dir>/<pretrain_ckpt>.pt` without optimizer state.
- `--freeze_params`: parser-exposed but the active freezing schedule is controlled mainly by `--scheduler layer_linear_warmup`.

Confidence training supports:

- `--restart_dir`: loads `<restart_dir>/last_model.pt` for confidence training.
- `--transfer_weights`: builds the confidence model from the original score-model arguments, then copies matching score checkpoint weights before training the confidence head.
- `--ckpt`: selects the score checkpoint inside `--original_model_dir` for transfer or confidence-dataset inference.

When restarting, verify the new command still points to the same dataset roots, split files, ESM embedding choices, `all_atoms` setting, and model-size flags as the original run unless deliberately changing them.

## Safe Scaling Decisions

Start small before committing compute:

- Use `--limit_complexes` to cap train/validation preprocessing and training.
- Use `--n_epochs 1` and small `--batch_size` for a dry training smoke after layout validation.
- Use `--num_dataloader_workers 0` while debugging path/import failures; increase only after the loader is stable.
- Avoid validation inference at first by setting a high `--val_inference_freq` or by omitting training plans that rely on inference metrics; validation inference samples complexes and is much more expensive than loss-only validation.
- Use separate cache paths for incompatible experiments, especially when changing `--all_atoms`, torsion, split file, max ligand size, receptor radius, atom radius, ESM embeddings, protein filename, or graph-neighbor settings.
- Enable `--wandb` only when the user has an intended W&B project/session and network/account access.

## Dataset-Specific Command Patterns

PDBBind score training:

```bash
python -m train --dataset pdbbind --pdbbind_dir data/PDBBind_processed --split_train data/splits/timesplit_no_lig_overlap_train --split_val data/splits/timesplit_no_lig_overlap_val --cache_path data/cache --log_dir workdir/score --run_name pdbbind_score
```

BindingMOAD score training:

```bash
python -m train --dataset moad --moad_dir data/BindingMOAD_2020_processed --split_train data/splits/timesplit_no_lig_overlap_train --split_val data/splits/timesplit_no_lig_overlap_val --cache_path data/cache --log_dir workdir/score --run_name moad_score --unroll_clusters
```

Combined PDBBind + MOAD training:

```bash
python -m train --dataset pdbbind --combined_training --pdbbind_dir data/PDBBind_processed --moad_dir data/BindingMOAD_2020_processed --cache_path data/cache --log_dir workdir/score --run_name combined_score
```

Sidechain/van der Mers training:

```bash
python -m train --dataset pdbsidechain --pdbsidechain_dir data/pdb_2021aug02_sample --cache_path data/cache --log_dir workdir/score --run_name sidechain_trial --sidechain_loss_weight 1.0
```

Confidence training:

```bash
python -m confidence.confidence_train --original_model_dir workdir/score/pdbbind_score --data_dir data/PDBBind_processed --cache_path data/cacheNew --log_dir workdir/confidence --run_name confidence_trial --ckpt best_model.pt
```

## Expensive-Run Boundary

The following actions are not safe background checks and require explicit user approval:

- Running `python -m train` or `python -m confidence.confidence_train` beyond a deliberately tiny smoke.
- Generating ESM embeddings with an external ESM model.
- Preprocessing full PDBBind, BindingMOAD, PoseBusters, or van der Mers datasets into graph caches.
- Generating confidence ligand-position/RMSD caches for large splits.
- Enabling W&B logging, Docker builds, or network dataset downloads.

Use [scripts/build_training_command.py](../scripts/build_training_command.py), [scripts/validate_dataset_layout.py](../scripts/validate_dataset_layout.py), and [scripts/validate_esm_embedding_index.py](../scripts/validate_esm_embedding_index.py) before requesting approval for heavy execution.
