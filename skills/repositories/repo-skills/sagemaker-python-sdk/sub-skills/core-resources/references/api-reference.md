# Core resources API reference

Use `sagemaker-core` when the task is about foundational SDK objects rather
than high-level training or deployment flows. This reference captures the core
surface for sessions, URI retrieval, low-level resource objects, helper wrappers,
and lineage.

## Import map

```python
from sagemaker.core.helper.session_helper import Session, get_execution_role
from sagemaker.core import image_uris, model_uris, script_uris
from sagemaker.core.processing import Processor, ScriptProcessor, FrameworkProcessor
from sagemaker.core.transformer import Transformer
from sagemaker.core.resources import (
    ProcessingJob,
    TransformJob,
    TrainingJob,
    Model,
    EndpointConfig,
    Endpoint,
    HyperParameterTuningJob,
)
from sagemaker.core.lineage import Context, Action, Artifact, Association
from sagemaker.core.inference_config import AsyncInferenceConfig, ServerlessInferenceConfig
```

## What each layer is for

| Layer | Use it for |
| --- | --- |
| `Session` | Region discovery, default bucket selection, client/session wiring, and SDK bootstrap |
| `image_uris` / `model_uris` / `script_uris` | Framework image, JumpStart model, and script artifact retrieval |
| `Processor` / `ScriptProcessor` / `FrameworkProcessor` | Processing jobs with a higher-level wrapper |
| `Transformer` | Batch transform helper wrapper |
| `ProcessingJob` / `TransformJob` / `TrainingJob` | Direct resource control and lifecycle management |
| `Model` / `EndpointConfig` / `Endpoint` | Resource CRUD for model hosting and invocation |
| `HyperParameterTuningJob` | Low-level tuning job control |
| `sagemaker.core.lineage` | Lineage graphs and compliance tracking |

## Common bootstrap pattern

```python
from sagemaker.core.helper.session_helper import Session, get_execution_role

session = Session()
region = session.boto_region_name
bucket = session.default_bucket()
role = get_execution_role(session)
```

Use an explicit role when role discovery is not available. Outside a SageMaker-
managed environment, `get_execution_role()` may fail because STS access is not
available.

## Resource chaining guidance

Many core resource and helper APIs accept a resource object or pipeline
variable. Prefer passing the upstream object directly when the type allows it.
If the call requires a plain string, fall back to `.name` or `get_name()` only
for that field.

Example:

```python
processing_job = ProcessingJob(...)
transform_job = TransformJob(...)
```

The exact chaining pattern depends on the resource constructor; the core rule is
to preserve the resource object when possible and only flatten to names at the
last boundary.

## Serverless and async endpoint config

Use the low-level shapes and config objects when the deployment surface needs
serverless or async control:

- `AsyncInferenceConfig`
- `ServerlessInferenceConfig`
- `ProductionVariantServerlessConfig` inside `ProductionVariant`

Treat these as cloud configuration objects. They are not local-only helpers.

## Lifecycle checklist

- Create or resolve a `Session` first.
- Resolve the image/model/script URI if the workflow needs a managed artifact.
- Use the appropriate resource class for create/get/wait/delete.
- Keep a cleanup plan for endpoints, jobs, and lineage entities.
- Avoid hardcoded AWS identifiers or credentials in examples.

## Where to go next

- Workflow recipes: [`workflows.md`](workflows.md)
- Core troubleshooting: [`troubleshooting.md`](troubleshooting.md)
- Root migration map: [`../../../references/migration-v2-to-v3.md`](../../../references/migration-v2-to-v3.md)
