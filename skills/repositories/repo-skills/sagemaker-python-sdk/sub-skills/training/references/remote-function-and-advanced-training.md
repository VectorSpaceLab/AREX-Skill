# Remote function and advanced training

Use this file for the advanced training surfaces that sit around the main
`ModelTrainer` flow: remote functions and AWS Batch training queues.

## Remote function

The current preferred entry point is the core package shim:

```python
from sagemaker.core.remote_function.client import remote, RemoteExecutor
```

The older `sagemaker.train.remote_function` module is a compatibility shim that
re-exports the core implementation. Prefer the core import path in new guidance.

### Remote executor capabilities

`RemoteExecutor` supports:

- `submit(...)`
- `map(...)`
- `shutdown(...)`
- `wait(...)`
- `cancel(...)`

Use remote functions when you want code to run in a SageMaker-backed remote
context without writing the lower-level job plumbing by hand.

## AWS Batch training queue

Use `TrainingQueue` when the user needs queued SageMaker training jobs through
AWS Batch.

```python
from sagemaker.train.aws_batch.training_queue import TrainingQueue
```

### Queue capabilities

`TrainingQueue` exposes:

- `submit(...)`
- `map(...)`
- `list_jobs(...)`
- `list_jobs_by_share(...)`
- `get_job(...)`

### Critical rule

`TrainingQueue` requires a `ModelTrainer` configured with
`Mode.SAGEMAKER_TRAINING_JOB`. It does **not** accept local-container jobs.

## When to use this file

- queueing training jobs behind AWS Batch
- inspecting queued job status or queue membership
- using the remote-function execution path
- understanding the compatibility shim around `sagemaker.train.remote_function`

## Failure cues

- `Mode.LOCAL_CONTAINER` passed to `TrainingQueue`
- queue submission without a `ModelTrainer`
- trying to use the remote-function shim as if it were the canonical import

## Hand off

If the task becomes ordinary `ModelTrainer` setup, HPO, or JumpStart training,
return to `modeltrainer-workflows.md` or `hyperparameter-tuning.md`.
