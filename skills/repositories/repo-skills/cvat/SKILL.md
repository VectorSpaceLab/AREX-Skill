---
name: cvat
description: "Operate CVAT for computer-vision annotation, dataset workflows,
  SDK/CLI automation, auto-annotation, and self-hosted deployment."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# CVAT repo skill

Use this repo skill when a task involves CVAT (Computer Vision Annotation Tool): self-hosted computer-vision annotation, task/project automation, dataset import/export, Python SDK scripts, `cvat-cli`, auto-annotation functions, serverless model deployment, backups, frames, organizations, or deployment troubleshooting.

## Fast routing

| User intent | Read |
|---|---|
| Python automation with `cvat_sdk`, profiles, `Client`, task/project objects, uploads, downloads, backups, background operations | `sub-skills/sdk-automation/SKILL.md` |
| Terminal automation with `cvat-cli`, profiles/config, task/project commands, native function commands, JSON shell scripting | `sub-skills/cli-automation/SKILL.md` |
| Dataset formats, import/export, images included/excluded, manifests, frame downloads, backups, PyTorch dataset adapter | `sub-skills/dataset-ops/SKILL.md` |
| Auto-annotation functions, `annotate_task`, `task auto-annotate`, native functions, Nuclio/serverless CPU/GPU models | `sub-skills/auto-annotation/SKILL.md` |
| Docker Compose, serverless overlay, admin user creation, `CVAT_HOST`, `CVAT_VERSION`, Helm/Kubernetes orientation, service failures | `sub-skills/deployment-admin/SKILL.md` |

## Repo-level references

- Read `references/cvat-overview.md` for the product surface, package map, optional extras, and workflow boundaries.
- Read `references/troubleshooting.md` for cross-cutting CVAT install/import/auth/version/service issues before drilling into a sub-skill.
- Read `references/repo-provenance.md` when checking whether this generated skill is stale for a newer CVAT checkout or package version.
- `references/repo-routing-metadata.json` is structured metadata for managed repo-skill routing.
- Run `scripts/cvat_env_check.py` for safe local package/CLI import checks; it does not contact a server unless extended by a user.

## Installation anchors

For automation against an existing CVAT server:

```bash
pip install cvat-sdk cvat-cli
```

Minimal verification after install:

```bash
python scripts/cvat_env_check.py --skip-cli-help
```

Use optional SDK extras only for selected workflows:

```bash
pip install "cvat-sdk[masks]"
pip install "cvat-sdk[pytorch]"
```

For self-hosted CVAT Community deployment, route to `sub-skills/deployment-admin/SKILL.md` before suggesting commands that start containers, build images, mutate databases, expose a host, or delete volumes.

## Safe defaults

- Prefer Personal Access Tokens and saved profiles over password strings in commands or code.
- Include the server URL scheme (`http://` or `https://`) and explicitly set organization context when operating in a team workspace.
- Treat task/project delete, annotation overwrite, import, backup restore, Docker volume removal, and serverless deployment as side-effecting operations.
- Use a tiny task/archive/image sample before scaling import/export, auto-annotation, or dataset conversion.
- Do not assume GPU/serverless/Docker availability from a Python SDK import check; those are separate backend/service gates.

## When not to use this skill

- Pure image modeling/augmentation tasks that do not involve CVAT data, APIs, CLI, annotation, or deployment.
- General Kubernetes/Docker administration with no CVAT-specific files, variables, or service names.
- Text annotation platform workflows unrelated to CVAT's computer-vision data model.
