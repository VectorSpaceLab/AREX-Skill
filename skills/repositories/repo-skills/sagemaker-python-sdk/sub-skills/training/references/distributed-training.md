# Distributed training

Use this reference when the training task needs more than one process, node,
or GPU. The key idea is to configure the `ModelTrainer` and `distributed`
objects, not to copy the package's internal driver scripts.

## Import map

```python
from sagemaker.train import ModelTrainer
from sagemaker.train.distributed import Torchrun, MPI, SMP, DistributedConfig
from sagemaker.core.training.configs import SourceCode, Compute
from sagemaker.train.model_trainer import Mode
```

## Distributed options

| Option | When to use |
| --- | --- |
| `Torchrun` | PyTorch multi-GPU or multi-node training |
| `MPI` | `mpirun`-style distributed launches |
| `SMP` | SageMaker Model Parallelism v2 / tensor-parallel configuration |
| `DistributedConfig` | Common base when a custom distributed config is needed |

## Rules that matter

- `distributed` requires `source_code`.
- Use a clear training entry script and make sure the script understands the
  driver-provided environment variables.
- Keep the container image aligned with the framework and backend you are
  using.
- For `Torchrun`, `SMP` can be nested inside the distributed config when model
  parallelism tuning is needed.
- For `MPI`, the package's internal MPI driver handles the launch mechanics;
  the user-facing task is still to configure `ModelTrainer` correctly.

## Local distributed training

When the user wants to test distributed training locally:

- set `training_mode=Mode.LOCAL_CONTAINER`
- use `Compute(instance_type="local_cpu" or "local_gpu", instance_count=...)`
- require Docker and the relevant framework image
- treat the local run as a validation of wiring, not as proof of cloud-scale
  performance

## Example pattern

```python
from sagemaker.train import ModelTrainer
from sagemaker.train.distributed import Torchrun, SMP
from sagemaker.core.training.configs import SourceCode, Compute

trainer = ModelTrainer(
    training_image="<training-image-uri>",
    role="<role-name-or-arn>",
    source_code=SourceCode(source_dir="./src", entry_script="train.py"),
    compute=Compute(instance_type="ml.p4d.24xlarge", instance_count=2),
    distributed=Torchrun(smp=SMP(random_seed=123456)),
)
```

## Failure cues

- missing `source_code` when `distributed` is configured
- Docker missing for local distributed mode
- image or framework mismatch for the requested backend
- too few instances or incompatible `instance_type` for the chosen driver

## Hand off when needed

If the task is really about HPO, AWS Batch queues, or remote-function launch,
move to the matching training reference instead of extending this file.
