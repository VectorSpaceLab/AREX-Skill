# ModelTrainer workflows

Use `ModelTrainer` for the standard SageMaker Python SDK v3 training flow.
This is the main training path when the task is about managed training, local
container training, JumpStart training, or a one-off fine-tuning job.

## Import map

```python
from sagemaker.core import image_uris
from sagemaker.train import ModelTrainer
from sagemaker.train.model_trainer import Mode
from sagemaker.core.training.configs import (
    SourceCode,
    Compute,
    HyperPodCompute,
    Networking,
    InputData,
    OutputDataConfig,
    CheckpointConfig,
    StoppingCondition,
    TrainingImageConfig,
)
```

Prefer `sagemaker.core.training.configs` over the deprecated compatibility shim
`sagemaker.train.configs` in new examples.

## Constructor shape

`ModelTrainer` accepts the core training ingredients:

- `training_image` or `algorithm_name`
- `source_code`
- `compute`
- `networking`
- `stopping_condition`
- `output_data_config`
- `input_data_config`
- `checkpoint_config`
- `training_input_mode`
- `environment`
- `hyperparameters`
- `tags`
- `role`
- `base_job_name`
- `training_mode`
- `sagemaker_session`

Do not supply both `training_image` and `algorithm_name`.

## Standard flow

1. Resolve the framework image with `image_uris.retrieve(...)` when the task
   uses a managed framework image.
2. Build `SourceCode`, `Compute`, `InputData`, and any networking/output
   config objects first.
3. Construct `ModelTrainer` with an explicit role when role discovery is not
   guaranteed.
4. Call `train(input_data_config=..., dry_run=True)` first when you want config
   validation without launching a billable job.
5. Call `train(wait=True, logs=True)` when the user authorizes job submission.
6. Store the returned or latest training job object for downstream serving or
   MLOps handoff.

## Safe starter example

```python
from sagemaker.core import image_uris
from sagemaker.train import ModelTrainer
from sagemaker.core.training.configs import SourceCode, Compute, InputData, StoppingCondition

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
    compute=Compute(instance_type="ml.m5.xlarge", instance_count=1),
    stopping_condition=StoppingCondition(max_runtime_in_seconds=3600),
)

trainer.train(
    input_data_config=[InputData(channel_name="train", data_source="s3://<bucket>/train")],
    dry_run=True,
)
```

## JumpStart training

Use `ModelTrainer.from_jumpstart_config(...)` when the training job is based on
JumpStart model metadata rather than a hand-built image. The resulting trainer
still uses the same `train(...)` flow.

## Local training

- Set `training_mode=Mode.LOCAL_CONTAINER`.
- Use `Compute(instance_type="local_cpu" or "local_gpu", ...)`.
- Require Docker and local source files.
- Treat local training as a convenience/testing path, not a cloud job.

## What to hand off next

- Deployment: `../serving/SKILL.md`
- Pipeline integration: `../mlops/SKILL.md`
- Low-level job/resource inspection: `../core-resources/SKILL.md`
- Foundation-model customization: `../model-customization/SKILL.md`
