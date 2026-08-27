# Deployment modes and InferenceSpec

Use this file when the task is about custom request/response handling or local
vs cloud deployment mode selection.

## InferenceSpec

Import it from `sagemaker.serve` or from the concrete module path:

```python
from sagemaker.serve import InferenceSpec
from sagemaker.serve.builder.schema_builder import SchemaBuilder
```

`InferenceSpec` is the abstract interface for custom inference logic.
Do not instantiate it directly; subclass it and implement:

- `load(model_dir)`
- `invoke(input_object, model)`
- optionally `preprocess(...)`, `postprocess(...)`, and `prepare(...)`

Use it when the model needs custom Python-side load and invoke behavior.

## SchemaBuilder

`SchemaBuilder(sample_input, sample_output, input_translator=None, output_translator=None)`
auto-detects the serializer and deserializer from example payloads.
Use it when the input/output schema can be inferred from representative
payloads.
If the examples are insufficient, supply a custom payload translator instead
of forcing the auto-detection path.
## Deployment modes

| Mode | Best for | Notes |
| --- | --- | --- |
| `Mode.SAGEMAKER_ENDPOINT` | cloud serving | creates SageMaker resources |
| `Mode.LOCAL_CONTAINER` | Docker-based local validation | requires Docker and local images |
| `Mode.IN_PROCESS` | pure Python local validation | quickest local path |

## When to choose which

- Use `IN_PROCESS` when you only need a quick local check of custom logic.
- Use `LOCAL_CONTAINER` when you want container parity with the cloud runtime.
- Use `SAGEMAKER_ENDPOINT` when the user wants a real SageMaker endpoint.

## Invocation guidance

- Build the model before invoking it.
- Use `endpoint.invoke(...)` or the local endpoint's `invoke(...)` method.
- Keep `content_type` and `accept` aligned with the schema or translator.

## Failure cues

- custom payload translator does not match the sample input/output
- local mode is chosen without Docker or local runtime support
- cloud mode is selected without region, credentials, or role metadata
