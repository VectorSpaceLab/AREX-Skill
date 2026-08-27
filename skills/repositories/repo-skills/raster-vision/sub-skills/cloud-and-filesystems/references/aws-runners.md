# AWS runners and CloudFormation

This reference covers the Raster Vision cloud execution surfaces owned by `cloud-and-filesystems`. It does **not** define pipeline command semantics; those stay with the pipeline-cli sub-skill.

## Runner selection at a glance

- `local` and `inprocess` are local execution modes.
- `batch` submits a DAG of jobs to AWS Batch.
- `sagemaker` translates the pipeline to a SageMaker Pipeline.
- Batch and SageMaker both consume command classification from the pipeline object:
  - `gpu_commands` selects GPU resources.
  - `split_commands` may fan out to array jobs or split steps.
  - `job_queue` and `job_def` on the pipeline or command object override global config.

## AWS Batch

### Config surface

Use either the `[BATCH]` RV config section or these environment variables:

| Setting | Meaning |
| --- | --- |
| `gpu_job_queue` / `GPU_JOB_QUEUE` | Queue for GPU jobs |
| `gpu_job_def` / `GPU_JOB_DEF` | Job definition for GPU jobs |
| `cpu_job_queue` / `CPU_JOB_QUEUE` | Queue for CPU jobs |
| `cpu_job_def` / `CPU_JOB_DEF` | Job definition for CPU jobs |
| `attempts` / `ATTEMPTS` | Retry count for transient Batch failures |

Set `attempts` above 1 unless you have a strong reason not to; Batch can stop jobs without a useful error.

### Runner behavior

- `AWSBatchRunner.build_cmd()` emits `python -m rastervision.pipeline.cli ... run_command ... --runner batch`.
- Split commands add `--num-splits` and become array jobs when `num_splits > 1`.
- `AWS_BATCH_JOB_ARRAY_INDEX` carries the split index inside an array job.
- GPU selection is per command; commands listed in `gpu_commands` use GPU resources, everything else uses CPU resources.
- Remote Batch jobs run inside the image defined by the Batch job definition, so they cannot rely on local filesystem state.

### CloudFormation batch stack

The bundled Batch CloudFormation setup creates the AWS resources needed for the Batch runner:

- service and instance IAM roles
- instance profile and security group
- CPU and GPU compute resources
- queues and job definitions
- optional ECR-backed image flow for custom images

This sub-skill bundles two templates under `templates/cloudformation/`:

- `batch-environment-template.yml` for the Batch environment stack.
- `job-definition-template.yml` for project- or user-scoped job definitions.

Common stack inputs include a namespacing prefix, VPC, subnet IDs, key pair name, CPU/GPU instance types, and optional ECR repository metadata. Creating or updating a stack mutates AWS infrastructure; inspect the bundled template and confirm cost/permission boundaries before deployment.

## AWS SageMaker

### Config surface

Use either the `[SAGEMAKER]` RV config section or these environment variables:

| Setting | Meaning |
| --- | --- |
| `role` / `SAGEMAKER_ROLE` | IAM role with SageMaker permissions |
| `cpu_image` / `SAGEMAKER_CPU_IMAGE` | Docker image for CPU steps |
| `cpu_instance_type` / `SAGEMAKER_CPU_INSTANCE_TYPE` | Instance type for CPU steps |
| `gpu_image` / `SAGEMAKER_GPU_IMAGE` | Docker image for GPU steps |
| `gpu_instance_type` / `SAGEMAKER_GPU_INSTANCE_TYPE` | Instance type for GPU steps |
| `train_image` / `SAGEMAKER_TRAIN_IMAGE` | Docker image for training steps |
| `train_instance_type` / `SAGEMAKER_TRAIN_INSTANCE_TYPE` | Instance type for training |
| `train_instance_count` / `SAGEMAKER_TRAIN_INSTANCE_COUNT` | Parallel training nodes |
| `use_spot_instances` / `SAGEMAKER_USE_SPOT_INSTANCES` | Spot training toggle |
| `spot_instance_max_wait_time` / `SPOT_INSTANCE_MAX_WAIT_TIME` | Spot wait limit |
| `max_run_time` / `MAX_RUN_TIME` | Max job runtime |

### Runner behavior

- Non-`train` commands become `ProcessingStep` objects.
- `train` becomes a `TrainingStep` and can use distributed PyTorch.
- The runner uses the configured role to look up the role ARN before starting the pipeline.
- `use_spot_instances` applies to training jobs only; other steps force spot off.
- `train_uri` must be an S3 URI; the runner rejects non-S3 training roots.

### CloudFormation and AWS prerequisites

SageMaker usage still depends on cloud account setup:

- a valid IAM role with SageMaker permissions
- suitable instance quotas for the instance types you want
- ECR images or the hosted image flow, depending on your deployment
- S3-based experiment storage for training roots and bundled assets

## Practical routing notes

- Use this sub-skill for cloud transport and resource selection.
- Use the pipeline-cli sub-skill for command syntax and command sequencing.
- Use the data-and-models or pytorch-workflows sub-skills for task recipes, dataset shape, or model configuration.
