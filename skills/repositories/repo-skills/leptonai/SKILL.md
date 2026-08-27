---
name: leptonai
description: "Use the LeptonAI Python SDK and lep CLI for NVIDIA DGX Cloud
  Lepton workspaces, endpoint calls, workloads, storage, secrets, ingress
  routing, and safe cloud-operation planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LeptonAI

Use this repo skill when the task involves the `leptonai` Python package, the `lep` CLI, or NVIDIA DGX Cloud Lepton workspace operations: endpoints, jobs, dev pods, Ray clusters, fine-tuning jobs, storage, secrets, ingress, logs, or Python endpoint clients.

Do **not** run live Lepton cloud mutations just because this skill is loaded. Creating, updating, stopping, deleting, uploading, downloading, setting ingress endpoints, creating secrets, or opening `pod ssh` requires explicit user confirmation for the single target after a read-first plan.

## First checks

Install for normal use:

```bash
pip install -U leptonai
lep --help
```

For a source checkout or contributor context:

```bash
pip install -e .
# add tests only when needed for repo-native validation
pip install -e .[test]
```

Minimal Python import smoke:

```python
import leptonai
from leptonai.client import Client, local
print(leptonai.__version__)
print(local(8080))
```

Safe bundled checks that do not contact Lepton:

```bash
python scripts/leptonai_smoke_check.py --groups endpoint workspace job pod ingress storage
python scripts/inspect_leptonai.py
```

## Route by task

| User task | Read next |
| --- | --- |
| Discover `lep`, list command groups, classify read-only vs mutating commands, handle hidden aliases or abbreviations, scope outputs/logs | [sub-skills/cli-operations/SKILL.md](sub-skills/cli-operations/SKILL.md) |
| Log in, choose/switch workspaces, inspect auth state safely, build `APIClient`, troubleshoot 401/403/404/token/URL issues | [sub-skills/workspace-and-auth/SKILL.md](sub-skills/workspace-and-auth/SKILL.md) |
| Call a deployed endpoint from Python, inspect OpenAPI-derived `Client` paths, build SDK scripts with v2 API resources or Pydantic specs | [sub-skills/sdk-client/SKILL.md](sub-skills/sdk-client/SKILL.md) |
| Operate endpoints/deployments, dev pods, jobs, Ray clusters, fine-tunes, templates, resource shapes, logs, events, nodes | [sub-skills/workload-management/SKILL.md](sub-skills/workload-management/SKILL.md) |
| Plan storage/file transfer, secrets, ingress/canary routing, IP allowlists, tokens, mount/env/secret validation | [sub-skills/storage-secrets-ingress/SKILL.md](sub-skills/storage-secrets-ingress/SKILL.md) |
| Check package version, Python support, entry points, and refresh baseline | [references/package-overview.md](references/package-overview.md) and [references/repo-provenance.md](references/repo-provenance.md) |
| Diagnose install/import, CLI availability, version warnings, credentials, network, or stale skill concerns | [references/troubleshooting.md](references/troubleshooting.md) |

## Safety defaults

1. Prefer help and read-only commands before any mutation: `lep --help`, `lep <group> --help`, `lep workspace list/status/id/url`, `lep endpoint list/status`, `lep job list/get`, `lep ingress get`, or `lep storage ls`.
2. Expand hidden aliases and abbreviations to full names in plans. Prefer `lep endpoint` over hidden legacy `lep deployment`, and prefer `lep storage` over hidden `lep file` unless a user explicitly needs compatibility.
3. Redact tokens and secret values. Avoid `lep workspace token` unless the user explicitly asks to retrieve the raw token as the task.
4. Treat `create`, `update`, `stop`, `start`, `restart`, `remove`, `delete`, `rm`, `rmdir`, `upload`, `download` to sensitive local paths, `ingress set-endpoints`, and `pod ssh` as mutating or high-impact.
5. For mutations, read current state first, show exact command, workspace, target resource/path/domain, observed state, and one-sentence impact; ask for explicit confirmation for that target only.
6. Live Lepton operations require authenticated workspace context and may incur cost, alter traffic, expose endpoints, or delete cloud data.

## Important boundaries

- Local GPU hardware is not required to use the SDK/CLI package. Lepton workloads may request GPU resource shapes in the remote workspace, but that is a cloud-capacity decision, not a local CUDA install requirement.
- `Client(...)` for a real URL/workspace endpoint fetches OpenAPI metadata and makes network calls. Use `no_check=True` only when intentionally deferring that check.
- `APIClient()` and its resource methods are live workspace API clients. Do not instantiate or call them for mutation unless the workspace/auth route has established context and the user has approved the operation.
- This generated skill is self-contained. If the current package source, CLI commands, or tests differ from [references/repo-provenance.md](references/repo-provenance.md), refresh the skill rather than relying on stale routes.
