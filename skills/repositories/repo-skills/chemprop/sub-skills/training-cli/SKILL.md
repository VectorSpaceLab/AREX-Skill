---
name: training-cli
description: "Build, validate, and troubleshoot Chemprop CLI training commands,
  including task/loss/metric choices, split handling, config files,
  transfer/foundation starts, ensembles, replicates, outputs, and hpopt
  handoff."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Chemprop Training CLI

Use this sub-skill when the user wants to design, review, debug, or smoke-test a `chemprop train` command. It covers Chemprop 2.2.x molecule-level CLI training workflows plus training-adjacent handoff to `chemprop hpopt`.

## Route Here For

- Creating `chemprop train` commands for regression, binary classification, multiclass, and spectral tasks.
- Choosing `--task-type`, `--loss-function`, `--metrics`, and `--tracking-metric` combinations.
- Handling CSV schemas, inferred targets, missing target cells, split columns/files, separate CSVs, replicates, ensembles, and saved split outputs.
- Reusing `config.toml`, explaining command-line overrides, and diagnosing config-based reruns.
- Transfer/foundation initialization with `--checkpoint`, `--freeze-encoder`, `--frzn-ffn-layers`, or `--from-foundation`.
- Preparing a training command that can later be adapted for `chemprop hpopt`.

## Route Elsewhere

- Prediction or fingerprint commands after a model exists: use `../prediction-fingerprints/SKILL.md`.
- Python API datasets, modules, model construction, or training loops: use `../python-api-modeling/SKILL.md`.
- Deep reaction, multicomponent, atom/bond, constraints, or schema design beyond basic routing: use `../specialized-molecular-tasks/SKILL.md`.
- Deep Ray Tune search-space design, uncertainty calibration, conformal analysis, or advanced uncertainty outputs: use `../uncertainty-advanced/SKILL.md`.

## Fast Start

Minimal regression smoke test:

```bash
chemprop train \
  --data-path data.csv \
  --task-type regression \
  --epochs 3 \
  --num-workers 0 \
  --accelerator cpu \
  --output-dir runs/regression_smoke
```

Explicit binary classification command:

```bash
chemprop train \
  --data-path toxicity.csv \
  --smiles-columns smiles \
  --target-columns tox_a tox_b tox_c \
  --task-type classification \
  --metrics roc prc accuracy f1 \
  --tracking-metric prc \
  --class-balance \
  --output-dir runs/toxicity_cls
```

Generate a shell-safe command without running Chemprop:

```bash
python sub-skills/training-cli/scripts/chemprop_train_command_builder.py \
  --data-path trainval.csv test.csv \
  --smiles-columns smiles \
  --target-columns y \
  --task-type regression \
  --split-sizes 0.9 0.1 0.0 \
  --epochs 3 \
  --output-dir runs/two_file_smoke
```

## Required Reading

- `references/training-workflows.md`: practical commands for common training patterns, config reuse, transfer/foundation starts, and hpopt handoff.
- `references/cli-reference.md`: task/loss/metric tables, important flags, split semantics, output structure, and validation rules.
- `references/data-formats.md`: CSV/header/target inference, missing labels, split schemas, separate files, descriptors/features, and two/three path semantics.
- `references/troubleshooting.md`: fixes for common failures including removed `-k`, split errors, class balance misuse, config override surprises, CPU/CUDA issues, and checkpoint/freeze conflicts.
- `scripts/chemprop_train_command_builder.py`: self-contained command printer with lightweight schema and flag checks.

## Command Design Checklist

1. Confirm the installed `chemprop` CLI is available and compatible with Python 3.11 through less than 3.15.
2. Use CSV training inputs; expect a header row unless `--no-header-row` is deliberate.
3. Prefer explicit `--smiles-columns` and `--target-columns` when the CSV contains metadata, split, descriptor, or weight columns.
4. Match task semantics: continuous values for regression/spectral, `0`/`1` or blank for binary classification, class ids for multiclass.
5. Choose a split strategy: default random, scaffold-style, user split column, JSON split file, or two/three separate CSV files.
6. Set a stable `--output-dir`, then inspect `config.toml`, `model_*/best.pt`, logs, predictions, and saved split files as needed.
7. Keep `--tracking-metric` as `val_loss` or include the tracked metric in `--metrics`.
8. For local debugging, add `--epochs 3 --num-workers 0 --accelerator cpu` before scaling up.

## Safe Defaults

- Start with `--epochs 3` for schema validation, then increase for real training.
- Add `--output-dir runs/<experiment>` rather than relying on timestamped defaults.
- Use `--num-workers 0` when diagnosing hangs or working on Windows/macOS.
- Use `--accelerator cpu` when GPU availability is uncertain.
- Use `--save-data-splits` or `--save-smiles-splits` when split reproducibility matters.
- Use `--split-sizes 0.8 0.1 0.1` for one-file random/scaffold splits and `--split-sizes 0.9 0.1 0.0` for two-file trainval/test workflows.

## Task Types At A Glance

- `regression`: continuous targets; common metrics include `rmse`, `mae`, `mse`, and `r2`.
- `regression-mve`, `regression-evidential`, `regression-quantile`: training variants for uncertainty-related regression; route calibration and interpretation elsewhere.
- `classification`: binary targets with `0`, `1`, or blank labels; supports `--class-balance`.
- `classification-dirichlet`: uncertainty-aware binary classification training; route calibration elsewhere.
- `multiclass`: integer class labels; set `--multiclass-num-classes` when needed.
- `multiclass-dirichlet`: uncertainty-aware multiclass training; route calibration elsewhere.
- `spectral`: spectral vector targets; common losses/metrics include `sid` and `wasserstein`.

## Output Expectations

A single-replicate, single-model run usually writes:

```text
<output-dir>/
  config.toml
  model_0/
    best.pt
    checkpoints/last.ckpt
    trainer_logs/version_0/
    test_predictions.csv
```

With replicates and ensembles, outputs nest under directories such as `replicate_2/model_1/`. If split saving is enabled, expect files such as `splits.json`, `train_smiles.csv`, `val_smiles.csv`, `test_smiles.csv`, and optionally split CSV/feature files.

## Common Pitfalls

- `-k` / `--num-folds` was removed; use `--num-replicates`.
- With two `--data-path` CSVs, the second is the test set; set the test split fraction to `0.0` unless using split column/file behavior.
- `--class-balance` is only valid for `--task-type classification`.
- Command-line flags override values from `--config-path`.
- `--freeze-encoder` requires `--checkpoint`; `--checkpoint` and `--from-foundation` are mutually exclusive.
- Foundation model downloads may require network/cache availability and can ignore message-passing architecture flags.
- Optional `cuik_molmaker` and hpopt/Ray Tune dependencies are not needed for ordinary training.

## Evidence Base

This sub-skill distills Chemprop 2.2.3 behavior from CLI training and hpopt parser code, shared CLI parsing utilities, public training/hpopt documentation, and CLI tests covering regression, classification, parser rules, split columns/files, separate data files, config round trips, output structure, replicates, and ensembles. The runtime content is self-contained and does not require reopening repository docs or tests.
