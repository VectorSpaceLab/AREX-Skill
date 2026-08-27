# CLI Reference

Commands in this reference are templates. Replace placeholder paths with user-approved local paths and prefer copied config files for edits.

## Config Diagnostics

Run the bundled diagnostic checker before any training or evaluation command:

```bash
python scripts/saprot_config_check.py -c <copied-task-config.yaml> --repo-root <run-root> --check-exists
```

Useful options:

```bash
python scripts/saprot_config_check.py -c <config.yaml>
python scripts/saprot_config_check.py -c <config.yaml> --repo-root <run-root> --check-exists
python scripts/saprot_config_check.py -c <config.yaml> --json
```

The checker reports, but does not execute, the effective training/evaluation risk profile: dynamic module names, dataset paths, output paths, Foldseek path, trainer resources, logger status, DDP env values, and likely expensive-run settings.

## Training Launcher Templates

Pretraining template after explicit approval:

```bash
python <sa-prot-training-launcher.py> -c <copied-pretraining-config.yaml>
```

Downstream fine-tuning template after explicit approval:

```bash
python <sa-prot-training-launcher.py> -c <copied-downstream-config.yaml>
```

Do not run launcher templates directly as a first step. Copy the config, inspect it, lower resource settings for a smoke run, then request user confirmation for expensive execution.

## Zero-Shot Launcher Templates

ProteinGym template after explicit approval:

```bash
python <sa-prot-zero-shot-launcher.py> -c <copied-proteingym-config.yaml>
```

ClinVar template after explicit approval:

```bash
python <sa-prot-zero-shot-launcher.py> -c <copied-clinvar-config.yaml>
```

Zero-shot configs still instantiate a large model and may iterate many benchmark folders. Treat full benchmark runs as expensive.

## ClinVar AUC Aggregation

Use explicit paths:

```bash
python scripts/compute_clinvar_auc.py \
  --log-dir <clinvar-log-dir> \
  --labels-csv <clinvar-labels.csv>
```

Helpful options:

```bash
python scripts/compute_clinvar_auc.py \
  --log-dir <log-dir> \
  --labels-csv <labels.csv> \
  --output-csv <merged.csv> \
  --json

python scripts/compute_clinvar_auc.py \
  --log-dir <log-dir> \
  --labels-csv <labels.csv> \
  --allow-conflicting-duplicates \
  --duplicate-keep last
```

Default duplicate behavior drops exact duplicate rows and fails on conflicting duplicate predictions for the same protein/mutation pair. Use `--allow-conflicting-duplicates` only when the user has chosen a deterministic resolution policy.

## One-GPU Dry-Run Edit Checklist

For a copied GPU config:

- Set `setting.os_environ.CUDA_VISIBLE_DEVICES` to one device such as `0`.
- Keep `setting.os_environ.WORLD_SIZE: 1` and `setting.os_environ.NODE_RANK: 0`.
- Set `Trainer.accelerator: gpu` and `Trainer.devices: 1`.
- Set `Trainer.logger: false` unless the user explicitly wants WandB.
- Set `dataset.dataloader_kwargs.num_workers` to a small value such as `0`, `1`, or `2`.
- Use smaller `batch_size` and, if needed, adjust `accumulate_grad_batches` to preserve approximate effective batch size.
- Add or lower `limit_train_batches`, `limit_val_batches`, and `limit_test_batches` for smoke testing when compatible with the intended launcher.
- Keep `precision: 16` only when the selected GPU and installed Lightning stack support it; otherwise use `32`.

## CPU Diagnostic Edit Checklist

For a copied CPU-only diagnostic config:

- Set `Trainer.accelerator: cpu` and `Trainer.devices: 1`.
- Set `Trainer.precision: 32`.
- Set `Trainer.logger: false`.
- Set `dataset.dataloader_kwargs.num_workers: 0`.
- Use tiny copied datasets or Lightning batch limits.
- Expect checkpoint loading and large-model inference to be slow; CPU mode is for wiring checks, not benchmark-quality results.

## Path Review Checklist

Review every path-like value before execution:

- `model.kwargs.config_path`: local Hugging Face model directory or model asset path expected by the selected model class.
- `model.kwargs.foldseek_path`: local Foldseek executable for Foldseek mutation models; avoid stale absolute paths copied from examples.
- `model.save_path`: output checkpoint path; ensure the user wants the run to overwrite or create it.
- `dataset.train_lmdb`, `dataset.valid_lmdb`, `dataset.test_lmdb`: supervised LMDB directories.
- `setting.dataset_dir`: parent directory containing benchmark LMDB children for zero-shot sweeps.
- `setting.out_path`: optional TSV output file for benchmark Spearman rows.
- `model.kwargs.log_dir`: ClinVar prediction CSV output directory.
- `setting.wandb_config`: external logging metadata; check secrets are not stored in shared configs.

## Minimal Decision Prompts

Ask for confirmation when any command will:

- Start pretraining or a full downstream fine-tuning run.
- Evaluate all ProteinGym or ClinVar entries rather than a small subset.
- Use more than one GPU or multiple nodes.
- Write checkpoints into an existing weights directory.
- Enable WandB logging or consume a WandB API key.
- Depend on an absolute Foldseek path or data path that was copied from another machine.
