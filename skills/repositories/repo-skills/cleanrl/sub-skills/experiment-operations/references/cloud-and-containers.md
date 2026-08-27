# Cloud and Containers

CleanRL's operational stack can build Docker images, generate Docker run commands, submit AWS Batch jobs, and preview Slurm arrays. These workflows are powerful and side-effectful. Default to inspection and dry-run outputs until the user explicitly approves execution.

## Container Shape

The CleanRL container pattern uses a CUDA runtime base image, installs system packages needed for Python, video rendering, and OpenGL-style environments, installs the Python package, copies training scripts, and starts a virtual X display in the entrypoint. This supports tracked video capture in headless containers.

Container planning checks:

- Confirm the image tag, registry, CUDA/runtime expectations, and CPU/GPU target before build.
- Verify whether `--build`, `--push`, or multi-architecture build flags are requested; each can be slow or mutate a registry.
- Do not use placeholder tags such as `latest` for archival experiments unless the user accepts non-reproducibility.
- For GPU containers, confirm host runtime support and requested `num_gpu` match the target queue or host.
- Keep secrets out of `docker run` previews; prefer environment references or redacted placeholders.

## Docker Command Generation

CleanRL's submission utility can create Docker run commands from a base command and seed count. Without a cloud provider, this is useful as an inspection step: it prints and writes commands but does not submit AWS jobs. However, it may still require a W&B key and may print an environment assignment, so use placeholder or redacted values in shared transcripts.

Safe dry-run workflow:

1. Validate W&B environment with `sub-skills/experiment-operations/scripts/check_wandb_env.py --require-wandb`.
2. Generate or inspect Docker commands with placeholder credentials if the result will be shared.
3. Check seed expansion, image tag, CPU pinning, and base command.
4. Ask before running generated Docker commands or queuing them through a Docker scheduler.

## AWS Batch

AWS Batch submission registers a job definition, submits jobs to a named queue, attaches vCPU/memory/GPU requirements, sets retry and timeout policies, and passes W&B resume/tracking environment variables into the container.

Before any AWS action:

- Run `sub-skills/experiment-operations/scripts/check_wandb_env.py --require-wandb --require-aws` and resolve missing or placeholder-like variables without printing values.
- Confirm `AWS_DEFAULT_REGION` or `AWS_REGION`, credentials, queue name, compute type, GPU needs, memory, timeout, and retry count.
- Prefer spot queues for cost-aware exploratory runs only when interruption is acceptable.
- Confirm the Docker image exists in a registry accessible from AWS Batch.
- Ask for explicit approval before `terraform apply`, `terraform destroy`, Docker push, or AWS job submission.

## Terraform Infrastructure

The infrastructure workflow can initialize and apply Terraform under the cloud configuration to create AWS Batch resources. This mutates cloud infrastructure and can incur cost once jobs are submitted.

Guardrails:

- Use `terraform plan` before `terraform apply` when possible.
- Confirm region, profile, queue names, and intended cleanup path.
- Treat `terraform destroy` as destructive and require explicit user confirmation.
- Do not embed cloud account ids, access keys, or local profile paths in runtime skill content or shared handoffs.

## Slurm Integration

Slurm integration is a scheduler preview/execution boundary:

- Previewing a script is safe when it only renders text.
- Creating files under a `slurm/` directory is a local mutation.
- Running `sbatch` schedules work on a shared cluster and requires explicit approval.

Check template placeholders before submission: array range, concurrency, partition, node constraints, GPU count, CPU-per-GPU, total tasks, log path, and the final `srun` command. Cluster-specific partitions, node exclusions, account names, and memory defaults should be reviewed by the user rather than copied from examples.

## Side-Effect Classification

- Read-only: help text, environment presence checks, command matrix generation, Slurm preview text.
- Local mutation: writing generated Docker scripts, cache directories, plot outputs, Slurm files, local databases.
- Long local execution: benchmark workers, tuner trials, Docker runs, plotting large W&B projects.
- External mutation: W&B run creation, artifact upload, Docker registry push, Terraform apply/destroy, AWS Batch submission, Slurm `sbatch`.

Escalate from read-only to any higher category only after the user accepts the cost, runtime, and credential implications.
