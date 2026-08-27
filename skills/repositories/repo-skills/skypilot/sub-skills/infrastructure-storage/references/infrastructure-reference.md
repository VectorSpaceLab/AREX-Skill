# SkyPilot Infrastructure And Storage Reference

This reference distills the infrastructure, resource, GPU, storage, and volume surfaces owned by the `infrastructure-storage` sub-skill.

## Infrastructure Selection

SkyPilot can optimize across clouds when the user describes requirements instead of a fixed provider. Use `infra` only when placement matters.

| Intent | Preferred form | Notes |
| --- | --- | --- |
| Let SkyPilot choose | `accelerators: H100:1`, `cpus`, `memory`, `disk_size`, `use_spot` | Best default for multi-cloud cost/availability optimization. |
| Pin cloud only | `infra: aws`, `infra: gcp`, `infra: azure`, `infra: lambda`, etc. | Use when credentials, compliance, data locality, or provider-specific features require it. |
| Pin cloud + region | `infra: aws/us-east-1` | Narrows failover; use for data locality, quotas, or latency. |
| Pin cloud + region + zone | `infra: gcp/us-central1/a` | Most restrictive; use only when topology or volume locality requires it. |
| Kubernetes | `infra: k8s`, `infra: kubernetes`, `infra: k8s/<context>` | `k8s` is accepted as an alias and normalizes to Kubernetes. The context is stored as the infra region. |
| Slurm | `infra: slurm`, `infra: slurm/<cluster>`, `infra: slurm/<cluster>/<partition>` | Slurm cluster maps to region; partition maps to zone. |
| SSH node pool | `infra: ssh`, `infra: ssh/<pool>` | SSH node pools are exposed as contexts whose internal names start with `ssh-`. Zones are not supported. |
| RunPod volumes | `infra: runpod` or a RunPod data-center form for volume YAML | Volumes are supported on RunPod in addition to Kubernetes. |

Prefer `--infra` in CLI commands. Older `--cloud`, `--region`, and `--zone` flags are compatibility surfaces and should not be mixed with `--infra`.

## Credential And Workspace Checks

Use these commands as local user actions; do not request raw credential files.

| Check | Command | Use when |
| --- | --- | --- |
| All configured infrastructures | `sky check` | Initial setup or disabled-cloud triage. |
| One provider | `sky check aws`, `sky check gcp`, `sky check azure`, `sky check kubernetes`, `sky check slurm`, `sky check ssh` | Error mentions a provider, context, cluster, or node pool. |
| Workspace-specific readiness | `sky check --workspace <name>` | User uses workspaces or reports workspace-scoped disabled clouds. |
| GPU catalog | `sky gpus list` | User asks what accelerators are supported or how to spell GPU names. |
| Provider GPU details | `sky gpus list H100 --infra aws/us-east-1` | User needs provider/region-specific details. |
| Kubernetes real-time GPUs | `sky gpus list --infra k8s` or `sky gpus list --cloud k8s` | User is on Kubernetes and needs requestable quantities or utilization. |
| Slurm real-time GPUs | `sky gpus list --cloud slurm -v` | User is on Slurm and needs per-partition accelerator availability. |

`sky check` reports enabled and disabled infrastructures. Disabled clouds normally mean missing credentials, missing provider SDK/CLI, insufficient permissions, or workspace policy exclusions. Capacity and quota failures usually happen later during optimizer/provisioning and should not be treated as credential failures.

Workspaces can restrict clouds and Kubernetes contexts. Additive changes that only add Kubernetes allowed contexts are treated as safe for existing contexts; removing or changing contexts can affect cluster/job placement.

## Resource Selection Rules

- Start with `accelerators`, `cpus`, `memory`, `disk_size`, `ephemeral_storage`, `use_spot`, and `ports`; let SkyPilot map them to instances and locations.
- Use `instance_type` only when the user needs a known SKU, Slurm instance mapping, or provider-specific capacity target.
- Use `max_hourly_cost` or optimization targets instead of manually selecting a cheapest region from CLI tables.
- Use `ordered` or `any_of` resources in task YAML when the user wants explicit fallback order or multiple acceptable resource shapes; route exact YAML syntax to `task-yaml`.
- Treat `disk_size`, `disk_tier`, `network_tier`, `local_disk`, and `ephemeral_storage` as infrastructure properties, not storage mounts. Route field syntax to `task-yaml` and provider/availability symptoms here.
- For multi-node jobs with shared storage, check whether the storage mode supports all nodes. Kubernetes PVC volumes need `ReadWriteMany` access mode and a compatible storage class when mounted across multiple nodes.

## Kubernetes Reference

SkyPilot Kubernetes support expects a working kubeconfig or in-cluster context, Kubernetes v1.20 or later for normal setups, and GPU nodes configured with device resources plus GPU labels when accelerators are used.

Common Kubernetes forms:

```yaml
resources:
  infra: k8s/my-context
  accelerators: H100:1
  cpus: 8+
  memory: 32+
```

Kubernetes setup checkpoints:

- `kubectl config current-context` should match the intended context when using `infra: k8s`, or use `infra: k8s/<context>` for explicit placement.
- `sky check kubernetes` should show Kubernetes enabled without warnings for the selected workspace/context.
- NVIDIA GPU nodes need `nvidia.com/gpu` resources and a GPU label such as `nvidia.com/gpu.product`, `cloud.google.com/gke-accelerator`, `karpenter.k8s.aws/instance-gpu-name`, or `skypilot.co/accelerator`.
- `sky gpus label` can label NVIDIA GPU nodes when no recognized label exists; use `sky gpus label --cleanup` after failed labeler jobs.
- AMD GPU nodes need `amd.com/gpu` resources and AMD GPU Operator setup; label handling differs from NVIDIA and may require manual labels.
- Pod overrides, namespace, priority classes, service accounts, port exposure, FUSE, and custom volume mounts are advanced Kubernetes config surfaces; use them only when the user's cluster policy requires them.

Kubernetes instance-type strings can be synthesized from resource requests by SkyPilot. If a user accidentally passes a cloud VM instance type to Kubernetes, treat the resulting error as an infrastructure mismatch and either remove the `instance_type` or switch `infra` to the intended cloud.

## Slurm Reference

Slurm support maps SkyPilot regions and zones to scheduler concepts:

- Region: Slurm cluster name.
- Zone: Slurm partition.
- `infra: slurm` lets SkyPilot consider configured clusters and partitions.
- `infra: slurm/<cluster>` pins the Slurm cluster.
- `infra: slurm/<cluster>/<partition>` pins both cluster and partition.

Slurm readiness depends on a Slurm configuration known to SkyPilot, SSH access to the controller/login host, partitions with usable CPU/GPU resources, optional Pyxis support for container images, optional FUSE support for mounted object storage, and scheduler permissions.

For Slurm GPU availability, prefer `sky gpus list --cloud slurm -v` so the output includes per-partition details. If a GPU task fails with a partition or GRES error, check the partition's GPU map and whether the requested accelerator name/count is supported there.

## SSH Node Pool Reference

SSH node pools let SkyPilot use existing machines through an SSH pool abstraction. They share much of the Kubernetes scheduling/provisioning path but represent pools as SSH contexts.

Use `infra: ssh` or `infra: ssh/<pool>` for placement. A pool named `my-pool` is internally represented with an `ssh-my-pool` context; users should reason about the pool name, not edit internal context names manually. SSH node pools do not support zones.

Triage SSH pools by checking that the pool was set up with SkyPilot, the named pool exists, host SSH connectivity works from the API server/client context, the pool has enough CPU/memory/GPU resources, and any host volumes referenced by tasks exist on the target hosts.

## Object Storage And File Mounts

SkyPilot object storage is represented by `sky.Storage` and YAML storage configs. The installed API exposes `sky.Storage(name=None, source=None, stores=None, persistent=True, mode=StorageMode.MOUNT, ...)`.

Supported store families include S3, GCS, Azure Blob, Cloudflare R2, IBM, OCI, Nebius, CoreWeave, Hugging Face, and VAST Data, with provider-specific credentials and mount commands handled by SkyPilot.

Storage modes:

| Mode | Behavior | Use when |
| --- | --- | --- |
| `MOUNT` | Mounts an object store path into the cluster, usually through FUSE. This is the default storage mode. | Large datasets or outputs that should remain in object storage. |
| `COPY` | Copies data into the cluster as regular file mounts. Source must be specified when creating COPY-mode storage. | Small/medium inputs that should be local to the VM/container. |
| `MOUNT_CACHED` | Uses a cached object-store mount with configurable cache/writeback behavior. | Repeated reads, model/cache workloads, or cases needing cached remote object storage. |

`file_mounts` can map local paths or cloud URIs into remote paths. Object-store `COPY` storage is translated into cloud-to-remote file mounts during sync. `MOUNT` and `MOUNT_CACHED` may require FUSE or rclone-like support on the target infrastructure.

`sky storage ls` lists SkyPilot-managed storage objects. `sky storage delete <name>` deletes managed storage objects; use `--all` only after confirming the workspace and ownership scope.

## Volumes Reference

Volumes are high-performance alternatives to cloud buckets. They are region/infrastructure-local rather than cross-cloud object stores. Current volume support covers Kubernetes PVC-backed volumes and RunPod.

Persistent Kubernetes PVC volume YAML:

```yaml
name: shared-cache
type: k8s-pvc
infra: k8s/my-context
size: 100Gi
config:
  namespace: default
  storage_class_name: fast-rwx
  access_mode: ReadWriteMany
```

Mount a persistent volume in a task:

```yaml
volumes:
  /mnt/data: shared-cache
```

Ephemeral volume in a task:

```yaml
volumes:
  /mnt/cache:
    type: k8s-pvc
    infra: k8s/my-context
    size: 100Gi
    config:
      storage_class_name: fast-rwx
      access_mode: ReadWriteMany
```

Volume lifecycle:

| Surface | Lifecycle | Command/field |
| --- | --- | --- |
| Persistent volume | Independent of clusters; shared through API server/workspace state | `sky volumes apply`, `sky volumes ls`, `sky volumes delete`, task `volumes: /path: volume-name` |
| Ephemeral volume | Created for a cluster and deleted with `sky down` or autodown | Inline task `volumes: /path: {type, infra, size, config}` |
| Existing PVC | Managed outside SkyPilot or migrated across API servers | Volume YAML with `use_existing: true` |
| Advanced Kubernetes volume | Native PVC/NFS/hostPath through pod config | Kubernetes pod config, not normal SkyPilot volume lifecycle |

For multi-node clusters, choose an access mode and storage class that support mounting on all nodes. `sub_path` is supported for persistent volumes, not ephemeral volumes.

## Source Script Decisions

No source repository scripts were copied for this sub-skill. The bundled `scripts/resource_checklist.py` is an adapted DisCo helper that prints safe, provider/resource/storage preflight guidance from user-supplied arguments. It intentionally avoids SkyPilot imports, credential reads, kubeconfig reads, cloud API calls, and infrastructure mutations.
