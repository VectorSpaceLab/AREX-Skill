# Infrastructure And Storage Troubleshooting

Use this guide to triage infrastructure and storage failures without exposing credentials or running unsafe cloud actions.

## Safe Triage Protocol

1. Identify the failing surface: credentials/setup, optimizer/resource selection, provisioning capacity, Kubernetes/Slurm/SSH backend, object storage/file mounts, or volumes.
2. Ask the user to run the narrowest local check and share redacted output: `sky check <infra>`, `sky gpus list ...`, `sky storage ls`, `sky volumes ls`, or a bounded `sky launch --dryrun`.
3. Do not ask for raw secrets, kubeconfigs, SSH private keys, cloud credential files, provider account IDs, or full bucket tokens.
4. Separate authentication from capacity: credential failures happen during `sky check` or provider auth; capacity/quota failures happen during optimizer/provisioning and usually need fallback resources or quota changes.
5. Route exact YAML field fixes to `task-yaml`, lifecycle cleanup to `cluster-operations`, managed job controller symptoms to `managed-jobs`, and API server login/version issues to `sdk-api-server`.

## Disabled Clouds Or Missing Credentials

Symptoms:

- `sky check` lists a cloud as disabled.
- CLI errors mention missing provider CLI, SDK, credential file, project/subscription, region permission, or workspace policy.
- A launch fails before optimizer/provider capacity checks begin.

Actions:

- Ask the user to run `sky check <infra>` for the specific provider and share only the redacted status/error category.
- Confirm they installed the needed SkyPilot extra or provider tooling for that cloud if the error names a missing SDK/CLI.
- Confirm the active workspace with `sky check --workspace <name>` when a workspace-specific cloud policy may block the provider.
- If multiple providers are acceptable, remove the `infra` pin and let SkyPilot optimize across enabled clouds.
- If only one provider is acceptable, fix provider credentials/permissions first; do not mask auth failures by changing GPU, region, or instance type.

Do not interpret disabled-cloud output as a pricing or availability problem until credentials and workspace policy pass.

## Quota, Capacity, And Optimizer Failures

Symptoms:

- Error mentions quota, capacity, stockout, unavailable accelerator, no feasible resources, unsupported region/zone, or requested instance type not found.
- `sky check` succeeds but launch or dry run cannot find resources.

Actions:

- Run or ask for `sky launch --dryrun <task.yaml>` to get optimizer feedback without creating resources.
- Prefer broadening resource options: remove unnecessary `region`, `zone`, or `instance_type`; use `any_of`/`ordered`; allow more clouds; reduce exact GPU count; consider spot/on-demand alternatives.
- Use `sky gpus list <GPU> --all-regions` when the user needs region availability hints, but do not manually scrape tables to choose the cheapest region.
- For quota errors on a required provider/region, request quota increase or choose a smaller/alternate resource shape.
- For capacity errors on a pinned zone, remove the zone pin before changing code.

## GPU Catalog And Availability Confusion

Symptoms:

- User asks why `A100`, `A100-80GB`, `H100`, or a TPU name is not accepted.
- `sky gpus list` shows prices but launch still fails.
- Kubernetes/Slurm GPU output differs from cloud catalog output.

Actions:

- Use `sky gpus list` to discover supported accelerator spellings and counts.
- Use `sky gpus list <accelerator>` for details, `--all` to include less-common accelerators, and `--all-regions` only with a specific accelerator.
- For Kubernetes, use `sky gpus list --infra k8s` to see requestable quantities per node and real-time utilization.
- For Slurm, use `sky gpus list --cloud slurm -v` to see per-partition availability.
- Remember that catalog support does not guarantee live quota or stock. Treat catalog output as feasible-offering evidence, not launch success.

## Kubernetes Context And Node Problems

Symptoms:

- `sky check kubernetes` is disabled or warns.
- Error names a missing kube context, namespace, service account, pod scheduling failure, PVC binding failure, GPU labels, taints, or node resources.
- `infra: k8s/<context>` works differently from `infra: k8s`.

Actions:

- Confirm the intended context: `infra: k8s` uses the current/default Kubernetes context; `infra: k8s/<context>` pins a context.
- Ask the user to run `kubectl config current-context` and `sky check kubernetes`; they should share context names and error categories only, not kubeconfig content.
- If GPUs are requested, ask for `sky gpus list --infra k8s` and whether nodes expose GPU resources plus recognized GPU labels.
- If no recognized GPU labels exist for NVIDIA nodes, suggest `sky gpus label`; if it failed, suggest `sky gpus label --cleanup` before retrying.
- If a pod is pending, distinguish resource shortage from policy blockers: node selectors, taints/tolerations, namespace quotas, service account/RBAC, image pull secrets, priority classes, and storage/PVC binding can all block scheduling.
- For multi-context workspaces, confirm `allowed_contexts` includes the selected context.

## Slurm Cluster Or Partition Problems

Symptoms:

- Error names a missing Slurm cluster, unavailable partition, GRES/GPU mismatch, `sbatch` failure, missing Pyxis, FUSE not enabled, or SSH to Slurm controller failed.

Actions:

- Interpret `slurm/<cluster>` as cluster pin and `slurm/<cluster>/<partition>` as cluster plus partition pin.
- Use `sky check slurm` for setup and SSH/controller access checks.
- Use `sky gpus list --cloud slurm -v` for accelerator availability by partition.
- If a partition is pinned and unavailable, remove the partition pin or select a partition that supports the requested GPU/CPU/memory.
- If Docker/container images are used, confirm Pyxis or the configured container backend exists for the Slurm cluster.
- If object storage `MOUNT` or `MOUNT_CACHED` is used, confirm FUSE support for that Slurm cluster; otherwise use `COPY` or stage data differently.

## SSH Node Pool Problems

Symptoms:

- Error says an SSH node pool is not set up, a pool name is missing, SSH connection failed, zones are unsupported, or host volume path is unavailable.

Actions:

- Use `infra: ssh` to allow any configured SSH pool or `infra: ssh/<pool>` to pin a pool.
- Do not set a zone for SSH pools; SSH node pools do not support zones.
- Ask the user to verify the pool exists via SkyPilot's SSH node-pool setup command and that the API server/client can SSH to the hosts.
- If a task references host paths or host volumes, confirm the paths exist on every target host that can run the task.
- If GPU detection fails, use the same GPU-resource and label reasoning as Kubernetes-compatible backends, then check host driver visibility.

## Object Storage And File Mount Failures

Symptoms:

- Error mentions bucket not found, mount command failed, FUSE/rclone missing, cloud URI unsupported, missing source for `COPY`, destination path conflict, or provider-specific object store credentials.

Actions:

- Identify the surface: `workdir`, `file_mounts`, `sky.Storage`, or `sky storage` lifecycle.
- For `COPY`, require a source path or cloud URI. Tests confirm `COPY` mode without source is invalid.
- For `MOUNT`, check whether the target infrastructure supports FUSE and the provider mount command.
- For `MOUNT_CACHED`, check cache config and writeback expectations; route exact YAML syntax to `task-yaml`.
- For provider-specific object stores such as R2, Nebius, CoreWeave, VAST Data, OCI, IBM, S3, GCS, or Azure, ask the user to run the provider credential check locally and share only redacted categories.
- If a mount error appears in a task that also has disabled-cloud output, fix credentials for the store/provider first, then re-check mount mode and FUSE support.
- Use `sky storage ls` to inspect SkyPilot-managed storage objects. Use `sky storage delete <name>` only after confirming the object name and workspace.

## Volume And PVC Failures

Symptoms:

- `sky volumes apply` fails, volume remains pending, deletion says `IN_USE`, task launch reports PVC binding/mount errors, or multi-node launch cannot mount a volume.

Actions:

- Confirm whether the user means SkyPilot object storage or SkyPilot volumes. Volumes are infrastructure-local and currently support Kubernetes PVCs and RunPod.
- Persistent volumes are managed by `sky volumes apply`, `sky volumes ls`, and `sky volumes delete`; ephemeral volumes are created from task YAML and deleted with the cluster lifecycle.
- For Kubernetes persistent volumes, check `type: k8s-pvc`, `infra: k8s` or `k8s/<context>`, `size`, namespace, storage class, and access mode.
- For multi-node clusters, require a storage class and access mode that support mounting on all nodes, typically `ReadWriteMany`.
- If `use_existing: true` is set, confirm the PVC exists by exact name or has the expected SkyPilot label in the selected namespace/context.
- If deletion is blocked by `IN_USE`, first identify and clean up the cluster/job/service still using the volume; route lifecycle cleanup to the owning sub-skill.
- If `sub_path` is used, confirm it is a persistent volume use case; `sub_path` is not for ephemeral volumes.

## Difficult Combined Case: Disabled Cloud Plus Storage Mount Error

When a user reports both disabled-cloud output and a storage mount failure:

1. Redact and classify the disabled-cloud status from `sky check <infra>`.
2. Identify whether the storage target uses the same provider as the disabled cloud. For example, an S3 mount can fail because AWS credentials are disabled even if the compute cloud is Kubernetes or Slurm.
3. Check mount mode: `COPY` requires a source, `MOUNT` needs FUSE/mount support, and `MOUNT_CACHED` needs cache config plus object-store credentials.
4. Ask for command categories, not secrets: provider enabled/disabled, bucket exists/does not exist, permission denied/not found, FUSE missing, PVC pending, or quota exceeded.
5. Fix credentials or workspace policy first, then resource capacity, then mount-specific configuration.

## When To Escalate Or Route

- Exact YAML edits: route to `task-yaml` after identifying the infrastructure/storage intent.
- Resource launch lifecycle, logs, cleanup, or dry-run command sequences: route to `cluster-operations`.
- Job-controller recovery or managed-job logs: route to `managed-jobs`.
- SkyServe replica readiness or service routing: route to `serving`.
- API server login, request IDs, remote server credentials, or dashboard: route to `sdk-api-server`.
