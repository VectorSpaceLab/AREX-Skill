---
name: training-evaluation
description: "Plan safe SaProt pretraining, fine-tuning, zero-shot mutation
  benchmarks, ClinVar AUC aggregation, and trainer config changes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SaProt Training Evaluation

Use this sub-skill when an agent needs to inspect or adapt SaProt training, downstream fine-tuning, ProteinGym or ClinVar zero-shot mutation benchmarks, ClinVar AUC aggregation, or PyTorch Lightning trainer settings. Default to diagnostics and small dry-runs; do not launch full pretraining, multi-GPU fine-tuning, or benchmark sweeps unless the user explicitly requests an expensive run.

## Route First

- For LMDB record schema, dataset construction, or YAML dataset placement depth, route to `datasets-configs`.
- For direct model loading, embeddings, single-sequence mutation scoring, or inverse folding, route to `model-inference`.
- For PDB/mmCIF to AA+3Di conversion, Foldseek sequence generation, or pLDDT masking mechanics, route to `structure-sequences`.

## Safe First Step

Always run the bundled config diagnostic before proposing or executing a launcher command:

```bash
python scripts/saprot_config_check.py -c <config.yaml> --repo-root . --check-exists
```

The checker reads YAML only and intentionally avoids importing Torch, PyTorch Lightning, Transformers, or SaProt modules. It reports top-level config sections, model and dataset dynamic module paths, dataset locations, `foldseek_path`, `log_dir`, `out_path`, Trainer accelerator/devices/precision/logger settings, and common expensive-run risks.

## Launcher Mental Model

SaProt training and fine-tuning use one YAML config with four main sections:

- `setting`: seed, distributed environment variables, optional WandB config, benchmark `dataset_dir`, and benchmark `out_path`.
- `model`: `model_py_path`, task-specific `kwargs`, optimizer kwargs, scheduler kwargs, checkpoint `save_path`, and checkpoint reload flags.
- `dataset`: `dataset_py_path`, dataloader kwargs, train/valid/test LMDB paths, tokenizer path, and task-specific dataset kwargs.
- `Trainer`: PyTorch Lightning settings such as `accelerator`, `devices`, `num_nodes`, `strategy`, `precision`, `logger`, max steps/epochs, validation cadence, and batch limits.

The training launcher loads the model, dataset, and trainer dynamically, runs `trainer.fit`, then reloads `model.save_path` as the best checkpoint before `trainer.test` when a save path exists. If LoRA is enabled, it reloads by passing `lora_config_path` through `model.kwargs`; otherwise it calls the model checkpoint loader.

The zero-shot launcher loads the same model/dataset/trainer pattern, iterates every dataset directory under `setting.dataset_dir`, assigns each directory to the datamodule test LMDB, runs `trainer.test`, and optionally writes one Spearman row per dataset to `setting.out_path`. ClinVar configs also set `model.kwargs.log_clinvar: true` and `model.kwargs.log_dir` so the mutation model writes per-protein CSV logs.

## Safe Adaptation Recipes

For a one-GPU dry-run, set `CUDA_VISIBLE_DEVICES` to one device, `Trainer.devices: 1`, keep `Trainer.accelerator: gpu`, use `Trainer.logger: false`, lower dataloader `num_workers`, and add small `limit_train_batches`, `limit_val_batches`, and `limit_test_batches` values if the launcher path supports them.

For a CPU-only diagnostic config, set `Trainer.accelerator: cpu`, `Trainer.devices: 1`, `Trainer.precision: 32`, `Trainer.logger: false`, and `dataset.dataloader_kwargs.num_workers: 0`. Do not expect large SaProt checkpoints or Foldseek mutation benchmarks to be practical on CPU; use this only to validate wiring.

For zero-shot benchmark smoke tests, point `setting.dataset_dir` at a tiny copied subset, write `setting.out_path` to a disposable local output file, keep `Trainer.devices: 1`, disable logging, and verify that `model.kwargs.foldseek_path`, `model.kwargs.config_path`, and all LMDB inputs exist relative to the intended working directory.

## ClinVar AUC Aggregation

Use the bundled AUC helper instead of hard-coded output paths:

```bash
python scripts/compute_clinvar_auc.py \
  --log-dir <clinvar-log-dir> \
  --labels-csv <ClinVar_labels.csv>
```

The helper validates log columns, validates label columns, handles exact duplicate rows, detects conflicting duplicates by default, filters ambiguous `0.5` labels, checks missing prediction rows, and computes ROC AUC without relying on repository-local paths.

## Task Family Map

- Pretraining uses the language-model task family with `saprot_lm_model`, Foldseek LMDBs, long max-step schedules, AdamW, and the ESM-style learning-rate scheduler.
- Thermostability uses regression with Spearman/loss-driven checkpointing and pLDDT-aware tokenization.
- EC and GO use annotation classification with Fmax-style validation metrics and ontology-specific `anno_type` values.
- DeepLoc and MetalIonBinding use classification models with task-specific label counts.
- HumanPPI uses the pairwise PPI model and smaller per-device batch sizes.
- Contact uses contact prediction with contact-specific precision metrics and typically disables WandB logging in the provided SaProt config.
- ProteinGym and ClinVar use zero-shot mutation models, Foldseek structure handling, Spearman for benchmark datasets, and ClinVar CSV logs for AUC aggregation.

## References

- `references/workflows.md` for training, fine-tuning, zero-shot, ClinVar, checkpoint, and distributed workflow details.
- `references/cli-reference.md` for safe diagnostic commands, launch templates, and config-edit checklists.
- `references/troubleshooting.md` for missing assets, wrong working directory, CUDA/DDP, WandB, dependency pins, Foldseek, and ClinVar merge failures.
