# Deployment workflows

## Shell container contract

A GluonTS shell deployment container should install GluonTS with the shell dependencies and use the module entrypoint:

```Dockerfile
RUN pip install "gluonts[shell]"
ENTRYPOINT ["python", "-m", "gluonts.shell"]
```

Add model-specific extras in the same environment when the selected forecaster requires them, for example `gluonts[torch,shell]`, `gluonts[prophet,shell]`, or `gluonts[R,shell]` plus the non-Python requirements of that adapter. Old MXNet-oriented container recipes are legacy reference material only and are not a verified workflow in this skill.

The shell dispatches the container command to either:

```bash
python -m gluonts.shell train
python -m gluonts.shell serve
```

The bundled skill scripts intentionally do not build images, start `serve`, or call AWS.

## Training workflow

The training command constructs a SageMaker-style training environment from a data root with config, data channels, model, and output folders. In SageMaker this layout is mounted automatically; for local tests create the same shape explicitly.

Key inputs:

| Input | Effect |
| --- | --- |
| `hyperparameters.json` | Decoded into shell hyperparameters; root keys are passed to the forecaster. |
| `inputdataconfig.json` | Optional channel manifest. If absent, channels are discovered by listing the data channel directory. |
| `train` channel | Required for estimator/predictor construction through `from_inputs`. |
| `validation` channel | Optional validation dataset passed to trainable estimators when accepted. |
| `test` channel | Optional evaluation dataset; shell logs aggregate test scores and writes metrics into the model output. |
| `metadata` channel | If present, `metadata.json` supplies `freq` and injects it into hyperparameters. |
| `model` channel | Optional prior serialized predictor archive for incremental training workflows. |
| `code` channel | Optional dynamic code/dependency channel; see the dynamic code caveat below. |

Forecaster selection order:

1. `--forecaster` command-line option.
2. `GLUONTS_FORECASTER` environment variable.
3. Root hyperparameter `forecaster_name`.

Always use a fully qualified import path. If the selected class resolves to a `Predictor`, the shell skips training and can still run test evaluation. If it resolves to an `Estimator`, the shell trains it and serializes the resulting `Predictor`.

### Hyperparameter decoding and nesting

SageMaker passes hyperparameters as strings. GluonTS decodes values that look like JSON lists or dicts and leaves other strings alone. Integer-like strings are usually coerced later by validated model constructors.

Large encoded strings may be split into keys like `_0_name`, `_1_name`, then reassembled before decoding.

Nested keys use a `$namespace.field` prefix. Examples:

```json
{
  "prediction_length": "14",
  "forecaster_name": "gluonts.model.trivial.mean.MeanPredictor",
  "$env.num_workers": "4",
  "$evaluation.quantiles": "[0.1, 0.5, 0.9]"
}
```

Built-in shell handling consumes:

- the empty top-level namespace as forecaster hyperparameters;
- the `$env.*` namespace as GluonTS runtime environment overrides.

Other namespaces are decoded but are not used by the built-in train command unless custom code consumes them.

Common built-in hyperparameters with shell behavior include `freq`, `prediction_length`, `listify_dataset`, `num_workers`, `num_prefetch`, `shuffle_buffer_length`, and `test_quantiles`.

## Serving workflow

`python -m gluonts.shell serve` creates a Flask app and serves it through Waitress on port `8080` inside the container.

Routes:

| Route | Meaning |
| --- | --- |
| `/ping` | Health check; returns an empty successful response when the app is live. |
| `/execution-parameters` | Reports SageMaker transform limits such as max payload and worker count. |
| `/invocations` | Scores normal JSON envelopes or batch JSON Lines depending on batch mode. |

### Static serving

Use static serving when a trained predictor has already been serialized into the model directory. Do not set `GLUONTS_FORECASTER`, or set `GLUONTS_FORCE_STATIC=true` if a forecaster value is present but should be ignored.

The request `configuration` still controls output formatting and `ListDataset` frequency. It does not construct the predictor in static mode.

### Dynamic serving

Use dynamic serving when `--forecaster` or `GLUONTS_FORECASTER` names a predictor class. The server constructs a predictor for each request by calling `from_hyperparameters(**configuration)`.

Dynamic mode is useful for lightweight predictors such as mean, seasonal naive, constant-value, or optional adapter predictors, but it can be expensive if the predictor performs fitting inside prediction. Keep `configuration` limited to fields accepted by the target predictor plus GluonTS serving fields.

## Normal inference payload

The non-batch `/invocations` request is a JSON object:

```json
{
  "instances": [
    {"start": "2023-01-01", "target": [1.0, 2.0, 3.0, 4.0]}
  ],
  "configuration": {
    "freq": "D",
    "prediction_length": 2,
    "num_eval_samples": 100,
    "output_types": ["mean", "quantiles"],
    "quantiles": ["0.1", "0.5", "0.9"]
  }
}
```

Rules distilled from the serving app:

- Top-level `instances` must be a list.
- Each instance is a GluonTS `ListDataset` entry; at minimum provide `start` and `target`.
- `configuration.freq` is required by the serving config and by `ListDataset`.
- `num_eval_samples` is the accepted alias for the number of forecast samples; `num_samples` is the internal field name.
- `output_types` may include `mean`, `quantiles`, and `samples`.
- `quantiles` are strings such as `"0.1"`, `"0.5"`, and `"0.9"`.
- Non-batch responses are JSON with a `predictions` field containing encoded forecast outputs.

Validate request envelopes with `scripts/shell_payload_validator.py` before sending them to a service.

## Batch transform JSON Lines

Batch mode is enabled by setting `SAGEMAKER_BATCH=true`. In this mode:

- `INFERENCE_CONFIG` supplies the JSON configuration normally sent inside the request envelope. Include at least `freq`; include output controls such as `output_types`, `quantiles`, and `num_eval_samples` as needed.
- The `/invocations` body is newline-delimited JSON: one instance per line, not a top-level `instances` envelope.
- Output is newline-delimited JSON, one prediction per line.
- `GLUONTS_FORWARD_FIELDS` can be a JSON list of input fields to copy from each input record into the corresponding output prediction.
- `GLUONTS_BATCH_TIMEOUT`, `GLUONTS_BATCH_FALLBACK_PREDICTOR`, and `GLUONTS_BATCH_SUPPRESS_ERRORS` control timeout and error behavior.

The bundled validator checks normal JSON envelopes. For batch payloads, validate each line as a standalone instance object and separately validate the `INFERENCE_CONFIG` JSON.

## Dynamic code channel caveat

A `code` channel is powerful and should be treated as trusted code only. The shell can install or copy code from that channel, update `PYTHONPATH`, set a reload marker, and restart the Python process. Supported dynamic code shapes include:

- folders with `setup.py`, installed with `pip` into the runtime code package area;
- folders with `__init__.py`, copied as Python packages;
- `.py` files, copied as modules;
- requirements files, installed with `pip`;
- tar or zip archives, unpacked and then processed recursively.

Training also copies the code channel into the serialized model so serving can apply the same dynamic-code logic. Because this can execute package installation and arbitrary import code, use it only in controlled, reproducible containers.

## SageMaker SDK boundary

The shell runtime does not require the SageMaker Python SDK to parse mounted training/serving files. Install `gluonts[sagemaker]` only when the task is to create or submit SageMaker jobs from Python. AWS credentials, Docker registry access, and cloud permissions are outside this skill's verified local runtime scope.
