---
name: auth-sync-transport
description: "Authenticate PySyft clients, manage SyftBox transport, peer
  lifecycle, checkpoints, and version diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# auth-sync-transport

Use this sub-skill for `login_do`, `login_ds`, OAuth token files, Google Drive/SyftBox sync, peer requests, approvals/rejections, checkpoints, rolling state, version negotiation, and safe cleanup.

## Workflow

1. Identify role: data owner, data scientist, or both.
2. For local/Jupyter usage, require explicit `email` and `token_path`; Colab may use browser auth.
3. Validate token shape safely with [scripts/validate_token_file.py](scripts/validate_token_file.py). Use `--live-drive-check` only with permission because it contacts Google Drive.
4. DS calls `add_peer(do_email)`; DO calls `load_peers()` then `approve_peer_request(ds_email)` or `reject_peer_request(...)`.
5. Both sides call `sync()` and re-check `peers` before moving to datasets/jobs.
6. Diagnose peer version mismatch before forcing `skip_peer_on_patch_version_diff` or `ignore_peer_version`.

Read [references/authentication.md](references/authentication.md), [references/transport-internals.md](references/transport-internals.md), [references/api-reference.md](references/api-reference.md), and [references/troubleshooting.md](references/troubleshooting.md).

Route dataset issues to [../datasets-permissions/SKILL.md](../datasets-permissions/SKILL.md), jobs to [../jobs-execution/SKILL.md](../jobs-execution/SKILL.md), background services to [../background-services/SKILL.md](../background-services/SKILL.md), and enclaves/restrict to [../enclaves-restrict/SKILL.md](../enclaves-restrict/SKILL.md).
