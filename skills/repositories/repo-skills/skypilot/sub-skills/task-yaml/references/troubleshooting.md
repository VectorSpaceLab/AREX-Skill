# Task YAML Troubleshooting

Use parser output first. The bundled validator reports the first parser exception for each file and never launches cloud resources.

## Schema or Unknown Field Errors

Symptoms:

- `Invalid task YAML:` or `Invalid resources YAML:`
- Unexpected key appears in the error.
- Final assertion says invalid task/resource args remain.

Fixes:

- Check indentation: `resources`, `file_mounts`, `volumes`, `config`, and `service` are top-level task fields; resource details must live under `resources`.
- Move lifecycle hooks to `config.hooks`; `resources.hooks` is intentionally rejected.
- Remove source-code/internal fields unless they are documented YAML fields.
- For service fields, put service-specific keys under `service:` in a task YAML or validate the file as a service-spec fragment with `--kind service`.

## Resource Syntax Failures

Symptoms:

- Errors around `infra`, `accelerators`, `any_of`, `ordered`, `cpus`, `memory`, `disk_size`, or `ports`.

Fixes:

- Prefer `infra: cloud/region/zone` over mixing legacy `cloud`, `region`, and `zone` fields.
- Use strings for lower bounds: `cpus: 4+`, `memory: 32+`.
- Use `accelerators: H100:1`, `accelerators: {H100: 1}`, or candidate entries. Avoid list-valued accelerators with `ordered` or ordered accelerator preference with `any_of`.
- Do not put both `any_of` and `ordered` under `resources`.
- If using `any_of` or `ordered`, keep candidate-specific values inside each list item and shared defaults at the base `resources` level.

## `any_of` vs `ordered` Confusion

Use `any_of` when candidates are equivalent alternatives and SkyPilot can optimize among them. Use `ordered` when user preference order matters.

Bad:

```yaml
resources:
  accelerators: [H100:1, A100:1]
  ordered:
    - infra: aws/us-east-1
    - infra: aws/us-west-2
```

Good:

```yaml
resources:
  ordered:
    - infra: aws/us-east-1
      accelerators: H100:1
    - infra: aws/us-west-2
      accelerators: A100:1
```

## Service Section in Normal Task

Symptoms:

- A YAML meant for `sky launch` contains `service:` and now validates as a service task.
- Service parser complains about `readiness_probe`, `replicas`, `replica_policy`, or `ports`.

Fixes:

- For ordinary cluster launch/exec YAML, remove `service:` and keep only task/resource fields.
- For SkyServe YAML, keep `service:` and validate with `--kind service`.
- Do not confuse `resources.ports` with `service.ports`; the former opens instance ports, the latter configures service routing.
- A service readiness path must start with `/`; `post_data` must be a dict or valid JSON string.

## Env and Secret Misuse

Symptoms:

- `Environment variable ... is None`.
- `Secret variable ... is None`.
- `Array items must use the secrets: prefix`.
- Docker login variables error about being split between `envs` and `secrets`.

Fixes:

- Replace null env values with explicit empty strings when intentional: `MY_VAR: ""`.
- Inline secret values use dict form: `secrets: {HF_TOKEN: "..."}`.
- Managed secret references use array entries such as `secrets:HF_TOKEN`, or dict keys `secrets:HF_TOKEN:` with a null value.
- Keep all related Docker login variables in either `envs` or `secrets`, not split across both.
- Do not include real secret values in reusable examples; use placeholders and explain how the user should provide them.

## Workdir and File Mount Pitfalls

Symptoms:

- Parser or later runtime says a local path does not exist.
- Remote files are missing because a relative path resolved from the wrong directory.
- Storage object validation fails before launch.

Fixes:

- Use absolute remote destinations such as `/data` or `/remote/project`.
- Remember local relative paths are evaluated from the caller's current directory at runtime.
- For parser-only checks of local mounts, use small existing temporary fixtures or omit local mounts until the actual user path is known.
- Do not tell future agents to depend on original repo examples/scripts; distill the pattern into the YAML they are authoring.
- Use `workdir` for source trees needed by `setup`/`run`; use `file_mounts` for data, configs, or object stores.

## Storage Mode Confusion

Symptoms:

- `COPY mode` complains about missing source.
- Mount-cached type/config errors.
- Object-store mount behavior does not match expectations.

Fixes:

- `MOUNT` is default and presents a mounted object-store directory remotely.
- `COPY` requires a source and copies data instead of mounting.
- `MOUNT_CACHED` is for rclone VFS cache workflows; set `type` to `MODEL_CHECKPOINT_RO`, `MODEL_CHECKPOINT_RW`, `DATASET_RO`, or `DATASET_RW` when a preset fits.
- `config.mount_cached` fields only apply to `MOUNT_CACHED`; `config.mount` fields only apply to `MOUNT`.
- Provider credential, bucket access, and Kubernetes volume topology failures belong to `../../infrastructure-storage/SKILL.md`.

## API Server Access Surprises

Symptoms:

- Task environment includes API server credentials unexpectedly.
- Serialized YAML omits `api_server_access`.

Fixes:

- `api_server_access` defaults to `true`.
- Set `api_server_access: false` when the task should not receive API server endpoint/token environment variables.
- Serialization omits `api_server_access` when it is true and includes it when false.

## Safe Triage Sequence

1. Run `python scripts/validate_task_or_service_yaml.py --kind auto FILE.yaml`.
2. If the file contains `service:`, route service runtime questions to `../../serving/SKILL.md` after schema fixes.
3. If parser validation passes but cloud/provider/storage access fails later, route to `../../infrastructure-storage/SKILL.md`.
4. If the YAML is for `sky jobs launch`, route job lifecycle and recovery semantics to `../../managed-jobs/SKILL.md` after the task YAML itself parses.
5. If the user wants to run it, route launch/status/log/cleanup planning to `../../cluster-operations/SKILL.md`.
