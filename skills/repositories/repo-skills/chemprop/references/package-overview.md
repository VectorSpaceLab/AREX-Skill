# Chemprop Package Overview

## What Chemprop Provides

Chemprop is a molecular property prediction toolkit centered on message passing neural networks. In version 2.2.3 it provides:

- A `chemprop` CLI with `train`, `predict`, `fingerprint`, `convert`, and `hpopt` subcommands.
- Public Python APIs under `chemprop.data`, `chemprop.featurizers`, `chemprop.models`, `chemprop.nn`, and `chemprop.uncertainty`.
- Molecule, reaction, multicomponent, atom/bond, spectral, and uncertainty-aware task families.
- Checkpoint/model save-load helpers for downstream prediction and fingerprint generation.

## Core CLI Modes

| Mode | Purpose | Owning sub-skill |
| --- | --- | --- |
| `train` | Train models from CSV inputs with task, split, metric, loss, architecture, and trainer flags | `training-cli` |
| `predict` | Generate predictions from `.pt`, `.ckpt`, or directories of model files | `prediction-fingerprints` |
| `fingerprint` | Extract learned representations from a chosen FFN block | `prediction-fingerprints` |
| `convert` | Convert v1 or early v2 model files into newer v2 formats | `uncertainty-advanced` |
| `hpopt` | Run Ray Tune hyperparameter optimization | `uncertainty-advanced` with training handoff |

## Verified Registry Values

Task/predictor types include `regression`, `regression-mve`, `regression-evidential`, `regression-quantile`, `classification`, `classification-dirichlet`, `multiclass`, `multiclass-dirichlet`, and `spectral`.

Common losses and metrics include:

- Regression losses/metrics: `mse`, `mae`, `rmse`, `bounded-mse`, `bounded-mae`, `bounded-rmse`, `r2`.
- Classification/multiclass: `bce`, `ce`, `binary-mcc`, `multiclass-mcc`, `roc`, `prc`, `accuracy`, `f1`, `dirichlet`.
- Uncertainty/special losses: `mve`, `evidential`, `quantile-point`, `pinball-point`, `quantile`, `pinball`, `sid`, `earthmovers`, `wasserstein`, `nlogprob_enrichment`.

Molecule featurizers include `morgan_binary`, `morgan_count`, `rdkit_2d`, `v1_rdkit_2d`, `v1_rdkit_2d_normalized`, and `charge`. Aggregations include `mean`, `sum`, and `norm`.

Uncertainty estimators include `none`, `mve`, `ensemble`, `classification`, `evidential-total`, `evidential-epistemic`, `evidential-aleatoric`, `dropout`, `classification-dirichlet`, `multiclass-dirichlet`, and `quantile-regression`.

Uncertainty calibrators include `zscaling`, `zelikman-interval`, `mve-weighting`, `conformal-regression`, `platt`, `isotonic`, `conformal-multilabel`, `conformal-multiclass`, `conformal-adaptive`, and `isotonic-multiclass`.

Uncertainty evaluators include `nll-regression`, `miscalibration_area`, `ence`, `spearman`, `conformal-coverage-regression`, `nll-classification`, `conformal-coverage-classification`, `nll-multiclass`, and `conformal-coverage-multiclass`.

## Dependency Notes

Core Chemprop usage requires Python `>=3.11,<3.15`, PyTorch, Lightning, RDKit, NumPy, pandas, scikit-learn, SciPy, astartes, ConfigArgParse, rich, and descriptastorus. Hyperparameter optimization requires the optional hpopt dependencies. Accelerated featurization with `cuik-molmaker` is optional and should not be assumed available.

## Output Artifacts

Training normally writes a `config.toml`, model subdirectories, best model files, checkpoint files, trainer logs, split files when requested, and prediction outputs when a test set is available. Prediction can write CSV or pickle outputs. Fingerprints can write CSV or NPZ outputs. Exact naming varies with ensembles, replicates, and model directories; use the owning sub-skill for details.
