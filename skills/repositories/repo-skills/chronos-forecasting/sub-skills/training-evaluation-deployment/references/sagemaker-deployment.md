# SageMaker deployment reference

## Scope
This file is a deployment reference only. It describes the AWS/SageMaker workflow shape for Chronos-2, but it does not execute cloud actions or assume credentials.

For local use, prefer the in-process Chronos pipeline APIs instead of deploying an endpoint.

## Deployment modes

### 1) Real-time inference with JumpStart
This is the simplest AWS path.

Typical shape:

```python
from sagemaker.jumpstart.model import JumpStartModel

js_model = JumpStartModel(
    model_id="pytorch-forecasting-chronos-2",
    instance_type="ml.g5.2xlarge",
    role=role,
)

predictor = js_model.deploy()
```

Notes:
- use a SageMaker execution role, or `None` only when the notebook runtime already has the correct role
- JumpStart fills in the image and deployment details for you
- the endpoint keeps billing until you delete it
- CPU instance types are supported, but GPU is the more common low-latency path for large requests

### 2) Serverless inference
Serverless inference is CPU-only and requires a repackaged model artifact.

Typical shape:

```python
from sagemaker.serverless import ServerlessInferenceConfig

serverless_predictor = chronos_model.deploy(
    serverless_inference_config=ServerlessInferenceConfig(
        memory_size_in_mb=6144,
        max_concurrency=1,
    ),
    serializer=JSONSerializer(),
    deserializer=JSONDeserializer(),
)
```

Notes:
- CPU only
- cold starts are expected
- 6 GB is the maximum memory size shown in the notebook
- use this when traffic is sporadic and you want scale-to-zero behavior

### 3) Batch Transform
Batch transform is also CPU-only and uses the same repackaged model artifact.

Typical shape:

```python
from sagemaker.transformer import Transformer

transformer = Transformer(
    model_name=chronos_model.name,
    instance_count=1,
    instance_type="ml.c5.4xlarge",
    output_path=output_s3_uri,
    strategy="SingleRecord",
    assemble_with="Line",
    accept="application/json",
)
```

Notes:
- input data must already be staged in S3
- each JSONL line can hold one request payload
- `SingleRecord` + `Line` makes the output easier to recombine
- this is for offline jobs, not interactive use

## Request payload shape

Chronos-2 endpoint requests use a JSON object with `inputs` and `parameters`.

### `inputs`
A list of up to 1000 time series. Each item may include:
- `target` required
  - univariate: a flat list of numbers
  - multivariate: a list of lists, one list per target dimension
- `item_id` optional, unique identifier for the series
- `start` optional ISO timestamp for the first observation
- `past_covariates` optional dict of past covariate arrays
- `future_covariates` optional dict of known-future covariate arrays

Rules to remember:
- each past covariate series must have the same length as the target history
- each future covariate series must have length `prediction_length`
- a covariate appearing in both past and future is treated as known-future
- if `start` is supplied, `parameters.freq` must also be supplied

### `parameters`
Common fields:
- `prediction_length`
- `quantile_levels`
- `freq`
- `batch_size`
- `cross_learning`

Useful interpretation:
- larger `batch_size` can speed up inference but may increase memory use
- `cross_learning=True` lets Chronos-2 share information across items in the batch
- `quantile_levels` controls which probabilistic forecast levels are returned

## Response shape
The endpoint returns probabilistic forecasts for each requested input series.
The notebook’s response helpers expect forecast records that include:
- `mean` or point forecasts
- requested quantiles
- optional `item_id`
- optional `start`

For multivariate forecasts, the returned values are nested by target dimension.
When converting endpoint output back to a DataFrame, keep both the target dimension and the forecast horizon aligned.

## Minimal request examples

Univariate:

```python
payload = {
    "inputs": [{"target": [0.0, 4.0, 5.0, 1.5, -3.0]}],
    "parameters": {"prediction_length": 10},
}
```

Covariates and timestamps:

```python
payload = {
    "inputs": [
        {
            "target": [1.0, 2.0, 3.0, 2.0, 1.0],
            "item_id": "series_A",
            "start": "2024-01-01T01:00:00",
            "past_covariates": {"feat_1": [1.0, 2.0, 3.0, 2.0, 1.0]},
            "future_covariates": {"feat_1": [1.5, 1.2, 1.1]},
        }
    ],
    "parameters": {"prediction_length": 3, "freq": "1h", "quantile_levels": [0.1, 0.5, 0.9]},
}
```

## Credentials and IAM caveats
- do not hardcode AWS keys, tokens, or roles in runtime files
- use a SageMaker execution role or explicit IAM role ARN
- ensure the role can read the model artifact and any S3 input/output locations
- delete the predictor when done to stop endpoint charges
- if the notebook needs a local helper, keep the data conversion code local and out of the runtime skill tree

## Local alternatives
If you do not have AWS credentials or do not want to create an endpoint:
- stay local with `Chronos2Pipeline.predict_df(...)`
- use `predict_quantiles(...)` or `predict_fev(...)` in-process
- use the deployment notebook only as a pattern reference, not as a required runtime dependency

## Reference-only boundary
This sub-skill treats cloud deployment as optional/reference-only unless the user explicitly asks for a live AWS run and supplies the needed permissions.
