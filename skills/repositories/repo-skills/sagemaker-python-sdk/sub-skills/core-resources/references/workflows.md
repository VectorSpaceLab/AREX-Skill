# Core resource workflows

This file turns the core resource surface into a few repeatable patterns. It is
intentionally narrow: if the task becomes training orchestration, deployment,
or pipeline composition, hand off to the sibling sub-skill.

## 1. Bootstrap and inspect the environment

```python
from sagemaker.core.helper.session_helper import Session

session = Session()
print(session.boto_region_name)
print(session.default_bucket())
```

Use this first when the task is about region, bucket, or session wiring.

## 2. Retrieve artifacts

```python
from sagemaker.core import image_uris, model_uris, script_uris

training_image = image_uris.retrieve(
    framework="pytorch",
    region=session.boto_region_name,
    version="2.0.0",
    py_version="py310",
    instance_type="ml.p3.2xlarge",
    image_scope="training",
)
```

Use `model_uris.retrieve(...)` and `script_uris.retrieve(...)` in the same way
for JumpStart artifacts.

## 3. Manage low-level jobs

Use the resource objects when you need direct create/get/wait/delete control.
The relevant classes live in `sagemaker.core.resources`:

- `ProcessingJob`
- `TransformJob`
- `TrainingJob`
- `Model`
- `EndpointConfig`
- `Endpoint`
- `HyperParameterTuningJob`

Typical sequencing for hosting is:

1. build or resolve a `Model`
2. create an `EndpointConfig`
3. create an `Endpoint`
4. wait for the endpoint to reach `InService`
5. invoke it through `Endpoint.invoke(...)`

## 4. Use the helper wrappers when you want a higher-level interface

- `Processor`, `ScriptProcessor`, `FrameworkProcessor` for processing jobs
- `Transformer` for batch transform jobs

These wrappers are usually easier to use when the task looks like an example or
workflow snippet rather than a resource lifecycle utility.

## 5. Build lineage

Use `sagemaker.core.lineage` when the task is about provenance, audit trails,
associations, or model/data lineage.

```python
from sagemaker.core.lineage import Context, Action, Artifact, Association
```

Keep lineage cleanup explicit. Delete associations before removing the entities
that they connect.

## 6. Serverless and async endpoint shapes

For endpoint configuration that needs serverless or async settings, prefer the
shapes under `sagemaker.core.inference_config` and the low-level serverless
config objects under `sagemaker.core.shapes`.

## 7. When to stop and hand off

Stop in this sub-skill when the user asks for any of the following:

- `ModelTrainer` orchestration or HPO flow setup
- `ModelBuilder` deployment or local inference setup
- `Pipeline` or workflow composition
- foundation-model customization or evaluation

Those are separate sub-skills.
