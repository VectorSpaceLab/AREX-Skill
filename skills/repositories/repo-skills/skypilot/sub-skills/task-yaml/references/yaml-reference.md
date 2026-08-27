# SkyPilot Task and Service YAML Reference

This reference distills the SkyPilot YAML parser and schema behavior into safe authoring guidance. It is self-contained for future agents and intentionally avoids depending on the original repository checkout.

## Parser-First Workflow

1. Draft the YAML with only the fields needed for the user's workflow.
2. Validate syntax and schema locally with `scripts/validate_task_or_service_yaml.py --kind auto FILE.yaml`.
3. Fix parser errors before choosing clouds or launching. Parser validation catches schema/field errors but does not prove cloud credentials, quotas, image IDs, ports, buckets, or instance availability.
4. Route actual launch, job, serve, or infrastructure checks to the neighboring sub-skills.

Useful safe APIs:

```python
import sky

task = sky.Task.from_yaml('task.yaml')
task_from_dict = sky.Task.from_yaml_config({'run': 'echo hello'})
resource = sky.Resources(infra='aws/us-east-1', accelerators='H100:1')
```

Verified signatures include:

- `sky.Task(name=None, *, setup=None, run=None, envs=None, secrets=None, workdir=None, num_nodes=None, file_mounts=None, storage_mounts=None, volumes=None, resources=None, docker_image=None, event_callback=None, blocked_resources=None, api_server_access=True, ...)`
- `sky.Task.from_yaml(yaml_path: str) -> Task`
- `sky.Task.from_yaml_config(config: Dict[str, Any], env_overrides=None, secrets_overrides=None) -> Task`
- `sky.Resources(cloud=None, instance_type=None, cpus=None, memory=None, accelerators=None, accelerator_args=None, infra=None, use_spot=None, job_recovery=None, region=None, zone=None, image_id=None, disk_size=None, ephemeral_storage=None, disk_tier=None, network_tier=None, local_disk=None, max_hourly_cost=None, ports=None, labels=None, autostop=None, hooks=None, priority=None, priority_class=None, volumes=None, ...)`

Prefer `infra` over legacy `cloud`, `region`, and `zone`. `infra` has the form `cloud`, `cloud/region`, `cloud/region/zone`, or `k8s/context-name`.

## Top-Level Task Fields

All task YAML fields are optional, but practical YAMLs usually contain at least `run`, `setup`, `workdir`, or a service definition.

| Field | Accepted shape | Guidance |
| --- | --- | --- |
| `name` | string | Display/task name. Valid names start/end with alphanumeric characters and may contain letters, digits, `_`, `.`, and `-` without triple separators. |
| `workdir` | string path or git dict | Local directory, relative path, or git repo config. Commands run under `~/sky_workdir` remotely. Relative local paths are evaluated from where `sky` is invoked, not from this skill. |
| `num_nodes` | integer | Total nodes including head. A task can request fewer nodes than an existing cluster size. |
| `resources` | mapping | Per-node resource requirements. Empty or omitted resources are allowed and let SkyPilot infer defaults later. |
| `envs` | mapping | Environment variables. Parser coerces keys/values to strings, but `null` values are invalid; use `VAR: ""` for empty string. |
| `secrets` | mapping or list | Inline secret values use dict form; managed secret references use `secrets:NAME` entries or dict keys with `null` values. Do not put real secrets in public examples. |
| `api_server_access` | boolean | Defaults to `true`; set `false` to avoid auto-injecting API server endpoint/token into the task environment. Serialized YAML omits the field when true. |
| `volumes` | mapping | Kubernetes volume mounts by remote mount path; value is a volume name or an ephemeral volume dict with `size` and optional config. |
| `file_mounts` | mapping | Remote path to local path, cloud URI, or storage mount dict. Use absolute remote paths. |
| `setup` | string or list | Commands run before `run`. Multiline strings with `|` are the normal YAML shape. |
| `run` | string or list | Main command. Future agents should not launch it during validation. |
| `config` | mapping | Task-level overrides such as provider config and lifecycle `hooks`. Put lifecycle hooks at `config.hooks`, not under `resources`. |
| `service` | mapping | SkyServe service spec embedded in a task YAML. Runtime serving belongs to the serving sub-skill. |
| `pool` | mapping | Cluster pool spec parsed through service-spec code. Managed pool operations belong to managed-jobs/serving guidance. |

The parser substitutes values from `envs` and inline `secrets` into `file_mounts`, `service`, `workdir`, and `volumes` for `$VAR` and `${VAR}` references. Managed secret reference array entries do not provide inline values for substitution.

## Resource Fields

Basic resource example:

```yaml
resources:
  infra: aws/us-west-2
  accelerators: H100:1
  cpus: 8+
  memory: 64+
  use_spot: true
  disk_size: 256
  disk_tier: medium
  ports:
    - 8080
```

| Field | Guidance |
| --- | --- |
| `infra` | Public cloud, optional region/zone, or Kubernetes context. Examples: `aws`, `aws/us-east-1`, `aws/us-east-1/us-east-1a`, `k8s`, `k8s/my-context`. |
| `accelerators` | String (`V100`, `V100:2`, `tpu-v2-8`), dict (`{V100: 2}`), or list for preference order. `gpus` is accepted as an alias for `accelerators`. |
| `cpus`, `memory` | Exact values or lower bounds as strings like `4+`, `32+`. `memory` is in GiB unless units are accepted by the parser. |
| `instance_type` | Cloud-specific instance type. Avoid mixing with generic fields unless you intentionally constrain further. |
| `use_spot` | Boolean. Spot recovery semantics for managed jobs are covered by `job_recovery` and the managed-jobs sub-skill. |
| `job_recovery` | String strategy or dict. String `none` disables recovery. Dicts can include `strategy`, `max_restarts_on_errors`, and `recover_on_exit_codes`; plugin fields may pass through client-side for server validation. |
| `disk_size`, `ephemeral_storage` | Size as integer or size string. `disk_size` controls OS disk; `ephemeral_storage` is a separate resource field where supported. |
| `disk_tier`, `network_tier` | Performance tier strings, commonly `medium` for disk and `standard`/`best` for network. |
| `image_id` | Provider image string or region-to-image mapping; Docker images may be represented through image handling. Credential/debug details belong to infrastructure-storage. |
| `ports` | Integer, string, list, or tuple accepted by `sky.Resources`; use service-level ports for SkyServe readiness/routing. |
| `labels` | Key/value labels passed to supported providers. Candidate-specific labels merge with base labels in `any_of` and `ordered`. |
| `autostop` | `false`, integer minutes, time string, or dict with `idle_minutes`, `down`, and `wait_for`. Cluster autostop operations route to cluster-operations. |
| `priority` | Integer from `-1000` to `1000`, higher means higher scheduling priority. |
| `priority_class` | Logical priority class; do not set both `priority` and `priority_class` for server-side admin-policy flows. |

### `any_of` and `ordered`

`resources.any_of` and `resources.ordered` are top-level resource candidate lists, not sibling top-level task fields.

```yaml
resources:
  cpus: 8+
  memory: 32+
  any_of:
    - infra: aws/us-west-2
      accelerators: A10G:1
    - infra: gcp/us-central1
      accelerators: L4:1
```

```yaml
resources:
  ordered:
    - infra: aws/us-east-1
      accelerators: H100:1
    - infra: aws/us-west-2
      accelerators: A100:1
```

Rules to remember:

- Do not specify both `any_of` and `ordered` in the same `resources` mapping.
- Base resource fields are copied into each candidate, then candidate fields override the base.
- Candidate `labels` merge with base labels rather than replacing them wholesale.
- A list-valued `accelerators` expresses preferred accelerator order. It conflicts with `ordered`, and ordered accelerator lists conflict with `any_of`; expand accelerator choices into explicit candidates instead.

## File Mounts, Storage, and Volumes

Local copy and object-store examples:

```yaml
file_mounts:
  /remote/project-data: ./data
  /checkpoints:
    source: s3://my-existing-bucket/checkpoints
    mode: MOUNT
  /dataset:
    source: s3://my-dataset
    mode: MOUNT_CACHED
    type: DATASET_RO
```

Storage dict fields accepted under `file_mounts` include:

| Field | Guidance |
| --- | --- |
| `source` | Local path, cloud URL, or list of local paths. Missing local sources can fail parser construction because storage objects validate eagerly. |
| `name` | Storage/bucket name when creating or referencing a named store. |
| `store` | Store type such as `S3`, `GCS`, `AZURE`, `R2`, `IBM`, `OCI`, `NEBIUS`, `COREWEAVE`, `VASTDATA`, `HF`, or `VOLUME`. |
| `persistent` | Defaults to `true`. Set `false` only when deletion after cluster teardown is intended. |
| `mode` | `MOUNT` by default; also supports `COPY` and `MOUNT_CACHED`. Mode is case-insensitive in the parser. |
| `type` | `MOUNT_CACHED` preset: `MODEL_CHECKPOINT_RO`, `MODEL_CHECKPOINT_RW`, `DATASET_RO`, or `DATASET_RW`. |
| `config.mount_cached` | Rclone tuning fields such as `transfers`, `buffer_size`, `vfs_cache_max_size`, `vfs_cache_max_age`, `vfs_read_ahead`, `vfs_read_chunk_size`, `vfs_read_chunk_streams`, `vfs_write_back`, `read_only`. |
| `config.mount` | Mount-mode fields such as `read_only` and Hugging Face-specific `hf_mount_args`. |

Storage mode decision guide:

- Use plain string local mounts for small local files/directories copied to remote paths.
- Use `MOUNT` for object stores that should appear as mounted remote directories.
- Use `COPY` when the object store should be synchronized/copied rather than mounted.
- Use `MOUNT_CACHED` for large model or dataset reads where rclone VFS cache tuning matters.
- Use `store: volume` only for the special volume-backed file-mount path that translates into resource volume config; ordinary Kubernetes volumes normally use top-level `volumes`.

Top-level `volumes` examples:

```yaml
volumes:
  /mnt/data: existing-volume-name
  /mnt/cache:
    size: 100Gi
```

Top-level `volumes` values must be either an existing volume name or a dict with enough information for an ephemeral volume, typically `size`. Empty dicts, lists, or dicts without `name`/`size` are invalid. Volume topology can conflict with resource topology; route deeper provider/Kubernetes diagnosis to `../../infrastructure-storage/SKILL.md`.

## Envs and Secrets

Good patterns:

```yaml
envs:
  MODEL_SIZE: 13b
  DATA_DIR: /data
secrets:
  HF_TOKEN: "replace-at-submit-time"
```

Managed secret references:

```yaml
secrets:
  - secrets:HF_TOKEN
  - secrets:workspace.WANDB_API_KEY
```

Dict-form managed references require null values:

```yaml
secrets:
  secrets:HF_TOKEN:
```

Rules:

- `envs` and inline `secrets` must not have `null` values; use empty strings when required.
- Array-form `secrets` entries must start with `secrets:` and represent managed secret references, not inline values.
- Dict keys prefixed with `secrets:` are managed references and must have null values.
- Docker login variables must live entirely in `envs` or entirely in `secrets`; splitting related Docker variables across both fails validation.
- Do not include real secret values in generated examples. Use placeholders and tell users to provide secrets via CLI/user secret management when appropriate.

## `config` Field

`config` carries task-level provider/runtime overrides. Common examples include provider sections and lifecycle hooks:

```yaml
config:
  kubernetes:
    provision_timeout: 600
  hooks:
    - events: [preemption, down]
      timeout: 60
      run: |
        echo "cleanup or checkpoint command"
```

Important parser behavior:

- Lifecycle hooks belong under top-level `config.hooks`.
- `resources.hooks` is explicitly rejected; move that list to `config.hooks`.
- Hook entries require `run`; `events` defaults to all supported events when omitted and may include `stop`, `preemption`, and `down`.
- Large hook bodies should be moved into scripts inside `workdir` and called from the hook command.

## Service YAML Fields

A SkyServe YAML is usually a task YAML plus a `service:` section:

```yaml
name: text-generation
resources:
  accelerators: L4:1
  ports: 8000
run: |
  python -m http.server 8000
service:
  readiness_probe:
    path: /
    initial_delay_seconds: 10
    timeout_seconds: 5
  replicas: 2
  ports: 8000
```

The service-spec parser accepts these common fields:

| Field | Guidance |
| --- | --- |
| `readiness_probe` | String path like `/health` or mapping with `path`, `post_data`, `headers`, `initial_delay_seconds`, `timeout_seconds`, `endpoint_probe_interval_seconds`, and `consecutive_failure_threshold_timeout`. Paths must start with `/`. `post_data` may be a dict or a JSON string. |
| `replicas` | Simplified fixed replica count. Do not combine with `replica_policy`. |
| `replica_policy` | Advanced policy with `min_replicas`, optional `max_replicas`, `num_overprovision`, `target_qps_per_replica`, fallback and delay fields. `target_qps_per_replica` requires `max_replicas`. |
| `ports` | Service port integer from 1 to 65535. Task-level `resources.ports` opens ports on instances; service-level `service.ports` is service routing config. |
| `load_balancer` | Includes `stream_timeout_seconds`. |
| `load_balancing_policy` | Must be a known policy. Dict-valued `target_qps_per_replica` requires `instance_aware_least_load`. |
| `pool`, `workers`, `min_workers`, `max_workers` | Cluster pool service spec shapes. Do not combine incompatible pool fields with service fields. |

Rules:

- `replicas` and `replica_policy` are mutually exclusive.
- `replicas` and `workers` are mutually exclusive.
- `pool` cannot be combined with top-level task `service` in the same task config path.
- If `max_replicas` differs from `min_replicas`, set `target_qps_per_replica` to enable autoscaling.
- Runtime service up/update/status/logs belong to the serving sub-skill; this sub-skill only validates and authors YAML fields.

## Distilled Recipes

### Minimal Task

```yaml
name: hello-sky
resources:
  cpus: 2+
run: |
  echo "hello from SkyPilot"
```

### Candidate Resources with Mounts and Substitution

```yaml
name: train-candidates
envs:
  MODEL: llama
  DATA_BUCKET: my-dataset-bucket
resources:
  any_of:
    - infra: aws/us-west-2
      accelerators: A10G:1
      use_spot: true
    - infra: gcp/us-central1
      accelerators: L4:1
file_mounts:
  /data:
    source: s3://${DATA_BUCKET}
    mode: MOUNT_CACHED
    type: DATASET_RO
setup: |
  pip install -r requirements.txt
run: |
  python train.py --model ${MODEL} --data /data
```

### Ordered Fallback Without Accelerator List Conflict

```yaml
resources:
  ordered:
    - infra: aws/us-east-1
      accelerators: H100:1
    - infra: aws/us-west-2
      accelerators: A100:1
run: python benchmark.py
```

Do not write `accelerators: [H100:1, A100:1]` together with `ordered`; expand each accelerator into an explicit ordered candidate.

### Service Task with Readiness

```yaml
name: web-service
resources:
  infra: k8s/my-context
  ports: 8080
run: |
  python -m http.server 8080
service:
  readiness_probe:
    path: /
    initial_delay_seconds: 5
    timeout_seconds: 5
  replicas: 1
  ports: 8080
```

Validate this with `--kind service` or `--kind auto`; use the serving sub-skill for `sky serve up`, update, status, and logs.
