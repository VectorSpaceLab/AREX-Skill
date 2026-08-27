# Uncertainty Estimation, Calibration, and Evaluation

Chemprop uncertainty is a prediction-time workflow layered onto trained models through `chemprop predict`. The command loads model artifact(s), builds a test dataloader, optionally builds a calibration dataloader, runs an uncertainty estimator, optionally fits and applies a calibrator, optionally evaluates uncertainty metrics when test labels are present, then writes predictions and uncertainty columns.

## Prediction-Time Flags

Core uncertainty flags:

```bash
chemprop predict \
  --test-path test.csv \
  --model-path model.pt \
  --output preds.csv \
  --uncertainty-method <estimator> \
  --cal-path calibration.csv \
  --calibration-method <calibrator> \
  --evaluation-methods <evaluator> [<evaluator> ...]
```

Optional controls:

- `--uncertainty-dropout-p`: Monte Carlo dropout probability; default `0.1`.
- `--dropout-sampling-size`: number of dropout samples; default `10`.
- `--calibration-interval-percentile`: percentile used by interval calibrators; default `95` and must be between `1` and `100` for CLI use.
- `--conformal-alpha`: conformal target error rate; default `0.1` and must be between `0` and `1`.
- `--cal-descriptors-path`, `--cal-atom-features-path`, `--cal-atom-descriptors-path`, `--cal-bond-features-path`, `--cal-bond-descriptors-path`, and `--cal-constraints-path`: calibration-side versions of feature/descriptor/constraint side files.

The `--evaluation-methods` flag makes Chemprop read target columns from the test CSV. Do not use evaluation methods for unlabeled production inputs.

## Estimator Aliases

Available `--uncertainty-method` values:

| Estimator | Best fit | Notes |
| --- | --- | --- |
| `none` | Ordinary prediction | No uncertainty columns except special handling to collapse MVE/evidential/quantile model outputs to point predictions. |
| `mve` | `regression-mve` models | Interprets predictor output as mean and variance. |
| `ensemble` | Multiple compatible model artifacts | Uses variance across model predictions; requires more than one model. |
| `classification` | Binary classification probability output | Treats class-1 probability as uncertainty-like confidence for classification calibration/evaluation. |
| `evidential-total` | `regression-evidential` models | Uses evidential regression total uncertainty. |
| `evidential-epistemic` | `regression-evidential` models | Uses evidential epistemic component. |
| `evidential-aleatoric` | `regression-evidential` models | Uses evidential aleatoric component. |
| `dropout` | Models where MC dropout is acceptable | Runs repeated stochastic predictions using `--uncertainty-dropout-p` and `--dropout-sampling-size`. |
| `classification-dirichlet` | `classification-dirichlet` models | Binary Dirichlet classification uncertainty. |
| `multiclass-dirichlet` | `multiclass-dirichlet` models | Multiclass Dirichlet uncertainty. |
| `quantile-regression` | `regression-quantile` models | Produces interval-style uncertainty for quantile workflows and conformal regression. |

Compatibility is not only a flag choice: the trained predictor must emit the shape and semantics expected by the estimator. For example, `mve` needs an MVE regression predictor, evidential methods need evidential regression outputs, and Dirichlet methods need Dirichlet classification task types.

## Calibrator Aliases

Available `--calibration-method` values:

| Calibrator | Task family | Typical pairing |
| --- | --- | --- |
| `zscaling` | Regression variance | `mve`, `ensemble`, evidential, or dropout variance-like regression uncertainty. |
| `zelikman-interval` | Regression interval/variance | Uses `--calibration-interval-percentile` as a target percentile. |
| `mve-weighting` | Regression MVE ensembles | Fits weights over per-model variance predictions; requires individual MVE uncertainty outputs. |
| `conformal-regression` | Regression intervals | Often paired with `quantile-regression`; uses `--conformal-alpha`. |
| `platt` | Binary classification | Probability calibration for binary classification uncertainty. |
| `isotonic` | Binary classification | Nonparametric binary probability calibration. |
| `conformal-multilabel` | Multilabel/binary classification | Produces conformal label-set style outputs for multiple binary tasks. |
| `conformal-multiclass` | Multiclass classification | Conformal multiclass calibration. |
| `conformal-adaptive` | Multiclass classification | Adaptive multiclass conformal calibration. |
| `isotonic-multiclass` | Multiclass classification | Class-probability calibration for multiclass outputs. |

Calibration requires `--cal-path`. The calibration file must have the same molecular input layout as the test file and target columns corresponding to the model outputs. If training/prediction uses descriptors, atom features, atom descriptors, bond features, bond descriptors, constraints, reaction columns, or multicomponent SMILES columns, provide the matching calibration flags and files too.

## Evaluator Aliases

Available `--evaluation-methods` values:

| Evaluator | Requires labels? | Task family |
| --- | --- | --- |
| `nll-regression` | Yes | Regression variance likelihood. |
| `miscalibration_area` | Yes | Regression calibration curve area. |
| `ence` | Yes | Regression expected normalized calibration error. |
| `spearman` | Yes | Rank correlation between uncertainty and absolute error. |
| `conformal-coverage-regression` | Yes | Regression interval coverage. |
| `nll-classification` | Yes | Binary classification negative log likelihood. |
| `conformal-coverage-classification` | Yes | Binary/multilabel conformal coverage. |
| `nll-multiclass` | Yes | Multiclass negative log likelihood. |
| `conformal-coverage-multiclass` | Yes | Multiclass conformal coverage. |

Evaluation logs metric values; prediction outputs remain the main CSV or pickle file. Evaluators need labels in `--test-path`, not just `--cal-path`.

## Output Interpretation

- Point predictions are written to the model output columns loaded from the model artifact when available; otherwise Chemprop uses generic names such as `pred_0`.
- For uncertainty methods other than `none` and `classification`, Chemprop appends columns named like `<target>_unc` to the main prediction output.
- With multiple models, Chemprop also writes an `_individual` output file containing per-model prediction columns and, when applicable, per-model uncertainty columns.
- Multiclass prediction outputs include predicted class labels plus formatted probability strings.
- `none` with MVE, evidential, or quantile predictors collapses the predictor output to the point prediction component instead of writing uncertainty columns.

## Compatibility Recipes

### Regression MVE

Train with the MVE regression task, then predict with `mve`:

```bash
chemprop train \
  --data-path train.csv \
  --task-type regression-mve \
  --output-dir runs/mve

chemprop predict \
  --test-path test.csv \
  --model-path runs/mve/model_0/best.pt \
  --output test_mve.csv \
  --uncertainty-method mve
```

Add calibration and labels when available:

```bash
chemprop predict \
  --test-path test_with_targets.csv \
  --model-path runs/mve/model_0/best.pt \
  --output test_mve_calibrated.csv \
  --uncertainty-method mve \
  --cal-path calibration.csv \
  --calibration-method zscaling \
  --evaluation-methods nll-regression miscalibration_area ence spearman
```

### Ensemble Uncertainty

Use at least two model artifacts trained for the same schema and task:

```bash
chemprop predict \
  --test-path test.csv \
  --model-paths runs/replicate_0/model_0/best.pt runs/replicate_1/model_0/best.pt \
  --output ensemble_unc.csv \
  --uncertainty-method ensemble
```

Do not use `ensemble` with a single model path. Directory paths discover `.pt` model files recursively; `.ckpt` files must be passed explicitly.

### MC Dropout

Use when repeated stochastic dropout prediction is the intended uncertainty estimate:

```bash
chemprop predict \
  --test-path test.csv \
  --model-path model.pt \
  --output dropout_unc.csv \
  --uncertainty-method dropout \
  --uncertainty-dropout-p 0.1 \
  --dropout-sampling-size 30
```

Use larger sampling sizes for more stable estimates, but expect slower prediction.

### Quantile Conformal Regression

Use quantile regression outputs and conformal calibration:

```bash
chemprop train \
  --data-path train.csv \
  --task-type regression-quantile \
  --output-dir runs/quantile

chemprop predict \
  --test-path test_with_targets.csv \
  --model-path runs/quantile/model_0/best.pt \
  --output quantile_conformal.csv \
  --uncertainty-method quantile-regression \
  --cal-path calibration.csv \
  --calibration-method conformal-regression \
  --conformal-alpha 0.1 \
  --evaluation-methods conformal-coverage-regression
```

### Classification Calibration

For ordinary binary classification probabilities:

```bash
chemprop predict \
  --test-path test_with_targets.csv \
  --model-path binary_model.pt \
  --output binary_calibrated.csv \
  --uncertainty-method classification \
  --cal-path calibration.csv \
  --calibration-method platt \
  --evaluation-methods nll-classification
```

Use Dirichlet-specific estimators only with Dirichlet-trained classification or multiclass models.

## Calibration Data Alignment

When calibration fails or produces suspicious values, compare these between the test and calibration command segments:

- Same `--smiles-columns` or same `--reaction-columns` and reaction mode.
- Same descriptor source style: `--descriptors-path` / `--descriptors-columns` for test, and `--cal-descriptors-path` for calibration when side files are used.
- Same atom/bond feature and descriptor side-file shapes for test and calibration.
- Same constraints columns for atom/bond constrained prediction.
- Same featurizer mode and graph flags, especially for converted v1 models.
- Calibration target columns exist and correspond to the model output columns.

If evaluating uncertainty, the test CSV also needs labels; calibration labels alone are insufficient for `--evaluation-methods`.
