# ModelBuilder workflows

Use `ModelBuilder` for the standard SageMaker Python SDK v3 deployment flow.
This is the main path for cloud endpoints, local testing, JumpStart serving,
train-to-inference handoff, and inference recommender flows.

## Import map

```python
from sagemaker.serve import ModelBuilder, InferenceSpec, ModelServer
from sagemaker.serve.builder.schema_builder import SchemaBuilder
from sagemaker.serve.mode.function_pointers import Mode
```

## Constructor ingredients

`ModelBuilder` can be built from:

- a trained model object
- a `ModelTrainer`
- a `TrainingJob`
- a `ModelPackage`
- a JumpStart model ID string
- a raw S3 model artifact URI
- a custom `InferenceSpec`

Common constructor fields include:

- `role_arn`
- `sagemaker_session`
- `image_uri`
- `s3_model_data_url`
- `source_code`
- `schema_builder`
- `model_server`
- `mode`
- `env_vars`
- `model_metadata`

Use `role_arn` explicitly when role discovery is not guaranteed.

## Recommended workflow

1. Start from the trained model or artifact source.
2. Define the transport contract with `InferenceSpec` or `SchemaBuilder`.
3. Pick the mode: cloud endpoint, local container, or in-process.
4. Call `build()` first when you want the model resource created separately.
5. Call `deploy()` for cloud serving or `deploy_local()` for local testing.
6. Use the returned endpoint's `invoke(...)` method instead of the old
   predictor pattern.

## Mode selection

| Mode | Meaning |
| --- | --- |
| `Mode.SAGEMAKER_ENDPOINT` | create a cloud endpoint |
| `Mode.LOCAL_CONTAINER` | run a Docker-backed local endpoint |
| `Mode.IN_PROCESS` | run a pure Python local endpoint |

`deploy_local()` only supports `LOCAL_CONTAINER` and `IN_PROCESS`.

## Safe starter example

```python
from sagemaker.serve import ModelBuilder
from sagemaker.serve.spec.inference_spec import InferenceSpec
from sagemaker.serve.builder.schema_builder import SchemaBuilder
from sagemaker.serve.mode.function_pointers import Mode

builder = ModelBuilder(
    model="<trained-model-or-artifact>",
    role_arn="<role-name-or-arn>",
    inference_spec=<your-custom-inference-spec>,
    schema_builder=SchemaBuilder(sample_input={"text": "hello"}, sample_output={"label": 1}),
    mode=Mode.IN_PROCESS,
)
```

## JumpStart and reuse

- Use `ModelBuilder.from_jumpstart_config(...)` for JumpStart models.
- Use `reuse_resources=True` when you want the builder to reuse an existing
  model or endpoint created from the same source.

## Handoff rules

- For lower-level endpoint or batch-transform control, use the core-resources
  sub-skill.
- For deployment optimization and recommendations, use the sibling reference
  file.
- For Bedrock deployment, use the sibling reference file.
