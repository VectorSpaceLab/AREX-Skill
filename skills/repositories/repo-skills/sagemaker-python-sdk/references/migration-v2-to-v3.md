# Migration from SageMaker SDK v2 to v3

Use this map when you are converting legacy SageMaker code to the v3 modular
SDK. The rule is simple: keep the task in the SageMaker Python SDK, replace the
v2 surface with the v3 surface, and then route to the owning sub-skill for the
final workflow.

## Core migration rules

- Prefer `pip install sagemaker` for the v3 meta package.
- Use `sagemaker-core`, `sagemaker-train`, `sagemaker-serve`, and
  `sagemaker-mlops` as the modular packages.
- Replace deprecated v2 imports with the v3 import that owns the workflow.
- Keep examples placeholder-only; do not introduce real account IDs, ARNs,
  bucket names, subnets, security groups, or credentials.
- If the code creates resources, add cleanup and region/role guidance.

## Common replacements

| v2 pattern | v3 replacement | Route to |
| --- | --- | --- |
| `from sagemaker.estimator import Estimator` | `from sagemaker.train import ModelTrainer` | `../sub-skills/training/SKILL.md` |
| framework estimators such as `PyTorch`, `TensorFlow`, `SKLearn`, `XGBoost`, `HuggingFace` | `ModelTrainer` plus `sagemaker.core.image_uris.retrieve(...)` | `../sub-skills/training/SKILL.md` |
| `estimator.fit(...)` | `model_trainer.train(...)` | `../sub-skills/training/SKILL.md` |
| `from sagemaker.model import Model` and `model.deploy(...)` | `from sagemaker.serve import ModelBuilder` and `ModelBuilder.deploy(...)` | `../sub-skills/serving/SKILL.md` |
| `from sagemaker.predictor import Predictor` and `predictor.predict(...)` | use the `Endpoint` returned by v3 deployment and call `Endpoint.invoke(...)` | `../sub-skills/serving/SKILL.md` or `../sub-skills/core-resources/SKILL.md` |
| `from sagemaker.processing import Processor` / `ScriptProcessor` | `sagemaker.core.resources.ProcessingJob` or the v3 helper flow for the same job type | `../sub-skills/core-resources/SKILL.md` |
| `from sagemaker.transformer import Transformer` | `sagemaker.core.resources.TransformJob` or the v3 helper flow that owns batch transform | `../sub-skills/core-resources/SKILL.md` |
| `from sagemaker.tuner import HyperparameterTuner` | `sagemaker.train.tuner.HyperparameterTuner` or low-level `HyperParameterTuningJob` | `../sub-skills/training/SKILL.md` |
| `from sagemaker.workflow.* import ...` | `from sagemaker.mlops.workflow import ...` | `../sub-skills/mlops/SKILL.md` |
| `from sagemaker.lineage.* import ...` | `from sagemaker.core.lineage import ...` | `../sub-skills/core-resources/SKILL.md` or `../sub-skills/mlops/SKILL.md` |
| `sagemaker.session.Session` / `sagemaker.image_uris` / `sagemaker.model_uris` / `sagemaker.script_uris` | `sagemaker.core.helper.session_helper.Session` and `sagemaker.core.image_uris` / `model_uris` / `script_uris` | `../sub-skills/core-resources/SKILL.md` |
| `sagemaker.workflow.pipeline.Pipeline` | `sagemaker.mlops.workflow.Pipeline` | `../sub-skills/mlops/SKILL.md` |
| `sagemaker.workflow.steps.*` | `sagemaker.mlops.workflow` step classes | `../sub-skills/mlops/SKILL.md` |
| `sagemaker.train.configs` in new examples | prefer `sagemaker.core.training.configs` when available; keep `sagemaker.train.configs` only for compatibility examples | `../sub-skills/training/SKILL.md` |

## Deprecated or removed v2-only patterns

Do not introduce these in new guidance unless the task is explicitly about
migration notes:

- legacy framework estimators and `fit()`-driven training flows
- `Predictor.predict()` as the main deployment interface
- legacy `sagemaker.workflow.*` imports
- legacy `sagemaker.lineage.*` imports
- `MXNet`, `Chainer`, `RLEstimator`, or Training Compiler patterns that are no
  longer part of v3

## Migration workflow

1. Identify the original v2 surface and the user intent behind it.
2. Replace the import path first, then map arguments to the v3 constructor or
   method.
3. If the task is training, deployment, processing, or workflow orchestration,
   move to the matching sub-skill and keep the migration note short.
4. Re-check the output for banned v2 names and hardcoded AWS identifiers.
5. If the task involves a live cloud resource, ask for the missing region,
   role, bucket, and authorization details before submitting a billable job.

## Examples

### Training

```python
from sagemaker.core import image_uris
from sagemaker.train import ModelTrainer
from sagemaker.core.training.configs import Compute, InputData, SourceCode

training_image = image_uris.retrieve(
    framework="pytorch",
    region="us-west-2",
    version="2.0.0",
    py_version="py310",
    instance_type="ml.p3.2xlarge",
    image_scope="training",
)

trainer = ModelTrainer(
    training_image=training_image,
    role="<role-name-or-arn>",
    source_code=SourceCode(source_dir="./src", entry_script="train.py"),
    compute=Compute(instance_type="ml.p3.2xlarge", instance_count=1),
)
trainer.train(input_data_config=[InputData(channel_name="train", data_source="s3://<bucket>/train")])
```

### Deployment

```python
from sagemaker.serve import ModelBuilder

builder = ModelBuilder(
    model="<trained-model-or-artifact>",
    role_arn="<role-name-or-arn>",
)
endpoint = builder.deploy(instance_type="ml.m5.large", initial_instance_count=1)
```

### Pipelines

```python
from sagemaker.mlops.workflow import Pipeline

pipeline = Pipeline(name="<pipeline-name>", steps=[])
```

## Handoff

After migration, hand the task to the owning sub-skill and report:

- the original v2 surface
- the chosen v3 replacement
- whether the result is a code rewrite, a doc note, or a usage example
- any AWS or Docker prerequisites still missing
