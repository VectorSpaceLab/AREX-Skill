# Mounts, env vars, secrets, and local preflight parsing

LeptonAI workload commands share helper logic for mount strings and environment/secret references. Use this reference to validate inputs before routing the actual workload create/update to `workload-management`.

## Where these flags appear

The same parsing rules are used by multiple workload surfaces:

| Surface | Mount flag | Env flag | Secret flag |
|---|---|---|---|
| Endpoint create/update | `--mount` | `--env` / `-e` | `--secret` / `-s` |
| Dev pod create | `--mount` | `--env` | `--secret` |
| Job create | `--mount` | `--env` | `--secret` |
| Fine-tune job create | `--mount` | selected job flags | selected fixed secret helpers plus `--secret`-style injection internally |
| Ray cluster create | `--head-mount` and worker-group `--mount` | `--head-env` and worker-group env | `--head-secret` and worker-group secret |

Only validate and explain the flags here. Do not perform workload deployment from this sub-skill.

## Mount string format

Mount strings are split on the first two colons:

```text
FROM_PATH:MOUNT_PATH:VOLUME
```

- `FROM_PATH`: source path for the storage or node volume.
- `MOUNT_PATH`: path where the workload sees the volume.
- `VOLUME`: documented forms are `node-local` or `node-<type>:<storage_name>`.

Because parsing splits only on the first two colons, the `VOLUME` part may itself contain one colon, which is required for named node volumes.

Valid examples:

```bash
--mount ./data:/mnt/data:node-local
--mount storage-cache:/cache:node-nfs:my-nfs
```

Invalid examples and corrections:

| Invalid input | Why it fails | Safer correction |
|---|---|---|
| `storage-cache:/cache` | Missing `VOLUME`. | `storage-cache:/cache:node-local` or a named volume form. |
| `storage-cache:/cache:node-nfs` | `node-nfs` is a named node volume type but lacks `storage_name`. | `storage-cache:/cache:node-nfs:my-nfs` |
| `storage-cache:/cache:node-nfs:` | Empty `storage_name`. | Provide a real storage name after the final colon. |
| `storage-cache:/cache:node-:my-nfs` | Empty storage type after `node-`. | Use a concrete type such as `node-nfs:my-nfs`. |
| `storage-cache:/cache:node-nfs:name:extra` | More than one colon after `node-<type>`. | Use exactly `node-nfs:<storage_name>`. |

Implementation notes:

- The helper rejects an empty `VOLUME`.
- The helper specifically validates `node-*` volumes. Non-`node-*` volume strings may pass local parsing, but the command help documents `node-local` and named `node-<type>:<storage_name>` forms; prefer documented forms unless the platform explicitly supports another value.
- The helper does not prove that a storage path or named volume exists. Use authorized read commands, file-system listing, or platform UI/API checks before a live workload launch.

## Environment variables

`--env` values must be `NAME=VALUE` and are split on the first `=`. The value can contain additional `=` characters.

```bash
--env MODE=production
--env CONFIG_JSON='{"debug": false}'
```

Rules and safety:

- Missing `=` is invalid.
- Empty or whitespace-only command-line values are rejected by the CLI's global Click validation.
- Platform-reserved environment names are rejected.
- Values may contain credentials accidentally; redact values in plans unless the user confirms they are safe to show.

## Secret references as environment variables

`--secret` injects a secret reference into an environment variable rather than embedding a literal value in the command payload.

Forms:

```bash
# Env var name and secret name are the same
--secret API_KEY

# Env var name differs from the secret name
--secret APP_API_KEY=PROD_API_KEY
```

Rules and safety:

- If there is no `=`, the helper treats the string as `NAME=NAME`.
- The environment variable name is checked against platform-reserved names.
- The helper does not prove that the referenced secret already exists. Use `lep secret list` only after the user authorizes a workspace read.
- Secret values are never needed for workload command construction; do not ask the user to paste them unless the task is explicitly to create or rotate a secret.

## Endpoint access-control local checks

The bundled preflight script can also lint endpoint access-control choices used by endpoint create/update plans:

```bash
python scripts/validate_mounts_env.py \
  --public \
  --token '<redacted-token-placeholder>'

python scripts/validate_mounts_env.py \
  --ip-whitelist '203.0.113.0/24,198.51.100.10' \
  --token '<redacted-token-placeholder>'
```

The script reports that `--public` and `--ip-whitelist` are mutually exclusive. It counts token arguments but does not print token values. Actual endpoint mutation remains owned by `workload-management`.

## Ingress endpoint-list local checks

For `lep ingress set-endpoints`, the script can compare an existing endpoint list with a proposed complete replacement list:

```bash
# Fails because stable-v1 would be removed by set-endpoints.
python scripts/validate_mounts_env.py \
  --existing-endpoint stable-v1:100 \
  --existing-endpoint canary-v2:10 \
  --set-endpoint canary-v2:100

# Succeeds only when the full intended list is supplied or explicitly acknowledged.
python scripts/validate_mounts_env.py \
  --existing-endpoint stable-v1:100 \
  --existing-endpoint canary-v2:10 \
  --set-endpoint stable-v1:90 \
  --set-endpoint canary-v2:10
```

Use `--ack-complete-set` only after the user confirms that omitted endpoints should be removed. This flag is a local lint acknowledgment; it does not call Lepton.

## Bundled preflight script

Run:

```bash
python scripts/validate_mounts_env.py --help
```

Useful examples:

```bash
# Validate mount/env/secret syntax only.
python scripts/validate_mounts_env.py \
  --mount storage-cache:/cache:node-nfs:my-nfs \
  --env MODE=production \
  --secret APP_API_KEY=PROD_API_KEY

# Emit sanitized JSON for another planning tool.
python scripts/validate_mounts_env.py \
  --mount storage-cache:/cache:node-nfs:my-nfs \
  --env MODE=production \
  --secret API_KEY \
  --json

# Show a clear diagnostic for a missing named-volume storage name.
python scripts/validate_mounts_env.py \
  --mount storage-cache:/cache:node-nfs
```

Expected behavior:

- Exit `0` when there are no errors and no unacknowledged destructive `set-endpoints` risk.
- Exit nonzero when a mount/env/secret/IP/endpoint-list error is found.
- Print only sanitized values by default; token, env, and secret values are not displayed.
- Import package parsing helpers when they are installed and usable; otherwise use equivalent local fallback logic.
- Never construct `APIClient`, read workspace records, contact Lepton APIs, or transfer data.
