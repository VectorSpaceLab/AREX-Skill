---
name: storage-secrets-ingress
description: "Use LeptonAI storage/file, secret, ingress routing, access
  controls, and mount/env/secret parsing safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# storage-secrets-ingress

Use this sub-skill when a LeptonAI task involves workspace file storage, secrets, ingress/domain routing, canary endpoint weights, endpoint access-control flags, or validating storage mount/env/secret strings before a workload command.

## Route here for

- `lep storage ...` file-system commands and the hidden `lep file ...` alias.
- Storage operations: `upload`, `download`, `rm`, `rmdir`, `mkdir`, `du`, `ls`, and `ls-file-system`.
- `lep secret create/list/remove` planning, redaction, and secret-to-env references.
- `lep ingress list/create/get/delete/add-endpoint/remove-endpoint/update-endpoint/set-endpoints` planning.
- Canary routing with relative ingress weights and safe rollout/rollback command sequences.
- Endpoint access-control review involving `--public`, `--ip-whitelist`, and `--tokens`.
- Mount strings of the form `FROM_PATH:MOUNT_PATH:VOLUME`, including `node-local` and `node-nfs:<storage_name>`.
- Preflight parsing of `--mount`, `--env`, `--secret`, IP allowlist, token, and complete ingress endpoint-list plans without contacting Lepton.

## Route elsewhere

- Creating, updating, stopping, deleting, or scaling endpoints/jobs/pods/Ray/fine-tune workloads themselves: use `workload-management` and return here only for storage, secret, mount, ingress, or access-control details.
- Login, workspace selection, credential persistence, or token refresh: use `workspace-and-auth`.
- Python SDK endpoint calls and `APIClient` programming patterns not specific to storage/secret/ingress resource methods: use `sdk-client`.
- General `lep` command discovery, shell safety, and top-level CLI behavior: use `cli-operations`.

## Required safety posture

Lepton storage, secret, ingress, and endpoint access-control commands are workspace-scoped cloud operations. Do not run list/create/update/delete/upload/download commands unless the user has authorized the live workspace operation. Before any mutation or data transfer, produce a read-first plan, name the target resource/path/domain, ask for confirmation, and redact tokens and secret values.

Prefer these bundled references:

- [storage-and-secrets.md](references/storage-and-secrets.md) for file-storage and secret workflows.
- [ingress-and-routing.md](references/ingress-and-routing.md) for ingress lifecycle, canary weights, and access-control interplay.
- [mounts-env-secrets.md](references/mounts-env-secrets.md) for mount, env, secret, IP allowlist, token, and endpoint-list preflights.
- [troubleshooting.md](references/troubleshooting.md) for destructive replacements, path-confirmation errors, redaction, and delete safeguards.

## Quick safe preflight

Use the bundled parser before building workload or ingress commands:

```bash
python scripts/validate_mounts_env.py \
  --mount ./data:/mnt/data:node-local \
  --mount storage-cache:/cache:node-nfs:my-nfs \
  --env MODE=production \
  --secret API_KEY \
  --ip-whitelist 203.0.113.0/24 \
  --existing-endpoint stable:100 \
  --set-endpoint stable:90 \
  --set-endpoint canary:10
```

The script performs only local parsing/linting. It never opens a Lepton workspace client and never transfers data or mutates cloud state.

## Minimal mutation checklist

1. Identify the exact live target: storage path/file-system, secret name, ingress domain/name, endpoint name, or complete endpoint list.
2. Run a read command first when authorized: `lep storage ls ...`, `lep secret list`, `lep ingress get -n ...`, or the workload status route.
3. Validate local syntax with `scripts/validate_mounts_env.py` when mounts/env/secrets/IP allowlists or `set-endpoints` are involved.
4. Ask for explicit confirmation for `upload`, `download` overwrites, `rm`, `rmdir`, `secret remove`, `ingress delete`, `remove-endpoint`, and especially `set-endpoints`.
5. Execute only the confirmed command; do not print secret values or literal access tokens in logs.
