# `chemprop train` CLI Reference

This is a practical reference for Chemprop 2.2.x `chemprop train`. Use `chemprop train --help` in the target environment to confirm exact parser choices exposed by that install.

## Core Invocation

```bash
chemprop train --data-path <csv> --task-type <task> --output-dir <dir>
```

Aliases:

- `-i` is an alias for `--data-path`.
- `-o` and `--save-dir` are aliases for `--output-dir`.
- `-t` is an alias for `--task-type`.
- `-l` is an alias for `--loss-function`.
- `--metric` is an alias for `--metrics`.
- `--split` is an alias for `--split-type`.
- `--agg` is an alias for `--aggregation`.
- `--features-generators` is an alias for `--molecule-featurizers` in verified 2.2.x behavior.

If `--output-dir` is omitted, Chemprop writes under a timestamped training directory derived from the input stem and environment defaults. Prefer an explicit output directory for reproducibility.

## Input Data Flags

| Flag | Use |
| --- | --- |
| `--data-path` / `-i` | One, two, or three CSV paths. One file is split; two means train/val source plus test file; three means train, val, test. |
| `--smiles-columns` / `-s` | One or more molecule SMILES column names. Defaults to the first CSV column if neither SMILES nor reaction columns are supplied. |
| `--reaction-columns` / `-r` | Reaction SMILES columns in `REACTANT>AGENT>PRODUCT` form. Route detailed reaction design to `../specialized-molecular-tasks/SKILL.md`. |
| `--target-columns` | Molecule-level target columns. Defaults to all non-input, non-ignored, non-split, non-weight columns. |
| `--ignore-columns` | Metadata columns to exclude from inferred targets. |
| `--weight-column` / `-w` | Per-row weights column. |
| `--no-header-row` | Treat input as headerless; default uses a header row. |
| `--descriptors-columns` | Extra datapoint descriptors stored in CSV columns. |
| `--descriptors-path` | External descriptor `.npz`; rows must align to the CSV. |
| `--atom-features-path`, `--bond-features-path` | External atom/bond feature `.npz`; may use component-index/path pairs for multicomponent data. |
| `--atom-descriptors-path`, `--bond-descriptors-path` | External atom/bond descriptors; ordering must match featurized molecules. |

Deep atom/bond/constraints and reaction schema details belong in `../specialized-molecular-tasks/SKILL.md`.

## Task Types

Supported task types verified for Chemprop 2.2.3:

- `regression`
- `regression-mve`
- `regression-evidential`
- `regression-quantile`
- `classification`
- `classification-dirichlet`
- `multiclass`
- `multiclass-dirichlet`
- `spectral`

Task type selects default predictor, loss, and metric behavior.

## Losses And Metrics

Important flags:

- `--loss-function`: training loss; if omitted, Chemprop uses the task default.
- `--metrics` / `--metric`: one or more evaluation metrics. If `--tracking-metric` is not set, the training criterion/default validation loss behavior is used for checkpointing.
- `--tracking-metric`: metric monitored for early stopping/checkpointing and hpopt objective selection. Defaults to `val_loss`.
- `--show-individual-scores`: show per-target scores.
- `--task-weights`: target task weights in the loss.

Common compatibility table:

| Task | Common losses | Common metrics |
| --- | --- | --- |
| `regression` | `mse`, `mae`, `rmse`, `bounded-mse`, `bounded-mae`, `bounded-rmse` | `rmse`, `mae`, `mse`, `bounded-mae`, `bounded-mse`, `bounded-rmse`, `r2` |
| `regression-mve` | `mve` | `rmse`, `mae`, `mse`, `r2` |
| `regression-evidential` | `evidential` | `rmse`, `mae`, `mse`, `r2` |
| `regression-quantile` | `quantile`, `pinball`, `quantile-point`, `pinball-point` | `rmse`, `mae`, `mse` |
| `classification` | `bce`, `binary-mcc`, `dirichlet` | `roc`, `prc`, `accuracy`, `f1`, `bce`, `binary-mcc` |
| `multiclass` | `ce`, `multiclass-mcc`, `dirichlet` | `ce`, `multiclass-mcc` |
| `spectral` | `sid`, `earthmovers`, `wasserstein` | `sid`, `wasserstein` |

Additional verified registry names include `nlogprob_enrichment`. Use `chemprop train --help` to confirm final names accepted by the active environment.

Tracking rule: `--tracking-metric` must be `val_loss` or a metric available through the selected task defaults or `--metrics`. For mixed molecule/atom/bond targets, append `-mol`, `-atom`, or `-bond` for non-default target-specific metrics.

## Training Hyperparameters

Common flags:

- `--epochs`: number of epochs; default is 50.
- `--warmup-epochs`: linear warmup epochs; default is 2.
- `--init-lr`, `--max-lr`, `--final-lr`: learning-rate schedule values.
- `--batch-size` / `-b`: batch size; default is 64.
- `--num-workers` / `-n`: dataloader workers; default is 0.
- `--patience`: early stopping patience.
- `--min-delta`: minimum monitored-metric improvement.
- `--grad-clip`: Lightning trainer gradient clipping value.
- `--pytorch-seed`: seed for PyTorch initialization/randomness.
- `--accelerator`, `--devices`: passed to Lightning Trainer. Use `--accelerator cpu` for deterministic local smoke tests.

Validation rule: `--epochs` must be greater than `--warmup-epochs` unless using the special installed behavior for `--epochs -1`.

## Model Architecture Flags

Common message-passing and FFN flags:

- `--message-hidden-dim`: message hidden dimension; single-component data accepts one value.
- `--depth`: message-passing steps; single-component data accepts one value.
- `--dropout`: dropout probability.
- `--activation`: activation name from installed PyTorch activation choices.
- `--aggregation` / `--agg`: graph aggregation mode; verified modes include `mean`, `sum`, and `norm`.
- `--aggregation-norm`: normalization factor for `norm` aggregation.
- `--atom-messages`: pass messages on atoms rather than bonds.
- `--ffn-hidden-dim`: FFN hidden dimensions. One value expands to `--ffn-num-layers`; multiple values imply per-layer dimensions.
- `--ffn-num-layers`: FFN hidden-layer count.
- `--batch-norm`: add batch normalization after aggregation.
- `--multiclass-num-classes`: class count for multiclass tasks.

Pitfalls:

- Single-component data rejects multiple `--message-hidden-dim` or `--depth` values.
- `--mpn-shared` cannot be combined with component-specific `--message-hidden-dim` or `--depth` values.
- Multiple `--ffn-hidden-dim` values must match `--ffn-num-layers`.

## Split Flags

| Flag | Use |
| --- | --- |
| `--split-type` / `--split` | Split method; default is `random`. Choices are case-insensitive registry names. |
| `--split-sizes` | Three floats for train/validation/test proportions; default `0.8 0.1 0.1`. |
| `--split-key-molecule` | Component index for constrained multicomponent split types. |
| `--num-replicates` | Number of replicate split/training runs. |
| `--splits-column` | CSV column containing `train`, `val`, or `test`. |
| `--splits-file` | JSON split file with zero-indexed lists/ranges. |
| `--data-seed` | Split seed; replicates add 1 to this seed. |
| `--save-smiles-splits` | Save split SMILES files. |
| `--save-data-splits` | Save split data files and aligned feature/descriptor split files. |

`-k` / `--num-folds` was removed; use `--num-replicates`.

## Config Files

`--config-path` points to a config file parsed by the CLI. Command-line arguments override config values. Every training run writes `config.toml` into the output directory before training starts.

Recommended workflow:

1. Run a small explicit smoke command with `--epochs 3`.
2. Inspect the generated `config.toml`.
3. Reuse it with `--config-path` and explicit command-line overrides such as `--epochs` and a new `--output-dir`.

## Transfer And Foundation Flags

- `--checkpoint`: load weights from checkpoint/model files, directories, or lists.
- `--freeze-encoder`: freeze message-passing weights from `--checkpoint`; requires `--checkpoint`.
- `--frzn-ffn-layers`: freeze the first `n` FFN layers; requires checkpoint/frozen-model setup.
- `--from-foundation`: initialize message passing from a named foundation model or a local model file.
- `--model-frzn`: deprecated compatibility path; prefer `--checkpoint` with `--freeze-encoder`.

Validation rules:

- `--checkpoint` and `--from-foundation` are mutually exclusive.
- `--checkpoint` and `--model-frzn` are mutually exclusive.
- `--freeze-encoder` without `--checkpoint` is invalid.
- `--frzn-ffn-layers > 0` with `--checkpoint` also requires `--freeze-encoder`.
- Named foundation models may download on first use and can ignore message-passing architecture flags.

## Featurization Flags

- `--molecule-featurizers` / `--features-generators`: registry-backed molecule featurizers. Verified names include `morgan_binary`, `morgan_count`, `rdkit_2d`, `v1_rdkit_2d`, `v1_rdkit_2d_normalized`, and `charge`.
- `--multi-hot-atom-featurizer-mode`: atom feature mode; common modes include `V2`, `V1`, `ORGANIC`, and `RIGR`.
- `--keep-h`, `--add-h`, `--ignore-stereo`, `--reorder-atoms`: molecule parsing/featurization behavior.
- `--rxn-mode` / `--reaction-mode`: reaction featurization mode for reaction workflows.
- `--use-cuikmolmaker-featurization`: optional accelerated featurizer requiring optional `cuik_molmaker` support.

Do not include `--use-cuikmolmaker-featurization` unless that optional package is installed and compatible with the requested flags.

## Output Structure

Single replicate, single model:

```text
<output-dir>/
  config.toml
  model_0/
    best.pt
    checkpoints/
      last.ckpt
    trainer_logs/
      version_0/
    test_predictions.csv
```

Replicates and ensembles nest model directories:

```text
<output-dir>/
  replicate_0/
    model_0/
    model_1/
  replicate_1/
    model_0/
    model_1/
```

Split-saving flags add files such as `splits.json`, `train_smiles.csv`, `val_smiles.csv`, `test_smiles.csv`, `train.csv`, `val.csv`, `test.csv`, and aligned feature/descriptor split files.

## Hpopt Adjacent Flags

`chemprop hpopt` accepts shared training flags plus search/resource flags, including:

- `--search-parameter-keywords`: `basic`, `learning_rate`, `all`, or individual search parameters.
- `--hpopt-save-dir`: output directory for optimization results.
- `--raytune-num-samples`: number of trials.
- `--raytune-search-algorithm`: `random`, `hyperopt`, or `optuna`.
- `--raytune-trial-scheduler`: `FIFO` or `AsyncHyperBand`.
- `--raytune-num-workers`, `--raytune-use-gpu`, `--raytune-num-cpus`, `--raytune-num-gpus`, `--raytune-max-concurrent-trials`: resource controls.

Hpopt requires optional dependencies. Keep training command correctness here, and route deep search-space/resource tuning elsewhere.

## Help And Registry Inspection

Use:

```bash
chemprop train --help
chemprop hpopt --help
```

Confirm installed choices for activations, aggregations, featurizers, losses, metrics, split types, and foundation models before promising exact registry compatibility in a user's environment.
