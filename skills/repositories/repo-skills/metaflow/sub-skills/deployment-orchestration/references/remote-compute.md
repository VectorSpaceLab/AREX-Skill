# Remote Compute

## AWS Batch

Use `@batch` or `--with batch` for AWS Batch task execution. Important constraints from source behavior:

- `@batch` requires `--datastore=s3`.
- Resources are merged from `@resources` and `@batch` with defaults for CPU, GPU, and memory.
- Remote timeouts under 60 seconds are invalid.
- Batch can use container image, queue, IAM/execution roles, shared memory, swap, tmpfs, Inferentia/Trainium, EFA, tags, and privileged settings.

## Kubernetes

Use `@kubernetes` or `--with kubernetes` for Kubernetes task execution. Important constraints:

- Kubernetes execution requires `--datastore=s3`, `--datastore=azure`, or `--datastore=gs`.
- `@batch` and `@kubernetes` cannot both mark the same step.
- `@parallel` with `@catch` is not supported on Kubernetes.
- GPU vendor must be `amd` or `nvidia`.
- CPU, disk, memory, tmpfs, and shared memory values must be positive where set.

## Resources, parallelism, and GPU

`@resources(cpu=..., memory=..., gpu=..., disk=..., shared_memory=...)` describes requirements independently of the backend. It does not install PyTorch or prove GPU availability. `@parallel` and `@pytorch_parallel` require backend-specific multinode support and should be verified in the actual target environment.
