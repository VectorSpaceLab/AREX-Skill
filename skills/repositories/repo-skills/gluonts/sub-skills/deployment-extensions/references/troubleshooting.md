# Deployment and extension troubleshooting

## `python -m gluonts` fails before showing help

Cause: the package CLI imports Click. Install `click`, or install an extra that brings it transitively. Then rerun:

```bash
python -m gluonts --help
python -m gluonts version
```

## `python -m gluonts.shell --help` fails

Cause: shell dependencies are missing. Install the shell extra in the active environment:

```bash
pip install "gluonts[shell]"
```

The shell command group imports Waitress and uses Flask for serving. Missing `waitress`, `flask`, or Click means the container cannot serve.

## JSON warning about `orjson` or `ujson`

GluonTS may warn that it is using Python's standard `json` module and suggest `orjson` or `ujson` for speed. This is a performance warning, not a functional failure. Install a faster JSON backend only when serialization throughput matters.

## `ForecasterNotFound` or cannot locate estimator

Use a fully qualified import path for `--forecaster`, `GLUONTS_FORECASTER`, or root hyperparameter `forecaster_name`:

```text
gluonts.model.trivial.mean.MeanPredictor
gluonts.model.seasonal_naive.SeasonalNaivePredictor
gluonts.ext.prophet.ProphetPredictor
```

If the class lives in a dynamic code channel, ensure the code channel has been installed and the process has restarted before resolving the forecaster.

## Training cannot find `forecaster_name`

If neither `--forecaster` nor `GLUONTS_FORECASTER` is provided, the train command reads root hyperparameter `forecaster_name`. Put it at the root of `hyperparameters.json`, not under a custom namespace:

```json
{"forecaster_name": "gluonts.model.trivial.mean.MeanPredictor"}
```

## Training cannot infer frequency

The shell loads datasets with `FileDataset(freq=hyperparameters["freq"])`. Provide root hyperparameter `freq`, or provide a metadata channel whose `metadata.json` contains the frequency. Without `freq`, dataset loading fails before model training.

## Nested hyperparameters do not affect the model

Only root hyperparameters are passed to the forecaster by the built-in shell. `$env.*` keys become GluonTS runtime environment overrides. Other namespaces are decoded but unused unless custom training code consumes them.

For forecaster constructor parameters, keep keys at the root:

```json
{
  "prediction_length": "7",
  "freq": "D",
  "$env.use_tqdm": "false"
}
```

## Inference request validation fails

A normal `/invocations` payload must be a JSON object with `instances` as a list. Each instance must contain `start` and `target`; `configuration`, when present, must be a JSON object and should include `freq`.

Run:

```bash
python path/to/scripts/shell_payload_validator.py --input request.json
```

Common fixes:

- Encode `target` as a JSON list, not a string.
- Encode `start` as a timestamp string, such as `"2023-01-01"`.
- Put output controls under `configuration`, not beside each instance.
- Use `num_eval_samples` or `num_samples` as a positive integer.
- Use `output_types` values from `mean`, `samples`, and `quantiles`.

## Static serving returns dynamic-mode errors

If `GLUONTS_FORECASTER` is set, serving enters dynamic mode unless forced static. Remove the variable or set `GLUONTS_FORCE_STATIC=true` when serving a serialized predictor from the model directory.

## Dynamic serving repeatedly constructs slow predictors

Dynamic mode calls `from_hyperparameters(**configuration)` for each request. Avoid dynamic serving for expensive estimators or predictors that fit during prediction. Prefer static serving with a serialized predictor for trained models.

## Batch transform receives normal JSON envelope

Batch mode expects newline-delimited JSON instances, not `{ "instances": [...] }`. Supply the configuration in `INFERENCE_CONFIG` and set `SAGEMAKER_BATCH=true`. Each input line should be one instance object with fields such as `start`, `target`, and optional forwarded fields.

## Dynamic code channel behaves unexpectedly

The shell may install packages, copy modules, modify `PYTHONPATH`, and restart itself once. Use only trusted code channels. If the process keeps reloading, check that the reload marker is preserved and that package installation is not failing during startup.

## Optional adapter import fails

Install the adapter's extra and any non-Python dependencies:

| Adapter | Likely fix |
| --- | --- |
| Prophet | `pip install "gluonts[prophet]"` or install `prophet` directly. |
| R forecast | Install system R, `pip install "gluonts[R]"`, then install R packages `forecast`, `nnfor`, and/or `hts`. |
| statsforecast | `pip install "gluonts[statsforecast]"`. |
| hierarchicalforecast | `pip install "gluonts[hierarchicalforecast]"`. |
| Rotbaum | `pip install "gluonts[rotbaum]"`; add `gluonts[rotbaum-extra]` for LightGBM quantile regression; verify `skgarden` separately for QRF. |
| SageMaker SDK | `pip install "gluonts[sagemaker]"` for client-side job submission. |

Optional adapter imports were not part of the required verified backend gate; run a tiny adapter-specific smoke in the target environment before relying on one.

## AWS or Docker operation fails

This skill does not verify Docker build, registry push, SageMaker job submission, IAM permissions, or cloud networking. Treat these as environment/platform tasks. The verified local boundary is package CLI, shell command dispatch/help, payload validation, and distilled shell contracts.

## MXNet-related deployment request

MXNet modules and old container recipes are legacy in this skill scope. No MXNet extra was selected as a verified required workflow. Ask the user for a compatible MXNet environment and run separate backend verification before claiming support.
