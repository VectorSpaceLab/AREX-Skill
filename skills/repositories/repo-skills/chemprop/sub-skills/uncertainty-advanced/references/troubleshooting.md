# Troubleshooting Advanced Chemprop Workflows

Use this guide when uncertainty, hpopt, conversion, transfer/foundation, or interpretation-adjacent workflows fail.

## Missing Hpopt Dependencies

Symptoms:

- `chemprop hpopt` fails while `chemprop train` works.
- Import errors mention Ray Tune, HyperOptSearch, OptunaSearch, `hyperopt`, or `optuna`.

Fixes:

- Install Chemprop with the hpopt extra or install Ray Tune plus the selected search backend in the active environment.
- Use `--raytune-search-algorithm random` when HyperOpt/Optuna-specific packages are not available.
- For quick validation, run a short `chemprop train` before hpopt to separate data/schema errors from Ray dependency errors.
- Reduce concurrency with `--raytune-max-concurrent-trials`, `--raytune-num-workers 1`, and explicit CPU/GPU resource flags if Ray over-allocates resources.

## Calibration Dataset Feature Mismatch

Symptoms:

- Calibration fails while plain prediction succeeds.
- Shape errors mention descriptors, atom features, bond features, constraints, or featurizer dimensions.
- Calibrated uncertainty values are nonsensical compared with uncalibrated outputs.

Fixes:

- Ensure `--cal-path` uses the same molecular schema as `--test-path`: same SMILES/reaction/multicomponent columns and same header behavior.
- Mirror test-time side files with calibration-side flags: `--cal-descriptors-path`, `--cal-atom-features-path`, `--cal-atom-descriptors-path`, `--cal-bond-features-path`, `--cal-bond-descriptors-path`, and `--cal-constraints-path`.
- Keep feature side-file row order aligned with calibration CSV row order.
- Use the same graph flags and featurizer mode for calibration and test data.
- If using converted v1 models, add `--multi-hot-atom-featurizer-mode v1` to the prediction/calibration command.

## Evaluator Requires Target Labels

Symptoms:

- `--evaluation-methods` fails on an unlabeled production CSV.
- Errors mention missing target columns, output columns, masks, or labels.

Fixes:

- Use `--evaluation-methods` only when `--test-path` contains target labels matching the model output columns.
- Do not assume `--cal-path` labels are enough; evaluators score test predictions against test labels.
- For production inference, omit `--evaluation-methods` and keep calibration only if `--cal-path` is available.
- For bounded regression losses, ensure the test CSV target columns use the expected bounded format when evaluation is requested.

## Incompatible Method and Model Task

Symptoms:

- Tensor shape errors during uncertainty estimation.
- MVE/evidential/quantile estimators fail on ordinary regression models.
- Dirichlet estimators fail on ordinary classification or multiclass models.
- `ensemble` reports it needs multiple models.

Fixes:

- Match estimator to training task family:
  - `mve` with `regression-mve`.
  - `evidential-total`, `evidential-epistemic`, or `evidential-aleatoric` with `regression-evidential`.
  - `quantile-regression` with `regression-quantile`.
  - `classification-dirichlet` with `classification-dirichlet`.
  - `multiclass-dirichlet` with `multiclass-dirichlet`.
  - `classification` with ordinary binary classification probabilities.
- For `ensemble`, pass at least two compatible model files or directories that discover multiple `.pt` files.
- First run with `--uncertainty-method none` to prove model loading and data parsing before adding advanced uncertainty flags.

## Conformal Alpha and Interval Problems

Symptoms:

- Conformal calibration errors mention `alpha` bounds.
- Coverage is trivially high or intervals are unexpectedly wide.
- Conformal regression behaves like a constant interval around point predictions.

Fixes:

- Keep `--conformal-alpha` in the `(0, 1)` range for practical CLI use.
- Use enough calibration examples; if alpha is too small relative to calibration size, conformal quantiles can become trivial.
- Pair `conformal-regression` with `quantile-regression` when possible; otherwise it can fall back to intervals around point predictions.
- Use `conformal-coverage-regression`, `conformal-coverage-classification`, or `conformal-coverage-multiclass` only when test labels are present.

## V1 Conversion and Featurizer Mode

Symptoms:

- Converted v1 model loads but prediction fails with featurizer dimension mismatch.
- Warning says v1 default featurizer dimensions match and Chemprop is switching featurizers.
- Reaction-solvent or multicomponent converted models appear to swap component order.

Fixes:

- After `chemprop convert --conversion v1_to_v2`, run prediction with `--multi-hot-atom-featurizer-mode v1`.
- Reuse the same SMILES/reaction columns and side-feature flags that the original model expected.
- Let Chemprop's prediction loader handle the known v1 reaction-solvent component-order correction, but make the command explicit when possible.
- Confirm the converted output path ends in `.pt`.

## Foundation Model Download or Local Path Issues

Symptoms:

- `--from-foundation` fails with an unknown model name or missing local file.
- Training tries to download a foundation model but the environment lacks network/cache access.
- Chemprop rejects the featurizer mode for the foundation model.
- Hpopt appears not to search message-passing parameters.

Fixes:

- Use a recognized foundation model name or a real local model file path.
- If network access is unavailable, provide a local foundation model file instead of relying on download.
- For CheMeleon, use V2 atom featurization.
- Do not combine `--checkpoint` and `--from-foundation`; choose one initialization source.
- Expect hpopt to prune foundation-owned message-passing parameters.

## Transfer Freeze Conflicts

Symptoms:

- Errors mention `--freeze-encoder`, `--checkpoint`, `--frzn-ffn-layers`, or deprecated `--model-frzn`.

Fixes:

- Use `--checkpoint` to load pretrained weights.
- Add `--freeze-encoder` when freezing the message-passing layer.
- Add `--frzn-ffn-layers <n>` only when using `--checkpoint` and, with checkpoint transfer, pair it with `--freeze-encoder`.
- Avoid the deprecated `--model-frzn`; use `--checkpoint --freeze-encoder` instead.

## Interpretation Workflow Confusion

Symptoms:

- The user asks for interpretation but the implementation path could be CLI prediction, Python API inference, or a custom search loop.

Fixes:

- Ask what output the interpretation loop needs: point predictions, uncertainty columns, fingerprints, gradients/attributions, or custom model calls.
- Use `prediction-fingerprints` for CLI prediction and representation extraction.
- Use `python-api-modeling` for custom model calls or dataloaders.
- Use this sub-skill when the interpretation plan depends on uncertainty calibration, foundation/transfer provenance, or conversion compatibility.
